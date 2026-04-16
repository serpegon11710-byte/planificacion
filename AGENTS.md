AGENTS — Guía rápida

Nota: la documentación principal del repositorio se ha consolidado en la carpeta `docs/`.
Antes de editar, revisa los ficheros en [docs/](docs/), especialmente las guías para agentes y el formato de logs.

Este archivo sirve como punto de entrada para agentes (humanos o automatizados) que vayan a editar o revisar ficheros del repositorio.

Si vas a manipular scripts PowerShell (.ps1):

- Lee primero: PS1_AGENT_GUIDELINES.md
  - Ruta: [docs/PS1_AGENT_GUIDELINES.md](docs/PS1_AGENT_GUIDELINES.md)
- Consulta la tabla de codificación de caracteres: encoding.txt
  - Ruta: encoding.txt

Documentación de logs y utilidades:
- Formato del log: [docs/PLAN_LOG_FORMAT.md](docs/PLAN_LOG_FORMAT.md)
- Normalizar `plan.log`: [docs/NORMALIZE_PLAN_LOG.md](docs/NORMALIZE_PLAN_LOG.md)
 - DB schema changes: [Añadir nuevos campos a la BBDD](docs/DB_FIELD_ADDITION.md)
 - Inicializar app / crear DB: [docs/INIT_APP.md](docs/INIT_APP.md)

Buenas prácticas
- Antes de editar, abre `PS1_AGENT_GUIDELINES.md` y sigue las reglas descritas.
- Si añades nuevos caracteres no-ASCII, actualiza `encoding.txt` respetando el orden por código hexadecimal.

Contacto
- Si necesitas ajustar las normas, modifica `PS1_AGENT_GUIDELINES.md` y abre una PR con la justificación.
