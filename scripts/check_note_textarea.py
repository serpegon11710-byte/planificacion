from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
print('modal textarea:', '<textarea name="note" id="modal-note"' in html)
print('legacy note input absent in modal:', '<input name="note" id="modal-note"' not in html)
