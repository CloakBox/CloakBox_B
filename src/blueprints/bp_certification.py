from flask import Blueprint, request, jsonify
from flask_restx import Resource
from extensions import db, app_logger
from models.user_model.user import User
from models.user_model.user_ip import UserIp
from models.user_model.user_agent import UserAgent
from models.user_model.user_login_log import UserLoginLog
from typing import Dict, Any
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
from datetime import datetime, timezone
import time

certification_bp = Blueprint("certification", __name__, url_prefix=f'/{settings.API_PREFIX}')

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
            if not request.json:
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            # DTO를 사용한 입력 검증
            try:
                certification_data = SendCertificationCodeDTO(**request.json)
            except ValidationError as e:
                return {
                    "status": "error",
                    "message": "입력 데이터 검증 실패",
                    "error": str(e.errors())
                }, 400
            
            # 만료된 인증번호 정리
            try:
                cleanup_expired_codes()
            except Exception as e:
                app_logger.warning(f"만료된 인증번호 정리 중 오류: {str(e)}")
            
            # 인증번호 생성 및 저장
            try:
                certification_code = create_certification_code(
                    certification_data.email
                )
            except Exception as e:
                app_logger.error(f"인증번호 생성 중 오류: {str(e)}")
                error_message = str(e)
                if "1분 이내에 재생성할 수 없습니다" in error_message:
                    return {
                        "status": "error",
                        "message": "1분 이내에 재생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
                        "error": "Too frequent requests"
                    }, 429  # Too Many Requests
                else:
                    return {
                        "status": "error",
                        "message": "인증번호 생성에 실패했습니다.",
                        "error": str(e)
                    }, 500
            
            # 이메일 전송
            try:
                if not send_certification_email(certification_data.email, certification_code.code):
                    db.session.delete(certification_code)
                    db.session.commit()
                    
                    return {
                        "status": "error",
                        "message": "이메일 전송에 실패했습니다.",
                        "error": "Failed to send email"
                    }, 500

            except Exception as e:
                app_logger.error(f"이메일 전송 중 오류: {str(e)}")
                try:
                    db.session.delete(certification_code)
                    db.session.commit()
                except:
                    pass
                
                return {
                    "status": "error",
                    "message": "이메일 전송 중 오류가 발생했습니다.",
                    "error": str(e)
                }, 500
            
            return {
                "status": "success",
                "message": "인증번호가 전송되었습니다.",
                "data": {
                    "expires_at": certification_code.expires_at.isoformat() if certification_code.expires_at else None
                }
            }, 200

        except Exception as e:
            app_logger.error(f"인증번호 전송 중 예상치 못한 오류: {str(e)}")
            import traceback
            app_logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"인증번호 전송 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

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
                return {
                    "status": "error",
                    "message": "요청 데이터가 없습니다.",
                    "error": "Request data is missing"
                }, 400
            
            # DTO를 사용한 입력 검증
            try:
                verification_data = VerifyCertificationCodeDTO(**request.json)
            except ValidationError as e:
                return {
                    "status": "error",
                    "message": "입력 데이터 검증 실패",
                    "error": str(e.errors())
                }, 400
            
            # 만료된 인증번호 정리
            cleanup_expired_codes()
            
            # 인증번호 검증
            certification_code = verify_certification_code(
                verification_data.email,
                verification_data.code
            )
            
            if not certification_code:
                return {
                    "status": "error",
                    "message": "유효하지 않거나 만료된 인증번호입니다.",
                    "error": "Invalid or expired certification code"
                }, 409
            
            # 사용자 조회
            user = User.query.filter_by(
                email=verification_data.email
            ).first()
            
            # 응답 데이터 구조
            response_data: dict[str, Any] = {
                "verified": True,
                "user_exists": user is not None
            }
            
            # 사용자가 존재하면 토큰 생성
            if user is not None:
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
                
                # 사용자 토큰 생성
                user_token = create_user_token(user)
                user.user_ip_id = user_ip_record.id
                user.user_agent_id = user_agent_record.id

                db.session.commit()

                response_data.update({
                    'access_token': user_token['access_token'],
                    'refresh_token': user_token['refresh_token'],
                    'token_type': "Bearer"
                })
            
            return {
                "status": "success",
                "message": "인증번호가 확인되었습니다.",
                "data": response_data
            }, 200
                
        except Exception as e:
            app_logger.error(f"인증번호 확인 중 오류가 발생했습니다: {str(e)}")
            return {
                "status": "error",
                "message": f"인증번호 확인 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500