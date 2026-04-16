from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
checks = {
    'project modal': 'id="project-modal-form"' in html,
    'item modal': 'id="item-modal-form"' in html,
    'open project edit': 'id="open-project-edit"' in html,
    'open item add': 'id="open-item-add"' in html,
    'delete item route hint': '/item/' in html,
}
for key, value in checks.items():
    print(f'{key}: {value}')
