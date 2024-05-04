from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .tasks import run_code
from celery.result import AsyncResult

from .utils import clean_tmp_directory


class AddTask(APIView):
    def post(self, request):
        clean_tmp_directory()
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
            return Response({'status': 'Completed', 'result': result.get()})
        else:
            return Response({'status': 'Pending'})
