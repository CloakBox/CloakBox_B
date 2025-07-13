from flask_restx import fields
from swagger_config import api

# 시스템 버전 응답 모델
system_version_model = api.model('SystemVersion', {
    'version': fields.String(required=True, description='API 버전', example='1.0.0'),
    'version_date': fields.String(required=True, description='버전 날짜', example='2025-01-01'),
})

# 시스템 상태 응답 모델
system_health_model = api.model('SystemHealth', {
    'status': fields.String(required=True, description='시스템 상태', example='healthy'),
    'message': fields.String(required=True, description='상태 메시지', example='시스템이 정상적으로 작동 중입니다.'),
})

# 일반 성공 응답 모델
success_response_model = api.model('SuccessResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='요청이 성공적으로 처리되었습니다.'),
    'data': fields.Raw(description='응답 데이터', example={})
})

# 에러 응답 모델
error_response_model = api.model('ErrorResponse', {
    'status': fields.String(required=True, description='에러 상태', example='error'),
    'message': fields.String(required=True, description='에러 메시지', example='요청 처리 중 오류가 발생했습니다.'),
    'error': fields.String(description='상세 에러 정보', example='Internal Server Error')
})