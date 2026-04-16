# Añadir nuevos campos a la base de datos: procedimiento seguro

Resumen
- Cada vez que se añade un nuevo campo (columna) al modelo y al código, hay que verificar que la base de datos existente lo soporte antes de arrancar la aplicación. Este documento recoge pasos seguros para comprobar y corregir la DB local.

Checklist rápido
- Backup: siempre copia la DB antes de cualquier cambio.
- Verificar esquema actual.
- Probar arrancar la aplicación (buscar errores).
- Aplicar `ALTER TABLE` o migración si falta la columna.
- Volver a arrancar y comprobar que no hay errores.

Pasos detallados

1) Hacer copia de seguridad
- Copia manual (Linux/macOS):
```bash
cp path/to/your.db path/to/your.db.bak.$(date +%Y%m%d%H%M%S)
```
- En Windows PowerShell:
```powershell
Copy-Item .\your.db ".\your.db.bak.$((Get-Date).ToString('yyyyMMddHHmmss'))"
```

2) Comprobar columnas de la tabla (SQLite)
```bash
sqlite3 path/to/your.db "PRAGMA table_info(project);"
```
Busca el nombre de la columna nueva (por ejemplo `start_date`). Si no aparece, la DB necesita actualizarse.

3) Intentar arrancar la app y leer el stack trace
- Ejecuta la app (por ejemplo `python app.py` o `flask run`) y observa si hay un error como `sqlite3.OperationalError: no such column: project.start_date`. Si existe, pasar al paso 4.

4) Corregir la DB rápidamente (opción directa para SQLite)
- Añadir columna (tipo seguro: `TEXT`):
```bash
sqlite3 path/to/your.db "ALTER TABLE project ADD COLUMN start_date TEXT;"
```
o desde Python (ejemplo con SQLAlchemy):
```python
from sqlalchemy import create_engine
engine = create_engine('sqlite:///path/to/your.db')
with engine.connect() as conn:
    conn.execute("ALTER TABLE project ADD COLUMN start_date TEXT;")
    conn.commit()
```
Nota: SQLite solo soporta `ADD COLUMN` simple; para cambios complejos crea una nueva tabla y migra datos.

5) Alternativa recomendada: usar migraciones (Alembic)
- Crear revisión: `alembic revision --autogenerate -m "Add start_date to project"`
- Aplicar: `alembic upgrade head`
Ventaja: historial, reversible y seguro en entornos con más control.

Recomendación de trabajo (obligatoria)
- En este repositorio usamos `Flask-Migrate`/`Alembic` para versionar cambios. Antes de abrir una PR que modifique modelos:
    1. Ejecuta `scripts/migrate.ps1 -Action migrate -Message "..."` para generar la migración.
    2. Revisa la migración auto-generada en `migrations/versions/`.
    3. Ejecuta `scripts/migrate.ps1 -Action upgrade` para aplicar los cambios localmente.
    4. Arranca la aplicación y verifica que no explote.

Si prefieres comandos `flask db ...`, consulta `docs/MIGRATIONS.md`.

6) Verificar y probar
- Ejecuta `PRAGMA table_info(project);` otra vez para confirmar.
- Arranca la app y revisa que no haya excepciones en los logs.
- Prueba las rutas relevantes que usan el campo nuevo (crear/editar proyecto).

7) Buenas prácticas
- Añade tests que cubran la lectura/escritura del nuevo campo.
- Si el campo puede contener NULL, asegúrate de que el código lo maneje.
- Para despliegues en servidores, aplica migración en mantenimiento (downtime mínimo) y verifica backups.

Ejemplo de script seguro (opcional)
- Script Python rápido que hace backup y añade la columna si falta:
```python
# scripts/add_start_date_safe.py
import shutil, sqlite3, time, os
db = 'path/to/your.db'
bak = f'{db}.bak.{time.strftime("%Y%m%d%H%M%S")}'
shutil.copy2(db, bak)
conn = sqlite3.connect(db)
cur = conn.cursor()
cols = [r[1] for r in cur.execute("PRAGMA table_info(project);").fetchall()]
if 'start_date' not in cols:
    cur.execute("ALTER TABLE project ADD COLUMN start_date TEXT;")
    conn.commit()
print('Done. Backup:', bak)
conn.close()
```

Contacto
- Si quieres, puedo preparar un script que haga el `ALTER TABLE` y cree el backup automáticamente en tu repo.
