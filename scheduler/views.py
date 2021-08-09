from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .forms import TaskForm

from scheduler.lhoraire_scheduler.model import TaskModel
from scheduler.lhoraire_scheduler.reposition import Reposition
from scheduler.lhoraire_scheduler.filter import Filter
from scheduler.lhoraire_scheduler.helpers import *


def get_name(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = TaskForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            task_cumulation = {}
            task_name = form.cleaned_data['task_name']
            work = form.cleaned_data['work']
            due_date = getDateDelta(form.cleaned_data['due_date'])
            gradient = form.cleaned_data['gradient']

            task = TaskModel(id=1, due=due_date, work=work,
                             week_day_work=6, days=0, gradient=gradient, today=getDateDelta(datetime.now()) + 1)
            task_cumulation[(1, task_name, due_date)] = task

            newtasks = Filter(task_cumulation)
            process = Reposition(newtasks, (6, 10), (8, 14), {})

            print(process.schedule)
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
