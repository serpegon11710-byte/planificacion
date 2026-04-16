from urllib.request import urlopen
print(urlopen('http://127.0.0.1:5000/project/2/').read().decode('utf-8')[:800])
