#!/usr/bin/env python3
"""
E2E test para el flujo: crear usuario (cliente), añadir rol entrenador, ejecutar DELETE ?mode=hard

Uso:
  - Asegúrate que la API corre en http://127.0.0.1:5000
  - Exporta ADMIN_EMAIL y ADMIN_PASSWORD en tu sesión o ingrésalos cuando se soliciten
  - Instala requests: pip install requests
  - Ejecuta: python scripts/e2e_hard_delete_test.py

El script no toca la base directamente; usa los endpoints admin expuestos.
"""
import os
import sys
import time
import uuid
import getpass
import json

try:
    import requests
except Exception:
    print('Este script requiere la librería requests. Instálala: pip install requests')
    sys.exit(1)

API_BASE = os.environ.get('API_BASE', 'http://127.0.0.1:5000')


def prompt_env(name, prompt_text):
    v = os.environ.get(name)
    if v:
        return v
    return input(prompt_text).strip()


def admin_login(email, password):
    url = f"{API_BASE}/api/usuarios/login"
    r = requests.post(url, json={'email': email, 'password': password})
    if r.status_code != 200:
        print('Login admin failed:', r.status_code, r.text)
        return None
    return r.json().get('token')


def admin_create_user(token, email, password, role='cliente'):
    url = f"{API_BASE}/api/admin/usuarios"
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'email': email, 'password': password, 'nombre': email, 'role': role}
    r = requests.post(url, json=payload, headers=headers)
    return r


def admin_set_role(token, user_id, desired_role):
    url = f"{API_BASE}/api/admin/usuarios/{user_id}/set_role"
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.post(url, json={'role': desired_role}, headers=headers)
    return r


def admin_delete_hard(token, user_id):
    url = f"{API_BASE}/api/admin/usuarios/{user_id}?mode=hard"
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.delete(url, headers=headers)
    return r


def main():
    admin_email = prompt_env('ADMIN_EMAIL', 'Admin email: ')
    admin_pwd = os.environ.get('ADMIN_PASSWORD')
    if not admin_pwd:
        admin_pwd = getpass.getpass('Admin password: ')

    token = admin_login(admin_email, admin_pwd)
    if not token:
        print('No se pudo autenticar como admin. Abortando.')
        sys.exit(1)
    print('Admin login ok. Token length:', len(token))

    # Create test user
    test_email = f"test.user.{uuid.uuid4().hex[:8]}@test.local"
    test_pwd = 'TestPass1234'
    print('Creando usuario de prueba:', test_email)
    r = admin_create_user(token, test_email, test_pwd, role='cliente')
    if r.status_code not in (200, 201):
        print('Falló crear usuario:', r.status_code, r.text)
        sys.exit(1)
    data = r.json()
    user_id = data.get('id') or data.get('usuario_id')
    if not user_id:
        # Try to fetch by email
        print('No se obtuvo id en respuesta; buscando por email...')
        q = requests.get(f"{API_BASE}/api/admin/usuarios", headers={'Authorization': f'Bearer {token}'})
        # Best-effort parse
        try:
            users = q.json()
            for u in users:
                if u.get('email') == test_email:
                    user_id = u.get('id') or u.get('usuario_id')
                    break
        except Exception:
            pass
    if not user_id:
        print('No pude determinar el id del usuario creado. Respuesta:', r.text)
        sys.exit(1)

    print('Usuario creado id=', user_id)

    # Promote to entrenador (adds entrenador row, leaving cliente intact)
    print('Añadiendo rol entrenador al usuario...')
    r2 = admin_set_role(token, user_id, 'entrenador')
    print('set_role status:', r2.status_code, r2.text)

    # Wait a moment for DB consistency
    time.sleep(1)

    # Attempt hard delete
    print('Ejecutando DELETE hard...')
    r3 = admin_delete_hard(token, user_id)
    print('DELETE status:', r3.status_code)
    try:
        print('DELETE response:', json.dumps(r3.json(), indent=2, ensure_ascii=False))
    except Exception:
        print('DELETE raw text:', r3.text)

    if r3.status_code == 200:
        print('E2E hard-delete OK')
    else:
        print('E2E hard-delete falló; revisa logs del servidor para detalles.')


if __name__ == '__main__':
    main()
