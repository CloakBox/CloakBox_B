from .bp_system import system_bp
from .bp_user import user_bp
from .bp_certification import certification_bp
from .bp_kakao import kakao_bp
from .bp_google import google_bp

def register_blueprints(app):
    try:
        app.register_blueprint(system_bp)
        app.register_blueprint(user_bp)
        app.register_blueprint(certification_bp)
        app.register_blueprint(kakao_bp)
        app.register_blueprint(google_bp)
    except Exception as e:
        print(f"Error registering blueprints: {e}")
        raise e