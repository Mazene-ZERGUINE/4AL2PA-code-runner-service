from celery import shared_task
import subprocess
import uuid
import os
from celery.utils.log import get_task_logger
from code_runner_service import settings

DIR_PATH = os.path.join(settings.BASE_DIR, 'resources')
VENV_PATH = '/app/.venv/bin/python'
PHP_AUTOLOAD_PATH = os.getenv('PHP_AUTOLOAD_PATH', '/app/resources/php/vendor/autoload.php')
logger = get_task_logger(__name__)

@shared_task
def run_code(source_code, programming_language):
    unique_id = uuid.uuid4()
    extension = {
        'python': 'py',
        'javascript': 'js',
        'php': 'php',
        'c++': 'cpp'
    }.get(programming_language, 'txt')
    temp_filename = os.path.join(DIR_PATH, f'{programming_language}/code_to_run_{unique_id}.{extension}')
    container_path = f'/app/resources/{programming_language}/code_to_run_{unique_id}.{extension}'

    os.makedirs(os.path.dirname(temp_filename), exist_ok=True)

    with open(temp_filename, 'w') as f:
        f.write(source_code)

    if programming_language == 'python':
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', VENV_PATH, container_path]
    elif programming_language == 'javascript':
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'node', container_path]
    elif programming_language == 'php':
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'php', '-r', f'require "{PHP_AUTOLOAD_PATH}"; include "{container_path}";']
    elif programming_language == 'c++':
        compiled_path = f'/app/resources/{programming_language}/compiled_{unique_id}'
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'g++', container_path, '-o', compiled_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f'Error compiling C++ code: {result.stderr}')
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', compiled_path]
    else:
        logger.error(f'Unsupported programming language: {programming_language}')
        return {'error': 'Unsupported programming language'}

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        logger.info(f'Execution result for {programming_language} code: {result}')

        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        logger.error(f'Execution time exceeded the limit for {programming_language} code')
        return {'error': 'Execution time exceeded the limit'}
    except subprocess.CalledProcessError as e:
        logger.error(f'Error executing {programming_language} code: {e}')
        return {'error': str(e)}
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
