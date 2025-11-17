import jwt
import json
from datetime import datetime, timedelta
import uuid
import urllib.request

JWT_SECRET = 'dev-secret-change-me'
JWT_ALGORITHM = 'HS256'

def generate_token():
    data = {'user_id': 7, 'role': 'entrenador', 'nombre': 'Test'}
    data['exp'] = (datetime.utcnow() + timedelta(seconds=3600)).timestamp()
    data['jti'] = str(uuid.uuid4())
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)

if __name__ == '__main__':
    token = generate_token()
    print('TOKEN:', token)
    url = 'http://127.0.0.1:5000/api/rutinas'
    payload = {
        'nombre': 'test from assistant',
        'descripcion': 'desc',
        'objetivo_principal': 'obj',
        'enfoque_rutina': 'enc',
        'cualidades_clave': 'cual',
        'duracion_frecuencia': 'dur',
        'material_requerido': 'mat',
        'instrucciones_estructurales': 'inst',
        'nivel': 'Básico',
        'entrenador_id': '7'
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            print('STATUS', resp.status)
            print('BODY', body[:4000])
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode('utf-8')
        except Exception:
            body = '<no body>'
        print('HTTP ERROR', e.code)
        print('BODY', body[:4000])
    except Exception as e:
        print('REQUEST ERROR', e)
