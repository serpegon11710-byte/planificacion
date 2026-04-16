from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
print('plans panel class present:', 'class="plans-panel"' in html)
