from flask import Blueprint, jsonify, request
import constants
import settings

system_bp = Blueprint("system", __name__, url_prefix=f'/{settings.API_PREFIX}')

# @system_bp.before_request
# def check_token():
#     excluded_routes = []
#     if request.path in excluded_routes:
#         return None
#     else:
#         return None

@system_bp.route('/system/version', methods=['GET'], endpoint='system_version')
def system_version():
    try:
        return jsonify({
            "version": constants.API_VERSION,
            "version_date": constants.API_VERSION_DATE
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500