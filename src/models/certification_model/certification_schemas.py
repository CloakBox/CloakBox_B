from flask_restx import fields
from swagger_config import api

# 인증번호 전송 요청 모델
send_certification_code_model = api.model('SendCertificationCode', {
    'email': fields.String(required=True, description='인증번호를 받을 이메일', example='user@example.com'),
})

# 인증번호 확인 요청 모델
verify_certification_code_model = api.model('VerifyCertificationCode', {
    'email': fields.String(required=True, description='인증번호를 받은 이메일', example='user@example.com'),
    'code': fields.String(required=True, description='인증번호', example='123456'),
})

# 인증번호 전송 응답 모델
send_certification_response_model = api.model('SendCertificationResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='인증번호가 전송되었습니다.'),
    'data': fields.Nested(api.model('SendCertificationData', {
        'email': fields.String(description='이메일', example='user@example.com'),
        'user_uuid': fields.String(description='사용자 UUID', example='123e4567-e89b-12d3-a456-426614174000'),
        'expires_at': fields.String(description='만료 시간', example='2025-01-01T00:05:00'),
    }), description='인증번호 전송 데이터')
})

# 인증번호 확인 응답 모델
verify_certification_response_model = api.model('VerifyCertificationResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='인증번호가 확인되었습니다.'),
    'data': fields.Nested(api.model('VerifyCertificationData', {
        'email': fields.String(description='이메일', example='user@example.com'),
        'user_uuid': fields.String(description='사용자 UUID', example='123e4567-e89b-12d3-a456-426614174000'),
        'verified': fields.Boolean(description='인증 완료 여부', example=True),
    }), description='인증번호 확인 데이터')
})

# 에러 응답 모델
certification_error_response_model = api.model('CertificationErrorResponse', {
    'status': fields.String(required=True, description='응답 상태', example='error'),
    'message': fields.String(required=True, description='응답 메시지', example='에러가 발생했습니다.'),
    'error': fields.String(required=True, description='상세 에러 정보', example='에러 메시지')
})