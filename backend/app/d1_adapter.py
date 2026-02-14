"""
D1 Database Adapter for Cloudflare Workers.

This adapter provides a SQLAlchemy-like interface for D1 operations.
D1 is Cloudflare's serverless SQL database built on SQLite.
"""
from typing import Any, List, Dict, Optional, Type, Union
from contextvars import ContextVar
import json
from datetime import date, datetime

# Context variable to store D1 binding per request
_d1_binding: ContextVar[Optional[Any]] = ContextVar('d1_binding', default=None)


def set_d1_binding(db):
    """Set the D1 binding for the current request context."""
    _d1_binding.set(db)


def get_d1_binding():
    """Get the D1 binding for the current request context."""
    return _d1_binding.get()


class D1Query:
    """Query builder that mimics SQLAlchemy Query API for D1."""
    
    def __init__(self, session, model_class):
        self.session = session
        self.model_class = model_class
        self._filters = []
        self._order_by_clauses = []
        
    def filter_by(self, **kwargs):
        """Add WHERE conditions using keyword arguments."""
        for key, value in kwargs.items():
            self._filters.append((key, '=', value))
        return self
    
    def filter(self, *conditions):
        """Add WHERE conditions using SQLAlchemy-style expressions."""
        # For simple expressions like Model.field == value
        for condition in conditions:
            # Parse condition string representation
            condition_str = str(condition)
            # Handle basic == comparisons
            if '==' in condition_str:
                parts = condition_str.split('==')
                if len(parts) == 2:
                    field = parts[0].strip().split('.')[-1]
                    value = parts[1].strip().strip("'\"")
                    self._filters.append((field, '=', value))
            elif '!=' in condition_str:
                parts = condition_str.split('!=')
                if len(parts) == 2:
                    field = parts[0].strip().split('.')[-1]
                    value = parts[1].strip().strip("'\"")
                    self._filters.append((field, '!=', value))
        return self
    
    def order_by(self, *columns):
        """Add ORDER BY clauses."""
        for col in columns:
            col_str = str(col)
            # Handle desc() calls
            if 'desc()' in col_str or 'DESC' in col_str:
                field = col_str.split('.')[1].split()[0]
                self._order_by_clauses.append(f"{field} DESC")
            else:
                field = col_str.split('.')[-1]
                self._order_by_clauses.append(f"{field} ASC")
        return self
    
    def first(self):
        """Get first result matching query (returns awaitable)."""
        return self._first_async()
    
    async def _first_async(self):
        results = await self._execute_query(limit=1)
        if results and len(results) > 0:
            return self._row_to_model(results[0])
        return None
    
    def all(self):
        """Get all results matching query (returns awaitable)."""
        return self._all_async()
    
    async def _all_async(self):
        results = await self._execute_query()
        return [self._row_to_model(row) for row in results]
    
    def scalar(self):
        """Get scalar value (returns awaitable)."""
        return self._scalar_async()
    
    async def _scalar_async(self):
        results = await self._execute_query(limit=1)
        if results and len(results) > 0:
            # Return first column of first row
            first_row = results[0]
            if isinstance(first_row, dict):
                return list(first_row.values())[0]
            return first_row
        return None
    
    async def _execute_query(self, limit=None):
        """Execute the constructed query."""
        try:
            table_name = self.model_class.__tablename__
            
            # Build SELECT query
            query = f"SELECT * FROM {table_name}"
            
            # Add WHERE clauses
            params = []
            if self._filters:
                where_clauses = []
                for field, op, value in self._filters:
                    where_clauses.append(f"{field} {op} ?")
                    params.append(value)
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add ORDER BY
            if self._order_by_clauses:
                query += " ORDER BY " + ", ".join(self._order_by_clauses)
            
            # Add LIMIT
            if limit:
                query += f" LIMIT {limit}"
            
            # Log the query for debugging
            print(f"D1 Query: {query}")
            print(f"D1 Params: {params}")
            
            # Execute query
            db = self.session.db
            if params:
                stmt = db.prepare(query).bind(*params)
            else:
                stmt = db.prepare(query)
            
            result = await stmt.all()
            
            # Log the result type and structure
            print(f"D1 Result Type: {type(result)}")
            
            # Convert JsProxy to Python (Pyodide interop)
            try:
                # Check if we're in Pyodide environment
                import sys
                if 'pyodide' in sys.modules:
                    # Convert JavaScript object to Python
                    if hasattr(result, 'to_py'):
                        result = result.to_py()
                        print(f"D1 Result converted to Python: {type(result)}")
            except Exception as e:
                print(f"Note: Could not convert JsProxy (might not be needed): {e}")
            
            # Handle different result formats
            if isinstance(result, dict):
                results = result.get('results', [])
            elif hasattr(result, 'results'):
                # Handle JsProxy with results attribute
                results = result.results
                if hasattr(results, 'to_py'):
                    results = results.to_py()
            else:
                results = result if isinstance(result, list) else []
            
            # Ensure each row is a Python dict
            python_results = []
            for row in results:
                if hasattr(row, 'to_py'):
                    python_results.append(row.to_py())
                elif hasattr(row, 'items'):
                    python_results.append(dict(row))
                else:
                    # Try to convert JsProxy attributes to dict
                    try:
                        row_dict = {}
                        for key in dir(row):
                            if not key.startswith('_'):
                                row_dict[key] = getattr(row, key, None)
                        if row_dict:
                            python_results.append(row_dict)
                        else:
                            python_results.append(row)
                    except:
                        python_results.append(row)
            
            print(f"D1 Final Results ({len(python_results)} rows): {type(python_results[0]) if python_results else 'empty'}")
            return python_results
            
        except Exception as e:
            print(f"ERROR in _execute_query: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            raise
    
    def _row_to_model(self, row):
        """Convert database row to model instance."""
        if not row:
            return None
        
        try:
            # Create model instance
            obj = self.model_class()
            
            # Convert JsProxy to dict if needed
            if hasattr(row, 'to_py'):
                row = row.to_py()
            
            # Set attributes from row
            if isinstance(row, dict):
                for key, value in row.items():
                    # Handle column name mapping (D1 name -> SQLAlchemy attribute)
                    # Map 'name' to 'full_name' for User model
                    if key == 'name' and not 'full_name' in row:
                        setattr(obj, 'full_name', value)
                    else:
                        setattr(obj, key, value)
            elif hasattr(row, '__dict__'):
                for key, value in row.__dict__.items():
                    if not key.startswith('_'):
                        if key == 'name' and hasattr(obj, 'full_name'):
                            setattr(obj, 'full_name', value)
                        else:
                            setattr(obj, key, value)
            else:
                # Try to get attributes from JsProxy
                print(f"Row type: {type(row)}, attempting attribute extraction...")
                for key in dir(row):
                    if not key.startswith('_') and not callable(getattr(row, key, None)):
                        value = getattr(row, key, None)
                        if key == 'name' and hasattr(obj, 'full_name'):
                            setattr(obj, 'full_name', value)
                        else:
                            setattr(obj, key, value)
            
            return obj
            
        except Exception as e:
            print(f"ERROR in _row_to_model: {type(e).__name__}: {str(e)}")
            print(f"Row type: {type(row)}")
            print(f"Row content: {row}")
            import traceback
            print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            raise


class D1Session:
    """
    D1 database session that mimics SQLAlchemy's Session API.
    Uses D1's native API for database operations.
    """
    
    def __init__(self, db_binding):
        self.db = db_binding
        self._closed = False
        self._pending_adds = []
        self._pending_updates = []
    
    def query(self, model_class):
        """Create a query for a model class."""
        return D1Query(self, model_class)
    
    def add(self, obj):
        """Add an object to be inserted on commit."""
        self._pending_adds.append(obj)
    
    def commit(self):
        """Commit all pending changes (returns awaitable)."""
        return self._commit_async()
    
    async def _commit_async(self):
        if self._closed:
            raise RuntimeError("Session is closed")
        
        try:
            print(f"D1 Commit: {len(self._pending_adds)} adds, {len(self._pending_updates)} updates")
            
            # Process inserts
            for obj in self._pending_adds:
                await self._insert_object(obj)
            
            # Process updates
            for obj in self._pending_updates:
                await self._update_object(obj)
            
            # Clear pending operations
            self._pending_adds.clear()
            self._pending_updates.clear()
            
            print("D1 Commit: Complete")
            
        except Exception as e:
            print(f"ERROR in commit: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            raise
    
    def refresh(self, obj):
        """Refresh an object from the database (returns awaitable)."""
        return self._refresh_async(obj)
    
    async def _refresh_async(self, obj):
        if self._closed:
            raise RuntimeError("Session is closed")
        
        try:
            table_name = obj.__tablename__
            obj_id = getattr(obj, 'id', None)
            
            if obj_id is None:
                return
            
            query = f"SELECT * FROM {table_name} WHERE id = ?"
            result = await self.db.prepare(query).bind(obj_id).first()
            
            # Convert JsProxy to Python
            if result and hasattr(result, 'to_py'):
                result = result.to_py()
            
            if result:
                if isinstance(result, dict):
                    for key, value in result.items():
                        setattr(obj, key, value)
                else:
                    # Handle JsProxy attributes
                    for key in dir(result):
                        if not key.startswith('_') and not callable(getattr(result, key, None)):
                            value = getattr(result, key, None)
                            setattr(obj, key, value)
                            
        except Exception as e:
            print(f"ERROR in _refresh_async: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            raise
    
    async def _insert_object(self, obj):
        """Insert an object into the database."""
        try:
            table_name = obj.__tablename__
            
            print(f"D1 Insert: table={table_name}")
            
            # Get all attributes except id (auto-increment)
            columns = []
            values = []
            placeholders = []
            
            for key, value in obj.__dict__.items():
                if key.startswith('_') or key == 'id':
                    continue
                columns.append(key)
                values.append(value)
                placeholders.append('?')
            
            if not columns:
                print("D1 Insert: No columns to insert")
                return
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            print(f"D1 Insert Query: {query}")
            print(f"D1 Insert Values: {values}")
            
            result = await self.db.prepare(query).bind(*values).run()
            
            print(f"D1 Insert Result Type: {type(result)}")
            
            # Convert JsProxy to Python if needed
            if hasattr(result, 'to_py'):
                result_py = result.to_py()
                print(f"D1 Insert Result (Python): {result_py}")
            else:
                result_py = result
            
            # Set the ID on the object if returned
            # Try multiple ways to access last_row_id
            last_row_id = None
            
            if isinstance(result_py, dict):
                # If result is a dict, check for meta
                meta = result_py.get('meta', {})
                last_row_id = meta.get('last_row_id')
            elif hasattr(result, 'meta'):
                # JsProxy with meta attribute
                meta = result.meta
                if hasattr(meta, 'to_py'):
                    meta = meta.to_py()
                if isinstance(meta, dict):
                    last_row_id = meta.get('last_row_id')
                elif hasattr(meta, 'last_row_id'):
                    last_row_id = meta.last_row_id
            
            if last_row_id:
                obj.id = last_row_id
                print(f"D1 Insert: Set obj.id to {obj.id}")
                
        except Exception as e:
            print(f"ERROR in _insert_object: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            raise
    
    async def _update_object(self, obj):
        """Update an object in the database."""
        table_name = obj.__tablename__
        obj_id = getattr(obj, 'id', None)
        
        if obj_id is None:
            return
        
        # Get all attributes to update
        set_clauses = []
        values = []
        
        for key, value in obj.__dict__.items():
            if key.startswith('_') or key == 'id':
                continue
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        if not set_clauses:
            return
        
        values.append(obj_id)  # For WHERE clause
        
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = ?"
        await self.db.prepare(query).bind(*values).run()
    
    async def execute(self, query: str, params: Optional[List] = None):
        """Execute a raw SQL query."""
        if self._closed:
            raise RuntimeError("Session is closed")
        
        # D1 API call
        if params:
            result = await self.db.prepare(query).bind(*params).all()
        else:
            result = await self.db.prepare(query).all()
        
        return result
    
    async def execute_many(self, queries: List[str]):
        """Execute multiple queries in a batch."""
        if self._closed:
            raise RuntimeError("Session is closed")
        
        # D1 batch API
        statements = [self.db.prepare(q) for q in queries]
        results = await self.db.batch(statements)
        return results
    
    def close(self):
        """Close the session."""
        self._closed = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def is_d1_available() -> bool:
    """Check if D1 binding is available in current context."""
    return get_d1_binding() is not None


async def execute_d1_query(query: str, params: Optional[List] = None) -> Any:
    """
    Execute a single D1 query.
    
    Args:
        query: SQL query string
        params: Optional query parameters
    
    Returns:
        Query results
    """
    db = get_d1_binding()
    if not db:
        raise RuntimeError("D1 binding not available. Are you running in Cloudflare Workers?")
    
    if params:
        result = await db.prepare(query).bind(*params).all()
    else:
        result = await db.prepare(query).all()
    
    return result


async def execute_d1_batch(queries: List[str]) -> List[Any]:
    """
    Execute multiple D1 queries in a batch.
    
    Args:
        queries: List of SQL query strings
    
    Returns:
        List of query results
    """
    db = get_d1_binding()
    if not db:
        raise RuntimeError("D1 binding not available. Are you running in Cloudflare Workers?")
    
    statements = [db.prepare(q) for q in queries]
    results = await db.batch(statements)
    
    return results
