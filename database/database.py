from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Create SQLAlchemy instance here and initialize it from app with db.init_app(app)
db = SQLAlchemy()


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # relaciones
    cliente = db.relationship('Cliente', back_populates='usuario', uselist=False)
    entrenador = db.relationship('Entrenador', back_populates='usuario', uselist=False)

    def __repr__(self):
        return f'<Usuario {self.email}>'


class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    edad = db.Column(db.Integer)
    peso = db.Column(db.Float)
    altura = db.Column(db.Float)

    usuario = db.relationship('Usuario', back_populates='cliente')
    rutinas = db.relationship('Rutina', back_populates='cliente')
    mediciones = db.relationship('Medicion', back_populates='cliente')

    def __repr__(self):
        return f'<Cliente {self.id}>'


class Entrenador(db.Model):
    __tablename__ = 'entrenadores'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    speciality = db.Column(db.String(200))

    usuario = db.relationship('Usuario', back_populates='entrenador')

    def __repr__(self):
        return f'<Entrenador {self.id}>'


class Rutina(db.Model):
    __tablename__ = 'rutinas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    cliente = db.relationship('Cliente', back_populates='rutinas')
    ejercicios = db.relationship('Ejercicio', secondary='rutina_ejercicio', back_populates='rutinas')

    def __repr__(self):
        return f'<Rutina {self.nombre}>'


class Ejercicio(db.Model):
    __tablename__ = 'ejercicios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)

    rutinas = db.relationship('Rutina', secondary='rutina_ejercicio', back_populates='ejercicios')

    def __repr__(self):
        return f'<Ejercicio {self.nombre}>'


# Tabla many-to-many
rutina_ejercicio = db.Table(
    'rutina_ejercicio',
    db.Column('rutina_id', db.Integer, db.ForeignKey('rutinas.id'), primary_key=True),
    db.Column('ejercicio_id', db.Integer, db.ForeignKey('ejercicios.id'), primary_key=True)
)


class Medicion(db.Model):
    __tablename__ = 'mediciones'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    peso = db.Column(db.Float)
    altura = db.Column(db.Float)
    cintura = db.Column(db.Float)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('Cliente', back_populates='mediciones')
