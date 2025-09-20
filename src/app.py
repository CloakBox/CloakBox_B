from flask import Flask, make_response, request
from extensions import init_extensions, tunnel_manager
import config
import settings
from swagger_config import api

def create_app() -> Flask:
    
    app = Flask(__name__)
    
    should_use_tunnel = config.Config.should_use_tunnel()

    if should_use_tunnel:
        try:
            # 기본 터널 생성
            tunnel = tunnel_manager.get_or_create_tunnel("default")
            if tunnel:
                # 터널링을 통해 데이터베이스 설정 업데이트
                config.update_database_config_with_tunnel(tunnel.local_port)
                
                # Flask 앱 설정
                app.config.from_object(config.config['default'])
                init_extensions(app)
                
                print(f"SSH 터널링을 통해 데이터베이스에 연결됨: localhost:{tunnel.local_port}")
                
            else:
                raise Exception("SSH 터널링 생성 실패")
                
        except Exception as e:
            print(f"SSH 터널링 설정 실패: {str(e)}")
            print("기본 데이터베이스 연결을 사용합니다.")
            # SSH 터널링 실패 시 기본 설정 사용
            app.config.from_object(config.config['default'])
            init_extensions(app)
    else:
        # 기본 설정 사용 (SSH 터널링 비활성화 시)
        print("SSH 터널링 비활성화 시 기본 설정 사용")
        app.config.from_object(config.config['default'])
        init_extensions(app)
    
    # @app.before_request
    # def handle_options_request():
    #     if request.method == "OPTIONS":
    #         return make_response('', 204)

    @app.after_request
    def add_cors_header(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "X-Access-Token, X-Refresh-Token"
        return response
    
    api.init_app(app)
    
    from blueprints import register_blueprints
    register_blueprints(app)
    return app

app = create_app()

if __name__ == '__main__':
    print(" ### CloakBox API 서버를 시작합니다. ###")
    print(" ### 서버 주소: http://0.0.0.0:" + str(settings.DEV_PORT) + " ###")
    print(" ### Swagger 문서: http://0.0.0.0:" + str(settings.DEV_PORT) + "/api/docs ###")
    print(" ### 개발 모드로 실행 중. ###")
    
    app.run(debug=settings.DEBUG_MODE > 0, port=settings.DEV_PORT)