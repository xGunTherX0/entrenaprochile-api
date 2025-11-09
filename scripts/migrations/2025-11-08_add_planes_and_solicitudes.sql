-- Migration: add planes_alimenticios and solicitudes_plan tables
-- Run this on Postgres production. Review before applying.

CREATE TABLE IF NOT EXISTS planes_alimenticios (
  id SERIAL PRIMARY KEY,
  entrenador_id INTEGER NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  descripcion TEXT,
  contenido TEXT,
  es_publico BOOLEAN DEFAULT FALSE,
  creado_en TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- FK: entrenador_id -> entrenadores(id)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
    WHERE tc.table_name = 'planes_alimenticios' AND tc.constraint_type = 'FOREIGN KEY'
  ) THEN
    BEGIN
      ALTER TABLE planes_alimenticios
      ADD CONSTRAINT fk_planes_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id);
    EXCEPTION WHEN duplicate_object THEN
      -- ignore
    END;
  END IF;
END$$;

-- Solicitudes de plan (vincula cliente con rutina o plan)
CREATE TABLE IF NOT EXISTS solicitudes_plan (
  id SERIAL PRIMARY KEY,
  cliente_id INTEGER NOT NULL,
  rutina_id INTEGER,
  plan_id INTEGER,
  estado VARCHAR(50) DEFAULT 'pendiente',
  nota TEXT,
  creado_en TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- FKs for solicitudes_plan
DO $$
BEGIN
  -- cliente_id -> clientes(id)
  IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage ccu WHERE ccu.table_name = 'solicitudes_plan' AND ccu.column_name = 'cliente_id') THEN
    BEGIN
      ALTER TABLE solicitudes_plan ADD CONSTRAINT fk_solicitudes_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id);
    EXCEPTION WHEN duplicate_object THEN
      NULL;
    END;
  END IF;

  -- rutina_id -> rutinas(id)
  IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage ccu WHERE ccu.table_name = 'solicitudes_plan' AND ccu.column_name = 'rutina_id') THEN
    BEGIN
      ALTER TABLE solicitudes_plan ADD CONSTRAINT fk_solicitudes_rutina FOREIGN KEY (rutina_id) REFERENCES rutinas(id);
    EXCEPTION WHEN duplicate_object THEN
      NULL;
    END;
  END IF;

  -- plan_id -> planes_alimenticios(id)
  IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage ccu WHERE ccu.table_name = 'solicitudes_plan' AND ccu.column_name = 'plan_id') THEN
    BEGIN
      ALTER TABLE solicitudes_plan ADD CONSTRAINT fk_solicitudes_plan FOREIGN KEY (plan_id) REFERENCES planes_alimenticios(id);
    EXCEPTION WHEN duplicate_object THEN
      NULL;
    END;
  END IF;
END$$;

-- Indexes to speed lookups
CREATE INDEX IF NOT EXISTS idx_planes_entrenador_id ON planes_alimenticios (entrenador_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_cliente_id ON solicitudes_plan (cliente_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_rutina_id ON solicitudes_plan (rutina_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_plan_id ON solicitudes_plan (plan_id);
