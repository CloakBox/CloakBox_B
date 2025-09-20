from flask import Blueprint, request, jsonify, make_response, redirect
from flask_restx import Resource
from extensions import db, app_logger
from models.user_model.user import User
from models.user_model.user_login_log import UserLoginLog
from models.user_model.user_setting import UserSetting
import settings
from swagger_config import google_ns
from models.google_model.google_schemas import (
    google_auth_model,
    google_auth_success_model,
    google_callback_model,
    google_callback_success_model,
    google_token_model,
    google_token_success_model,
    google_user_info_model,
    google_user_info_success_model,
    google_debug_model,
    google_debug_success_model
)
from utils.google_manager import GoogleManager
from service.user_logic.user_service import create_user_token
from datetime import datetime
import time
from utils import func

google_bp = Blueprint('google', __name__, url_prefix=f'/{settings.API_PREFIX}')

def create_user_login_log(user_id, user_ip_id, user_agent_id):
    """사용자 로그인 로그 생성 또는 업데이트"""
    existing_log = UserLoginLog.query.filter_by(user_id=user_id).first()
    
    if existing_log:
        existing_log.event_at = datetime.now()
        existing_log.event_at_unix = int(time.time())
        existing_log.ip_id = user_ip_id
        existing_log.user_agent_id = user_agent_id
    else:
        user_login_log = UserLoginLog(
            user_id=user_id,
            ip_id=user_ip_id,
            user_agent_id=user_agent_id
        )
        db.session.add(user_login_log)

def create_or_update_user_google(google_user_info, user_ip_id, user_agent_id):
    """구글 사용자 생성 또는 업데이트"""
    email = google_user_info['email'].lower()
    name = google_user_info.get('name', '')
    picture = google_user_info.get('picture', '')
    
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
            name=name or email.split('@')[0],
            email=email,
            nickname=name or email.split('@')[0],
            gender='',
            bio='',
            login_type='google',
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
        user.login_type = 'google'
        if name and not user.name:
            user.name = name
    
    return user, is_need_info

def process_google_login(code, request_obj):
    """구글 로그인 공통 처리"""
    # 사용자 IP와 User-Agent 정보 저장
    user_ip_id = func.get_user_ip(request_obj, db)
    user_agent_id = func.get_user_agent(request_obj, db)
    
    google_manager = GoogleManager()
    
    # 1. 토큰 교환
    token_data = google_manager.exchange_code_for_token(code)
    access_token = token_data.get('access_token')
    
    # 2. 구글 사용자 정보 조회
    google_user_info = google_manager.get_user_info(access_token)
    
    if not google_user_info.get('email'):
        raise ValueError("구글 계정에서 이메일 정보를 가져올 수 없습니다.")
    
    # 3. 사용자 생성 또는 업데이트
    user, is_need_info = func.handle_database_operation(
        create_or_update_user_google, google_user_info, user_ip_id, user_agent_id
    )
    
    # 4. 로그인 로그 기록
    func.handle_database_operation(
        create_user_login_log, user.id, user_ip_id, user_agent_id
    )
    
    # 5. 커밋
    db.session.commit()
    
    # 6. JWT 토큰 생성
    user_token = create_user_token(user)
    
    return {
        'user': user,
        'tokens': user_token,
        'is_need_info': is_need_info,
        'google_info': {
            'email': google_user_info['email'],
            'name': google_user_info.get('name', ''),
            'picture': google_user_info.get('picture', '')
        }
    }

@google_ns.route('/login')
class GoogleLogin(Resource):
    @google_ns.expect(google_callback_model)
    @google_ns.response(200, 'Success')
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(401, 'Unauthorized')
    @google_ns.response(404, 'User Not Found')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 로그인 처리"""
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
            
            # 구글 로그인 처리
            result = process_google_login(code, request)
            
            app_logger.info(f"구글 로그인 성공: {result['google_info']['email']}")
            return {
                "status": "success",
                "message": "구글 로그인이 완료되었습니다.",
                "data": {
                    "access_token": result['tokens']['access_token'],
                    "refresh_token": result['tokens']['refresh_token'],
                    "token_type": "Bearer",
                    "google_info": result['google_info']
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"구글 로그인 실패: {str(e)}")
            return func.create_error_response(str(e), "GOOGLE_LOGIN_FAILED", 401)
        except Exception as e:
            app_logger.error(f"구글 로그인 중 오류: {str(e)}")
            return func.create_error_response(
                f"구글 로그인 중 오류가 발생했습니다: {str(e)}", 
                "INTERNAL_SERVER_ERROR", 
                500
            )

@google_ns.route('/auth')
class GoogleAuth(Resource):
    @google_ns.expect(google_auth_model)
    @google_ns.response(200, 'Success', google_auth_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 인증 URL 생성"""
        try:
            is_valid, error_response = func.validate_request_json()
            if not is_valid:
                return error_response
            
            scope = request.json.get('scope', 'email profile')
            prompt = request.json.get('prompt', 'consent select_account')
            
            google_manager = GoogleManager()
            auth_url = google_manager.get_auth_url(scope=scope, prompt=prompt)
            
            return {
                "status": "success",
                "message": "구글 인증 URL이 생성되었습니다.",
                "data": {
                    "auth_url": auth_url,
                    "scope": scope,
                    "prompt": prompt
                }
            }, 200
            
        except Exception as e:
            app_logger.error(f"구글 인증 URL 생성 중 오류: {str(e)}")
            return func.create_error_response(
                f"구글 인증 URL 생성 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@google_ns.route('/callback')
class GoogleCallback(Resource):
    @google_ns.response(200, 'Success')
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(500, 'Internal Server Error')
    def get(self):
        """구글 인증 코드를 GET 방식으로 받아서 직접 토큰 처리"""
        try:
            code = request.args.get('code')
            
            if not code:
                return redirect(f"{settings.GOOGLE_FRONTEND_CALLBACK_URL}?error=authorization_code_required")
            
            # 구글 로그인 처리
            result = process_google_login(code, request)
            
            # 토큰을 쿠키에 설정하고 프론트엔드로 리디렉트
            response = make_response(redirect(settings.GOOGLE_FRONTEND_CALLBACK_URL))
            
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
            app_logger.error(f"구글 GET 콜백 처리 중 오류: {str(e)}")
            error_url = f"{settings.GOOGLE_FRONTEND_CALLBACK_URL}?error=google_callback_error&message={str(e)}"
            return redirect(error_url)

    @google_ns.expect(google_callback_model)
    @google_ns.response(200, 'Success', google_callback_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(401, 'Unauthorized')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 인증 코드를 토큰으로 교환"""
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
            
            # 구글 로그인 처리
            result = process_google_login(code, request)
            
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
            app_logger.error(f"구글 토큰 교환 실패: {str(e)}")
            return func.create_error_response(str(e), "TOKEN_EXCHANGE_FAILED", 401)
        except Exception as e:
            app_logger.error(f"구글 토큰 교환 중 오류: {str(e)}")
            return func.create_error_response(
                f"구글 토큰 교환 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@google_ns.route('/token/refresh')
class GoogleTokenRefresh(Resource):
    @google_ns.expect(google_token_model)
    @google_ns.response(200, 'Success', google_token_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(401, 'Unauthorized')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 토큰 갱신"""
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
            
            google_manager = GoogleManager()
            token_data = google_manager.refresh_token(refresh_token)
            
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
            app_logger.error(f"구글 토큰 갱신 실패: {str(e)}")
            return func.create_error_response(str(e), "TOKEN_REFRESH_FAILED", 401)
        except Exception as e:
            app_logger.error(f"구글 토큰 갱신 중 오류: {str(e)}")
            return func.create_error_response(
                f"구글 토큰 갱신 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@google_ns.route('/user/info')
class GoogleUserInfo(Resource):
    @google_ns.expect(google_user_info_model)
    @google_ns.response(200, 'Success', google_user_info_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(401, 'Unauthorized')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 사용자 정보 조회"""
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
            
            google_manager = GoogleManager()
            
            # 토큰 유효성 검사
            if not google_manager.validate_token(access_token):
                return func.create_error_response("유효하지 않은 토큰입니다.", "INVALID_TOKEN", 401)
            
            # 사용자 정보 조회
            user_info = google_manager.get_user_info(access_token)
            
            # 토큰 정보 조회
            token_info = google_manager.get_token_info(access_token)
            
            return {
                "status": "success",
                "message": "사용자 정보가 조회되었습니다.",
                "data": {
                    "user_info": user_info,
                    "scopes_status": {
                        "token_info": token_info,
                        "token_valid": True
                    }
                }
            }, 200
            
        except Exception as e:
            app_logger.error(f"구글 사용자 정보 조회 중 오류: {str(e)}")
            return func.create_error_response(
                f"구글 사용자 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@google_ns.route('/debug')
class GoogleDebug(Resource):
    @google_ns.expect(google_debug_model)
    @google_ns.response(200, 'Success', google_debug_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 디버그 정보 조회"""
        try:
            access_token = None
            if request.json:
                access_token = request.json.get('access_token')
            
            google_manager = GoogleManager()
            debug_info = google_manager.get_debug_info(access_token)
            
            return {
                "status": "success",
                "message": "디버그 정보가 조회되었습니다.",
                "data": debug_info
            }, 200
            
        except Exception as e:
            app_logger.error(f"구글 디버그 정보 조회 중 오류: {str(e)}")
            return func.create_error_response(
                f"구글 디버그 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )