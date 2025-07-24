# 네이버 관련 모델들
from flask_restx import fields
from swagger_config import api

naver_auth_model = api.model('NaverAuth', {
    'state': fields.String(description='네이버 인증 상태값', example='random_state_string'),
    'scope': fields.String(description='네이버 권한 범위', example='profile,email')
})

naver_auth_success_model = api.model('NaverAuthSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('NaverAuthData', {
        'auth_url': fields.String(description='네이버 인증 URL'),
        'state': fields.String(description='인증 상태값'),
        'scope': fields.String(description='권한 범위')
    }))
})

naver_login_success_model = api.model('NaverLoginSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('NaverLoginData', {
        'access_token': fields.String(description='JWT 액세스 토큰'),
        'refresh_token': fields.String(description='JWT 리프레시 토큰'),
        'token_type': fields.String(description='토큰 타입'),
        'naver_info': fields.Nested(api.model('NaverUserData', {
            'email': fields.String(description='네이버 이메일'),
            'nickname': fields.String(description='네이버 닉네임'),
            'name': fields.String(description='네이버 이름')
        }))
    }))
})

naver_callback_model = api.model('NaverCallback', {
    'code': fields.String(required=True, description='네이버 인증 코드', example='authorization_code_here'),
    'state': fields.String(required=True, description='네이버 인증 상태값', example='state_value_here')
})

naver_callback_success_model = api.model('NaverCallbackSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('NaverCallbackData', {
        'is_need_info': fields.Boolean(description='사용자 정보 입력 여부'),
        'access_token': fields.String(description='JWT 액세스 토큰'),
        'refresh_token': fields.String(description='JWT 리프레시 토큰')
    }))
})

naver_token_model = api.model('NaverToken', {
    'refresh_token': fields.String(required=True, description='리프레시 토큰')
})

naver_token_success_model = api.model('NaverTokenSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('NaverTokenData', {
        'access_token': fields.String(description='새로운 액세스 토큰'),
        'refresh_token': fields.String(description='새로운 리프레시 토큰'),
        'token_type': fields.String(description='토큰 타입'),
        'expires_in': fields.Integer(description='토큰 만료 시간')
    }))
})

naver_user_info_model = api.model('NaverUserInfo', {
    'access_token': fields.String(required=True, description='액세스 토큰')
})

naver_user_info_success_model = api.model('NaverUserInfoSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('NaverUserInfoData', {
        'user_info': fields.Raw(description='사용자 정보')
    }))
})

naver_debug_model = api.model('NaverDebug', {
    'access_token': fields.String(description='액세스 토큰 (선택사항)')
})

naver_debug_success_model = api.model('NaverDebugSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Raw(description='디버그 정보')
})