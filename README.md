# Planificación — Aplicación simple

Aplicación mínima en Flask para organizar proyectos, ítems y planificaciones.

Requisitos:

- Python 3.8+
- Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Iniciar:

```powershell
python app.py
# luego abrir http://127.0.0.1:5000
```

Descripción rápida:

- Crear proyectos desde la página principal.
- Dentro de cada proyecto crear ítems y añadir planificaciones (recurrentes o puntuales).
- La base de datos es `plan.db` en la carpeta del proyecto y se crea/semilla al primer arranque.
