-- Idempotent schema fixes for EntrenaProChile
-- Run as a DB superuser or a user with ALTER privileges against the production DB.
-- Usage: psql "$DATABASE_URL" -f scripts/fix_entrenadores_schema.sql

BEGIN;

-- usuarios table columns
ALTER TABLE IF EXISTS usuarios
  ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT true,
  ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP NULL;

-- entrenadores table columns
ALTER TABLE IF EXISTS entrenadores
  ADD COLUMN IF NOT EXISTS speciality VARCHAR(255),
  ADD COLUMN IF NOT EXISTS bio TEXT,
  ADD COLUMN IF NOT EXISTS telefono VARCHAR(50),
  ADD COLUMN IF NOT EXISTS instagram_url VARCHAR(255),
  ADD COLUMN IF NOT EXISTS youtube_url VARCHAR(255);

-- rutinas table: some deployments are missing these columns; add idempotently
ALTER TABLE IF EXISTS rutinas
  ADD COLUMN IF NOT EXISTS seccion_descripcion TEXT,
  ADD COLUMN IF NOT EXISTS objetivo_principal TEXT,
  ADD COLUMN IF NOT EXISTS enfoque_rutina TEXT,
  ADD COLUMN IF NOT EXISTS cualidades_clave TEXT,
  ADD COLUMN IF NOT EXISTS duracion_frecuencia VARCHAR(255),
  ADD COLUMN IF NOT EXISTS material_requerido TEXT,
  ADD COLUMN IF NOT EXISTS instrucciones_estructurales TEXT,
  ADD COLUMN IF NOT EXISTS link_url VARCHAR(1024),
  ADD COLUMN IF NOT EXISTS nivel VARCHAR(50),
  ADD COLUMN IF NOT EXISTS es_publica BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS creado_en TIMESTAMP;

-- revoked_tokens table (used for JWT revocation)
CREATE TABLE IF NOT EXISTS revoked_tokens (
  id SERIAL PRIMARY KEY,
  jti VARCHAR(255) UNIQUE NOT NULL,
  revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMIT;

-- Notes:
-- - These ALTERs are idempotent and safe to re-run.
-- - If your DB user lacks ALTER privileges, ask an admin or run via the Render dashboard "Launch Shell".
-- - After applying, redeploy is still recommended to ensure code and schema align.
