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
    activo = db.Column(db.Boolean, default=True)
    # Número de intentos fallidos de login consecutivos
    failed_attempts = db.Column(db.Integer, default=0)
    # Si está bloqueado temporalmente, datetime hasta el que permanece bloqueado
    locked_until = db.Column(db.DateTime, nullable=True)
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
    bio = db.Column(db.Text)
    telefono = db.Column(db.String(50))
    instagram_url = db.Column(db.String(255))
    youtube_url = db.Column(db.String(255))

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
    # Nueva columna: sección de la descripción seleccionada por el entrenador
    seccion_descripcion = db.Column(db.String(200))
    # Campos separados para cada sección de la descripción (más flexibles que un select)
    objetivo_principal = db.Column(db.Text)
    enfoque_rutina = db.Column(db.Text)
    cualidades_clave = db.Column(db.Text)
    duracion_frecuencia = db.Column(db.Text)
    material_requerido = db.Column(db.Text)
    instrucciones_estructurales = db.Column(db.Text)
    # URL opcional asociada a la rutina (por ejemplo página externa, video, recurso)
    link_url = db.Column(db.String(512))
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


class ContentReview(db.Model):
    __tablename__ = 'content_review'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))  # 'rutina' | 'plan'
    content_id = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(50), default='pendiente')
    creado_por = db.Column(db.Integer, nullable=True)  # usuario_id who created the content
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContentReview {self.tipo}:{self.content_id} {self.estado}>'


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


class RevokedToken(db.Model):
    __tablename__ = 'revoked_tokens'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(128), unique=True, nullable=False)
    revoked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RevokedToken {self.jti}>'
