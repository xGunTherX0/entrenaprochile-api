from backend import db
from database.database import Usuario, Cliente, Entrenador
from backend.auth import generate_token


def create_user_with_client(app, email='user@test.local'):
    with app.app_context():
        user = Usuario(email=email, nombre='Test User', hashed_password='x')
        db.session.add(user)
        db.session.commit()
        cliente = Cliente(usuario_id=user.id)
        db.session.add(cliente)
        db.session.commit()
        return user


def test_admin_hard_delete_removes_user_and_cliente(client):
    from backend import app as _app
    # create admin token
    admin_payload = {'role': 'admin', 'email': 'admin@test.local'}
    token = generate_token(admin_payload, expires_in=60)

    # create a regular user with cliente row
    user = create_user_with_client(_app, email='victim@test.local')

    # perform delete
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.delete(f'/api/admin/usuarios/{user.id}?mode=hard', headers=headers)
    assert resp.status_code == 200, resp.get_data(as_text=True)

    # ensure user and cliente gone
    with _app.app_context():
        assert Usuario.query.filter_by(id=user.id).first() is None
        assert Cliente.query.filter_by(usuario_id=user.id).first() is None
