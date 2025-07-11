from flask import Flask, make_response, request
from blueprints import register_blueprints
import settings

def create_app():
    
    app = Flask(__name__)

    @app.before_request
    def handle_options_request():
        if request.method == "OPTIONS":
            return make_response('', 204)

    @app.after_request
    def add_cors_header(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    
    register_blueprints(app)
    return app

app = create_app()

if __name__ == "__main__":
    print(" ### CloakBox API 서버를 시작합니다. ###")
    print(" ### 서버 주소: http://0.0.0.0:" + str(settings.DEV_PORT) + " ###")
    print(" ### 개발 모드로 실행 중. ###")
    app.run(host="0.0.0.0", port=settings.DEV_PORT, debug=True)