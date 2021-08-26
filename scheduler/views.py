from datetime import date, datetime
from math import floor
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
import pytz
import pprint

from .forms import TaskForm, TaskModelFormSet, UserInfoForm

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
from django.template.defaulttags import register

WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def to_date(strdate):
    return datetime.strptime(strdate, '%Y-%m-%d').strftime('%d/%m')


@register.filter
def to_day(strdate):
    return WEEKDAYS[datetime.strptime(strdate, '%Y-%m-%d').weekday()]


@register.filter
def readable_hrs(hour):
    hour = float(hour)
    if floor(hour) == 0:
        return str(round((hour - floor(hour)) * 60)) + " mins"
    else:
        return str(floor(hour)) + " hrs " + str(round((hour - floor(hour)) * 60)) + " mins"


def get_local_date(userinfo):
    timezone = pytz.common_timezones[userinfo.time_zone]
    local_date = datetime.now(
        pytz.timezone(timezone)).date()
    return local_date


@login_required
def get_name(request):
    TaskFormSet = formset_factory(TaskForm, extra=1)

    # if there was a POST in the form
    if request.method == 'POST':
        formset = TaskFormSet(request.POST)         # collection of all forms

        # check whether the formset is valid:
        if formset.is_valid():
            # print('1 IS PASSED')
            # getting the ONLY UserInfo obj of this user
            userinfo = UserInfo.objects.get(user=request.user)

            # fetching old tasks in json/dict format for the backend to understand
            tasks = TaskInfo.objects.filter(user__user=request.user)
            taskinfoserializer = TaskInfoSerializer(tasks, many=True)

            oldtasks = {f"{info['id']}": [float(info['hours_needed']), info['gradient'], [getDateDelta(info['start_date']), getDateDelta(info['due_date'])], 0,
                                          getDateDelta(info['modified_date'])] for info in taskinfoserializer.data}

            # getting timezone of the user, so as to prevent schedule miscalculations
            local_date = get_local_date(userinfo)

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

            # print('newtask:    ', newtask_cumulation)

            # filtering the new tasks and old tasks to know which all tasks to be included in the reschedule
            new_tasks_filtered = Filter(newtask_cumulation, oldtasks)

            # fetching existing schedule as json/dict, so that it can be used by backend
            days = Days.objects.filter(user__user=request.user)
            daysserializer = DaysSerializer(days, many=True)
            exist_schedule_formated = {day['date']: {'quots': {f"t{n}": k for n, k in json.loads(day['tasks_jsonDump']).items()}}
                                       for day in daysserializer.data}

            # print('EXIST:   ', exist_schedule_formated)
            # performing backend schedule generation
            process = Reposition(new_tasks_filtered, exist_schedule_formated,
                                 oldtasks, (userinfo.week_day_work, userinfo.max_week_day_work), (userinfo.week_end_work, userinfo.max_week_end_work), {})

            # results of backend
            final_schedule = process.schedule       # schedule as dict
            # task start_date and excess data (if any) as list
            updated_tasks = process.worked_tasks()

            # updated_tasks_data = [{'id': task, 'task_name': '', 'hours_needed': info[0], 'gradient': info[1],
            #                        'start_date':info[2][0], 'due_date': info[2][1], 'modified_date': local_date} for task, info in updated_tasks.items()]

            # pprint.pprint(final_schedule)

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

            new_schedule_reformated = [
                {'date': datestr, 'tasks_jsonDump': {n.strip('t'): k for n, k in info['quots'].items()}, 'user': userinfo} for datestr, info in final_schedule.items()]

            # updates days info
            daysserializer.update(days, new_schedule_reformated)

            # redirect to a new URL:
            return HttpResponseRedirect('/scheduler/')

    # if a GET (or any other method) we'll create a blank form
    else:
        return TaskFormSet()
    # return render(request, 'scheduler/create.html', {'formset': formset})


@login_required
def index(request):
    if not UserInfo.objects.filter(user=request.user).exists():
        return redirect('/scheduler/initial-info')

    user_query = UserInfo.objects.get(user=request.user)
    local_date = get_local_date(user_query)

    schedule_query = Days.objects.filter(
        user__user=request.user).order_by('date')

    # print('SCHEDULE QUERY', schedule_query)
    if schedule_query.exists():
        # TODO earliest
        daysserializer = DaysSerializer(schedule_query, many=True)
        schedule = {day['date']: {'quote': json.loads(day['tasks_jsonDump'])}
                    for day in daysserializer.data}

        latest = Days.objects.filter(
            user__user=request.user).latest('date')
        day_count = int((latest.date - local_date).days) + 1

        for single_date in (local_date + timedelta(n) for n in range(day_count)):
            if single_date.strftime('%Y-%m-%d') not in list(schedule.keys()):
                schedule[single_date.strftime(
                    '%Y-%m-%d')] = {'quote': {'0': 0}}

        schedule = dict(sorted(schedule.items(),
                               key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))

        # pprint.pprint(schedule)

        last_day = list(schedule.keys())[-1]

        todays_todo = schedule[local_date.strftime(
            '%Y-%m-%d')]['quote'] if schedule[local_date.strftime('%Y-%m-%d')]['quote'] != {'0': 0} else {}
    else:
        schedule = {}
        todays_todo = {}
        last_day = 0

    tasks_query = TaskInfo.objects.filter(user__user=request.user)
    # print("TASKS", tasks_query)
    if tasks_query.exists():
        taskinfoserializer = TaskInfoSerializer(tasks_query, many=True)

        tasks = {f"{info['id']}": [float(info['hours_needed']), info['gradient'], [getDateDelta(info['start_date']), getDateDelta(info['due_date'])], 0,
                                   getDateDelta(info['modified_date']), info['task_name'], info['color'], info['task_description']] for info in taskinfoserializer.data}
        # print(tasks)
    else:
        tasks = {}

    taskformset = get_name(request=request)

    # if user_query.exists():

    return render(request, 'scheduler/dashboard.html', {
        'schedule': schedule,
        'tasks': tasks,
        'formset': taskformset,
        'userinfo': user_query,
        'todays_todo': todays_todo,
        'last_day': last_day,
        'upper_limit': user_query.max_week_end_work if user_query.max_week_end_work > user_query.max_week_day_work else user_query.max_week_day_work
    })


@ api_view(['GET', 'POST'])
def schedule(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            days = Days.objects.filter(
                tasks__task__user__user=request.user).order_by('date')
            daysserializer = DaysSerializer(days, many=True)
            result = {(day['date']): {'quote': {task['task']: task['hours'] for task in day['tasks_jsonDump']}, 'date': getDateDelta(day['date'])}
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
            result = {info['id']: [float(info['hours_needed']), info['gradient'], [(info['start_date'], getDateDelta(info['start_date'])), (info['due_date'], getDateDelta(info['due_date']))],
                                   (info['modified_date'], getDateDelta(info['modified_date']))] for info in taskinfoserializer.data}
            return Response(result)


@login_required
def userinfo(request):
    if request.method == 'POST':
        form = UserInfoForm(request.POST)
        if form.is_valid():
            a = form.save(commit=False)
            a.user = request.user
            a.save()
            return HttpResponseRedirect('/scheduler/')
    elif not UserInfo.objects.filter(user=request.user).exists():
        form = UserInfoForm()
        return render(request, 'scheduler/user_info.html', {'form': form})
    else:
        return redirect('/scheduler/')
