from datetime import datetime, timedelta
import json
import pprint
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from .models import TaskInfo, Tasks, Days


class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = ['task', 'hours']


class DaysListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data, localdate):
        # Maps for id->instance and id->data item.
        old_day_mapping = {day.date.strftime(
            "%Y-%m-%d"): day for day in instance}
        new_day_mapping = {item['date']: item for item in validated_data}
        # print('old')
        # pprint.pprint(old_day_mapping)
        # print('new')
        # pprint.pprint(new_day_mapping)

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
                if datetime.strptime(date, '%Y-%m-%d').date() - localdate > timedelta(0):
                    day.delete()

        return ret


class DaysSerializer(serializers.ModelSerializer):
    class Meta:
        list_serializer_class = DaysListSerializer
        model = Days
        fields = ['date', 'tasks_jsonDump', 'extra_hours']
        # depth = 2

    # create the day object
    def create(self, validated_data):
        new_tasks = {k: round(v, 4) for k, v in validated_data.pop(
            'tasks_jsonDump').items()}

        tasks_jsonDump = json.dumps(new_tasks)

        day = Days.objects.create(
            date=validated_data['date'], tasks_jsonDump=tasks_jsonDump, user=validated_data['user'], extra_hours=validated_data['extra_hours'])
        return day

    # update existing day objects
    def update(self, instance, validated_data):
        # print('UPDATING....', validated_data)
        instance.date = validated_data.get('date', instance.date)
        if 'tasks_jsonDump' in validated_data:
            instance.tasks_jsonDump = json.dumps(
                validated_data['tasks_jsonDump'])
        else:
            instance.tasks_jsonDump = instance.tasks_jsonDump
        instance.extra_hours = instance.extra_hours
        # instance.created = validated_data.get('created', instance.created)
        instance.save()
        return instance


class TaskInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskInfo
        fields = ['id', 'task_name', 'task_description', 'hours_needed', 'start_date',
                  'due_date', 'gradient', 'modified_date', 'color', 'to_reschedule', 'total_hours']
