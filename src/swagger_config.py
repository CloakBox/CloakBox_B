# src/swagger_config.py
from flask_restx import Api

api = Api(
    title='CloakBox API',
    version='1.0',
    description='CloakBox REST API 문서',
    doc='/api/docs',
    prefix='/v1',
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

user_ns = api.namespace('user', description='사용자 관련 API')
system_ns = api.namespace('system', description='시스템 관련 API')
certification_ns = api.namespace('certification', description='인증 관련 API')