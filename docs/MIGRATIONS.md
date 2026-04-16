# Migraciones (Alembic / Flask-Migrate)

Propósito
- Usar migraciones versionadas para aplicar cualquier cambio en el esquema de la base de datos y evitar arrancadas que fallen por columnas/tipos faltantes.

Política obligatoria
- Cada vez que se modifica un modelo (añadir/renombrar/quitar columna, tabla, índices, etc.) debes:
  1. Crear una migración (autogenerate cuando sea posible).
  2. Ejecutar la migración localmente contra tu DB de desarrollo.
  3. Arrancar la aplicación y verificar que no hay errores (logs y rutas afectadas).
  4. Añadir la migración al control de versiones y abrir PR.

Instalación
```bash
pip install -r requirements.txt
```

Inicializar (solo la primera vez)
```powershell
$env:FLASK_APP='app.py'
.\.venv\Scripts\python.exe -m flask db init
```

Flujo común
- Crear migración (autogenerate):
```powershell
$env:FLASK_APP='app.py'
.\.venv\Scripts\python.exe -m flask db migrate -m "Add start_date to project"
```
- Aplicar migraciones (localmente):
```powershell
$env:FLASK_APP='app.py'
.\.venv\Scripts\python.exe -m flask db upgrade
```
- Revertir una migración (última):
```powershell
$env:FLASK_APP='app.py'
.\.venv\Scripts\python.exe -m flask db downgrade -1
```

Notas importantes
- `alembic`/`Flask-Migrate` intentan autogenerar cambios; revisa siempre la migración generada antes de aplicarla.
- En SQLite algunas operaciones complejas no pueden autogenerarse y requieren editar la migración manualmente (crear tabla nueva, copiar datos, renombrar, etc.).
- No olvides hacer backup de la DB antes de aplicar cambios en entornos no recreables.

Integración en el flujo de trabajo
- Añade una verificación en tu PR checklist: "Migraciones añadidas y probadas localmente".
- Si tu despliegue automatizado usa CI, añade paso `alembic upgrade head` en el despliegue para aplicar migraciones.

Uso del helper `scripts/migrate.ps1`
- Hay un helper en `scripts/migrate.ps1` para facilitar comandos comunes (ver README en el script). Úsalo como alternativa a ejecutar `flask db ...` manualmente.
