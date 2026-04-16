from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
checks = {
    'modal form': 'id="plan-modal-form"' in html,
    'add modal button': 'class="open-plan-modal" data-mode="add"' in html,
    'delete modal button': 'data-mode="delete"' in html,
    'edit modal button': 'data-mode="edit"' in html,
}
for key, value in checks.items():
    print(f'{key}: {value}')
