import json
import pytest

from backend import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def login_admin(client, api_base='/api'):
    # default seeded admin in app.py
    data = {'email': 'admin@test.local', 'password': 'admin123'}
    rv = client.post(f'{api_base}/usuarios/login', data=json.dumps(data), content_type='application/json')
    assert rv.status_code == 200
    j = rv.get_json()
    assert 'token' in j
    return j['token']


def test_admin_endpoints_flow(client):
    token = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}

    # list users
    rv = client.get('/api/admin/usuarios', headers=headers)
    assert rv.status_code == 200
    users = rv.get_json()
    assert isinstance(users, list)

    # create a new normal user to promote/delete
    new_email = 'test_user_for_admin@example.com'
    rv = client.post('/api/usuarios/register', data=json.dumps({'email': new_email, 'password': 'pw1234', 'nombre': 'TestUser'}), content_type='application/json')
    assert rv.status_code in (201, 409)
    if rv.status_code == 201:
        new_id = rv.get_json().get('id')
    else:
        # user exists — find it in users list
        users = client.get('/api/admin/usuarios', headers=headers).get_json()
        found = [u for u in users if u.get('email') == new_email]
        assert found
        new_id = found[0]['id']

    # promote the user to entrenador
    rv = client.post(f'/api/admin/usuarios/{new_id}/promote', headers=headers)
    assert rv.status_code in (200, 201)

    # metrics
    rv = client.get('/api/admin/metrics', headers=headers)
    assert rv.status_code == 200
    m = rv.get_json()
    assert 'total_users' in m

    # delete the user
    rv = client.delete(f'/api/admin/usuarios/{new_id}', headers=headers)
    assert rv.status_code == 200
