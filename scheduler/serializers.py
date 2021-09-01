import json
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from .models import TaskInfo, Tasks, Days


class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = ['task', 'hours']


class DaysListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        old_day_mapping = {day.date: day for day in instance}
        new_day_mapping = {item['date']: item for item in validated_data}

        # Perform creations and updates.
        ret = []
        for date, data in new_day_mapping.items():
            # each day is seperately created/updated
            day = old_day_mapping.get(date, None)
            if day is None:
                ret.append(self.child.create(data))
            else:
                ret.append(self.child.update(day, data))

        # Perform deletions.
        for date, day in old_day_mapping.items():
            if date not in new_day_mapping:
                day.delete()

        return ret


class DaysSerializer(serializers.ModelSerializer):
    # tasks = TasksSerializer(many=True)
    # id = serializers.IntegerField()

    class Meta:
        list_serializer_class = DaysListSerializer
        model = Days
        fields = ['date', 'tasks_jsonDump']
        # depth = 2

    def create(self, validated_data):
        new_tasks = validated_data.pop('tasks_jsonDump')
        # tasks = validated_data.pop('tasks')
        tasks_jsonDump = json.dumps(new_tasks)

        day = Days.objects.create(
            date=validated_data['date'], tasks_jsonDump=tasks_jsonDump, user=validated_data['user'])
        # for task in new_tasks:
        #     created_task = Tasks.objects.create(
        #         hours=task['hours'], task=TaskInfo.objects.get(id=task['task']))
        #     day.tasks.add(created_task)
        return day

    def update(self, instance, validated_data):
        instance.date = validated_data.get('date', instance.date)
        instance.tasks_jsonDump = validated_data.get(
            'tasks_jsonDump', instance.tasks)
        # instance.created = validated_data.get('created', instance.created)
        instance.save()
        return instance


class TaskInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskInfo
        fields = ['id', 'task_name', 'task_description', 'hours_needed', 'start_date',
                  'due_date', 'gradient', 'modified_date', 'color', 'to_reschedule']
