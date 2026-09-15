import subprocess
import zipfile
import os
import datetime

project_root = r"E:\Rackle Infotech\eduaiq-fixed\eduaiq"

# Get git status files
git_output = subprocess.check_output(['git', 'status', '--porcelain'], cwd=project_root, text=True).splitlines()

file_set = set()
for line in git_output:
    path = line[3:].strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    norm_path = os.path.normpath(path)
    full_path = os.path.join(project_root, norm_path)
    if os.path.isfile(full_path) and not norm_path.startswith('.gemini') and not norm_path.startswith('tmp') and norm_path != 'db.sqlite3':
        file_set.add(norm_path)

# Also check files modified today
today = datetime.date(2026, 9, 10)
for root, dirs, files in os.walk(project_root):
    dirs[:] = [d for d in dirs if d not in ['.git', 'venv', 'env', 'node_modules', '.gemini', 'tmp', '__pycache__']]
    for file in files:
        if file == 'db.sqlite3' or file.endswith('.zip') or file.endswith('.pyc'):
            continue
        filepath = os.path.join(root, file)
        relpath = os.path.normpath(os.path.relpath(filepath, project_root))
        try:
            mtime = datetime.date.fromtimestamp(os.path.getmtime(filepath))
            if mtime == today and relpath not in file_set:
                file_set.add(relpath)
        except Exception:
            pass

zip_filename = os.path.join(project_root, 'edited_files_today.zip')

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for f in sorted(file_set):
        full_f = os.path.join(project_root, f)
        # Store in zip using posix forward slashes
        zip_arcname = f.replace('\\', '/')
        zipf.write(full_f, zip_arcname)

print(f"ZIP_SUCCESS: {zip_filename}")
print(f"UNIQUE_FILES_COUNT: {len(file_set)}")

with open(os.path.join(project_root, 'tmp_zip_list.txt'), 'w', encoding='utf-8') as out:
    for f in sorted(file_set):
        out.write(f.replace('\\', '/') + '\n')
