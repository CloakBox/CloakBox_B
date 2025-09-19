from flask import Blueprint, request, make_response
from flask_restx import Resource
from extensions import db, app_logger
from models.user_model.user import User
from models.user_model.user_ip import UserIp
from models.user_model.user_agent import UserAgent
from models.user_model.user_login_log import UserLoginLog
from typing import Dict, Any, Tuple
import settings
from swagger_config import certification_ns
from pydantic import ValidationError
from models.certification_model.certification_dto import SendCertificationCodeDTO, VerifyCertificationCodeDTO
from models.certification_model.certification_schemas import (
    send_certification_code_model,
    verify_certification_code_model,
    send_certification_success_model,
    verify_certification_success_model,
)
from service.certification_logic.certification_service import (
    create_certification_code,
    send_certification_email,
    verify_certification_code,
    cleanup_expired_codes
)
from service.user_logic.user_service import create_user_token
from datetime import datetime
import time
from utils import func
from sqlalchemy.exc import SQLAlchemyError

certification_bp = Blueprint("certification", __name__, url_prefix=f'/{settings.API_PREFIX}')

# 공통 유틸리티 함수
def create_error_response(message: str, error_code: str, status_code: int) -> Tuple[Dict[str, Any], int]:
    """에러 응답 생성"""
    return {
        "status": "error",
        "message": message,
        "error": error_code
    }, status_code

def validate_request_json() -> Tuple[bool, Tuple[Dict[str, Any], int]]:
    """요청 JSON 데이터 검증"""
    if not request.json:
        return False, create_error_response("요청 데이터가 없습니다.", "REQUEST_DATA_MISSING", 400)
    return True, None

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Tuple[bool, Tuple[Dict[str, Any], int]]:
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
    """DB 작업 예외 처리"""
    try:
        return func(*args, **kwargs)
    except SQLAlchemyError as e:
        db.session.rollback()
        app_logger.error(f"데이터베이스 오류: {str(e)}")
        raise e

def create_user_login_log(user_id: int, user_ip_id: int, user_agent_id: int) -> None:
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

@certification_ns.route('/send-certification-code')
class SendCertificationCode(Resource):
    @certification_ns.expect(send_certification_code_model)
    @certification_ns.response(200, 'Success', send_certification_success_model)
    @certification_ns.response(400, 'Bad Request')
    @certification_ns.response(429, 'Too Many Requests')
    @certification_ns.response(500, 'Internal Server Error')
    def post(self):
        """인증번호 전송"""
        try:
            # 요청 데이터 검증
            is_valid, error_response = validate_request_json()
            if not is_valid:
                return error_response
            
            # DTO를 사용한 입력 검증
            try:
                certification_data = SendCertificationCodeDTO(**request.json)
            except ValidationError as e:
                return create_error_response(
                    "입력 데이터 검증 실패",
                    "VALIDATION_ERROR",
                    400
                )
            
            # 만료된 인증번호 정리
            try:
                cleanup_expired_codes()
            except Exception as e:
                app_logger.warning(f"만료된 인증번호 정리 중 오류: {str(e)}")
            
            # 인증번호 생성 및 저장
            try:
                certification_code = create_certification_code(certification_data.email)
            except Exception as e:
                app_logger.error(f"인증번호 생성 중 오류: {str(e)}")
                error_message = str(e)
                if "1분 이내에 재생성할 수 없습니다" in error_message:
                    return create_error_response(
                        "1분 이내에 재생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
                        "TOO_FREQUENT_REQUESTS",
                        429
                    )
                else:
                    return create_error_response(
                        "인증번호 생성에 실패했습니다.",
                        "CERTIFICATION_CODE_CREATION_FAILED",
                        500
                    )
            
            # 이메일 전송
            try:
                if not send_certification_email(certification_data.email, certification_code.code):
                    db.session.delete(certification_code)
                    db.session.commit()
                    
                    return create_error_response(
                        "이메일 전송에 실패했습니다.",
                        "EMAIL_SEND_FAILED",
                        500
                    )
            except Exception as e:
                app_logger.error(f"이메일 전송 중 오류: {str(e)}")
                try:
                    db.session.delete(certification_code)
                    db.session.commit()
                except:
                    pass
                
                return create_error_response(
                    "이메일 전송 중 오류가 발생했습니다.",
                    "EMAIL_SEND_ERROR",
                    500
                )
            
            return {
                "status": "success",
                "message": "인증번호가 전송되었습니다.",
                "data": {
                    "expires_at": certification_code.expires_at.isoformat() if certification_code.expires_at else None
                }
            }, 200

        except Exception as e:
            app_logger.error(f"인증번호 전송 중 예상치 못한 오류: {str(e)}")
            return create_error_response(
                f"인증번호 전송 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )

@certification_ns.route('/verify-certification-code')
class VerifyCertificationCode(Resource):
    @certification_ns.expect(verify_certification_code_model)
    @certification_ns.response(200, 'Success', verify_certification_success_model)
    @certification_ns.response(400, 'Bad Request')
    @certification_ns.response(409, 'Code Not Found')
    @certification_ns.response(500, 'Internal Server Error')
    def post(self):
        """인증번호 검증"""
        try:
            # 사용자 IP와 User-Agent 정보 저장
            user_ip_id = func.get_user_ip(request, db)
            user_agent_id = func.get_user_agent(request, db)
            
            # 요청 데이터 검증
            is_valid, error_response = validate_request_json()
            if not is_valid:
                return error_response
            
            # DTO를 사용한 입력 검증
            try:
                verification_data = VerifyCertificationCodeDTO(**request.json)
            except ValidationError as e:
                return create_error_response(
                    "입력 데이터 검증 실패",
                    "VALIDATION_ERROR",
                    400
                )
            
            # 만료된 인증번호 정리
            cleanup_expired_codes()
            
            # 인증번호 검증
            certification_code = verify_certification_code(
                verification_data.email,
                verification_data.code
            )
            
            if not certification_code:
                return create_error_response(
                    "유효하지 않거나 만료된 인증번호입니다.",
                    "INVALID_OR_EXPIRED_CODE",
                    409
                )
            
            # 사용자 조회
            user = User.query.filter_by(email=verification_data.email).first()
            
            # 응답 데이터 구조
            response_data: Dict[str, Any] = {
                "verified": True,
                "user_exists": user is not None
            }
            
            # 사용자가 존재하면 토큰 생성
            if user is not None:
                # 로그인 로그 생성 또는 업데이트
                handle_database_operation(
                    create_user_login_log, user.id, user_ip_id, user_agent_id
                )
                
                # 사용자 정보 업데이트
                user.user_ip_id = user_ip_id
                user.user_agent_id = user_agent_id
                
                # 커밋
                db.session.commit()
                
                # 사용자 토큰 생성
                user_token = create_user_token(user)
                
                # 토큰을 헤더로 설정
                response = make_response({
                    "status": "success",
                    "message": "인증번호가 확인되었습니다.",
                    "data": response_data
                }, 200)
                
                # 토큰을 헤더에 추가
                response.headers['X-Access-Token'] = user_token['access_token']
                response.headers['X-Refresh-Token'] = user_token['refresh_token']
                
                return response
            
            # 사용자가 존재하지 않는 경우
            return {
                "status": "success",
                "message": "인증번호가 확인되었습니다.",
                "data": response_data
            }, 200
                
        except Exception as e:
            app_logger.error(f"인증번호 확인 중 오류가 발생했습니다: {str(e)}")
            return create_error_response(
                f"인증번호 확인 중 오류가 발생했습니다: {str(e)}",
                "INTERNAL_SERVER_ERROR",
                500
            )