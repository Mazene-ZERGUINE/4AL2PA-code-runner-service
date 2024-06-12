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
OUT_DIR = os.path.join(DIR_PATH, 'out/')


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
def execute_code_with_files(source_code, programming_language, source_files, output_files_formats):
    unique_id = uuid.uuid4()
    extension = {
        'python': 'py',
        'javascript': 'js',
        'php': 'php',
        'c++': 'cpp'
    }.get(programming_language, 'txt')

    temp_code_filename = os.path.join(DIR_PATH, f'{programming_language}/code_to_run_{unique_id}.{extension}')
    temp_output_dir = os.path.join(DIR_PATH, 'out')
    container_code_path = f'/app/resources/{programming_language}/code_to_run_{unique_id}.{extension}'

    os.makedirs(os.path.dirname(temp_code_filename), exist_ok=True)
    os.makedirs(temp_output_dir, exist_ok=True)

    # Prepare input files
    container_input_paths = []
    for idx, source_file in enumerate(source_files):
        file_extension = os.path.splitext(source_file)[1]
        container_input_path = f'/app/resources/{programming_language}/input_file_{unique_id}_{idx}{file_extension}'
        container_input_paths.append(container_input_path)
        input_file_path = os.path.join(DIR_PATH, f'{programming_language}/input_file_{unique_id}_{idx}{file_extension}')
        with open(input_file_path, 'wb') as input_file:
            with open(source_file, 'rb') as src_file:
                input_file.write(src_file.read())
        source_code = source_code.replace(f'INPUT_FILE_PATH_{idx}', f"'{container_input_path}'")

    # Prepare output files if output_files_formats is not empty or null
    output_file_paths = []
    if output_files_formats:
        for idx, file_output_format in enumerate(output_files_formats):
            container_output_path = f'/app/resources/out/output_file_{unique_id}_{idx}.{file_output_format}'
            output_file_paths.append(container_output_path)
            source_code = source_code.replace(f'OUTPUT_FILE_PATH_{idx}', f"'{container_output_path}'")

    with open(temp_code_filename, 'w') as f:
        f.write(source_code)

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

        output_paths = []
        if output_file_paths:  # Check if there are output files to process
            for path in output_file_paths:
                filename = path.split('/')[-1]
                local_path = OUT_DIR + filename
                logger.error(local_path)
                if os.path.exists(local_path):
                    output_filename = os.path.basename(local_path)
                    output_url = STATIC_FILES_URL + output_filename
                    output_paths.append(output_url)
                else:
                    logger.warning(f'Output file not found: {local_path}')

        return ProgramWithFileResultDto(result.stdout, result.stderr, result.returncode, output_paths).to_dict()
    except subprocess.TimeoutExpired:
        logger.error(f'Execution time exceeded the limit for {programming_language} code')
        return {'error': 'Execution time exceeded the limit'}
    except subprocess.CalledProcessError as e:
        logger.error(f'Error executing {programming_language} code: {e}')
        return {'error': str(e)}
    finally:
        if os.path.exists(temp_code_filename):
            os.remove(temp_code_filename)
        for input_file_path in container_input_paths:
            input_file_path = os.path.join(DIR_PATH, input_file_path.split('/app/resources/')[1])
            logger.error(input_file_path)
            if os.path.exists(input_file_path):
                os.remove(input_file_path)

