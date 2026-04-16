from urllib.request import urlopen
print(urlopen('http://127.0.0.1:5000/calendar?view=week&date=2026-04-26').read().decode('utf-8')[:2000])
