import os
import tempfile
import requests

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .tasks import run_code, execute_code_with_file
from celery.result import AsyncResult

class AddTask(APIView):
    def post(self, request):
        programming_language = request.data['programming_language']
        source_code = request.data['source_code']
        if programming_language is not None and source_code is not None:
            task = run_code.delay(source_code, programming_language)

            return Response({'task_id': task.id}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Missing  parameters'}, status=status.HTTP_400_BAD_REQUEST)


class GetTaskResult(APIView):
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        if result.ready():
            return Response({'status': 'Completed', 'result': result.get()}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'Pending'}, status=status.HTTP_200_OK)

class AddTaskWithFile(APIView):
    def post(self, request):
        programming_language = request.data['programming_language']
        source_code = request.data['source_code']
        file_paths = request.data['file_paths']
        file_output_fromat = request.data['file_output_fromat']

        input_file_url = file_paths['input_file_path']
        try:
            response = requests.get(input_file_url)
            response.raise_for_status()
        except requests.RequestException as e:
            return Response({'error': 'Failed to download the file: {}'.format(str(e))}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tmp_dir = tempfile.gettempdir()
            tmp_file_path = os.path.join(tmp_dir, os.path.basename(input_file_url))
            with open(tmp_file_path, 'wb') as tmp_file:
                tmp_file.write(response.content)
        except Exception as e:
            return Response({'error': 'Failed to save the file: {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            task = execute_code_with_file.delay(source_code, programming_language, tmp_file_path, file_output_fromat)
        except Exception as e:
            return Response({'error': 'Failed to create task: {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'task_id': task.id, 'status': 'Task created successfully'}, status=status.HTTP_200_OK)
