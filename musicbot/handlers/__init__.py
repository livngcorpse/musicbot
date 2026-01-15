# Handlers package for Telegram Music Bot

def register_handlers(app):
    """Register all command handlers"""
    from .play import register_play_handler
    from .control import register_control_handlers
    from .queue import register_queue_handlers
    from .admin import register_admin_handlers
    
    # Register all handlers
    register_play_handler(app)
    register_control_handlers(app)
    register_queue_handlers(app)
    register_admin_handlers(app)
    
    print("All handlers registered successfully")