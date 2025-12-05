    # EntrenaProChile (EntrenaPro)

    Plataforma web para la gestión de clientes, rutinas de entrenamiento y planes alimenticios.
    Frontend desacoplado (Vue + Tailwind) y Backend en Python/Flask con API REST.

    ---

    ## Tabla de contenido
    - [Descripción](#descripción)
    - [Diseño visual y estilo](#diseño-visual-y-estilo)
    - [Arquitectura y tecnologías](#arquitectura-y-tecnologías)
    - [Endpoints principales](#endpoints-principales)
    - [Requerimientos](#requerimientos)
    - [Roles y equipo](#roles-y-equipo)
    - [Migración SQLite → PostgreSQL](#migración-sqlite--postgresql)
    - [Diagramas y artefactos](#diagramas-y-artefactos)
    - [Conclusiones y próximos pasos](#conclusiones-y-próximos-pasos)

    ---

    ## Descripción
    EntrenaPro es una plataforma diseñada para centralizar y simplificar la gestión de clientes,
    planes de entrenamiento y dietas. Permite a entrenadores publicar rutinas y planes, y a
    clientes registrar mediciones y seguir su progreso.

    ## Diseño visual y estilo
    - Color primario (fondo): `#FFFFFF` (blanco)
    - Color secundario (texto / headers): `#000000` o azul oscuro `#0A192F`
    - Color de acento: azul vibrante (ej. `#007BFF`) para botones y enlaces
    - Tipografía sugerida: Montserrat o Roboto

    ## Arquitectura y tecnologías
    - Arquitectura desacoplada: Frontend y Backend desplegados separadamente.
    - Frontend: Vue 3, Vite, Tailwind CSS. Deploy en Netlify.
    - Backend: Python, Flask, SQLAlchemy. Deploy en Render.
    - Bases de datos: SQLite en desarrollo; PostgreSQL en producción.

    ### Patrones de diseño y estructura
    El backend sigue un **patrón en capas** (Layered Architecture) que separa la capa de
    presentación (endpoints/API), la capa de negocio (servicios) y la capa de acceso a datos.
    Adicionalmente se emplea el **Patrón Repositorio** para abstraer la lógica de persistencia
    y facilitar el soporte de múltiples motores (SQLite en desarrollo y PostgreSQL en producción).
    La API se expone siguiendo principios REST, manteniendo una clara separación de
    responsabilidades entre capas.

    ### Stack resumido
    - **Frontend:** Vue 3, Vite, Tailwind
    - **Backend:** Python, Flask, SQLAlchemy
    - **DB:** SQLite (dev), PostgreSQL (prod)
    - **Deploy:** Netlify (frontend), Render (backend)

    ## Endpoints principales
    Ejemplos y comportamiento esperado:

    - `POST /api/usuarios/login` — Autenticar usuario.
        - Request: `{ "email": "", "contrasena": "" }`
        - 200: `{ "token": "JWT_string" }`
        - 401: credenciales inválidas; 403: cuenta bloqueada

    - `GET /api/perfil` — Obtener info del usuario autenticado (header Authorization)

    - `GET /api/rutinas` — Listar rutinas públicas

    - `POST /api/mediciones` — Registrar mediciones: `{ "peso": 75.5, "altura": 1.75 }`

    ## Requerimientos

    ### Funcionales (resumen)
    - RF01: Inicio de sesión con email y contraseña
    - RF02: Bloqueo tras 3 intentos fallidos (30 minutos)
    - RF03: Redirección según rol (cliente/entrenador/admin)
    - RF04: Panel Admin (CRUD de usuarios y gestión de contenido)
    - RF05: Panel Entrenador (CRUD de rutinas/planes)
    - RF06: Panel Cliente (explorar y seleccionar rutinas/planes)
    - RF08: Generación de dieta basada en TMB

    ### No funcionales (resumen)
    - Responsividad (móvil → escritorio)
    - Seguridad: Bcrypt para contraseñas, JWT para autenticación, HTTPS obligatorio
    - Rendimiento: 95% respuestas < 500 ms bajo 100 usuarios concurrentes
    - Mantenibilidad: diseño en capas y documentación

    ## Roles y equipo
    - Equipo CFMC: Carlos Cancino (Arquitecto / Backend) y Felipe Marchant (UX/UI / Frontend)
    - Roles habituales: Arquitecto, Desarrollador Backend, Desarrollador Frontend, Diseñador UX/UI, Líder/QA

    ## Migración SQLite → PostgreSQL (análisis)
    - Problema observado: operaciones permitidas por SQLite que PostgreSQL rechaza
        (ej. establecer `usuario_id = NULL` cuando la columna tiene restricción `NOT NULL`).
    - Lección: mantener el esquema y las restricciones de producción en el entorno de
        desarrollo, adaptar la lógica de negocio y añadir pruebas que cubran diferencias entre motores.

    ## Diagramas y artefactos
    El documento original incluye diagramas (BD, clases, secuencias y casos de uso). Para
    ver los diagramas, abre `Documentacion cfmc.docx` en la raíz del proyecto.

    ## Conclusiones y próximos pasos
    - Integrar módulo de pagos (ej. Stripe) para monetización.
    - Añadir módulo de chat en tiempo real.
    - Mejorar panel de administración con analíticas y reportes.

    ---

    Documento convertido desde `Documentacion cfmc.docx` (26 sept 2025) — autores: Luis Felipe Marchant y Carlos Cancino.

    Si quieres que haga un resumen ejecutivo, que agregue diagramas en la carpeta `docs/` o que
    commitée y haga push del README, indícalo y lo ejecuto.

