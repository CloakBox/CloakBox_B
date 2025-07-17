# 구글 관련 모델들
from flask_restx import fields
from swagger_config import api

google_auth_model = api.model('GoogleAuth', {
    'scope': fields.String(description='구글 권한 범위', example='email profile'),
    'prompt': fields.String(description='구글 인증 프롬프트', example='consent select_account')
})

google_auth_success_model = api.model('GoogleAuthSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('GoogleAuthData', {
        'auth_url': fields.String(description='구글 인증 URL'),
        'scope': fields.String(description='권한 범위'),
        'prompt': fields.String(description='인증 프롬프트')
    }))
})

google_login_success_model = api.model('GoogleLoginSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('GoogleLoginData', {
        'access_token': fields.String(description='JWT 액세스 토큰'),
        'refresh_token': fields.String(description='JWT 리프레시 토큰'),
        'token_type': fields.String(description='토큰 타입'),
        'google_info': fields.Nested(api.model('GoogleUserData', {
            'email': fields.String(description='구글 이메일'),
            'name': fields.String(description='구글 이름'),
            'picture': fields.String(description='구글 프로필 사진')
        }))
    }))
})

google_callback_model = api.model('GoogleCallback', {
    'code': fields.String(required=True, description='구글 인증 코드', example='authorization_code_here')
})

google_callback_success_model = api.model('GoogleCallbackSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('GoogleCallbackData', {
        'access_token': fields.String(description='액세스 토큰'),
        'refresh_token': fields.String(description='리프레시 토큰'),
        'token_type': fields.String(description='토큰 타입'),
        'expires_in': fields.Integer(description='토큰 만료 시간'),
        'scope': fields.String(description='권한 범위')
    }))
})

google_token_model = api.model('GoogleToken', {
    'refresh_token': fields.String(required=True, description='리프레시 토큰')
})

google_token_success_model = api.model('GoogleTokenSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('GoogleTokenData', {
        'access_token': fields.String(description='새로운 액세스 토큰'),
        'refresh_token': fields.String(description='새로운 리프레시 토큰'),
        'token_type': fields.String(description='토큰 타입'),
        'expires_in': fields.Integer(description='토큰 만료 시간'),
        'scope': fields.String(description='권한 범위')
    }))
})

google_user_info_model = api.model('GoogleUserInfo', {
    'access_token': fields.String(required=True, description='액세스 토큰')
})

google_user_info_success_model = api.model('GoogleUserInfoSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('GoogleUserInfoData', {
        'user_info': fields.Raw(description='사용자 정보'),
        'scopes_status': fields.Raw(description='권한 상태')
    }))
})

google_debug_model = api.model('GoogleDebug', {
    'access_token': fields.String(description='액세스 토큰 (선택사항)')
})

google_debug_success_model = api.model('GoogleDebugSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Raw(description='디버그 정보')
})