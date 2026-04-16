from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
print('item edit button present:', 'title="Editar item"' in html)
print('item delete button present:', 'title="Eliminar item"' in html)
print('emoji buttons removed:', '✎' not in html and '🗑' not in html)
