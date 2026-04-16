# Inicializar la aplicación y la base de datos

Este documento explica cómo comprobar si la base de datos `plan.db` existe y crearla automáticamente si falta, usando el helper `init_app.bat` incluido en la raíz del proyecto.

Cuando renombres o elimines `plan.db` (por ejemplo durante pruebas), usa este script antes de arrancar la aplicación para recrear la DB y aplicar migraciones ligeras.

Uso (Windows)

1. Abre PowerShell en la raíz del proyecto.
2. Ejecuta:
```powershell
.\init_app.bat
```

Comportamiento
- Si `plan.db` existe: el script imprime "Database exists" y finaliza con código 0.
- Si `plan.db` NO existe: el script intenta ejecutar `app.init_db()` usando el `python` del venv (`.venv\Scripts\python.exe`). Si no existe venv intenta con el `python` del sistema.
- El script devuelve código 0 si la creación/initialización ha sido exitosa; devuelve código distinto de 0 en caso de error.

Consejos
- Después de crear la DB, si has modificado modelos, aplica migraciones con:
```powershell
.\scripts\migrate.ps1 -Action migrate -Message "Describe change"
.\scripts\migrate.ps1 -Action upgrade
```
- Para entornos no Windows usa el helper `scripts/run_init_db.ps1` o ejecuta directamente `python -c "import app; app.init_db()"` desde el entorno virtual.

Entrada en el flujo de trabajo
- Antes de arrancar la app en un entorno donde no estés seguro del estado de la DB, ejecuta `init_app.bat`.
- Añade en tu checklist de PRs: "He ejecutado `init_app.bat` y `scripts/migrate.ps1 -Action migrate` si he cambiado modelos".
