import os
from django.conf import settings


def clean_tmp_directory():
    tmp_dir_path = os.path.join(settings.BASE_DIR, 'tmp')
    files = os.listdir(tmp_dir_path)
    file_count = len(files)
    if file_count > 50:
        for file_name in files:
            file_path = os.path.join(tmp_dir_path, file_name)
            os.remove(file_path)
        return f"Deleted {file_count} files from the tmp directory."
    else:
        return f"Total files in tmp directory: {file_count}. No deletion performed."
