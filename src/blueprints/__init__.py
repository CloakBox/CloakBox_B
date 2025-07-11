from .bp_system import system_bp

def register_blueprints(app):
    try:
        app.register_blueprint(system_bp)
    except Exception as e:
        print(f"Error registering blueprints: {e}")
        raise e