from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/plan/8/edit').read().decode('utf-8')
checks = {
    'Editar planificación': 'Editar planificación' in html,
    'Guardar cambios': 'Guardar cambios' in html,
    'Todo el día': 'Todo el día' in html,
    'kind select': 'name="kind"' in html,
}
for key, value in checks.items():
    print(f'{key}: {value}')
