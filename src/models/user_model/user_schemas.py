from flask_restx import fields
from swagger_config import api

# 사용자 등록 요청 모델
user_register_model = api.model('UserRegister', {
    'name': fields.String(required=True, description='사용자 이름', example='홍길동'),
    'email': fields.String(required=True, description='사용자 이메일', example='a@test.com'),
    'password': fields.String(required=True, description='사용자 비밀번호', example='password'),
})

# 사용자 로그인 요청 모델
user_login_model = api.model('UserLogin', {
    'email': fields.String(required=True, description='사용자 이메일', example='a@test.com'),
    'password': fields.String(required=True, description='사용자 비밀번호', example='password'),
})

# 사용자 정보 모델
user_info_model = api.model('UserInfo', {
    'id': fields.String(required=True, description='사용자 ID', example='1'),
    'name': fields.String(required=True, description='사용자 이름', example='홍길동'),
    'email': fields.String(required=True, description='사용자 이메일', example='a@test.com'),
    'created_at': fields.String(description='생성일시', example='2025-01-01T00:00:00'),
})

# 사용자 응답 모델
user_response_model = api.model('UserResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='사용자 등록 성공'),
    'data': fields.Nested(user_info_model, description='사용자 데이터')
})

# 로그인 응답 모델 (토큰 포함)
user_login_response_model = api.model('UserLoginResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='로그인 성공'),
    'data': fields.Nested(api.model('UserLoginData', {
        'id': fields.String(required=True, description='사용자 ID', example='1'),
        'name': fields.String(required=True, description='사용자 이름', example='홍길동'),
        'email': fields.String(required=True, description='사용자 이메일', example='a@test.com'),
        'access_token': fields.String(description='액세스 토큰', example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
        'refresh_token': fields.String(description='리프레시 토큰', example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
        'token_type': fields.String(description='토큰 타입', example='Bearer')
    }), description='로그인 데이터')
})

# 로그인 실패 응답 모델
user_login_error_response_model = api.model('UserLoginErrorResponse', {
    'status': fields.String(required=True, description='응답 상태', example='error'),
    'message': fields.String(required=True, description='응답 메시지', example='로그인 실패'),
    'error': fields.String(required=True, description='상세 에러 정보', example='이메일 또는 비밀번호가 일치하지 않습니다.')
})

# 로그아웃 응답 모델
user_logout_response_model = api.model('UserLogoutResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='로그아웃 성공'),
    'data': fields.Raw(description='로그아웃 데이터', example={})
})

# 토큰 인증 에러 모델
token_auth_error_model = api.model('TokenAuthError', {
    'status': fields.String(required=True, description='에러 상태', example='error'),
    'message': fields.String(required=True, description='에러 메시지', example='토큰 인증 실패'),
    'error': fields.String(required=True, description='상세 에러 정보', example='토큰이 만료되었습니다.')
})

# 에러 응답 모델
error_response_model = api.model('ErrorResponse', {
    'status': fields.String(required=True, description='에러 상태', example='error'),
    'message': fields.String(required=True, description='에러 메시지', example='사용자 등록 실패'),
    'errors': fields.Raw(description='상세 에러 정보', example={})
})