import json

from backend import app as flask_app


import pytest


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


def test_create_and_list_plan(client):
    # create a fresh user
    new_email = 'trainer_for_plans@example.com'
    rv = client.post('/api/usuarios/register', data=json.dumps({'email': new_email, 'password': 'pw1234', 'nombre': 'TrainerPlan'}), content_type='application/json')
    assert rv.status_code in (201, 409)
    if rv.status_code == 201:
        new_id = rv.get_json().get('id')
    else:
        # find existing
        token = login_admin(client)
        headers = {'Authorization': f'Bearer {token}'}
        users = client.get('/api/admin/usuarios', headers=headers).get_json()
        found = [u for u in users if u.get('email') == new_email]
        assert found
        new_id = found[0]['id']

    # promote to entrenador using admin
    token = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    rv = client.post(f'/api/admin/usuarios/{new_id}/promote', headers=headers)
    assert rv.status_code in (200, 201)

    # login as the new entrenador
    rv = client.post('/api/usuarios/login', data=json.dumps({'email': new_email, 'password': 'pw1234'}), content_type='application/json')
    assert rv.status_code == 200
    j = rv.get_json()
    assert 'token' in j
    trener_token = j['token']
    tr_headers = {'Authorization': f'Bearer {trener_token}'}

    # create a plan
    payload = {'nombre': 'Plan Test', 'descripcion': 'Descripcion test', 'contenido': 'Desayuno: algo', 'es_publico': True}
    rv = client.post('/api/planes', headers=tr_headers, data=json.dumps(payload), content_type='application/json')
    assert rv.status_code == 201
    plan_id = rv.get_json().get('id')
    assert plan_id is not None

    # list public plans and assert our plan is present
    rv = client.get('/api/planes')
    assert rv.status_code == 200
    plans = rv.get_json()
    names = [p.get('nombre') for p in plans]
    assert 'Plan Test' in names


# reuse fixtures/helpers from other tests
from tests.test_admin import login_admin
