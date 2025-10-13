# EntrenaProChile API

Esta es la API para el proyecto EntrenaProChile.

## Descripción del Proyecto

**EntrenaProChile** es una plataforma web integral diseñada para simplificar y centralizar la gestión de clientes, rutinas de entrenamiento y planes alimenticios.

El objetivo principal es centralizar y simplificar la gestión de clientes, planes de entrenamiento y dietas en una plataforma única y fácil de usar.

### Roles de Usuario

La plataforma soporta tres roles principales:

1.  **Administrador:** Puede gestionar usuarios y contenido.
2.  **Entrenador:** Puede crear, leer, actualizar y eliminar (CRUD) sus propias rutinas y planes alimenticios.
3.  **Cliente:** Puede registrar sus mediciones corporales, ver su progreso en gráficas y seleccionar las rutinas y planes asignados por su entrenador.

## Características

- Registro de nuevos usuarios.
- Autenticación de usuarios existentes.
- Hash de contraseñas para un almacenamiento seguro.

## Stack Tecnológico

- **Backend:** Flask
- **Base de Datos:** PostgreSQL (en producción), SQLite (en desarrollo)
- **ORM:** SQLAlchemy
- **Despliegue:** Gunicorn
- **CORS:** Flask-Cors

## Configuración del Proyecto

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/xGunTherx0/entrenaprochile-api.git
    cd entrenaprochile-api
    ```

2.  **Crear un entorno virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    pip install -r backend/requirements.txt
    ```

## Configuración de la Base de Datos

-   **Desarrollo:** La aplicación utiliza una base de datos SQLite por defecto llamada `entrenapro.db` que se creará en el directorio `database`.
-   **Producción:** La aplicación está configurada para usar una base de datos PostgreSQL. La URL de conexión se debe proporcionar a través de la variable de entorno `DATABASE_URL`.

## Cómo Ejecutar la Aplicación

Para ejecutar la aplicación en modo de desarrollo, puedes usar el servidor de desarrollo de Flask:

```bash
export FLASK_APP=backend/app.py # En Windows: set FLASK_APP=backend/app.py
flask run
```

## Endpoints de la API

### Registro de Usuario

-   **URL:** `/api/usuarios/register`
-   **Método:** `POST`
-   **Body (JSON):**
    ```json
    {
      "email": "usuario@example.com",
      "nombre": "Nombre de Usuario",
      "password": "tu_contraseña"
    }
    ```

### Inicio de Sesión de Usuario

-   **URL:** `/api/usuarios/login`
-   **Método:** `POST`
-   **Body (JSON):**
    ```json
    {
      "email": "usuario@example.com",
      "password": "tu_contraseña"
    }
    ```
