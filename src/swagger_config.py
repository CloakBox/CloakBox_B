from flask_restx import Api
from flask import Blueprint

swagger_bp = Blueprint('swagger', __name__, url_prefix='/api/')

api = Api(
    swagger_bp,
    title='CloakBox API',
    version='1.0',
    description='CloakBox REST API 문서',
    doc='/docs',
    default='api',
    default_label='API 엔드포인트',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Bearer 토큰을 입력하세요. (예: Bearer <your-token>)',
        }
    },
    security='Bearer',
    validate=True,
    serve_challenge_on_401=True,
    catch_all_404s=True,
)

# 네임스페이스 정의
user_ns = api.namespace('user', description='사용자 관련 API')
system_ns = api.namespace('system', description='시스템 관련 API')

# 네임스페이스를 API에 등록
api.add_namespace(user_ns)
api.add_namespace(system_ns)