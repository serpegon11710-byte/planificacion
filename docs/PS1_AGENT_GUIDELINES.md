PS1 Agent Guidelines

Objetivo
- Establecer reglas claras para los agentes que editen scripts PowerShell (.ps1) en este repositorio.

Reglas obligatorias

- Uso de Write-Host
  - Todas las llamadas a `Write-Host` deben usar la forma:
    Write-Host ('...')
  - Cuando sea necesario incluir variables use formateo `-f` o concatenación dentro de la expresión pasada a `Write-Host ('...')`.
    Ejemplo: Write-Host ('PID almacenado en {0}: {1}' -f $pidFile, $pid)

- Caracteres no-ASCII / acentuados
  - No escribir caracteres acentuados o símbolos no-ASCII directamente en literales entre comillas.
  - Representar esos caracteres usando la forma `[char]0xHHHH` dentro de la concatenación o la cadena.
    Ejemplo: 'detenci' + [char]0x00F3 + 'n'  -> produce "detención"

- Archivo `encoding.txt`
  - Cuando se detecte un nuevo carácter no-ASCII en un `.ps1`, añádalo a `encoding.txt`.
  - Formato en `encoding.txt`:
    "á" = "" + [char]0x00E1 + ""
  - Mantener el orden por el valor hexadecimal (`0x00E1`, `0x00E9`, ...). Insertar nuevas entradas en el lugar correcto para mantener el archivo ordenado.

- Doble comprobación y pruebas
  - Antes de confirmar un cambio en scripts `.ps1`, ejecutar el script localmente en PowerShell para comprobar que no hay errores de sintaxis.
  - Verificar visualmente que la salida de la consola muestra los acentos correctamente tanto en `cmd.exe` (si se utiliza) como en PowerShell.

Notas para agentes
- Sea conservador: cuando convierta literales con acentos, prefiera usar concatenaciones y `[char]` para asegurar compatibilidad con distintas codificaciones.
- Evite mezclar comillas simples y dobles sin escaparlas; utilice la forma `Write-Host ('...')` para unificar.

Ejemplo rápido

Original (no permitido):
Write-Host "No se ha encontrado el identificador PID"

Correcto:
Write-Host ('No se ha encontrado el identificador PID')

Con acento mediante [char]:
Write-Host ('Para forzar la detenci' + [char]0x00F3 + ', invoca: ''stop_app.bat /f''')

Fin.
