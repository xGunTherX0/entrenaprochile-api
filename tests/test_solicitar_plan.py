import json
import pytest

from backend import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def login_admin(client, api_base='/api'):
    data = {'email': 'admin@test.local', 'password': 'admin123'}
    rv = client.post(f'{api_base}/usuarios/login', data=json.dumps(data), content_type='application/json')
    assert rv.status_code == 200
    j = rv.get_json()
    assert 'token' in j
    return j['token']


def test_entrenador_crea_plan_y_cliente_solicita(client):
    # Create and promote a trainer
    trainer_email = 'e2e_trainer@example.com'
    rv = client.post('/api/usuarios/register', data=json.dumps({'email': trainer_email, 'password': 'pw1234', 'nombre': 'E2ETrainer'}), content_type='application/json')
    assert rv.status_code in (201, 409)

    # Ensure trainer has an entrenador row
    admin_token = login_admin(client)
    headers = {'Authorization': f'Bearer {admin_token}'}
    # find id of trainer user
    users = client.get('/api/admin/usuarios', headers=headers).get_json()
    found = [u for u in users if u.get('email') == trainer_email]
    assert found
    trainer_user_id = found[0]['id']

    rv = client.post(f'/api/admin/usuarios/{trainer_user_id}/promote', headers=headers)
    assert rv.status_code in (200, 201)

    # login as trainer and create a plan
    rv = client.post('/api/usuarios/login', data=json.dumps({'email': trainer_email, 'password': 'pw1234'}), content_type='application/json')
    assert rv.status_code == 200
    trener_token = rv.get_json()['token']
    tr_headers = {'Authorization': f'Bearer {trener_token}'}

    payload = {'nombre': 'E2E Plan', 'descripcion': 'Plan e2e test', 'contenido': 'Comida', 'es_publico': True}
    rv = client.post('/api/planes', headers=tr_headers, data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 201
    plan_id = rv.get_json().get('id')
    assert plan_id is not None

    # create a client user
    client_email = 'e2e_client@example.com'
    rv = client.post('/api/usuarios/register', data=json.dumps({'email': client_email, 'password': 'pw1234', 'nombre': 'E2EClient'}), content_type='application/json')
    assert rv.status_code in (201, 409)

    # login as client and request the plan
    rv = client.post('/api/usuarios/login', data=json.dumps({'email': client_email, 'password': 'pw1234'}), content_type='application/json')
    assert rv.status_code == 200
    client_token = rv.get_json()['token']
    c_headers = {'Authorization': f'Bearer {client_token}'}

    rv = client.post(f'/api/planes/{plan_id}/solicitar', headers=c_headers)
    assert rv.status_code == 201
    solicitud_id = rv.get_json().get('id')
    assert solicitud_id is not None

    # fetch client's solicitudes and ensure our solicitud is present
    rv = client.get('/api/solicitudes/mis', headers=c_headers)
    assert rv.status_code == 200
    sols = rv.get_json()
    ids = [s.get('id') for s in sols]
    assert solicitud_id in ids
