from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
print('project edit button:', 'id="open-project-edit"' in html)
print('project delete button:', 'id="open-project-delete"' in html)
print('text button removed:', 'Editar proyecto</button>' not in html and 'Eliminar proyecto</button>' not in html)
