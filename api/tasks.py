import tempfile

from celery import shared_task
import subprocess
import uuid
import os
from celery.utils.log import get_task_logger
from code_runner_service import settings
from .utils import ProgramingLanguagesEnum, ProgramResultDto, ProgramWithFileResultDto

DIR_PATH = os.path.join(settings.BASE_DIR, 'resources')
VENV_PATH = '/app/.venv/bin/python'
PHP_AUTOLOAD_PATH = os.getenv('PHP_AUTOLOAD_PATH', '/app/resources/php/vendor/autoload.php')
logger = get_task_logger(__name__)


ENV = os.getenv('ENV', 'dev')
STATIC_FILES_URL = "http://127.0.0.1:8080/static/" if ENV == "dev" else "http://prod_domain/static/"


STATIC_FILES_URL = ""
if ENV == "dev":
    STATIC_FILES_URL = "http://127.0.0.1:8080/static/"

if ENV == "prod":
    STATIC_FILES_URL = "http://prod_domain/static/"


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

    if programming_language == ProgramingLanguagesEnum.PYTHON.value:
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', VENV_PATH,
               container_path]
    elif programming_language == ProgramingLanguagesEnum.JAVASCRIPT.value:
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'node',
               container_path]
    elif programming_language == ProgramingLanguagesEnum.PHP.value:
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'php', '-r',
               f'require "{PHP_AUTOLOAD_PATH}"; include "{container_path}";']
    elif programming_language == ProgramingLanguagesEnum.CPP.value:
        compiled_path = f'/app/resources/{programming_language}/compiled_{unique_id}'
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'g++', container_path,
               '-o', compiled_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f'Error compiling C++ code: {result.stderr}')
            return ProgramResultDto(result.stdout, result.stderr, result.returncode).to_dict()
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', compiled_path]
    else:
        logger.error(f'Unsupported programming language: {programming_language}')
        return {'error': 'Unsupported programming language'}

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        logger.info(f'Execution result for {programming_language} code: {result}')

        return ProgramResultDto(result.stdout, result.stderr, result.returncode).to_dict()
    except subprocess.TimeoutExpired:
        logger.error(f'Execution time exceeded the limit for {programming_language} code')
        return {'error': 'Execution time exceeded the limit'}
    except subprocess.CalledProcessError as e:
        logger.error(f'Error executing {programming_language} code: {e}')
        return {'error': str(e)}
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@shared_task
def execute_code_with_file(source_code, programming_language, source_file, file_output_fromat):
    unique_id = uuid.uuid4()
    extension = {
        'python': 'py',
        'javascript': 'js',
        'php': 'php',
        'c++': 'cpp'
    }.get(programming_language, 'txt')

    temp_code_filename = os.path.join(DIR_PATH, f'{programming_language}/code_to_run_{unique_id}.{extension}')
    temp_output_dir = os.path.join(DIR_PATH, 'out')
    temp_output_filename = os.path.join(temp_output_dir, f'output_file_{unique_id}.{file_output_fromat}')

    container_code_path = f'/app/resources/{programming_language}/code_to_run_{unique_id}.{extension}'
    container_input_path = f'/app/resources/{programming_language}/input_file_{unique_id}.txt'
    container_output_path = f'/app/resources/out/output_file_{unique_id}.{file_output_fromat}'

    os.makedirs(os.path.dirname(temp_code_filename), exist_ok=True)
    os.makedirs(temp_output_dir, exist_ok=True)

    source_code = source_code.replace('INPUT_FILE_PATH', f"'{container_input_path}'")
    source_code = source_code.replace('OUTPUT_FILE_PATH', f"'{container_output_path}'")

    with open(temp_code_filename, 'w') as f:
        f.write(source_code)

    input_file_path = os.path.join(DIR_PATH, f'{programming_language}/input_file_{unique_id}.txt')
    with open(input_file_path, 'wb') as input_file:
        with open(source_file, 'rb') as src_file:
            input_file.write(src_file.read())

    if programming_language == ProgramingLanguagesEnum.PYTHON.value:
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', VENV_PATH,
               container_code_path]
    elif programming_language == ProgramingLanguagesEnum.JAVASCRIPT.value:
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'node',
               container_code_path]
    elif programming_language == ProgramingLanguagesEnum.PHP.value:
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'php', '-r',
               f'require "{PHP_AUTOLOAD_PATH}"; include "{container_code_path}";']
    elif programming_language == ProgramingLanguagesEnum.CPP.value:
        compiled_path = f'/app/resources/{programming_language}/compiled_{unique_id}'
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', 'g++',
               container_code_path, '-o', compiled_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f'Error compiling C++ code: {result.stderr}')
            return ProgramResultDto(result.stdout, result.stderr, result.returncode).to_dict()
        cmd = ['docker', 'run', '--rm', '-v', f'{DIR_PATH}:/app/resources', 'code_runner:latest', compiled_path]
    else:
        logger.error(f'Unsupported programming language: {programming_language}')
        return {'error': 'Unsupported programming language'}
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        logger.info(f'Execution result for {programming_language} code: {result}')
        logger.info(f'Checking if output file exists: {os.path.exists(temp_output_filename)}')

        if os.path.exists(temp_output_filename):
            output_filename = temp_output_filename.split('/')[-1]

            output_file_path = STATIC_FILES_URL + output_filename.replace('txt', file_output_fromat)
        else:
            output_file_path = None

        return ProgramWithFileResultDto(result.stdout, result.stderr, result.returncode, output_file_path).to_dict()
    except subprocess.TimeoutExpired:
        logger.error(f'Execution time exceeded the limit for {programming_language} code')
        return {'error': 'Execution time exceeded the limit'}
    except subprocess.CalledProcessError as e:
        logger.error(f'Error executing {programming_language} code: {e}')
        return {'error': str(e)}
    finally:
        if os.path.exists(temp_code_filename):
            os.remove(temp_code_filename)
        if os.path.exists(input_file_path):
            os.remove(input_file_path)

