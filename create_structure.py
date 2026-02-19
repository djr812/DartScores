import os
import sys

# Create directory structure
dirs = [
    'app/models',
    'app/services', 
    'app/routes',
    'app/utils',
    'static/css',
    'static/js',
    'static/images',
    'templates'
]

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)
    print(f'Created directory: {dir_path}')

# Create empty __init__.py files
init_files = [
    'app/models/__init__.py',
    'app/services/__init__.py',
    'app/routes/__init__.py',
    'app/utils/__init__.py'
]

for file_path in init_files:
    with open(file_path, 'w') as f:
        f.write('')
    print(f'Created file: {file_path}')

print('Directory structure created successfully!')