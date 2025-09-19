from flask import Blueprint, request, jsonify
from flask_restx import Resource
from extensions import db, app_logger, transaction_manager, jwt_manager, require_auth
import settings
from pydantic import ValidationError
from models.user_model.user import User
from models.user_model.user_ip import UserIp
from models.user_model.user_agent import UserAgent
from models.user_model.user_login_log import UserLoginLog
from models.user_model.user_setting import UserSetting
from models.user_model.user_register_dto import UserRegisterDTO
from models.user_model.user_profile_update_dto import UserProfileUpdateDTO
from service.user_logic import user_service
from swagger_config import user_ns
from models.user_model.user_schemas import (
    user_register_model, 
    user_login_response_model,
    user_profile_response_model,
    user_profile_update_model,
    auth_error_response_model,
    profile_error_response_model,
    user_profile_update_response_model,
    validation_error_response_model,
    user_logout_response_model
)
from sqlalchemy import or_
from datetime import datetime
import time
from sqlalchemy.exc import SQLAlchemyError
from utils import func

# Blueprint 생성
user_bp = Blueprint("user", __name__, url_prefix=f'/{settings.API_PREFIX}')

# 공통 유틸리티 함수
def create_error_response(message, error_code, status_code):
    """에러 응답 생성"""
    return {
        "status": "error",
        "message": message,
        "error": error_code
    }, status_code

def validate_request_json():
    """요청 JSON 데이터 검증"""
    if not request.json:
        return False, create_error_response("요청 데이터가 없습니다.", "REQUEST_DATA_MISSING", 400)
    return True, None

def validate_required_fields(data, required_fields):
    """필수 필드 검증"""
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return False, create_error_response(
            f"필수 필드가 없습니다: {', '.join(missing_fields)}",
            "REQUIRED_FIELDS_MISSING",
            400
        )
    return True, None

def handle_database_operation(func, *args, **kwargs):
    """데이터베이스 작업 예외 처리"""
    try:
        return func(*args, **kwargs)
    except SQLAlchemyError as e:
        db.session.rollback()
        app_logger.error(f"데이터베이스 오류: {str(e)}")
        raise e

def create_user_login_log(user_id, user_ip_id, user_agent_id, event_type='LOGIN'):
    """사용자 로그인 로그 생성 또는 업데이트"""
    existing_log = UserLoginLog.query.filter_by(user_id=user_id).first()
    
    if existing_log:
        existing_log.event_at = datetime.now()
        existing_log.event_at_unix = int(time.time())
        existing_log.ip_id = user_ip_id
        existing_log.user_agent_id = user_agent_id
        existing_log.event_type = event_type
    else:
        user_login_log = UserLoginLog(
            user_id=user_id,
            ip_id=user_ip_id,
            user_agent_id=user_agent_id,
            event_type=event_type
        )
        db.session.add(user_login_log)

def validate_user_register_data(user_data):
    """사용자 등록 데이터 검증"""
    # 이메일과 이름 중복 확인
    existing_user = User.query.filter(
        or_(User.email == user_data.email, User.name == user_data.name)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            app_logger.warning(f"회원가입 요청: 이미 존재하는 이메일 - {user_data.email}")
            return False, create_error_response(
                "이미 존재하는 이메일입니다.", 
                "EMAIL_ALREADY_EXISTS", 
                400
            )
        else:
            app_logger.warning(f"회원가입 요청: 이미 존재하는 이름 - {user_data.name}")
            return False, create_error_response(
                "이미 존재하는 이름입니다.", 
                "NAME_ALREADY_EXISTS", 
                400
            )
    
    return True, None

def create_user_with_settings(user_data, user_ip_id, user_agent_id):
    """사용자 및 설정 생성"""
    # 사용자 설정 생성
    new_user_setting = UserSetting(
        dark_mode='N',
        editor_mode='light',
        lang_cd='ko'
    )
    
    db.session.add(new_user_setting)
    db.session.flush()
    
    # 새 사용자 생성
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        nickname=user_data.nickname,
        gender=user_data.gender,
        bio=user_data.bio,
        user_ip_id=user_ip_id,
        user_agent_id=user_agent_id,
        user_setting_id=new_user_setting.id
    )
    
    db.session.add(new_user)
    db.session.flush()
    
    return new_user

@user_ns.route('/register')
class UserRegister(Resource):
    @user_ns.expect(user_register_model)
    @user_ns.response(201, 'Success', user_login_response_model)
    @user_ns.response(400, 'Bad Request')
    @user_ns.response(500, 'Internal Server Error')
    @require_auth
    def post(self):
        """사용자 회원가입"""
        try:
            # 요청 데이터 검증
            is_valid, error_response = validate_request_json()
            if not is_valid:
                return error_response
            
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
            
            # 사용자 데이터 검증
            is_valid, error_response = validate_user_register_data(user_data)
            if not is_valid:
                return error_response
            
            # IP 및 User-Agent 정보 처리
            user_ip_id = func.get_user_ip(request, db)
            user_agent_id = func.get_user_agent(request, db)
            
            # 사용자 및 설정 생성
            new_user = handle_database_operation(
                create_user_with_settings, user_data, user_ip_id, user_agent_id
            )
            
            # 로그인 로그 생성
            handle_database_operation(
                create_user_login_log, new_user.id, user_ip_id, user_agent_id
            )
            
            # 트랜잭션 커밋
            if transaction_manager.commit():
                # JWT 토큰 생성
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
                return create_error_response(
                    "회원가입 중 오류가 발생했습니다.",
                    "REGISTRATION_FAILED",
                    500
                )
            
        except Exception as e:
            app_logger.error(f"회원가입 중 오류: {str(e)}")
            transaction_manager.rollback()
            return create_error_response(
                f"회원가입 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@user_ns.route('/logout')
class UserLogout(Resource):
    @user_ns.doc(
        security='Bearer',
        description="사용자 로그아웃",
        responses={
            200: ('성공', user_logout_response_model),
            401: ('인증 실패', auth_error_response_model),
            404: ('사용자 없음', profile_error_response_model),
            500: ('서버 오류', profile_error_response_model)
        }
    )
    @user_ns.response(200, 'Success', user_logout_response_model)
    @user_ns.response(401, 'Unauthorized', auth_error_response_model)
    @user_ns.response(404, 'User Not Found', profile_error_response_model)
    @user_ns.response(500, 'Internal Server Error', profile_error_response_model)
    @require_auth
    def post(self):
        """사용자 로그아웃"""
        try:
            # Request에서 사용자 정보 추출
            user_info = jwt_manager.validate_request_and_extract_user()
            
            if not user_info:
                app_logger.warning("로그아웃 요청: 사용자 정보 추출 실패")
                return create_error_response(
                    "유효하지 않은 토큰입니다.",
                    "INVALID_TOKEN",
                    401
                )
            
            # 사용자 조회
            user = User.query.filter_by(email=user_info['email']).first()
            if not user:
                app_logger.warning(f"로그아웃 요청: 사용자를 찾을 수 없음 - {user_info['email']}")
                return create_error_response(
                    "사용자를 찾을 수 없습니다.",
                    "USER_NOT_FOUND",
                    404
                )

            # IP 및 User-Agent 정보 처리
            user_ip_id = func.get_user_ip(request, db)
            user_agent_id = func.get_user_agent(request, db)
            
            # 로그아웃 로그 생성
            handle_database_operation(
                create_user_login_log, user.id, user_ip_id, user_agent_id, 'LOGOUT'
            )
            
            # 토큰 무효화
            if not jwt_manager.invalidate_request_token():
                app_logger.warning(f"토큰 무효화 실패: {user_info['email']}")
                return create_error_response(
                    "로그아웃 처리 중 오류가 발생했습니다.",
                    "TOKEN_INVALIDATION_FAILED",
                    500
                )
            
            # 변경사항 커밋
            if not transaction_manager.commit():
                app_logger.error("로그아웃 커밋 실패")
                return create_error_response(
                    "로그아웃 중 오류가 발생했습니다.",
                    "LOGOUT_FAILED",
                    500
                )
            
            app_logger.info(f"로그아웃 완료: {user_info['email']}")

            return {
                "status": "success",
                "message": "로그아웃이 완료되었습니다.",
                "data": None
            }, 200

        except Exception as e:
            app_logger.error(f"로그아웃 중 오류: {str(e)}")
            transaction_manager.rollback()
            return create_error_response(
                f"로그아웃 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@user_ns.route('/profile')
class UserProfile(Resource):
    @user_ns.doc(
        security='Bearer',
        description="사용자 프로필 조회",
        responses={
            200: ('성공', user_profile_response_model),
            401: ('인증 실패', auth_error_response_model),
            404: ('사용자 없음', profile_error_response_model),
            500: ('서버 오류', profile_error_response_model)
        }
    )
    @user_ns.response(200, 'Success', user_profile_response_model)
    @user_ns.response(401, 'Unauthorized', auth_error_response_model)
    @user_ns.response(404, 'User Not Found', profile_error_response_model)
    @user_ns.response(500, 'Internal Server Error', profile_error_response_model)
    @require_auth
    def get(self):
        """사용자 프로필 조회"""
        try:
            # Request에서 사용자 정보 추출
            user_info = jwt_manager.validate_request_and_extract_user(request)
            
            # 사용자 정보를 사용하여 사용자 프로필 조회    
            user_profile = user_service.get_user_profile_by_user_info(user_info)
            
            return {
                "status": "success",
                "message": "사용자 프로필 조회가 완료되었습니다.",
                "data": user_profile
            }, 200
        
        except Exception as e:
            app_logger.error(f"사용자 프로필 조회 중 오류: {str(e)}")
            return create_error_response(
                f"사용자 프로필 조회 중 오류가 발생했습니다: {str(e)}",
                "PROFILE_FETCH_FAILED",
                500
            )

    @user_ns.doc(
        security='Bearer',
        description="사용자 프로필 수정",
        responses={
            200: ('성공', user_profile_update_response_model),
            400: ('입력 데이터 오류', validation_error_response_model),
            401: ('인증 실패', auth_error_response_model),
            404: ('사용자 없음', profile_error_response_model),
            500: ('서버 오류', profile_error_response_model)
        }
    )
    @user_ns.expect(user_profile_update_model)
    @user_ns.response(200, 'Success', user_profile_update_response_model)
    @user_ns.response(400, 'Bad Request', validation_error_response_model)
    @user_ns.response(401, 'Unauthorized', auth_error_response_model)
    @user_ns.response(404, 'User Not Found', profile_error_response_model)
    @user_ns.response(500, 'Internal Server Error', profile_error_response_model)
    @require_auth
    def post(self):
        """사용자 프로필 수정"""
        try:
            # Request에서 사용자 정보 추출
            user_info = jwt_manager.validate_request_and_extract_user(request)
            
            # Request에서 사용자 프로필 수정 데이터 추출
            request_data = request.json if request.json else {}
            
            # Pydantic 모델을 사용하여 데이터 검증
            try:
                user_profile_update_data = UserProfileUpdateDTO(**request_data)
            except ValidationError as e:
                app_logger.warning(f"프로필 수정 요청: 입력 데이터 검증 실패 - {e.errors()}")
                return {
                    "status": "error",
                    "message": "입력 데이터 검증 실패",
                    "errors": e.errors()
                }, 400
            
            # 토큰을 사용하여 사용자 프로필 수정
            user_profile = user_service.update_user_profile_by_user_info(user_info, user_profile_update_data)
            
            return {
                "status": "success",
                "message": "사용자 프로필 수정이 완료되었습니다.",
                "data": user_profile
            }, 200
            
        except Exception as e:
            app_logger.error(f"사용자 프로필 수정 중 오류: {str(e)}")
            return create_error_response(
                f"사용자 프로필 수정 중 오류가 발생했습니다: {str(e)}",
                "PROFILE_UPDATE_FAILED",
                500
            )