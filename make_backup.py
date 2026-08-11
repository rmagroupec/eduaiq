import os
import zipfile

def zip_project():
    date_str = "2026_08_11"
    zip_name = f"eduaiq_backup_{date_str}.zip"
    project_dir = os.path.abspath(os.path.dirname(__file__))
    zip_path = os.path.join(project_dir, zip_name)

    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except Exception:
            pass

    exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.idea', '.vscode', 'env', 'ENV'}
    exclude_exts = {'.pyc', '.zip', '.tar', '.gz', '.log', '.mp4', '.mkv', '.avi', '.mov', '.webm'}

    print(f"Creating clean codebase backup zip: {zip_name}...")
    file_count = 0

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.venv')]
            for file in files:
                if file == zip_name or any(file.lower().endswith(ext) for ext in exclude_exts):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_dir)
                zipf.write(full_path, rel_path)
                file_count += 1

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print("[SUCCESS] Clean Backup Created Successfully!")
    print(f"File Name: {zip_name}")
    print(f"Path: {zip_path}")
    print(f"Total Files Zipped: {file_count}")
    print(f"Backup Size: {size_mb:.2f} MB")

if __name__ == "__main__":
    zip_project()
