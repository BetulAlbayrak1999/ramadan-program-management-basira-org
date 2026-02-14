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


def _convert_js_to_py(obj):
    """Convert JsProxy object to Python equivalent."""
    if obj is None:
        return None
    if hasattr(obj, 'to_py'):
        return obj.to_py()
    return obj


def _parse_sqlalchemy_condition(condition):
    """
    Parse a SQLAlchemy BinaryExpression/clause into (field, op, value) tuples
    or a raw SQL fragment dict.
    """
    # Handle SQLAlchemy BinaryExpression objects
    if hasattr(condition, 'left') and hasattr(condition, 'right'):
        # Get field name from left side
        left = condition.left
        field = None
        if hasattr(left, 'key'):
            field = left.key
        elif hasattr(left, 'name'):
            field = left.name

        if field is None:
            # Fallback to string parsing
            left_str = str(left)
            field = left_str.split('.')[-1]

        # Get operator
        op_obj = condition.operator
        op_name = op_obj.__name__ if hasattr(op_obj, '__name__') else str(op_obj)

        # Get value from right side
        right = condition.right
        if hasattr(right, 'effective_value'):
            value = right.effective_value
        elif hasattr(right, 'value'):
            value = right.value
        else:
            value = right

        # Convert date/datetime to string for D1
        if isinstance(value, date):
            value = value.isoformat()
        elif isinstance(value, datetime):
            value = value.isoformat()

        # Map SQLAlchemy operator names to SQL operators
        op_map = {
            'eq': '=',
            'ne': '!=',
            'lt': '<',
            'le': '<=',
            'gt': '>',
            'ge': '>=',
        }

        sql_op = op_map.get(op_name, '=')
        return [('param', field, sql_op, value)]

    # Handle ilike (case-insensitive LIKE)
    if hasattr(condition, 'clauses') or 'ilike' in str(type(condition)).lower():
        cond_str = str(condition)
        # Try to extract from compiled form
        if 'LIKE' in cond_str.upper():
            # Parse "table.field LIKE :value" style
            parts = cond_str.upper().split('LIKE')
            if len(parts) == 2:
                field = parts[0].strip().split('.')[-1].strip().lower()
                # The value is bound, try to extract it
                if hasattr(condition, 'right') and hasattr(condition.right, 'value'):
                    value = condition.right.value
                elif hasattr(condition, 'right') and hasattr(condition.right, 'effective_value'):
                    value = condition.right.effective_value
                else:
                    # Fallback: extract from string
                    val_part = parts[1].strip().strip("'\"").replace(':' + field + '_1', '%')
                    value = val_part
                return [('param', field, 'LIKE', value)]

    # Handle in_() clauses
    if hasattr(condition, 'clauses') and 'IN' in str(condition).upper():
        cond_str = str(condition)
        field_part = cond_str.split(' IN ')[0] if ' IN ' in cond_str.upper() else ''
        field = field_part.strip().split('.')[-1].strip()
        if hasattr(condition, 'right') and hasattr(condition.right, 'clauses'):
            values = []
            for clause in condition.right.clauses:
                if hasattr(clause, 'value'):
                    values.append(clause.value)
                elif hasattr(clause, 'effective_value'):
                    values.append(clause.effective_value)
            return [('in', field, values)]

    # Fallback: parse from string representation
    condition_str = str(condition)

    # Try comparison operators in order of specificity
    for op_str, sql_op in [('>=', '>='), ('<=', '<='), ('!=', '!='), ('==', '='), ('>', '>'), ('<', '<')]:
        if op_str in condition_str:
            parts = condition_str.split(op_str, 1)
            if len(parts) == 2:
                field = parts[0].strip().split('.')[-1].strip()
                raw_val = parts[1].strip().strip("'\"")
                # Try to parse as a bound parameter
                if raw_val.startswith(':'):
                    # It's a bound parameter, we can't extract the value this way
                    # but this shouldn't happen with our usage patterns
                    continue
                return [('param', field, sql_op, raw_val)]

    return []


class D1Query:
    """Query builder that mimics SQLAlchemy Query API for D1."""

    def __init__(self, session, model_class):
        self.session = session
        self.model_class = model_class
        self._filters = []  # list of ('param', field, op, value) or ('in', field, values) or ('raw', sql, params)
        self._order_by_clauses = []
        self._select_expr = '*'

    def filter_by(self, **kwargs):
        """Add WHERE conditions using keyword arguments."""
        for key, value in kwargs.items():
            if isinstance(value, date):
                value = value.isoformat()
            elif isinstance(value, datetime):
                value = value.isoformat()
            self._filters.append(('param', key, '=', value))
        return self

    def filter(self, *conditions):
        """Add WHERE conditions using SQLAlchemy-style expressions."""
        for condition in conditions:
            parsed = _parse_sqlalchemy_condition(condition)
            self._filters.extend(parsed)
        return self

    def order_by(self, *columns):
        """Add ORDER BY clauses."""
        for col in columns:
            # Check for SQLAlchemy desc() wrapper
            col_str = str(col)

            # Handle UnaryExpression (desc/asc)
            if hasattr(col, 'modifier'):
                # It's a desc() or asc() expression
                inner = col.element if hasattr(col, 'element') else col
                field_name = inner.key if hasattr(inner, 'key') else inner.name if hasattr(inner, 'name') else str(inner).split('.')[-1]
                modifier_str = str(col.modifier)
                if 'desc' in modifier_str.lower():
                    self._order_by_clauses.append(f"{field_name} DESC")
                else:
                    self._order_by_clauses.append(f"{field_name} ASC")
            elif 'DESC' in col_str.upper():
                # String-based detection fallback
                field = col_str.replace('DESC', '').replace('desc()', '').strip().split('.')[-1].strip()
                self._order_by_clauses.append(f"{field} DESC")
            else:
                field = col_str.split('.')[-1].strip()
                self._order_by_clauses.append(f"{field} ASC")
        return self

    async def first(self):
        """Get first result matching query."""
        results = await self._execute_query(limit=1)
        if results and len(results) > 0:
            return self._row_to_model(results[0])
        return None

    async def all(self):
        """Get all results matching query."""
        results = await self._execute_query()
        return [self._row_to_model(row) for row in results]

    async def count(self):
        """Get count of matching rows."""
        old_select = self._select_expr
        self._select_expr = 'COUNT(*) as cnt'
        try:
            results = await self._execute_query()
            if results and len(results) > 0:
                row = results[0]
                if isinstance(row, dict):
                    return row.get('cnt', 0)
                return 0
            return 0
        finally:
            self._select_expr = old_select

    async def scalar(self):
        """Get scalar value."""
        results = await self._execute_query(limit=1)
        if results and len(results) > 0:
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
            query = f"SELECT {self._select_expr} FROM {table_name}"

            # Add WHERE clauses
            params = []
            if self._filters:
                where_clauses = []
                for f in self._filters:
                    if f[0] == 'param':
                        _, field, op, value = f
                        where_clauses.append(f"{field} {op} ?")
                        params.append(value)
                    elif f[0] == 'in':
                        _, field, values = f
                        if values:
                            placeholders = ', '.join(['?'] * len(values))
                            where_clauses.append(f"{field} IN ({placeholders})")
                            params.extend(values)
                        else:
                            where_clauses.append("1 = 0")  # Empty IN -> no results
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

            # Add ORDER BY
            if self._order_by_clauses:
                query += " ORDER BY " + ", ".join(self._order_by_clauses)

            # Add LIMIT
            if limit:
                query += f" LIMIT {limit}"

            print(f"D1 Query: {query}")
            print(f"D1 Params: {params}")

            # Execute query
            db = self.session.db
            if params:
                stmt = db.prepare(query).bind(*params)
            else:
                stmt = db.prepare(query)

            result = await stmt.all()

            # Convert JsProxy to Python (Pyodide interop)
            result = _convert_js_to_py(result)

            # Handle different result formats
            if isinstance(result, dict):
                results = result.get('results', [])
            elif hasattr(result, 'results'):
                results = _convert_js_to_py(result.results)
            else:
                results = result if isinstance(result, list) else []

            # Ensure each row is a Python dict
            python_results = []
            for row in results:
                row = _convert_js_to_py(row)
                if isinstance(row, dict):
                    python_results.append(row)
                elif hasattr(row, 'items'):
                    python_results.append(dict(row))
                else:
                    try:
                        row_dict = {}
                        for key in dir(row):
                            if not key.startswith('_') and not callable(getattr(row, key, None)):
                                row_dict[key] = getattr(row, key, None)
                        if row_dict:
                            python_results.append(row_dict)
                        else:
                            python_results.append(row)
                    except:
                        python_results.append(row)

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
            obj = self.model_class()

            row = _convert_js_to_py(row)

            if isinstance(row, dict):
                for key, value in row.items():
                    if key == 'name' and 'full_name' not in row:
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
        self._pending_deletes = []

    def query(self, model_class):
        """Create a query for a model class."""
        return D1Query(self, model_class)

    async def get(self, model_class, obj_id):
        """Get object by primary key (mimics session.get(Model, id))."""
        if obj_id is None:
            return None
        table_name = model_class.__tablename__
        query = f"SELECT * FROM {table_name} WHERE id = ?"
        result = await self.db.prepare(query).bind(int(obj_id)).first()
        result = _convert_js_to_py(result)
        if not result:
            return None
        # Build model from row
        obj = model_class()
        if isinstance(result, dict):
            for key, value in result.items():
                if key == 'name' and 'full_name' not in result:
                    setattr(obj, 'full_name', value)
                else:
                    setattr(obj, key, value)
        return obj

    def add(self, obj):
        """Add an object to be inserted on commit."""
        self._pending_adds.append(obj)

    def delete(self, obj):
        """Mark an object for deletion on commit."""
        self._pending_deletes.append(obj)

    async def flush(self):
        """Flush pending changes (same as commit for D1)."""
        await self.commit()

    def rollback(self):
        """Rollback pending changes (clear pending ops)."""
        self._pending_adds.clear()
        self._pending_updates.clear()
        self._pending_deletes.clear()

    async def commit(self):
        """Commit all pending changes."""
        if self._closed:
            raise RuntimeError("Session is closed")

        try:
            # Process inserts
            for obj in self._pending_adds:
                await self._insert_object(obj)

            # Process updates
            for obj in self._pending_updates:
                await self._update_object(obj)

            # Process deletes
            for obj in self._pending_deletes:
                await self._delete_object(obj)

            # Clear pending operations
            self._pending_adds.clear()
            self._pending_updates.clear()
            self._pending_deletes.clear()

        except Exception as e:
            print(f"ERROR in commit: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
            raise

    async def refresh(self, obj):
        """Refresh an object from the database."""
        if self._closed:
            raise RuntimeError("Session is closed")

        try:
            table_name = obj.__tablename__
            obj_id = getattr(obj, 'id', None)

            if obj_id is None:
                return

            query = f"SELECT * FROM {table_name} WHERE id = ?"
            result = await self.db.prepare(query).bind(obj_id).first()
            result = _convert_js_to_py(result)

            if result and isinstance(result, dict):
                for key, value in result.items():
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

            columns = []
            values = []
            placeholders = []

            for key, value in obj.__dict__.items():
                if key.startswith('_') or key == 'id':
                    continue
                # Skip relationship attributes
                if hasattr(value, '__tablename__') or isinstance(value, list):
                    continue
                # Convert date/datetime to string
                if isinstance(value, date):
                    value = value.isoformat()
                elif isinstance(value, datetime):
                    value = value.isoformat()
                columns.append(key)
                values.append(value)
                placeholders.append('?')

            if not columns:
                return

            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

            print(f"D1 Insert Query: {query}")

            result = await self.db.prepare(query).bind(*values).run()

            result_py = _convert_js_to_py(result)

            # Set the ID on the object if returned
            last_row_id = None

            if isinstance(result_py, dict):
                meta = result_py.get('meta', {})
                last_row_id = meta.get('last_row_id')
            elif hasattr(result, 'meta'):
                meta = result.meta
                meta = _convert_js_to_py(meta)
                if isinstance(meta, dict):
                    last_row_id = meta.get('last_row_id')
                elif hasattr(meta, 'last_row_id'):
                    last_row_id = meta.last_row_id

            if last_row_id:
                obj.id = last_row_id

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

        set_clauses = []
        values = []

        for key, value in obj.__dict__.items():
            if key.startswith('_') or key == 'id':
                continue
            if hasattr(value, '__tablename__') or isinstance(value, list):
                continue
            if isinstance(value, date):
                value = value.isoformat()
            elif isinstance(value, datetime):
                value = value.isoformat()
            set_clauses.append(f"{key} = ?")
            values.append(value)

        if not set_clauses:
            return

        values.append(obj_id)

        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = ?"
        await self.db.prepare(query).bind(*values).run()

    async def _delete_object(self, obj):
        """Delete an object from the database."""
        table_name = obj.__tablename__
        obj_id = getattr(obj, 'id', None)

        if obj_id is None:
            return

        query = f"DELETE FROM {table_name} WHERE id = ?"
        await self.db.prepare(query).bind(obj_id).run()

    async def execute(self, query: str, params: Optional[List] = None):
        """Execute a raw SQL query."""
        if self._closed:
            raise RuntimeError("Session is closed")

        if params:
            result = await self.db.prepare(query).bind(*params).all()
        else:
            result = await self.db.prepare(query).all()

        return result

    async def execute_many(self, queries: List[str]):
        """Execute multiple queries in a batch."""
        if self._closed:
            raise RuntimeError("Session is closed")

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
    """Execute a single D1 query."""
    db = get_d1_binding()
    if not db:
        raise RuntimeError("D1 binding not available. Are you running in Cloudflare Workers?")

    if params:
        result = await db.prepare(query).bind(*params).all()
    else:
        result = await db.prepare(query).all()

    return result


async def execute_d1_batch(queries: List[str]) -> List[Any]:
    """Execute multiple D1 queries in a batch."""
    db = get_d1_binding()
    if not db:
        raise RuntimeError("D1 binding not available. Are you running in Cloudflare Workers?")

    statements = [db.prepare(q) for q in queries]
    results = await db.batch(statements)

    return results
