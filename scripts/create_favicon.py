import base64
import os

DATA = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='

def main():
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'favicon.ico')
    with open(out_path, 'wb') as fh:
        fh.write(base64.b64decode(DATA))
    print('Wrote', out_path)

if __name__ == '__main__':
    main()
