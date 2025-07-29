from flask_restx import fields
from swagger_config import api

# 사용자 등록 요청 모델
user_register_model = api.model('UserRegister', {
    'name': fields.String(required=True, description='사용자 이름', example='홍길동'),
    'email': fields.String(required=True, description='사용자 이메일', example='a@test.com'),
    'nickname': fields.String(required=False, description='사용자 닉네임', example='홍길동'),
    'gender': fields.String(required=False, description='성별', example='Woman, Man'),
    'bio': fields.String(required=False, description='자기소개', example='안녕하세요, 홍길동입니다.'),
})

# 사용자 로그인 요청 모델
user_login_model = api.model('UserLogin', {
    'email': fields.String(required=True, description='사용자 이메일', example='a@test.com'),
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

# 로그인 데이터 모델
user_login_data_model = api.model('UserLoginData', {
    'access_token': fields.String(description='액세스 토큰', example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
    'refresh_token': fields.String(description='리프레시 토큰', example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
    'token_type': fields.String(description='토큰 타입', example='Bearer')
})

# 로그인 응답 모델 (토큰 포함)
user_login_response_model = api.model('UserLoginResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='로그인 성공'),
    'data': fields.Nested(user_login_data_model, description='로그인 데이터')
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
    'message': fields.String(required=True, description='응답 메시지', example='로그아웃이 완료되었습니다.'),
    'data': fields.Raw(description='로그아웃 데이터', example=None)
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

# 사용자 프로필 데이터 모델 (먼저 정의)
user_profile_data_model = api.model('UserProfileData', {
    'id': fields.String(description='사용자 UUID', example='550e8400-e29b-41d4-a716-446655440000'),
    'name': fields.String(description='사용자 실명', example='홍길동'),
    'email': fields.String(description='사용자 이메일', example='hong@example.com'),
    'nickname': fields.String(description='사용자 닉네임', example='길동이'),
    'bio': fields.String(description='자기소개', example='안녕하세요, 홍길동입니다.'),
    'birth': fields.String(description='생년월일 (YYYY-MM-DD)', example='1990-01-01'),
    'gender': fields.String(description='성별', example='Man'),
    'login_type': fields.String(description='로그인 유형', example='email'),
    'login_yn': fields.Boolean(description='로그인 활성화 여부', example=True),
    'created_at': fields.String(description='계정 생성일시 (ISO 8601)', example='2025-01-01T12:00:00'),
    'updated_at': fields.String(description='계정 수정일시 (ISO 8601)', example='2025-01-18T12:00:00')
})

# 사용자 프로필 수정 요청 모델
user_profile_update_model = api.model('UserProfileUpdate', {
    'nickname': fields.String(required=False, description='닉네임 (1-255자)', example='새로운닉네임'),
    'gender': fields.String(required=False, description='성별', example='Man, Woman'),
    'bio': fields.String(required=False, description='자기소개', example='안녕하세요, 새로운 자기소개입니다.')
})

# 사용자 프로필 조회 응답 모델
user_profile_response_model = api.model('UserProfileResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='사용자 프로필 조회가 완료되었습니다.'),
    'data': fields.Nested(user_profile_data_model, description='사용자 프로필 데이터')
})

# 사용자 프로필 수정 성공 응답 모델
user_profile_update_response_model = api.model('UserProfileUpdateResponse', {
    'status': fields.String(required=True, description='응답 상태', example='success'),
    'message': fields.String(required=True, description='응답 메시지', example='사용자 프로필 수정이 완료되었습니다.'),
    'data': fields.Nested(user_profile_data_model, description='수정된 사용자 프로필 데이터')
})

# 프로필 관련 에러 응답 모델
profile_error_response_model = api.model('ProfileErrorResponse', {
    'status': fields.String(required=True, description='에러 상태', example='error'),
    'message': fields.String(required=True, description='에러 메시지', example='사용자 프로필 조회 중 오류가 발생했습니다: 사용자를 찾을 수 없습니다.'),
})

# 인증 에러 응답 모델  
auth_error_response_model = api.model('AuthErrorResponse', {
    'status': fields.String(required=True, description='에러 상태', example='error'),
    'message': fields.String(required=True, description='에러 메시지', example='유효하지 않은 토큰입니다.'),
})

# 입력 검증 에러 응답 모델
validation_error_response_model = api.model('ValidationErrorResponse', {
    'status': fields.String(required=True, description='에러 상태', example='error'),
    'message': fields.String(required=True, description='에러 메시지', example='입력 데이터 검증 실패'),
    'errors': fields.Raw(description='상세 에러 정보', example=[{
        'type': 'string_too_short',
        'loc': ['nickname'],
        'msg': 'String should have at least 1 character',
        'input': '',
        'ctx': {'min_length': 1}
    }])
})