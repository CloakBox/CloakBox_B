from flask import Blueprint, request, jsonify
from flask_restx import Resource
from extensions import db, app_logger
from models.user_model.user import User
from models.user_model.user_login_log import UserLoginLog
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

            kakao_manager = KaKaoManager()
            
            # 1. 토큰 교환
            token_data = kakao_manager.exchange_code_for_token(code)
            access_token = token_data.get('access_token')
            
            # 2. 카카오 사용자 정보 조회
            kakao_user_info = kakao_manager.get_user_info(access_token)
            kakao_account = kakao_user_info.get('kakao_account', {})
            
            # 카카오 이메일이 없는 경우 처리
            if not kakao_account.get('email'):
                return {
                    "status": "error",
                    "message": "카카오 계정에서 이메일 정보를 가져올 수 없습니다.",
                    "error": "Email not available from Kakao"
                }, 400
            
            email = kakao_account['email']
            nickname = kakao_account.get('profile', {}).get('nickname', '')
            
            # 3. 기존 사용자 확인 또는 새 사용자 생성
            user = User.query.filter_by(email=email.lower()).first()
            
            if not user:
                # 새 사용자 생성 (카카오 로그인 사용자)
                user = User(
                    name=nickname or email.split('@')[0],
                    email=email.lower(),
                    nickname=nickname or email.split('@')[0],
                    gender='',
                    bio='',
                    login_type='kakao',
                    user_ip_id=user_ip_id,
                    user_agent_id=user_agent_id
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
            
            app_logger.info(f"카카오 로그인 성공: {email}")
            return {
                "status": "success",
                "message": "카카오 로그인이 완료되었습니다.",
                "data": {
                    "access_token": user_token['access_token'],
                    "refresh_token": user_token['refresh_token'],
                    "token_type": "Bearer",
                    "kakao_info": {
                        "email": email,
                        "nickname": nickname
                    }
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"카카오 로그인 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Kakao login failed"
            }, 401
        except Exception as e:
            app_logger.error(f"카카오 로그인 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"카카오 로그인 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@kakao_ns.route('/auth')
class KakaoAuth(Resource):
    @kakao_ns.expect(kakao_auth_model)
    @kakao_ns.response(200, 'Success', kakao_auth_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 인증 URL 생성"""
        try:
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            scope = request.json.get('scope', 'friends,talk_message')
            prompt = request.json.get('prompt', 'consent,login')
            
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
            return {
                "status": "error",
                "message": f"카카오 인증 URL 생성 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@kakao_ns.route('/callback')
class KakaoCallback(Resource):
    @kakao_ns.expect(kakao_callback_model)
    @kakao_ns.response(200, 'Success', kakao_callback_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(401, 'Unauthorized')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 인증 코드를 토큰으로 교환"""
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
            kakao_manager = KaKaoManager()
            token_data = kakao_manager.exchange_code_for_token(code)
            
            access_token = token_data.get('access_token')
            
            # 2. 카카오 사용자 정보 조회
            kakao_user_info = kakao_manager.get_user_info(access_token)
            
            kakao_account = kakao_user_info.get('kakao_account', {})
            email = kakao_account.get('email')
            name = kakao_account.get('profile', {}).get('nickname', '')
            
            if not email:
                return {
                    "status": "error",
                    "message": "카카오 계정에서 이메일 정보를 가져올 수 없습니다.",
                    "error": "Email not available from Kakao"
                }, 400
            
            # 3. 기존 사용자 확인
            user = User.query.filter_by(email=email.lower()).first()
            
            is_need_info = False
            
            if not user:
                # 새 사용자 생성 (카카오 로그인 사용자)
                is_need_info = True
                user = User(
                    name=name or email.split('@')[0],
                    email=email.lower(),
                    nickname='',
                    gender='',
                    bio='',
                    login_type='kakao',
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
            app_logger.error(f"토큰 교환 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Token exchange failed"
            }, 401
        except Exception as e:
            app_logger.error(f"카카오 콜백 처리 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"카카오 콜백 처리 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

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
            app_logger.error(f"토큰 갱신 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Token refresh failed"
            }, 401
        except Exception as e:
            app_logger.error(f"토큰 갱신 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"토큰 갱신 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

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
            
            kakao_manager = KaKaoManager()
            
            # 토큰 유효성 검사
            if not kakao_manager.validate_token(access_token):
                return {
                    "status": "error",
                    "message": "유효하지 않은 토큰입니다.",
                    "error": "Invalid token"
                }, 401
            
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
            app_logger.error(f"사용자 정보 조회 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"사용자 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

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
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            access_token = request.json.get('access_token')
            message = request.json.get('message')
            link_url = request.json.get('link_url')
            friend_uuid = request.json.get('friend_uuid')
            
            if not access_token or not message:
                return {
                    "status": "error",
                    "message": "액세스 토큰과 메시지가 필요합니다.",
                    "error": "Access token and message are required"
                }, 400
            
            kakao_manager = KaKaoManager()
            
            # 토큰 유효성 검사
            if not kakao_manager.validate_token(access_token):
                return {
                    "status": "error",
                    "message": "유효하지 않은 토큰입니다.",
                    "error": "Invalid token"
                }, 401
            
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
            app_logger.error(f"메시지 전송 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"메시지 전송 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@kakao_ns.route('/debug')
class KakaoDebug(Resource):
    @kakao_ns.expect(kakao_debug_model)
    @kakao_ns.response(200, 'Success', kakao_debug_success_model)
    @kakao_ns.response(400, 'Bad Request')
    @kakao_ns.response(500, 'Internal Server Error')
    def post(self):
        """카카오 디버그 정보 조회"""
        try:
            access_token = request.json.get('access_token') if request.json else None
            
            kakao_manager = KaKaoManager()
            debug_info = kakao_manager.get_debug_info(access_token)
            
            return {
                "status": "success",
                "message": "디버그 정보가 조회되었습니다.",
                "data": debug_info
            }, 200
            
        except Exception as e:
            app_logger.error(f"디버그 정보 조회 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"디버그 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500