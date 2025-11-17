import jwt
import requests
from datetime import datetime, timedelta
import uuid

JWT_SECRET = 'dev-secret-change-me'
JWT_ALGORITHM = 'HS256'

def generate_token():
    data = {'user_id': 7, 'role': 'entrenador', 'nombre': 'Test'}
    data['exp'] = datetime.utcnow() + timedelta(seconds=3600)
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
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        print('STATUS', r.status_code)
        try:
            print('BODY', r.json())
        except Exception:
            print('BODY RAW', r.text[:2000])
    except Exception as e:
        print('REQUEST ERROR', e)
