from rest_framework import serializers

from .models import TaskInfo, Tasks, Days


class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = ['task', 'hours']


class DaysSerializer(serializers.ModelSerializer):
    tasks = TasksSerializer(many=True, read_only=True)

    class Meta:
        model = Days
        fields = ['date', 'user', 'tasks']
        # depth = 2
