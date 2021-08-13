from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .forms import TaskForm

from scheduler.lhoraire_scheduler.model import TaskModel
from scheduler.lhoraire_scheduler.reposition import Reposition
from scheduler.lhoraire_scheduler.filter import Filter
from scheduler.lhoraire_scheduler.helpers import *

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from .models import Days, TaskInfo
from .serializers import DaysSerializer
from rest_framework.response import Response


@login_required
def get_name(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:

        new_task = TaskInfo(user=request.user)

        form = TaskForm(request.POST, instance=new_task)
        # check whether it's valid:
        if form.is_valid():
            # task_cumulation = {}
            # task_name = form.cleaned_data['task_name']
            # work = form.cleaned_data['work']
            # due_date = getDateDelta(form.cleaned_data['due_date'])
            # gradient = form.cleaned_data['gradient']
            # form['user'] = request.user
            form.save()

            # task = TaskModel(id=1, due=due_date, work=work,
            #                  week_day_work=6, days=0, gradient=gradient, today=getDateDelta(datetime.now()) + 1)
            # task_cumulation[(1, task_name, due_date)] = task

            # newtasks = Filter(task_cumulation)
            # process = Reposition(newtasks, (6, 10), (8, 14), {})

            # print(process.schedule)
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/scheduler')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = TaskForm()

    return render(request, 'scheduler/create.html', {'form': form})


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@api_view(['GET', 'POST'])
def schedule(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            days = Days.objects.filter(tasks__task__user=request.user)
            daysserializer = DaysSerializer(days, many=True)
            result = {day['date']: {'quote': {task['task']: task['hours'] for task in day['tasks']}}
                      for day in daysserializer.data}
            return Response(result)
