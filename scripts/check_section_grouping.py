from urllib.request import urlopen
html = urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')
checks = {
    'plans section class': 'class="plans-section"' in html,
    'plans section header': 'class="plans-section-header"' in html,
    'selected item banner': 'class="selected-item-banner"' in html,
    'item details outside items section marker': 'id="item-details" class="item-details-host"' in html,
}
for key, value in checks.items():
    print(f'{key}: {value}')
