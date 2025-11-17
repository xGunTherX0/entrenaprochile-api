import os
import jwt
import uuid
from datetime import datetime
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta

JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-change-me')
JWT_ALGORITHM = 'HS256'
# Seconds for token expiration. Make configurable via env var.
JWT_EXPIRES_SECONDS = int(os.getenv('JWT_EXPIRES_SECONDS', '3600'))


def generate_token(payload, expires_in: int | None = None):
    """Generate a JWT including an 'exp' claim.

    expires_in: seconds until expiration. If None, uses JWT_EXPIRES_SECONDS.
    """
    data = payload.copy()
    ttl = JWT_EXPIRES_SECONDS if expires_in is None else int(expires_in)
    data['exp'] = datetime.utcnow() + timedelta(seconds=ttl)
    # Add a unique token id (jti) so we can revoke tokens server-side
    data['jti'] = str(uuid.uuid4())
    # PyJWT returns a str in modern versions
    token = jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        # token expired
        return None
    except jwt.PyJWTError:
        # invalid token
        return None


def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # Skip authentication for CORS preflight requests (OPTIONS).
        # Browsers send OPTIONS without Authorization header; if we
        # enforce auth here the preflight will fail and block the real
        # request from the frontend. Return 200 for OPTIONS so flask-cors
        # can attach the proper CORS headers.
        if request.method == 'OPTIONS':
            return ('', 200)

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'authorization required'}), 401
        token = auth_header.split(' ', 1)[1]
        decoded = decode_token(token)
        if not decoded:
            return jsonify({'error': 'invalid or expired token'}), 401

        # Check revocation (RevokedToken) if DB is available. Import lazily
        try:
            from database.database import RevokedToken
            from database.database import db as _db
            jti = decoded.get('jti')
            if jti:
                exists = _db.session.query(RevokedToken).filter_by(jti=jti).first()
                if exists:
                    return jsonify({'error': 'token revoked'}), 401
        except Exception:
            # If DB not available yet (app init), skip revocation check
            pass

        # attach decoded payload to request context
        request.jwt_payload = decoded
        return view_func(*args, **kwargs)
    return wrapper
