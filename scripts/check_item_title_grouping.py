from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
print('selected item inline:', 'class="selected-item-inline"' in html)
print('old selected banner removed:', 'class="selected-item-banner"' not in html)
print('plans header present:', 'class="plans-section-header"' in html)
