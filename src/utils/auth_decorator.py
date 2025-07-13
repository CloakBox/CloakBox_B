from functools import wraps
from flask import request, jsonify
from .jwt_manager import jwt_manager

def require_auth(f):
    """인증 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'status': 'error',
                'message': '토큰이 없습니다.'
            }), 401
        
        # Bearer 토큰 형식 확인
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'status': 'error',
                'message': '유효하지 않은 토큰 형식입니다.'
            }), 401
        
        # 토큰 추출
        token = auth_header.split(' ')[1]

        # 토큰 검증
        payload = jwt_manager.verify_token(token)
        if not payload:
            return jsonify({
                'status': 'error',
                'message': '유효하지 않은 토큰입니다.'
            }), 401
        
        # 토큰 타입 확인
        if payload.get('type') != 'access':
            return jsonify({
                'status': 'error',
                'message': '액세스 토큰이 필요합니다.'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function