from flask import Flask, make_response, request
import waitress
from blueprints import register_blueprints
import settings

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

def start_api_server():
    print(" ### CloakBox API 서버를 시작합니다. ###")
    print(" ### 서버 주소: http://0.0.0.0:" + str(settings.DEV_PORT) + " ###")
    print(" ### 개발 모드로 실행 중. ###")
    
    try:
        waitress.serve(
            app, 
            host="0.0.0.0", 
            port=settings.DEV_PORT,
            threads=4
        )
    except Exception as e:
        print(f" ### 서버 실행 중 오류 발생: {e} ###")
        raise

def start_app():
    print(" ### 애플리케이션을 초기화합니다. ### ")
    
    # 블루프린트 등록
    register_blueprints(app)
    print(" ### 블루프린트 등록 완료 ###")
    
    # 서버 시작 (메인 스레드에서 실행)
    start_api_server()
    
if __name__ == "__main__":
    start_app()