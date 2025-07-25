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

# 성공 응답 모델
certification_success_model = api.model('CertificationSuccess', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지'),
    'data': fields.Raw(description='응답 데이터'),
})

# 인증번호 전송 성공 응답 모델
send_certification_success_model = api.model('SendCertificationSuccess', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지'),
    'data': fields.Nested(api.model('SendCertificationData', {
        'expires_at': fields.String(description='만료 시간 (ISO 8601 형식)'),
    })),
})

# 인증번호 확인 성공 응답 모델
verify_certification_success_model = api.model('VerifyCertificationSuccess', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지'),
    'data': fields.Nested(api.model('VerifyCertificationData', {
        'access_token': fields.String(description='JWT 액세스 토큰'),
        'refresh_token': fields.String(description='JWT 리프레시 토큰'),
    })),
})