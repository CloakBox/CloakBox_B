from flask import Blueprint, request, jsonify, make_response, redirect
from flask_restx import Resource
from extensions import db, app_logger
from models.user_model.user import User
from models.user_model.user_setting import UserSetting
import settings
from swagger_config import kakao_ns
from models.kakao_model.kakao_schemas import (
    kakao_auth_model,
    kakao_auth_success_model,
    kakao_callback_model,
    kakao_callback_success_model,
    kakao_token_model,
    kakao_token_success_model,
    kakao_user_info_model,
    kakao_user_info_success_model,
    kakao_send_message_model,
    kakao_send_message_success_model,
    kakao_debug_model,
    kakao_debug_success_model
)
from utils.kakao_manager import KaKaoManager
from service.user_logic.user_service import create_user_token
from datetime import datetime
import time
from utils import func

kakao_bp = Blueprint("kakao", __name__, url_prefix=f'/{settings.API_PREFIX}')

def create_or_update_user_kakao(kakao_account, user_ip_id, user_agent_id):
    """카카오 사용자 생성 또는 업데이트"""
    email = kakao_account['email'].lower()
    nickname = kakao_account.get('profile', {}).get('nickname', '')
    
    user = User.query.filter_by(email=email).first()
    is_need_info = False
    
    if not user:
        # 새 사용자 생성
        is_need_info = True
        
        new_user_setting = UserSetting(
            dark_mode='N',
            editor_mode='light',
            lang_cd='ko'
        )
        
        db.session.add(new_user_setting)
        db.session.flush()
        
        user = User(
            name=nickname or email.split('@')[0],
            email=email,
            nickname=nickname or email.split('@')[0],
            gender='',
            bio='',
            login_type='kakao',
            user_ip_id=user_ip_id,
            user_agent_id=user_agent_id,
            user_setting_id=new_user_setting.id
        )
        db.session.add(user)
        db.session.flush()
    else:
        # 기존 사용자 정보 업데이트
        user.user_ip_id = user_ip_id
        user.user_agent_id = user_agent_id
        user.login_type = 'kakao'
        if nickname and not user.nickname:
            user.nickname = nickname
    
    return user, is_need_info

def process_kakao_login(code, request_obj):
    """카카오 로그인 공통 처리"""
    # 사용자 IP와 User-Agent 정보 저장
    user_ip_id = func.get_user_ip(request_obj, db)
    user_agent_id = func.get_user_agent(request_obj, db)
    
    kakao_manager = KaKaoManager()
    
    # 1. 토큰 교환
    token_data = kakao_manager.exchange_code_for_token(code)
    access_token = token_data.get('access_token')
    
    # 2. 카카오 사용자 정보 조회
    kakao_user_info = kakao_manager.get_user_info(access_token)
    kakao_account = kakao_user_info.get('kakao_account', {})
    
    if not kakao_account.get('email'):
        raise ValueError("카카오 계정에서 이메일 정보를 가져올 수 없습니다.")
    
    # 3. 사용자 생성 또는 업데이트
    user, is_need_info = func.handle_database_operation(
        create_or_update_user_kakao, kakao_account, user_ip_id, user_agent_id
    )
    
    # 4. 로그인 로그 기록
    func.handle_database_operation(
        func.create_user_login_log, user.id, user_ip_id, user_agent_id
    )
    
    # 5. 커밋
    db.session.commit()
    
    # 6. JWT 토큰 생성
    user_token = create_user_token(user)
    
    return {
        'user': user,
        'tokens': user_token,
        'is_need_info': is_need_info,
        'kakao_info': {
            'email': kakao_account['email'],
            'nickname': kakao_account.get('profile', {}).get('nickname', '')
        }
    }

@kakao_ns.route('/login')
class KakaoLogin(Resource):
    @kakao_ns.expect(kakao_callback_model)
    @kakao_ns.response(200, 'Success')
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(401, 'Unauthorized')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 로그인 처리"""
        try:
            # 요청 데이터 검증
            is_valid, error_response = func.validate_request_json()
            if not is_valid:
                return error_response
            
            code = request.json.get('code')
            
            # 필수 필드 검증
            is_valid, error_response = func.validate_required_fields(
                request.json, ['code']
            )
            if not is_valid:
                return error_response
            
            # 카카오 로그인 처리
            result = process_kakao_login(code, request)
            
            app_logger.info(f"카카오 로그인 성공: {result['kakao_info']['email']}")
            return {
                "status": "success",
                "message": "카카오 로그인이 완료되었습니다.",
                "data": {
                    "access_token": result['tokens']['access_token'],
                    "refresh_token": result['tokens']['refresh_token'],
                    "token_type": "Bearer",
                    "kakao_info": result['kakao_info']
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"카카오 로그인 실패: {str(e)}")
            return func.create_error_response(str(e), "KAKAO_LOGIN_FAILED", 401)
        except Exception as e:
            app_logger.error(f"카카오 로그인 중 오류: {str(e)}")
            return func.create_error_response(
                f"카카오 로그인 중 오류가 발생했습니다: {str(e)}", 
                "INTERNAL_SERVER_ERROR", 
                500
            )

@kakao_ns.route('/auth')
class KakaoAuth(Resource):
    @kakao_ns.expect(kakao_auth_model)
    @kakao_ns.response(200, 'Success', kakao_auth_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 인증 URL 생성"""
        try:
            is_valid, error_response = func.validate_request_json()
            if not is_valid:
                return error_response
            
            scope = request.json.get('scope', 'profile_nickname,profile_image,account_email')
            prompt = request.json.get('prompt', 'login')
            
            kakao_manager = KaKaoManager()
            auth_url = kakao_manager.get_auth_url(scope=scope, prompt=prompt)
            
            return {
                "status": "success",
                "message": "카카오 인증 URL이 생성되었습니다.",
                "data": {
                    "auth_url": auth_url,
                    "scope": scope,
                    "prompt": prompt
                }
            }, 200
            
        except Exception as e:
            app_logger.error(f"카카오 인증 URL 생성 중 오류: {str(e)}")
            return func.create_error_response(
                f"카카오 인증 URL 생성 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@kakao_ns.route('/callback')
class KakaoCallback(Resource):
    @kakao_ns.response(200, 'Success')
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(500, 'Internal Server Error')
    def get(self):
        """카카오 인증 코드를 GET 방식으로 받아서 직접 토큰 처리"""
        try:
            code = request.args.get('code')
            
            if not code:
                return redirect(f"{settings.KAKAO_FRONTEND_CALLBACK_URL}?error=authorization_code_required")
            
            # 카카오 로그인 처리
            result = process_kakao_login(code, request)
            
            # 토큰을 쿠키에 설정하고 프론트엔드로 리디렉트
            response = make_response(redirect(settings.KAKAO_FRONTEND_CALLBACK_URL))
            
            # 토큰을 쿠키에 설정 (보안 강화)
            response.set_cookie(
                'access_token', 
                result['tokens']['access_token'], 
                max_age=30*60, 
                httponly=True, 
                secure=True, 
                samesite='Strict',
                path='/'
            )
            response.set_cookie(
                'refresh_token', 
                result['tokens']['refresh_token'], 
                max_age=24*60*60, 
                httponly=True, 
                secure=True, 
                samesite='Strict',
                path='/'
            )
            
            return response
            
        except Exception as e:
            app_logger.error(f"카카오 GET 콜백 처리 중 오류: {str(e)}")
            error_url = f"{settings.KAKAO_FRONTEND_CALLBACK_URL}?error=kakao_callback_error&message={str(e)}"
            return redirect(error_url)

    @kakao_ns.expect(kakao_callback_model)
    @kakao_ns.response(200, 'Success', kakao_callback_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(401, 'Unauthorized')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 인증 코드를 토큰으로 교환"""
        try:
            is_valid, error_response = func.validate_request_json()
            if not is_valid:
                return error_response
            
            code = request.json.get('code')
            
            is_valid, error_response = func.validate_required_fields(
                request.json, ['code']
            )
            if not is_valid:
                return error_response
            
            # 카카오 로그인 처리
            result = process_kakao_login(code, request)
            
            # 토큰을 헤더로 설정
            response = make_response({
                "status": "success",
                "message": "토큰 교환이 완료되었습니다.",
                "data": {
                    "is_need_info": result['is_need_info']
                }
            }, 200)
            
            # 토큰을 헤더에 추가
            response.headers['X-Access-Token'] = result['tokens']['access_token']
            response.headers['X-Refresh-Token'] = result['tokens']['refresh_token']
            
            return response
            
        except ValueError as e:
            app_logger.error(f"카카오 토큰 교환 실패: {str(e)}")
            return func.create_error_response(str(e), "TOKEN_EXCHANGE_FAILED", 401)
        except Exception as e:
            app_logger.error(f"카카오 토큰 교환 중 오류: {str(e)}")
            return func.create_error_response(
                f"카카오 토큰 교환 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@kakao_ns.route('/token/refresh')
class KakaoTokenRefresh(Resource):
    @kakao_ns.expect(kakao_token_model)
    @kakao_ns.response(200, 'Success', kakao_token_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(401, 'Unauthorized')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 토큰 갱신"""
        try:
            is_valid, error_response = func.validate_request_json()
            if not is_valid:
                return error_response
            
            refresh_token = request.json.get('refresh_token')
            
            is_valid, error_response = func.validate_required_fields(
                request.json, ['refresh_token']
            )
            if not is_valid:
                return error_response
            
            kakao_manager = KaKaoManager()
            token_data = kakao_manager.refresh_token(refresh_token)
            
            return {
                "status": "success",
                "message": "토큰이 갱신되었습니다.",
                "data": {
                    "access_token": token_data.get('access_token'),
                    "refresh_token": token_data.get('refresh_token'),
                    "token_type": token_data.get('token_type', 'bearer'),
                    "expires_in": token_data.get('expires_in'),
                    "scope": token_data.get('scope')
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"카카오 토큰 갱신 실패: {str(e)}")
            return func.create_error_response(str(e), "TOKEN_REFRESH_FAILED", 401)
        except Exception as e:
            app_logger.error(f"카카오 토큰 갱신 중 오류: {str(e)}")
            return func.create_error_response(
                f"카카오 토큰 갱신 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@kakao_ns.route('/user/info')
class KakaoUserInfo(Resource):
    @kakao_ns.expect(kakao_user_info_model)
    @kakao_ns.response(200, 'Success', kakao_user_info_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(401, 'Unauthorized')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 사용자 정보 조회"""
        try:
            is_valid, error_response = func.validate_request_json()
            if not is_valid:
                return error_response
            
            access_token = request.json.get('access_token')
            
            is_valid, error_response = func.validate_required_fields(
                request.json, ['access_token']
            )
            if not is_valid:
                return error_response
            
            kakao_manager = KaKaoManager()
            
            # 토큰 유효성 검사
            if not kakao_manager.validate_token(access_token):
                return func.create_error_response("유효하지 않은 토큰입니다.", "INVALID_TOKEN", 401)
            
            # 사용자 정보 조회
            user_info = kakao_manager.get_user_info(access_token)
            
            # 권한 확인
            scopes_status = kakao_manager.check_required_scope(access_token)
            
            return {
                "status": "success",
                "message": "사용자 정보가 조회되었습니다.",
                "data": {
                    "user_info": user_info,
                    "scopes_status": scopes_status
                }
            }, 200
            
        except Exception as e:
            app_logger.error(f"카카오 사용자 정보 조회 중 오류: {str(e)}")
            return func.create_error_response(
                f"카카오 사용자 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@kakao_ns.route('/message/send')
class KakaoSendMessage(Resource):
    @kakao_ns.expect(kakao_send_message_model)
    @kakao_ns.response(200, 'Success', kakao_send_message_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(401, 'Unauthorized')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 메시지 전송"""
        try:
            is_valid, error_response = func.validate_request_json()
            if not is_valid:
                return error_response
            
            access_token = request.json.get('access_token')
            message = request.json.get('message')
            link_url = request.json.get('link_url')
            friend_uuid = request.json.get('friend_uuid')
            
            is_valid, error_response = func.validate_required_fields(
                request.json, ['access_token', 'message']
            )
            if not is_valid:
                return error_response
            
            kakao_manager = KaKaoManager()
            
            # 토큰 유효성 검사
            if not kakao_manager.validate_token(access_token):
                return func.create_error_response("유효하지 않은 토큰입니다.", "INVALID_TOKEN", 401)
            
            success = False
            result_message = ""
            
            if friend_uuid:
                # 친구에게 메시지 전송
                success = kakao_manager.send_message_to_friend(
                    access_token, friend_uuid, message, link_url
                )
                result_message = "친구에게 메시지 전송" + (" 성공" if success else " 실패")
            else:
                # 나에게 메시지 전송
                success = kakao_manager.send_message_to_self(
                    access_token, message, link_url
                )
                result_message = "나에게 메시지 전송" + (" 성공" if success else " 실패")
            
            return {
                "status": "success" if success else "error",
                "message": result_message,
                "data": {
                    "success": success,
                    "message_sent": message,
                    "link_url": link_url,
                    "friend_uuid": friend_uuid
                }
            }, 200 if success else 500
            
        except Exception as e:
            app_logger.error(f"카카오 메시지 전송 중 오류: {str(e)}")
            return func.create_error_response(
                f"카카오 메시지 전송 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@kakao_ns.route('/debug')
class KakaoDebug(Resource):
    @kakao_ns.expect(kakao_debug_model)
    @kakao_ns.response(200, 'Success', kakao_debug_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 디버그 정보 조회"""
        try:
            access_token = None
            if request.json:
                access_token = request.json.get('access_token')
            
            kakao_manager = KaKaoManager()
            debug_info = kakao_manager.get_debug_info(access_token)
            
            return {
                "status": "success",
                "message": "디버그 정보가 조회되었습니다.",
                "data": debug_info
            }, 200
            
        except Exception as e:
            app_logger.error(f"카카오 디버그 정보 조회 중 오류: {str(e)}")
            return func.create_error_response(
                f"카카오 디버그 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )