#!/usr/bin/env python3
import os
import sys

def main():
    src_path = os.path.join(os.path.dirname(__file__), 'src', 'main.py')

    if not os.path.isfile(src_path):
        print("❌ File src/main.py not found.")
        sys.exit(1)

    with open(src_path, 'rb') as f:
        code = compile(f.read(), src_path, 'exec')
        exec(code, {'__name__': '__main__'})

if __name__ == '__main__':
    main()