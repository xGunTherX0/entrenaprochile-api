-- SQL to create the password_reset_tokens table for Postgres
-- Run this in your production database (after taking a backup)

CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
  id SERIAL PRIMARY KEY,
  token VARCHAR(128) NOT NULL UNIQUE,
  usuario_id INTEGER NOT NULL REFERENCES public.usuarios(id),
  expires_at TIMESTAMPTZ NOT NULL,
  used BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_usuario_id ON public.password_reset_tokens(usuario_id);
