from datetime import date, datetime
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
import pytz
import pprint

from .forms import TaskForm, TaskModelFormSet

from scheduler.lhoraire_scheduler.model import TaskModel
from scheduler.lhoraire_scheduler.reposition import Reposition
from scheduler.lhoraire_scheduler.filter import Filter
from scheduler.lhoraire_scheduler.helpers import *

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from .models import Days, TaskInfo, UserInfo
from .serializers import DaysSerializer, TaskInfoSerializer
from rest_framework.response import Response


@login_required
def get_name(request):
    TaskFormSet = formset_factory(TaskForm, extra=1)

    # if there was a POST in the form
    if request.method == 'POST':

        formset = TaskFormSet(request.POST)         # collection of all forms

        # check whether the formset is valid:
        if formset.is_valid():

            # getting the ONLY UserInfo obj of this user
            userinfo = UserInfo.objects.filter(user=request.user).first()

            # fetching old tasks in json/dict format for the backend to understand
            tasks = TaskInfo.objects.filter(user__user=request.user)
            taskinfoserializer = TaskInfoSerializer(tasks, many=True)

            oldtasks = {f"t{info['id']}": [float(info['hours_needed']), info['gradient'], [getDateDelta(info['start_date']), getDateDelta(info['due_date'])], 0,
                                           getDateDelta(info['modified_date'])] for info in taskinfoserializer.data}

            # getting timezone of the user, so as to prevent schedule miscalculations
            timezone = pytz.common_timezones[userinfo.time_zone]
            local_date = datetime.now(
                pytz.timezone(timezone)).date()

            # fetching new tasks from the forms
            newtask_cumulation = {}

            for form in formset:
                obj = form.save(commit=False)
                obj.user = userinfo
                obj.save()
                # forming TaskModel using the form data for backend
                task = TaskModel(id=obj.id, due=getDateDelta(obj.due_date), work=float(obj.hours_needed),
                                 week_day_work=6, days=0, gradient=obj.gradient, today=getDateDelta(local_date) + 1)
                newtask_cumulation[(form.instance.pk, obj.task_name,
                                    getDateDelta(obj.due_date))] = task

            print(newtask_cumulation)

            # filtering the new tasks and old tasks to know which all tasks to be included in the reschedule
            new_tasks_filtered = Filter(newtask_cumulation, oldtasks)

            # fetching existing schedule as json/dict, so that it can be used by backend
            days = Days.objects.filter(tasks__task__user__user=request.user)
            daysserializer = DaysSerializer(days, many=True)
            exist_schedule_formated = {day['date']: {'quots': {task['task']: task['hours'] for task in day['tasks']}}
                                       for day in daysserializer.data}

            # performing backend schedule generation
            process = Reposition(new_tasks_filtered, exist_schedule_formated,
                                 oldtasks, (6, 10), (8, 14), {})

            # results of backend
            final_schedule = process.schedule       # schedule as dict
            # task start_date and excess data (if any) as list
            updated_tasks = process.worked_tasks()

            # updated_tasks_data = [{'id': task, 'task_name': '', 'hours_needed': info[0], 'gradient': info[1],
            #                        'start_date':info[2][0], 'due_date': info[2][1], 'modified_date': local_date} for task, info in updated_tasks.items()]

            pprint.pprint(final_schedule)

            new_schedule_reformated = [{'date': datestr, 'tasks': [
                {'task': int(f"{task.strip('t')}"), 'hours': quot} for task, quot in info['quots'].items()]} for datestr, info in final_schedule.items()]
            # daysdeserializer = DaysSerializer(
            #     data=new_schedule_reformated, many=True)
            # if daysdeserializer.is_valid():
            daysserializer.update(days, new_schedule_reformated)

            # saving the formset with the start date now available
            # for form in formset:
            #     obj = form.save(commit=False)
            #     obj.save(start_date=updated_tasks[form.instance.pk]
            #              [0], modified_date=local_date, user=userinfo)
            #     updated_tasks.pop(form.instance.pk)

            # updating the new and old tasks that were used with refreshed start dates
            for task, data in updated_tasks.items():
                taskobj = TaskInfo.objects.get(id=task)
                taskobj.start_date = date.fromisoformat(
                    getDatefromDelta(data[0]))
                taskobj.modified_date = local_date
                taskobj.save()

            # taskinput = TaskInfoSerializer(updated_tasks_data, many=True)
            # if taskinput.is_valid():
            #     taskinput.save(user=userinfo)

            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            # print(formset.cleaned_data)
            return HttpResponseRedirect('create')

    # if a GET (or any other method) we'll create a blank form
    else:
        formset = TaskFormSet()
    return render(request, 'scheduler/create.html', {'formset': formset})


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@ api_view(['GET', 'POST'])
def schedule(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            days = Days.objects.filter(tasks__task__user=request.user)
            daysserializer = DaysSerializer(days, many=True)
            result = {day['date']: {'quote': {task['task']: task['hours'] for task in day['tasks']}}
                      for day in daysserializer.data}
            return Response(result)


@ api_view(['GET', 'POST'])
def tasks(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            tasks = TaskInfo.objects.filter(user__user=request.user)
            taskinfoserializer = TaskInfoSerializer(tasks, many=True)
            # result = {day['date']: {'quote': {task['task']: task['hours'] for task in day['tasks']}}
            #           for day in daysserializer.data}
            result = {f"t{info['id']}": [float(info['hours_needed']), info['gradient'], [getDateDelta(info['start_date']), getDateDelta(info['due_date'])],
                                         getDateDelta(info['modified_date'])] for info in taskinfoserializer.data}
            return Response(result)
