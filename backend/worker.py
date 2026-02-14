"""
Cloudflare Worker entry point for FastAPI application.
Uses function-based handler for maximum compatibility.

IMPORTANT: All imports are lazy-loaded to avoid hitting the 1000ms startup CPU limit.
"""

# Global flag
_app = None


async def on_fetch(request, env, ctx):
    """
    Main HTTP handler for Cloudflare Workers (function-based approach).
    Lazy-loads FastAPI app on first request to minimize startup time.
    Passes D1 binding to the app via request state.
    
    Note: Database initialization is handled by:
    - Cron job (runs every minute)
    - Manual trigger via POST /system/initialize-database
    """
    global _app
    
    # CRITICAL: Inject Cloudflare env variables into os.environ
    # In Cloudflare Workers, env vars are NOT in os.environ by default
    # They're only accessible via the env parameter
    import os
    for key in dir(env):
        if not key.startswith('_') and key != 'DB':  # Skip private attrs and DB binding
            value = getattr(env, key, None)
            if value is not None and isinstance(value, (str, int, float, bool)):
                os.environ[key] = str(value)
    
    # Lazy load app only on first request
    if _app is None:
        # Reload config to pick up injected env vars
        import importlib
        from app import config
        importlib.reload(config)
        
        from main import app
        _app = app
    
    # Set D1 binding BEFORE processing the request
    # This makes it available to all route handlers
    if hasattr(env, 'DB'):
        from app.d1_adapter import set_d1_binding
        set_d1_binding(env.DB)
        print(f"DEBUG: D1 binding set, available: {env.DB is not None}")
    else:
        print("DEBUG: No D1 binding found in env")
    
    # Use Cloudflare's ASGI bridge for FastAPI
    import asgi
    return await asgi.fetch(_app, request, env)


async def on_scheduled(event, env, ctx):
    """
    Cron trigger handler for scheduled tasks.
    
    Triggered by Cloudflare Cron (see wrangler.toml [triggers.crons]).
    Currently used for:
    - Auto-initialization of D1 database on first run
    - Daily health checks
    """
    # CRITICAL: Inject Cloudflare env variables into os.environ
    import os
    for key in dir(env):
        if not key.startswith('_') and key != 'DB':
            value = getattr(env, key, None)
            if value is not None and isinstance(value, (str, int, float, bool)):
                os.environ[key] = str(value)
    
    # Set D1 binding for this context
    if hasattr(env, 'DB'):
        from app.d1_adapter import set_d1_binding
        set_d1_binding(env.DB)
        
        from app.d1_initialization import is_d1_initialized, initialize_d1_database
        
        # Check if database is already initialized
        if not await is_d1_initialized():
            # First run - initialize the database
            print("Cron: D1 database not initialized, running initialization...")
            report = await initialize_d1_database()
            
            if report["success"]:
                print(f"Cron: D1 database initialized successfully - {report}")
            else:
                print(f"Cron: D1 database initialization failed - {report}")
        else:
            # Already initialized - just log health check
            print("Cron: D1 database already initialized, health check OK")
    else:
        print("Cron: No D1 binding available")

