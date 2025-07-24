from flask import Blueprint, request, jsonify
from flask_restx import Resource
from extensions import db, app_logger
from models.user_model.user import User
from models.user_model.user_login_log import UserLoginLog
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

@google_ns.route('/login')
class GoogleLogin(Resource):
    @google_ns.expect(google_callback_model)
    @google_ns.response(200, 'Success')
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(404, 'User Not Found')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """  구글 로그인 처리 """
        try:
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            code = request.json.get('code')
            if not code:
                return {
                    "status": "error",
                    "message": "구글 인증 코드가 없습니다.",
                    "error": "Google authentication code is missing"
                }, 400
            
            # 사용자 IP와 User-Agent 정보 저장
            user_ip_id = func.get_user_ip(request, db)
            user_agent_id = func.get_user_agent(request, db)
            
            google_manager = GoogleManager()

            # 1. 토큰 교환
            token_data = google_manager.exchange_code_for_token(code)
            access_token = token_data.get('access_token')
            
            # 2. 구글 사용자 정보 조회
            google_user_info = google_manager.get_user_info(access_token)
            
            email = google_user_info.get('email')
            name = google_user_info.get('name', '')
            picture = google_user_info.get('picture', '')
            
            if not email:
                return {
                    "status": "error",
                    "message": "구글 계정에서 이메일 정보를 가져올 수 없습니다.",
                    "error": "Email not available from Google"
                }, 400
            
            # 3. 기존 사용자 확인 또는 새 사용자 생성
            user = User.query.filter_by(email=email.lower()).first()
            
            if not user:
                return {
                    "status": "success",
                    "message": "유저가 존재하지 않습니다.",
                    "data": {
                        'is_exist': False,
                        'code': google_user_info
                    }
                }, 200
            
            # 4. 로그인 로그 기록
            existing_log = UserLoginLog.query.filter_by(user_id=user.id).first()
            
            if existing_log:
                existing_log.event_at = datetime.now()
                existing_log.event_at_unix = int(time.time())
                existing_log.ip_id = user_ip_id
                existing_log.user_agent_id = user_agent_id
            else:
                user_login_log = UserLoginLog(
                    user_id=user.id,
                    ip_id=user_ip_id,
                    user_agent_id=user_agent_id
                )
                db.session.add(user_login_log)
            
            db.session.commit()
            
            # 5. JWT 토큰 생성
            user_token = create_user_token(user)
            
            app_logger.info(f"구글 로그인 성공: {email}")
            return {
                "status": "success",
                "message": "구글 로그인이 완료되었습니다.",
                "data": {
                    "access_token": user_token['access_token'],
                    "refresh_token": user_token['refresh_token'],
                    "token_type": "Bearer",
                    "google_info": {
                        "email": email,
                        "name": name,
                        "picture": picture
                    }
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"구글 로그인 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Google login failed"
            }, 401
        except Exception as e:
            app_logger.error(f"구글 로그인 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"구글 로그인 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@google_ns.route('/auth')
class GoogleAuth(Resource):
    @google_ns.expect(google_auth_model)
    @google_ns.response(200, 'Success', google_auth_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 인증 URL 생성"""
        try:
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
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
            return {
                "status": "error",
                "message": f"구글 인증 URL 생성 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@google_ns.route('/callback')
class GoogleCallback(Resource):
    @google_ns.expect(google_callback_model)
    @google_ns.response(200, 'Success', google_callback_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(401, 'Unauthorized')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 인증 코드를 토큰으로 교환"""
        try:
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            code = request.json.get('code')
            if not code:
                return {
                    "status": "error",
                    "message": "인증 코드가 필요합니다.",
                    "error": "Authorization code is required"
                }, 400
            
            # 사용자 IP와 User-Agent 정보 저장
            user_ip_id = func.get_user_ip(request, db)
            user_agent_id = func.get_user_agent(request, db)
            
            # 1. 토큰 교환
            google_manager = GoogleManager()
            token_data = google_manager.exchange_code_for_token(code)
            
            access_token = token_data.get('access_token')
            
            # 2. 구글 사용자 정보 조회
            google_user_info = google_manager.get_user_info(access_token)
            
            email = google_user_info.get('email')
            name = google_user_info.get('name', '')
            
            if not email:
                return {
                    "status": "error",
                    "message": "구글 계정에서 이메일 정보를 가져올 수 없습니다.",
                    "error": "Email not available from Google"
                }, 400
            
            # 3. 기존 사용자 확인
            user = User.query.filter_by(email=email.lower()).first()
            
            is_need_info = False
            
            # 기존 사용자가 없으면 새로 생성
            if not user:
                is_need_info = True
                user = User(
                    name=name or email.split('@')[0],
                    email=email.lower(),
                    nickname='',
                    gender='',
                    bio='',
                    login_type='google',
                    user_ip_id=user_ip_id,
                    user_agent_id=user_agent_id
                )
                db.session.add(user)
                db.session.flush()
            
            # 4. 로그인 로그 기록
            existing_log = UserLoginLog.query.filter_by(user_id=user.id).first()
            
            if existing_log:
                existing_log.event_at = datetime.now()
                existing_log.event_at_unix = int(time.time())
                existing_log.ip_id = user_ip_id
                existing_log.user_agent_id = user_agent_id
            else:
                user_login_log = UserLoginLog(
                    user_id=user.id,
                    ip_id=user_ip_id,
                    user_agent_id=user_agent_id
                )
                db.session.add(user_login_log)
            
            db.session.commit()
            
            # 5. JWT 토큰 생성
            user_token = create_user_token(user)
            
            return {
                "status": "success",
                "message": "토큰 교환이 완료되었습니다.",
                "data": {
                    "is_need_info": is_need_info,
                    "access_token": user_token['access_token'],
                    "refresh_token": user_token['refresh_token']
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"구글 토큰 교환 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Token exchange failed"
            }, 401
        except Exception as e:
            app_logger.error(f"구글 토큰 교환 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"구글 토큰 교환 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@google_ns.route('/token/refresh')
class GoogleTokenRefresh(Resource):
    @google_ns.expect(google_token_model)
    @google_ns.response(200, 'Success', google_token_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(401, 'Unauthorized')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 리프레시 토큰으로 액세스 토큰 갱신"""
        try:
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            refresh_token = request.json.get('refresh_token')
            if not refresh_token:
                return {
                    "status": "error",
                    "message": "리프레시 토큰이 필요합니다.",
                    "error": "Refresh token is required"
                }, 400
            
            google_manager = GoogleManager()
            token_data = google_manager.refresh_token(refresh_token)
            
            return {
                "status": "success",
                "message": "토큰 갱신이 완료되었습니다.",
                "data": {
                    "access_token": token_data.get('access_token'),
                    "refresh_token": token_data.get('refresh_token'),
                    "token_type": token_data.get('token_type', 'Bearer'),
                    "expires_in": token_data.get('expires_in'),
                    "scope": token_data.get('scope')
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"구글 토큰 갱신 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Token refresh failed"
            }, 401
        except Exception as e:
            app_logger.error(f"구글 토큰 갱신 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"구글 토큰 갱신 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

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
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            access_token = request.json.get('access_token')
            if not access_token:
                return {
                    "status": "error",
                    "message": "액세스 토큰이 필요합니다.",
                    "error": "Access token is required"
                }, 400
            
            google_manager = GoogleManager()
            
            # 사용자 정보 조회
            user_info = google_manager.get_user_info(access_token)
            
            # 토큰 정보 조회
            token_info = google_manager.get_token_info(access_token)
            
            return {
                "status": "success",
                "message": "사용자 정보 조회가 완료되었습니다.",
                "data": {
                    "user_info": user_info,
                    "scopes_status": {
                        "token_info": token_info,
                        "token_valid": google_manager.validate_token(access_token)
                    }
                }
            }, 200
            
        except Exception as e:
            app_logger.error(f"구글 사용자 정보 조회 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"구글 사용자 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@google_ns.route('/debug')
class GoogleDebug(Resource):
    @google_ns.expect(google_debug_model)
    @google_ns.response(200, 'Success', google_debug_success_model)
    @google_ns.response(400, 'Bad Request')
    @google_ns.response(500, 'Internal Server Error')
    def post(self):
        """구글 디버그 정보 조회"""
        try:
            access_token = request.json.get('access_token') if request.json else None
            
            google_manager = GoogleManager()
            debug_info = google_manager.get_debug_info(access_token)
            
            return {
                "status": "success",
                "message": "디버그 정보 조회가 완료되었습니다.",
                "data": debug_info
            }, 200
            
        except Exception as e:
            app_logger.error(f"구글 디버그 정보 조회 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"구글 디버그 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500