from flask import Blueprint, request, jsonify
from flask_restx import Resource
from extensions import db, app_logger, transaction_manager, jwt_manager, require_auth
import settings
from pydantic import ValidationError
from models.user_model.user import User
from models.user_model.user_ip import UserIp
from models.user_model.user_agent import UserAgent
from models.user_model.user_login_log import UserLoginLog
from models.user_model.user_register_dto import UserRegisterDTO
from service.user_logic import user_service
from swagger_config import user_ns
from models.user_model.user_schemas import (
    user_register_model, 
    user_login_model, 
    user_login_response_model,
)
from sqlalchemy import or_
from datetime import datetime, timezone
import time

# Blueprint 생성
user_bp = Blueprint("user", __name__, url_prefix=f'/{settings.API_PREFIX}')

@user_ns.route('/register')
class UserRegister(Resource):
    @user_ns.expect(user_register_model)
    @user_ns.response(201, 'Success', user_login_response_model)
    @user_ns.response(400, 'Bad Request')
    @user_ns.response(500, 'Internal Server Error')
    def post(self):
        """사용자 회원가입"""
        try:
            user_ip_str = request.remote_addr
            user_agent_str = request.headers.get('User-Agent', '')
            user_ip_record = UserIp.query.filter_by(ip_str=user_ip_str).first()
            if not user_ip_record:
                user_ip_record = UserIp(ip_str=user_ip_str)
                db.session.add(user_ip_record)
                db.session.flush()
            
            user_agent_record = UserAgent.query.filter_by(user_agent_str=user_agent_str).first()
            if not user_agent_record:
                user_agent_record = UserAgent(user_agent_str=user_agent_str)
                db.session.add(user_agent_record)
                db.session.flush()

            if not request.json:
                app_logger.warning("회원가입 요청: 요청 데이터 없음")
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다."
                }, 400
            
            # DTO를 사용한 입력 검증
            try:
                user_data = UserRegisterDTO(**request.json)
            except ValidationError as e:
                app_logger.warning(f"회원가입 요청: 입력 데이터 검증 실패 - {e.errors()}")
                return {
                    "status": "error",
                    "message": "입력 데이터 검증 실패",
                    "errors": e.errors()
                }, 400
            
            # 이메일과 이름 중복을 한 번에 확인
            existing_user = User.query.filter(
                or_(User.email == user_data.email, User.name == user_data.name)
            ).first()
            
            if existing_user:
                if existing_user.email == user_data.email:
                    app_logger.warning(f"회원가입 요청: 이미 존재하는 이메일 - {user_data.email}")
                    return {
                        "status": "error",
                        "message": "이미 존재하는 이메일입니다."
                    }, 400
                else:
                    app_logger.warning(f"회원가입 요청: 이미 존재하는 이름 - {user_data.name}")
                    return {
                        "status": "error",
                        "message": "이미 존재하는 이름입니다."
                    }, 400
            
            # 비밀번호 암호화
            hashed_password = user_service.hash_password(user_data.password)
            
            # 새 사용자 생성
            new_user = User(
                name=user_data.name,
                email=user_data.email,
                password=hashed_password
            )
            
            db.session.add(new_user)
            
            # 트랜잭션 매니저를 통한 안전한 커밋
            if transaction_manager.commit():
                new_user.user_ip_id = user_ip_record.id
                new_user.user_agent_id = user_agent_record.id
                db.session.commit()

                # 기존 로그인 로그 업데이트 또는 새로 생성
                existing_log = UserLoginLog.query.filter_by(user_id=new_user.id).first()
                
                if existing_log:
                    # 기존 로그 업데이트
                    existing_log.event_at = datetime.now(timezone.utc)
                    existing_log.event_at_unix = int(time.time())
                    existing_log.ip_id = user_ip_record.id
                    existing_log.user_agent_id = user_agent_record.id
                    db.session.commit()
                else:
                    # 새 로그 생성
                    user_login_log = UserLoginLog(
                        user_id=new_user.id,
                        ip_id=user_ip_record.id,
                        user_agent_id=user_agent_record.id
                    )
                    db.session.add(user_login_log)
                    db.session.commit()

                user_token = user_service.create_user_token(new_user)
                app_logger.info(f"회원가입 성공: {user_data.email}")
                return {
                    "status": "success",
                    "message": "회원가입이 완료되었습니다.",
                    "data": {
                        "access_token": user_token['access_token'],
                        "refresh_token": user_token['refresh_token'],
                        "token_type": "Bearer"
                    }
                }, 200
            else:
                app_logger.error("회원가입 커밋 실패")
                return {
                    "status": "error",
                    "message": "회원가입 중 오류가 발생했습니다."
                }, 500
            
        except Exception as e:
            app_logger.error(f"회원가입 중 오류: {str(e)}")
            transaction_manager.rollback()
            return {
                "status": "error",
                "message": f"회원가입 중 오류가 발생했습니다: {str(e)}"
            }, 500

@user_ns.route('/login')
class UserLogin(Resource):
    @user_ns.expect(user_login_model)
    @user_ns.response(200, 'Success', user_login_response_model)
    @user_ns.response(400, 'Bad Request')
    @user_ns.response(404, 'User Not Found')
    @user_ns.response(500, 'Internal Server Error')
    def post(self):
        """사용자 로그인"""
        try:
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

            # 요청 데이터 검증
            if not request.json:
                app_logger.warning("로그인 요청: 요청 데이터 없음")
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다."
                }, 400
            
            email = request.json.get('email')
            password = request.json.get('password')
            
            if not email or not password:
                app_logger.warning("로그인 요청: 이메일 또는 비밀번호 누락")
                return {
                    "status": "error",
                    "message": "이메일과 비밀번호를 입력해주세요."
                }, 400
            
            # 사용자 조회
            user = User.query.filter_by(email=email.lower()).first()
            if not user:
                app_logger.warning(f"로그인 시도: 존재하지 않는 사용자 - {email}")
                return {
                    "status": "error",
                    "message": "사용자를 찾을 수 없습니다."
                }, 404
            
            # 비밀번호 검증
            if not user_service.check_password_hash(password, user.password):
                app_logger.warning(f"로그인 시도: 잘못된 비밀번호 - {email}")
                return {
                    "status": "error",
                    "message": "비밀번호가 올바르지 않습니다."
                }, 401
            
            # 사용자 IP와 User-Agent 정보 업데이트
            user.user_ip_id = user_ip_record.id
            user.user_agent_id = user_agent_record.id
            
            # 기존 로그인 로그 업데이트 또는 새로 생성
            existing_log = UserLoginLog.query.filter_by(user_id=user.id).first()
            
            if existing_log:
                # 기존 로그 업데이트
                existing_log.event_at = datetime.now(timezone.utc)
                existing_log.event_at_unix = int(time.time())
                existing_log.ip_id = user_ip_record.id
                existing_log.user_agent_id = user_agent_record.id
                db.session.commit()

            else:
                # 새 로그 생성
                user_login_log = UserLoginLog(
                    user_id=user.id,
                    ip_id=user_ip_record.id,
                    user_agent_id=user_agent_record.id
                )
                db.session.add(user_login_log)
                db.session.commit()

            # 변경사항 커밋
            if not transaction_manager.commit():
                app_logger.error("로그인 시 사용자 정보 업데이트 실패")
                return {
                    "status": "error",
                    "message": "로그인 처리 중 오류가 발생했습니다."
                }, 500
            
            # JWT 토큰 생성
            token_data = {
                'email': user.email,
                'nickname': user.nickname
            }
            
            access_token = jwt_manager.create_access_token(token_data)
            refresh_token = jwt_manager.create_refresh_token(token_data)

            app_logger.info(f"로그인 성공: {email} (IP: {user_ip_str}, User-Agent: {user_agent_str[:50]}...)")
            return {
                "status": "success",
                "message": "로그인이 완료되었습니다.",
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }
            }, 200
        
        except Exception as e:
            app_logger.error(f"로그인 중 오류: {str(e)}")
            transaction_manager.rollback()
            return {
                "status": "error",
                "message": f"로그인 중 오류가 발생했습니다: {str(e)}"
            }, 500

@user_ns.route('/logout')
class UserLogout(Resource):
    @user_ns.doc(security='Bearer')
    @user_ns.response(200, 'Success')
    @user_ns.response(500, 'Internal Server Error')
    @require_auth
    def post(self):
        """사용자 로그아웃"""
        try:
            # Request에서 사용자 정보 추출
            user_info = jwt_manager.validate_request_and_extract_user()
            
            if not user_info:
                app_logger.warning("로그아웃 요청: 사용자 정보 추출 실패")
                return {
                    "status": "error",
                    "message": "유효하지 않은 토큰입니다."
                }, 401
            
            # 사용자 조회
            user = User.query.filter_by(email=user_info['email']).first()
            if not user:
                app_logger.warning(f"로그아웃 요청: 사용자를 찾을 수 없음 - {user_info['email']}")
                return {
                    "status": "error",
                    "message": "사용자를 찾을 수 없습니다."
                }, 404

            app_logger.info(f"로그아웃 요청 처리: {user_info['email']}")

            # IP 및 User-Agent 정보 처리
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
            
            # 로그아웃 로그 생성 (새로운 로그로 생성)
            user_login_log = UserLoginLog(
                user_id=user.id,
                event_type='LOGOUT',
                ip_id=user_ip_record.id,
                user_agent_id=user_agent_record.id
            )
            db.session.add(user_login_log)
            
            # 토큰 무효화
            if not jwt_manager.invalidate_request_token():
                app_logger.warning(f"토큰 무효화 실패: {user_info['email']}")
                return {
                    "status": "error",
                    "message": "로그아웃 처리 중 오류가 발생했습니다."
                }, 500
            
            # 변경사항 커밋
            if not transaction_manager.commit():
                app_logger.error("로그아웃 커밋 실패")
                return {
                    "status": "error",
                    "message": "로그아웃 중 오류가 발생했습니다."
                }, 500
            
            app_logger.info(f"로그아웃 완료: {user_info['email']}")

            return {
                "status": "success",
                "message": "로그아웃이 완료되었습니다.",
                "data": None
            }, 200

        except Exception as e:
            app_logger.error(f"로그아웃 중 오류: {str(e)}")
            transaction_manager.rollback()
            return {
                "status": "error",
                "message": f"로그아웃 중 오류가 발생했습니다: {str(e)}"
            }, 500