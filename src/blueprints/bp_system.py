from flask import Blueprint, jsonify, request
from flask_restx import Resource
import constants
import settings
from swagger_config import system_ns
from models.system_model.system_schemas import (
    system_version_model,
    system_health_model,
    success_response_model,
    error_response_model
)

system_bp = Blueprint("system", __name__, url_prefix=f'/{settings.API_PREFIX}')

@system_ns.route('/version')
class SystemVersion(Resource):
    @system_ns.response(200, 'Success', system_version_model)
    def get(self):
        """시스템 버전 정보 조회"""
        try:
            return {
                "version": constants.API_VERSION,
                "version_date": constants.API_VERSION_DATE
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"버전 정보 조회 중 오류가 발생했습니다: {str(e)}"
            }, 500

@system_ns.route('/health')
class SystemHealth(Resource):
    @system_ns.response(200, 'Success', system_health_model)
    def get(self):
        """시스템 상태 확인"""
        try:
            return {
                "status": "healthy",
                "message": "시스템이 정상적으로 작동 중입니다."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"시스템 상태 확인 중 오류가 발생했습니다: {str(e)}"
            }, 500