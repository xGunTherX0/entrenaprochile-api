-- Añade la columna entrenador_id a la tabla rutinas si falta y crea la FK
ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS entrenador_id INTEGER;
ALTER TABLE rutinas ADD CONSTRAINT IF NOT EXISTS fk_rutinas_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id);
