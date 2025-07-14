from flask import Blueprint, request, jsonify
from flask_restx import Resource
from extensions import db
import settings
from swagger_config import certification_ns
from pydantic import ValidationError
from models.certification_model.certification_dto import SendCertificationCodeDTO, VerifyCertificationCodeDTO
from models.certification_model.certification_schemas import (
    send_certification_code_model,
    verify_certification_code_model,
    send_certification_response_model,
    certification_error_response_model
)
from service.certification_logic.certification_service import (
    create_certification_code,
    send_certification_email,
    verify_certification_code,
    cleanup_expired_codes
)

certification_bp = Blueprint("certification", __name__, url_prefix=f'/{settings.API_PREFIX}')

@certification_ns.route('/send-certification-code')
class SendCertificationCode(Resource):
    @certification_ns.expect(send_certification_code_model)
    @certification_ns.response(200, 'Success')
    @certification_ns.response(400, 'Bad Request')
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
            cleanup_expired_codes()
            
            # 인증번호 생성 및 저장
            certification_code = create_certification_code(
                certification_data.email
            )
            
            # 이메일 전송
            if not send_certification_email(certification_data.email, certification_code.code):
                # 이메일 전송 실패 시 생성된 인증번호 삭제
                db.session.delete(certification_code)
                db.session.commit()
                
                return {
                    "status": "error",
                    "message": "이메일 전송에 실패했습니다.",
                    "error": "Failed to send email"
                }, 500
            
            return {
                "status": "success",
                "message": "인증번호가 전송되었습니다.",
                "data": {
                    "email": certification_code.recipient,
                    "user_uuid": str(certification_code.user_uuid) if certification_code.user_uuid else None,
                    "expires_at": certification_code.expires_at
                }
            }, 200
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"인증번호 전송 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500

@certification_ns.route('/verify-certification-code')
class VerifyCertificationCode(Resource):
    @certification_ns.expect(verify_certification_code_model)
    @certification_ns.response(200, 'Success')
    @certification_ns.response(400, 'Bad Request')
    @certification_ns.response(409, 'Code Not Found')
    @certification_ns.response(500, 'Internal Server Error')
    def post(self):
        """인증번호 검증"""
        try:
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
            
            return {
                "status": "success",
                "message": "인증번호가 확인되었습니다.",
                "data": {
                    "email": certification_code.recipient,
                    "user_uuid": str(certification_code.user_uuid) if certification_code.user_uuid else None,
                    "verified": True
                }
            }, 200
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"인증번호 확인 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }, 500