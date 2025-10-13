import os
import jwt
from functools import wraps
from flask import request, jsonify

JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-change-me')
JWT_ALGORITHM = 'HS256'

def generate_token(payload, expires_in=3600):
    data = payload.copy()
    # Optional: include exp in future
    # data['exp'] = datetime.utcnow() + timedelta(seconds=expires_in)
    token = jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.PyJWTError as e:
        return None


def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'authorization required'}), 401
        token = auth_header.split(' ', 1)[1]
        decoded = decode_token(token)
        if not decoded:
            return jsonify({'error': 'invalid or expired token'}), 401
        # attach decoded payload to request context
        request.jwt_payload = decoded
        return view_func(*args, **kwargs)
    return wrapper
