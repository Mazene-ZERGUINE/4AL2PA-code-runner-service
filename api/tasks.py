from celery import shared_task
import subprocess
import uuid
import os
from celery.utils.log import get_task_logger

from api.utils import clean_tmp_directory
from code_runner_service import settings


DIR_PATH = os.path.join(settings.BASE_DIR, 'tmp')
logger = get_task_logger(__name__)


@shared_task
def run_code(source_code, programming_language):
    unique_id = uuid.uuid4()
    temp_filename = os.path.join(DIR_PATH, f'code_to_run_{unique_id}.txt')
    container_path = f'/app/code_to_run_{unique_id}.txt'

    with open(temp_filename, 'w') as f:
        f.write(source_code)

    if programming_language == 'python':
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app', 'code_runner:latest', 'python3', container_path]
    elif programming_language == 'javascript':
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app', 'code_runner:latest', 'node', container_path]
    else:
        return {'error': 'Unsupported programming language'}
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Execution time exceeded the limit'}



