import json

from backend import app as flask_app


def test_cliente_solicita_rutina_autoacepta():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        # create trainer and rutina
        trainer_email = 'rutina_trainer@example.com'
        client.post('/api/usuarios/register', data=json.dumps({'email': trainer_email, 'password': 'pw1234', 'nombre': 'RutinaTrainer'}), content_type='application/json')
        # promote trainer via admin
        admin_login = client.post('/api/usuarios/login', data=json.dumps({'email': 'admin@test.local', 'password': 'admin123'}), content_type='application/json')
        assert admin_login.status_code == 200
        admin_token = admin_login.get_json()['token']
        headers = {'Authorization': f'Bearer {admin_token}'}
        users = client.get('/api/admin/usuarios', headers=headers).get_json()
        trainer_user = [u for u in users if u.get('email') == trainer_email][0]
        client.post(f"/api/admin/usuarios/{trainer_user['id']}/promote", headers=headers)

        # login as trainer and create rutina
        rv = client.post('/api/usuarios/login', data=json.dumps({'email': trainer_email, 'password': 'pw1234'}), content_type='application/json')
        ttoken = rv.get_json()['token']
        th = {'Authorization': f'Bearer {ttoken}'}
        rg = client.post('/api/rutinas', headers=th, data=json.dumps({'nombre': 'Rutina E2E', 'descripcion': 'Desc', 'nivel': 'medio', 'es_publica': True}), content_type='application/json')
        assert rg.status_code == 201
        rutina_id = rg.get_json()['rutina']['id']

        # create cliente and login
        client.post('/api/usuarios/register', data=json.dumps({'email': 'rutina_client@example.com', 'password': 'pw1234', 'nombre': 'RutinaClient'}), content_type='application/json')
        rv = client.post('/api/usuarios/login', data=json.dumps({'email': 'rutina_client@example.com', 'password': 'pw1234'}), content_type='application/json')
        ctoken = rv.get_json()['token']
        ch = {'Authorization': f'Bearer {ctoken}'}

        # client solicita rutina
        resp = client.post(f'/api/rutinas/{rutina_id}/solicitar', headers=ch)
        assert resp.status_code == 201
        sid = resp.get_json().get('id')
        assert sid is not None

        # check that the solicitud is created and estado == 'aceptado'
        sols = client.get('/api/solicitudes/mis', headers=ch).get_json()
        found = [s for s in sols if s.get('id') == sid]
        assert found, 'Solicitud not present in mis'
        assert found[0].get('estado') == 'aceptado'
