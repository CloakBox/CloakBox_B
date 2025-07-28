# 카카오 관련 모델들
from flask_restx import fields
from swagger_config import api

kakao_auth_model = api.model('KakaoAuth', {
    'scope': fields.String(description='카카오 권한 범위', example='account_email,profile_nickname'),
    'prompt': fields.String(description='카카오 인증 프롬프트', example='consent,login')
})

kakao_auth_success_model = api.model('KakaoAuthSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('KakaoAuthData', {
        'auth_url': fields.String(description='카카오 인증 URL'),
        'scope': fields.String(description='권한 범위'),
        'prompt': fields.String(description='인증 프롬프트')
    }))
})

kakao_login_success_model = api.model('KakaoLoginSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('KakaoLoginData', {
        'access_token': fields.String(description='JWT 액세스 토큰'),
        'refresh_token': fields.String(description='JWT 리프레시 토큰'),
        'token_type': fields.String(description='토큰 타입'),
        'kakao_info': fields.Nested(api.model('KakaoUserData', {
            'email': fields.String(description='카카오 이메일'),
            'nickname': fields.String(description='카카오 닉네임')
        }))
    }))
})

kakao_callback_model = api.model('KakaoCallback', {
    'code': fields.String(required=True, description='카카오 인증 코드', example='authorization_code_here')
})

kakao_callback_success_model = api.model('KakaoCallbackSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('KakaoCallbackData', {
        'is_need_info': fields.Boolean(description='사용자 정보 입력 여부'),
    }))
})

kakao_token_model = api.model('KakaoToken', {
    'refresh_token': fields.String(required=True, description='리프레시 토큰')
})

kakao_token_success_model = api.model('KakaoTokenSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('KakaoTokenData', {
        'access_token': fields.String(description='새로운 액세스 토큰'),
        'refresh_token': fields.String(description='새로운 리프레시 토큰'),
        'token_type': fields.String(description='토큰 타입'),
        'expires_in': fields.Integer(description='토큰 만료 시간'),
        'scope': fields.String(description='권한 범위')
    }))
})

kakao_user_info_model = api.model('KakaoUserInfo', {
    'access_token': fields.String(required=True, description='액세스 토큰')
})

kakao_user_info_success_model = api.model('KakaoUserInfoSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('KakaoUserInfoData', {
        'user_info': fields.Raw(description='사용자 정보'),
        'scopes_status': fields.Raw(description='권한 상태')
    }))
})

kakao_send_message_model = api.model('KakaoSendMessage', {
    'access_token': fields.String(required=True, description='액세스 토큰'),
    'message': fields.String(required=True, description='전송할 메시지'),
    'link_url': fields.String(description='링크 URL'),
    'friend_uuid': fields.String(description='친구 UUID (선택사항)')
})

kakao_send_message_success_model = api.model('KakaoSendMessageSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Nested(api.model('KakaoSendMessageData', {
        'success': fields.Boolean(description='전송 성공 여부'),
        'message_sent': fields.String(description='전송된 메시지'),
        'link_url': fields.String(description='링크 URL'),
        'friend_uuid': fields.String(description='친구 UUID')
    }))
})

kakao_debug_model = api.model('KakaoDebug', {
    'access_token': fields.String(description='액세스 토큰 (선택사항)')
})

kakao_debug_success_model = api.model('KakaoDebugSuccess', {
    'status': fields.String(description='응답 상태', example='success'),
    'message': fields.String(description='응답 메시지'),
    'data': fields.Raw(description='디버그 정보')
})