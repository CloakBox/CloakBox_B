from flask import Blueprint, request, jsonify
from flask_restx import Resource
from extensions import db, app_logger
from models.user_model.user import User
from models.user_model.user_ip import UserIp
from models.user_model.user_agent import UserAgent
from models.user_model.user_login_log import UserLoginLog
from typing import Dict, Any
import settings
from swagger_config import naver_ns
from pydantic import ValidationError
from models.naver_model.naver_schemas import (
    naver_auth_model,
    naver_auth_success_model,
    naver_callback_model,
    naver_callback_success_model,
    naver_token_model,
    naver_token_success_model,
    naver_user_info_model,
    naver_user_info_success_model,
    naver_debug_model,
    naver_debug_success_model
)
from utils.naver_manager import NaverManager
from service.user_logic.user_service import create_user_token
from datetime import datetime
import time

naver_bp = Blueprint("naver", __name__, url_prefix=f'/{settings.API_PREFIX}')

@naver_ns.route('/login')
class NaverLogin(Resource):
    @naver_ns.expect(naver_callback_model)
    @naver_ns.response(200, 'Success')
    @naver_ns.response(400, 'Bad Request')
    @naver_ns.response(401, 'Unauthorized')
    @naver_ns.response(500, 'Internal Server Error')
    def post(self):
        """네이버 로그인 처리"""
        try:
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            code = request.json.get('code')
            state = request.json.get('state')
            
            if not code:
                return {
                    "status": "error",
                    "message": "인증 코드가 필요합니다.",
                    "error": "Authorization code is required"
                }, 400
            
            if not state:
                return {
                    "status": "error",
                    "message": "상태값이 필요합니다.",
                    "error": "State parameter is required"
                }, 400
            
            # 사용자 IP와 User-Agent 정보 추출
            user_ip_str = request.remote_addr
            user_agent_str = request.headers.get('User-Agent', '')

            # IP 정보 저장 또는 조회
            user_ip_record = UserIp.query.filter_by(ip_str=user_ip_str).first()
            if not user_ip_record:
                user_ip_record = UserIp(ip_str=user_ip_str)
                db.session.add(user_ip_record)
                db.session.flush()

            # User-Agent 정보 저장 또는 조회
            user_agent_record = UserAgent.query.filter_by(user_agent_str=user_agent_str).first()
            if not user_agent_record:
                user_agent_record = UserAgent(user_agent_str=user_agent_str)
                db.session.add(user_agent_record)
                db.session.flush()
            
            naver_manager = NaverManager()
            
            # 1. 토큰 교환
            token_data = naver_manager.exchange_code_for_token(code, state)
            access_token = token_data.get('access_token')
            
            # 2. 네이버 사용자 정보 조회
            naver_user_info = naver_manager.get_user_info(access_token)
            response = naver_user_info.get('response', {})
            
            # 네이버 이메일이 없는 경우 처리
            if not response.get('email'):
                return {
                    "status": "error",
                    "message": "네이버 계정에서 이메일 정보를 가져올 수 없습니다.",
                    "error": "Email not available from Naver"
                }, 400
            
            email = response['email']
            nickname = response.get('nickname', '')
            name = response.get('name', '')
            
            # 3. 기존 사용자 확인 또는 새 사용자 생성
            user = User.query.filter_by(email=email.lower()).first()
            
            if not user:
                # 새 사용자 생성 (네이버 로그인 사용자)
                user = User(
                    name=name or nickname or email.split('@')[0],
                    email=email.lower(),
                    nickname=nickname or name or email.split('@')[0],
                    gender='',
                    bio='',
                    login_type='naver',
                    user_ip_id=user_ip_record.id,
                    user_agent_id=user_agent_record.id
                )
                db.session.add(user)
                db.session.flush()
            else:
                # 기존 사용자 정보 업데이트
                user.user_ip_id = user_ip_record.id
                user.user_agent_id = user_agent_record.id
                user.login_type = 'naver'
                if name and not user.name:
                    user.name = name
                if nickname and not user.nickname:
                    user.nickname = nickname

            # 4. 로그인 로그 기록
            existing_log = UserLoginLog.query.filter_by(user_id=user.id).first()
            
            if existing_log:
                existing_log.event_at = datetime.now()
                existing_log.event_at_unix = int(time.time())
                existing_log.ip_id = user_ip_record.id
                existing_log.user_agent_id = user_agent_record.id
            else:
                user_login_log = UserLoginLog(
                    user_id=user.id,
                    ip_id=user_ip_record.id,
                    user_agent_id=user_agent_record.id
                )
                db.session.add(user_login_log)
            
            db.session.commit()
            
            # 5. JWT 토큰 생성
            user_token = create_user_token(user)
            
            app_logger.info(f"네이버 로그인 성공: {email}")
            return {
                "status": "success",
                "message": "네이버 로그인이 완료되었습니다.",
                "data": {
                    "access_token": user_token['access_token'],
                    "refresh_token": user_token['refresh_token'],
                    "token_type": "Bearer",
                    "naver_info": {
                        "email": email,
                        "nickname": nickname,
                        "name": name
                    }
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"네이버 로그인 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Naver login failed"
            }, 401
        except Exception as e:
            app_logger.error(f"네이버 로그인 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"네이버 로그인 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@naver_ns.route('/auth')
class NaverAuth(Resource):
    @naver_ns.expect(naver_auth_model)
    @naver_ns.response(200, 'Success', naver_auth_success_model)
    @naver_ns.response(400, 'Bad Request')
    @naver_ns.response(500, 'Internal Server Error')
    def post(self):
        """네이버 인증 URL 생성"""
        try:
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            state = request.json.get('state')
            scope = request.json.get('scope', 'profile,email')
            
            naver_manager = NaverManager()
            auth_url, generated_state = naver_manager.get_auth_url(state=state, scope=scope)
            
            return {
                "status": "success",
                "message": "네이버 인증 URL이 생성되었습니다.",
                "data": {
                    "auth_url": auth_url,
                    "state": generated_state,
                    "scope": scope
                }
            }, 200
            
        except Exception as e:
            app_logger.error(f"네이버 인증 URL 생성 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"네이버 인증 URL 생성 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@naver_ns.route('/callback')
class NaverCallback(Resource):
    @naver_ns.expect(naver_callback_model)
    @naver_ns.response(200, 'Success', naver_callback_success_model)
    @naver_ns.response(400, 'Bad Request')
    @naver_ns.response(401, 'Unauthorized')
    @naver_ns.response(500, 'Internal Server Error')
    def post(self):
        """네이버 인증 코드를 토큰으로 교환"""
        try:
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            code = request.json.get('code')
            state = request.json.get('state')
            
            if not code:
                return {
                    "status": "error",
                    "message": "인증 코드가 필요합니다.",
                    "error": "Authorization code is required"
                }, 400
            
            if not state:
                return {
                    "status": "error",
                    "message": "상태값이 필요합니다.",
                    "error": "State parameter is required"
                }, 400
            
            naver_manager = NaverManager()
            token_data = naver_manager.exchange_code_for_token(code, state)
            
            return {
                "status": "success",
                "message": "토큰 교환이 완료되었습니다.",
                "data": {
                    "access_token": token_data.get('access_token'),
                    "refresh_token": token_data.get('refresh_token'),
                    "token_type": token_data.get('token_type', 'bearer'),
                    "expires_in": token_data.get('expires_in'),
                    "state": state
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"네이버 토큰 교환 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Token exchange failed"
            }, 401
        except Exception as e:
            app_logger.error(f"네이버 토큰 교환 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"네이버 토큰 교환 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@naver_ns.route('/token/refresh')
class NaverTokenRefresh(Resource):
    @naver_ns.expect(naver_token_model)
    @naver_ns.response(200, 'Success', naver_token_success_model)
    @naver_ns.response(400, 'Bad Request')
    @naver_ns.response(401, 'Unauthorized')
    @naver_ns.response(500, 'Internal Server Error')
    def post(self):
        """네이버 리프레시 토큰으로 액세스 토큰 갱신"""
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
            
            naver_manager = NaverManager()
            token_data = naver_manager.refresh_token(refresh_token)
            
            return {
                "status": "success",
                "message": "토큰 갱신이 완료되었습니다.",
                "data": {
                    "access_token": token_data.get('access_token'),
                    "refresh_token": token_data.get('refresh_token'),
                    "token_type": token_data.get('token_type', 'bearer'),
                    "expires_in": token_data.get('expires_in')
                }
            }, 200
            
        except ValueError as e:
            app_logger.error(f"네이버 토큰 갱신 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error": "Token refresh failed"
            }, 401
        except Exception as e:
            app_logger.error(f"네이버 토큰 갱신 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"네이버 토큰 갱신 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@naver_ns.route('/user/info')
class NaverUserInfo(Resource):
    @naver_ns.expect(naver_user_info_model)
    @naver_ns.response(200, 'Success', naver_user_info_success_model)
    @naver_ns.response(400, 'Bad Request')
    @naver_ns.response(401, 'Unauthorized')
    @naver_ns.response(500, 'Internal Server Error')
    def post(self):
        """네이버 사용자 정보 조회"""
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
            
            naver_manager = NaverManager()
            user_info = naver_manager.get_user_info(access_token)
            
            return {
                "status": "success",
                "message": "네이버 사용자 정보 조회가 완료되었습니다.",
                "data": {
                    "user_info": user_info
                }
            }, 200
            
        except Exception as e:
            app_logger.error(f"네이버 사용자 정보 조회 실패: {str(e)}")
            return {
                "status": "error",
                "message": f"네이버 사용자 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@naver_ns.route('/debug')
class NaverDebug(Resource):
    @naver_ns.expect(naver_debug_model)
    @naver_ns.response(200, 'Success', naver_debug_success_model)
    @naver_ns.response(400, 'Bad Request')
    @naver_ns.response(500, 'Internal Server Error')
    def post(self):
        """네이버 디버그 정보 조회"""
        try:
            access_token = None
            if request.json:
                access_token = request.json.get('access_token')
            
            naver_manager = NaverManager()
            debug_info = naver_manager.get_debug_info(access_token)
            
            return {
                "status": "success",
                "message": "네이버 디버그 정보 조회가 완료되었습니다.",
                "data": debug_info
            }, 200
            
        except Exception as e:
            app_logger.error(f"네이버 디버그 정보 조회 실패: {str(e)}")
            return {
                "status": "error",
                "message": f"네이버 디버그 정보 조회 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500