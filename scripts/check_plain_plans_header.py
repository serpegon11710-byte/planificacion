from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
print('plain title row:', 'class="section-header-row plans-title-row"' in html)
print('old boxed header removed:', 'class="plans-section-header"' not in html)
print('plans title text present:', 'Planificaciones de' in html)
