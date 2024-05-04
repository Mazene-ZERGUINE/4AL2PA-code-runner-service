from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .tasks import add
from celery.result import AsyncResult
from django_celery_results.models import TaskResult


class AddTask(APIView):
    def post(self, request):
        x = request.data.get('x')
        y = request.data.get('y')
        if x is not None and y is not None:
            task = add.delay(int(x), int(y))
            return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({'error': 'Missing x or y parameters'}, status=status.HTTP_400_BAD_REQUEST)


class GetTaskResult(APIView):
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        if result.ready():
            return Response({'status': 'Completed', 'result': result.get()})
        else:
            return Response({'status': 'Pending'})
