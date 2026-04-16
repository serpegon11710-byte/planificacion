from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
checks = {
    'plans title prefix': 'Planificaciones de &quot;' in html or 'Planificaciones de "' in html,
    'plans section class': 'class="plans-section"' in html,
    'plans panel class': 'class="plans-panel"' in html,
}
for key, value in checks.items():
    print(f'{key}: {value}')
