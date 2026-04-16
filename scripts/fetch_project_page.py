from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
checks = {
    'Guardar proyecto': 'Guardar proyecto' in html,
    'Fecha fin label': 'Fecha fin:' in html,
    'Nombre input': 'name="project_name"' in html,
    'End date input': 'name="end_date"' in html,
}
for key, value in checks.items():
    print(f'{key}: {value}')
