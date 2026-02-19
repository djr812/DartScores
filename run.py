# run.py - Complete logging suppression
"""Run the Flask application"""
import os
import logging
from app import create_app

# ============================================
# COMPLETE LOGGING SUPPRESSION
# ============================================

def suppress_all_logging():
    """Suppress all non-error logging"""
    
    # 1. Get the root logger and set to ERROR only
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.ERROR)
    
    # 2. Remove all existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 3. Create a new handler that only shows ERROR and CRITICAL
    class ErrorOnlyFilter(logging.Filter):
        def filter(self, record):
            return record.levelno >= logging.ERROR
    
    # Create handler with filter
    handler = logging.StreamHandler()
    handler.setLevel(logging.ERROR)
    handler.addFilter(ErrorOnlyFilter())
    
    # Simple formatter for errors only
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    
    root_logger.addHandler(handler)
    
    # 4. Specifically target and disable SQLAlchemy loggers
    sqlalchemy_loggers = [
        'sqlalchemy',
        'sqlalchemy.engine',
        'sqlalchemy.pool',
        'sqlalchemy.dialects',
        'sqlalchemy.orm'
    ]
    
    for logger_name in sqlalchemy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)  # Only show errors
        logger.propagate = False  # Don't propagate to root
        # Remove all handlers from SQLAlchemy loggers
        for h in logger.handlers[:]:
            logger.removeHandler(h)
    
    # 5. Disable Werkzeug completely
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)
    werkzeug_logger.disabled = True
    werkzeug_logger.propagate = False
    
    # 6. Disable Flask logging
    flask_logger = logging.getLogger('flask')
    flask_logger.setLevel(logging.ERROR)
    flask_logger.propagate = False
    
    print("✅ Logging suppressed: Only ERROR messages will show")

# ============================================
# ALTERNATIVE: Use NullHandler for complete silence
# ============================================

def silence_all_logging():
    """Complete silence - no logs at all"""
    import logging
    
    # Create a null handler
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
    
    # Get root logger and remove all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add null handler
    null_handler = NullHandler()
    root_logger.addHandler(null_handler)
    root_logger.setLevel(logging.CRITICAL)  # Only show critical errors
    
    # Apply to all known loggers
    loggers_to_silence = [
        'werkzeug',
        'flask',
        'sqlalchemy',
        'sqlalchemy.engine',
        'sqlalchemy.pool',
        'sqlalchemy.orm',
        'urllib3',
        'requests'
    ]
    
    for logger_name in loggers_to_silence:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.addHandler(null_handler)
    
    print("🔇 Complete silence: No logs will be shown")

# ============================================
# CHOOSE YOUR LOGGING LEVEL
# ============================================

# Option A: Suppress all but errors (recommended)
suppress_all_logging()

# Option B: Complete silence (no logs at all)
# silence_all_logging()

# ============================================
# APPLICATION STARTUP
# ============================================

app = create_app()

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app with minimal output
    print("=" * 50)
    print("🎯 Darts Scoring System")
    print(f"📡 Running on http://0.0.0.0:{port}")
    print(f"🌐 Access at http://127.0.0.1:{port}")
    print("=" * 50)
    
    # Disable Flask's default startup message
    import flask.cli
    flask.cli.show_server_banner = lambda *args: None
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False,
        # Additional options to reduce output
        passthrough_errors=True
    )
