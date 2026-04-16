from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
checks = {
    'items header row': 'class="section-header-row"' in html,
    'project section class': 'class="project-section"' in html,
    'items section class': 'class="items-section"' in html,
    'plans panel class': 'class="plans-panel"' in html,
}
for key, value in checks.items():
    print(f'{key}: {value}')
