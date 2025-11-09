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
    # Clientes pueden recibir rutinas, pero en esta versión las rutinas las crea el Entrenador.
    # Mantenemos relación vacía por si se asocia en el futuro.
    # rutinas = db.relationship('Rutina', back_populates='cliente')
    mediciones = db.relationship('Medicion', back_populates='cliente')

    def __repr__(self):
        return f'<Cliente {self.id}>'


class Entrenador(db.Model):
    __tablename__ = 'entrenadores'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    speciality = db.Column(db.String(200))

    usuario = db.relationship('Usuario', back_populates='entrenador')
    rutinas = db.relationship('Rutina', backref='entrenador', lazy=True)

    def __repr__(self):
        return f'<Entrenador {self.id}>'


class Rutina(db.Model):
    __tablename__ = 'rutinas'
    id = db.Column(db.Integer, primary_key=True)
    entrenador_id = db.Column(db.Integer, db.ForeignKey('entrenadores.id'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    nivel = db.Column(db.String(50))
    es_publica = db.Column(db.Boolean, default=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # relación hacia ejercicios (puede mantenerse para futuros asignamientos)
    ejercicios = db.relationship('Ejercicio', secondary='rutina_ejercicio', back_populates='rutinas')

    def __repr__(self):
        return f'<Rutina {self.nombre}>'


class PlanAlimenticio(db.Model):
    __tablename__ = 'planes_alimenticios'
    id = db.Column(db.Integer, primary_key=True)
    entrenador_id = db.Column(db.Integer, db.ForeignKey('entrenadores.id'), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    contenido = db.Column(db.Text)
    es_publico = db.Column(db.Boolean, default=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    entrenador = db.relationship('Entrenador', backref='planes')

    def __repr__(self):
        return f'<Plan {self.nombre}>'


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


class SolicitudPlan(db.Model):
    __tablename__ = 'solicitudes_plan'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    rutina_id = db.Column(db.Integer, db.ForeignKey('rutinas.id'), nullable=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('planes_alimenticios.id'), nullable=True)
    estado = db.Column(db.String(50), default='pendiente')
    nota = db.Column(db.Text)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship('Cliente', backref='solicitudes')
    rutina = db.relationship('Rutina', backref='solicitudes')
    plan = db.relationship('PlanAlimenticio', backref='solicitudes')
