Mini PWA móvil para mostrar eventos (solo lectura) y notas.

- Abrir `mobile/index.html` en navegador (preferible desde el mismo host donde corre la app Flask).
- La app usa `localStorage` para guardar eventos y notas.
- Pulsar "Sincronizar" para descargar eventos desde el servidor (por defecto ` /api/events `).
- La sincronización borra los eventos locales y los reemplaza por los del servidor.

Config:
- Cambia la URL de la API en el campo superior si tu servidor expone los eventos en otra ruta.
