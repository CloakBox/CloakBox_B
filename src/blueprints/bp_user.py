from flask import Blueprint, request, jsonify
from flask_restx import Resource
from extensions import db, app_logger, transaction_manager, jwt_manager, require_auth
import settings
from pydantic import ValidationError
from models.user_model.user import User
from models.user_model.user_register_dto import UserRegisterDTO
from service.user_logic import user_service
from swagger_config import user_ns
from models.user_model.user_schemas import (
    user_register_model, 
    user_login_model, 
    user_response_model,
    user_login_response_model,
    error_response_model,
    token_auth_error_model,
    user_logout_response_model,
    user_login_error_response_model
)

# Blueprint 생성
user_bp = Blueprint("user", __name__, url_prefix=f'/{settings.API_PREFIX}')

@user_ns.route('/register')
class UserRegister(Resource):
    @user_ns.expect(user_register_model)
    @user_ns.response(201, 'Success')
    @user_ns.response(400, 'Bad Request')
    @user_ns.response(500, 'Internal Server Error')
    def post(self):
        """사용자 회원가입"""
        try:
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
            
            # 기존 사용자 확인
            existing_user = User.query.filter_by(email=user_data.email).first()
            if existing_user:
                app_logger.warning(f"회원가입 요청: 이미 존재하는 이메일 - {user_data.email}")
                return {
                    "status": "error",
                    "message": "이미 존재하는 이메일입니다."
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
                app_logger.info(f"회원가입 성공: {user_data.email}")
                return {
                    "status": "success",
                    "message": "회원가입이 완료되었습니다.",
                    "data": {
                        "id": str(new_user.id),
                        "name": new_user.name,
                        "email": new_user.email,
                        "created_at": new_user.created_at.isoformat()
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
    @user_ns.response(200, 'Success')
    @user_ns.response(400, 'Bad Request')
    @user_ns.response(404, 'User Not Found')
    @user_ns.response(500, 'Internal Server Error')
    def post(self):
        """사용자 로그인"""
        try:
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
            
            # JWT 토큰 생성
            token_data = {
                'email': user.email,
                'name': user.name,
                'nickname': user.nickname
            }
            
            access_token = jwt_manager.create_access_token(token_data)
            refresh_token = jwt_manager.create_refresh_token(token_data)
            
            app_logger.info(f"로그인 성공: {email}")
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
            app_logger.info("로그아웃 요청 처리")
            return {
                "status": "success",
                "message": "로그아웃이 완료되었습니다.",
                "data": None
            }, 200
        
        except Exception as e:
            app_logger.error(f"로그아웃 중 오류: {str(e)}")
            return {
                "status": "error",
                "message": f"로그아웃 중 오류가 발생했습니다: {str(e)}"
            }, 500