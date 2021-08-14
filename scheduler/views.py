from datetime import date, datetime
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
import pytz

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
    # if this is a POST request we need to process the form data
    TaskFormSet = formset_factory(TaskForm, extra=1)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:

        # new_task = TaskInfo(user=request.user)

        formset = TaskFormSet(request.POST)
        # check whether it's valid:
        if formset.is_valid():
            newtask_cumulation = {}

            tasks = TaskInfo.objects.filter(user__user=request.user)
            taskinfoserializer = TaskInfoSerializer(tasks, many=True)
            # result = {day['date']: {'quote': {task['task']: task['hours'] for task in day['tasks']}}
            #           for day in daysserializer.data}
            oldtasks = {f"t{info['id']}": [float(info['hours_needed']), info['gradient'], [getDateDelta(info['start_date']), getDateDelta(info['due_date'])], 0,
                                           getDateDelta(info['modified_date'])] for info in taskinfoserializer.data}

            for i, form in enumerate(formset.forms):
                obj = form.save(commit=False)

                userinfo = UserInfo.objects.filter(user=request.user).first()
                timezone = pytz.common_timezones[userinfo.time_zone]
                t = datetime.now(
                    pytz.timezone(timezone)).date()
                print(timezone, t, datetime.now())

                obj.modified_date = t
                obj.user = userinfo

                task = TaskModel(id=1, due=getDateDelta(obj.due_date), work=float(obj.hours_needed),
                                 week_day_work=6, days=0, gradient=obj.gradient, today=getDateDelta(date.today()) + 1)
                obj.save()
                newtask_cumulation[(obj.id, obj.task_name,
                                    getDateDelta(obj.due_date))] = task

            print(newtask_cumulation)

            newtasks = Filter(newtask_cumulation, oldtasks)
            print('new: ', newtasks)
            # process = Reposition(newtasks, (6, 10), (8, 14), {})

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
