import os
from sqlalchemy import create_engine, text

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('DATABASE_URL not set')
    raise SystemExit(1)
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(db_url)
with engine.begin() as conn:
    try:
        # find entrenador for usuario_id=2 (admin)
        row = conn.execute(text("SELECT id, usuario_id FROM entrenadores WHERE usuario_id = 2 LIMIT 1")).fetchone()
        print('entrenador row:', row)
        if not row:
            print('No entrenador for usuario_id=2')
        else:
            entrenador_id = row[0]
            # insert plan
            conn.execute(text("INSERT INTO planes_alimenticios (entrenador_id, nombre, descripcion, contenido, es_publico) VALUES (:eid,:nombre,:desc,:cont, true)"),
                         {'eid': entrenador_id, 'nombre': 'Plan-directo', 'desc': 'Insertado directo', 'cont':'Desayuno: directo'})
            print('Inserted plan directly')
    except Exception as e:
        print('Insert failed:', e)
