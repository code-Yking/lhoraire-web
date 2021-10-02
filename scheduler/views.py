from datetime import date, datetime
from math import floor
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
import pytz
import pprint
import decimal

from .forms import ReschedulerDateForm, TaskForm, UserInfoForm

from scheduler.lhoraire_scheduler.model import TaskModel
from scheduler.lhoraire_scheduler.reposition import Reposition
from scheduler.lhoraire_scheduler.filter import Filter, set_old_schedule
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


def get_old_tasks(request, local_date):
    tasks = TaskInfo.objects.filter(user__user=request.user)

    if len(tasks):
        taskinfoserializer = TaskInfoSerializer(tasks, many=True)

        oldtasks = {f"{info['id']}": [float(info['hours_needed']), info['gradient'], [getDateDelta(info['start_date']), getDateDelta(info['due_date'])], 0,
                                      getDateDelta(info['modified_date'])] for info in taskinfoserializer.data if getDateDelta(info['due_date']) > getDateDelta(local_date)}
    else:
        oldtasks = {}
    return oldtasks


def get_old_schedule(request, oldtasks, localdate):
    # fetching existing schedule as json/dict, so that it can be used by backend
    days = Days.objects.filter(user__user=request.user)
    daysserializer = DaysSerializer(days, many=True)
    exist_schedule_formated = {day['date']: {'quots': {f"t{n}": k for n, k in json.loads(day['tasks_jsonDump']).items() if n in oldtasks.keys()}}
                               for day in daysserializer.data}

    # TODO check if this is needed
    for day, data in dict(exist_schedule_formated).items():
        if datetime.strptime(day, '%Y-%m-%d').date() - localdate < timedelta(1):
            print('DAY that is removed, ', day)
            exist_schedule_formated.pop(day)
            continue

        if not data['quots']:
            exist_schedule_formated.pop(day)

    extra_hours = {getDateDelta(day['date']): day['extra_hours']
                   for day in daysserializer.data}
    return days, daysserializer, exist_schedule_formated, extra_hours


def run_algorithm(exist_schedule_formated, userinfo, newtask_cumulation, oldtasks):
    # filtering the new tasks and old tasks to know which all tasks to be included in the reschedule
    new_tasks_filtered = Filter(newtask_cumulation, oldtasks)

    # print('EXIST:   ', exist_schedule_formated)
    # performing backend schedule generation
    process = Reposition(new_tasks_filtered, exist_schedule_formated,
                         oldtasks, (userinfo.week_day_work, userinfo.week_end_work), (userinfo.max_week_day_work, userinfo.max_week_end_work), {}, local_date)

    return process


def update_db(request, updated_tasks, final_schedule, final_to_reschedule, daysserializer, days, local_date, userinfo, extrahours):
    # updating the new and old tasks that were used with refreshed start dates

    show_to_resch_alert = 0

    for task, data in updated_tasks.items():
        taskobj = TaskInfo.objects.get(id=task)
        taskobj.start_date = date.fromisoformat(
            getDatefromDelta(data[0]))
        taskobj.modified_date = local_date
        if not taskobj.to_reschedule and final_to_reschedule.get(task, 0):
            show_to_resch_alert += 1
        taskobj.to_reschedule = final_to_reschedule.get(task, 0)
        taskobj.save()

    if show_to_resch_alert:
        messages.warning(request,
                         'Some tasks could not be scheduled. These tasks can be viewed by clicking on the top \
                             right Unschedulable Tasks button. <br> \
                         You can: <br> \
                          add extra hours to days by clicking the + button on hovering on them <br> \
                            or change the due date or hours needed in \
                             the All Tasks page for these tasks.'
                         )

    print('extrahours', extrahours)
    new_schedule_reformated = [
        {
            'date': datestr,
            'tasks_jsonDump': {n.strip('t'): k for n, k in info['quots'].items()},
            'user': userinfo,
            'extra_hours': extrahours.get(getDateDelta(datestr), 0)
        }
        for datestr, info in final_schedule.items()]

    print(new_schedule_reformated)
    # updates days info
    daysserializer.update(days, new_schedule_reformated, local_date)

# the process of running the algorithm and updating the database


def process(request, userinfo, oldtasks=None, newtask_cumulation={}, reschedule_range={}):
    print('new task cumul OLD')
    pprint.pprint(newtask_cumulation)
    # gets the local date of the user
    local_date = get_local_date(userinfo)

    # if there is no oldtasks given, get them.
    if oldtasks == None:
        oldtasks = get_old_tasks(request, local_date)
    # getting existing schedule and activating the days serializer

    days = get_old_schedule(request, oldtasks, local_date)[0]
    daysserializer = get_old_schedule(request, oldtasks, local_date)[1]
    exist_schedule_formated = get_old_schedule(
        request, oldtasks, local_date)[2]

    print('old schedule')
    pprint.pprint(exist_schedule_formated)

    # getting the extra hours
    extra_hours = get_old_schedule(request, oldtasks, local_date)[3]
    print('extra_hours BEFORE ', extra_hours)

    man_reschedule = False
    if reschedule_range:
        man_reschedule = True

    print('old tasks')
    pprint.pprint(oldtasks)

    print('new tasks cumulat')
    pprint.pprint(newtask_cumulation)
    print()

    new_tasks_filtered, used_day_ranged = Filter(
        newtask_cumulation, oldtasks, man_reschedule, reschedule_range, local_date, float(userinfo.week_day_work))

    old_schedule = set_old_schedule(exist_schedule_formated, used_day_ranged, float(userinfo.week_day_work), float(userinfo.week_end_work),
                                    float(userinfo.max_week_day_work), float(userinfo.max_week_end_work), extra_hours)
    # extra_hours = get_old_schedule(request, oldtasks)[3]

    print('EXIST:   ', old_schedule)
    # performing backend schedule generation
    schedule = Reposition(new_tasks_filtered, old_schedule,
                          oldtasks, (userinfo.week_day_work, userinfo.week_end_work), (userinfo.max_week_day_work, userinfo.max_week_end_work), extra_hours, local_date)
    print('extra_hours AFTER ', extra_hours)

    # results of backend
    final_schedule = schedule.schedule       # schedule as dict
    # task start_date and excess data (if any) as list
    updated_tasks = schedule.worked_tasks()

    final_to_reschedule = schedule.to_reschedule

    update_db(request, updated_tasks, final_schedule, final_to_reschedule,
              daysserializer, days, local_date, userinfo, extra_hours)

# function to add tasks or return the form
# @login_required(login_url='/accounts/login/')


def add_tasks(request, internal=False):
    TaskFormSet = formset_factory(TaskForm, extra=1)

    # if there was a POST in the form
    if request.method == 'POST':
        formset = TaskFormSet(request.POST)         # collection of all forms

        # check whether the formset is valid:
        if formset.is_valid():
            # getting the ONLY UserInfo obj of this user
            userinfo = UserInfo.objects.get(user=request.user)

            # fetching old tasks in json/dict format for the backend to understand
            local_date = get_local_date(userinfo)
            oldtasks = get_old_tasks(request, local_date)
            # getting timezone of the user, so as to prevent schedule miscalculations

            # fetching new tasks from the forms
            newtask_cumulation = {}

            for form in formset:
                obj = form.save(commit=False)
                obj.user = userinfo
                obj.to_reschedule = 0
                obj.total_hours = obj.hours_needed
                obj.save()
                # forming TaskModel using the form data for backend
                task = TaskModel(id=obj.id, due=getDateDelta(obj.due_date), work=float(obj.hours_needed),
                                 week_day_work=float(userinfo.week_day_work), days=0, gradient=obj.gradient, today=getDateDelta(local_date) + 1)
                newtask_cumulation[(form.instance.pk, obj.task_name,
                                    getDateDelta(obj.due_date))] = task

            process(request, userinfo, oldtasks, newtask_cumulation, {})

        else:
            messages.error(request, formset.errors)
            # redirect to a new URL:
        return HttpResponseRedirect('/scheduler/')

    # if a GET (or any other method) we'll create a blank form
    else:
        if internal:
            return TaskFormSet()
        else:
            return HttpResponseRedirect('/scheduler/')
    # return render(request, 'scheduler/create.html', {'formset': formset})

# removing previous days of the user and making the yesterday and today's readonly


def previous_days(earliest_day, user, local_date):
    day_count = int(
        (local_date - datetime.strptime(earliest_day, "%Y-%m-%d").date()).days)

    for readonly_date in (local_date - timedelta(n) for n in range(day_count)):
        print(readonly_date)
        day_obj = Days.objects.filter(
            user__user=user, date=readonly_date)

        if day_obj.exists():
            day_tasks = json.loads(day_obj[0].tasks_jsonDump)
        # print(day_tasks)
            for task, hours in day_tasks.items():
                task_obj = TaskInfo.objects.filter(
                    user__user=user, id=int(task))
                if task_obj.exists():
                    task = task_obj[0]
                    print(task.modified_date - local_date)
                    if (task.modified_date - local_date).days != 0:
                        task.hours_needed -= decimal.Decimal(hours)
                        task.modified_date = local_date
                        task.start_date = local_date + timedelta(1)
                        task.save()

        if (local_date - readonly_date).days > 2:
            print('delete')


def rescheduler(request, internal=False):
    # print(request.method)
    if request.method == "POST":
        form = ReschedulerDateForm(request.POST)
        if form.is_valid():
            userinfo = UserInfo.objects.get(user=request.user)
            # from_date = form.cleaned_data['from_date']
            extra_hours = form.cleaned_data['extra_hours']
            reschedule_date = form.cleaned_data['date']
            # print(date, hours)

            day_obj = Days.objects.get(
                user__user=request.user, date=date.fromisoformat(reschedule_date))
            day_obj.extra_hours = extra_hours
            day_obj.save()

            process(request, userinfo, None, {}, reschedule_range={
                    "0": (getDateDelta(reschedule_date), getDateDelta(reschedule_date))})

            return HttpResponseRedirect('/scheduler/')
    else:
        if internal:
            print('yes')
            return ReschedulerDateForm()
        else:
            return HttpResponseRedirect('/scheduler/')

# TODO fix this


@login_required(login_url='/accounts/login/')
def index(request):
    if not UserInfo.objects.filter(user=request.user).exists():
        return redirect('/scheduler/initial-info')

    user_query = UserInfo.objects.get(user=request.user)
    local_date = get_local_date(user_query)

    schedule_query = Days.objects.filter(
        user__user=request.user).order_by('date')

    # print('SCHEDULE QUERY', schedule_query)

    tasks_query = TaskInfo.objects.filter(user__user=request.user)
    # print("TASKS", tasks_query)
    if tasks_query.exists():
        taskinfoserializer = TaskInfoSerializer(tasks_query, many=True)

        tasks = {f"{info['id']}": [float(info['hours_needed']), info['gradient'], [getDateDelta(info['start_date']), getDateDelta(info['due_date'])], info['to_reschedule'],
                                   getDateDelta(info['modified_date']), info['task_name'], info['color'], info['task_description'], float(info['total_hours'])] for info in taskinfoserializer.data}
        # print(tasks)
        to_reschedule = {task: float(info[3])
                         for task, info in tasks.items() if float(info[3]) != 0}

        # getting due days that are within 10 days
        due_dates_comming_up = {task[5]: task[2][1] - getDateDelta(local_date) for task in tasks.values() if task[2][1] - getDateDelta(
            local_date) <= 10 and task[2][1] - getDateDelta(local_date) > 0}

        due_dates_comming_up = dict(
            sorted(due_dates_comming_up.items(), key=lambda item: item[1]))

        progress = {task[5]: 1 - task[8] / task[0]
                    for task in tasks.values() if task[2][1] - getDateDelta(local_date) > 1 and task[8] / task[0]}

        progress = dict(
            sorted(progress.items(), key=lambda item: item[1], reverse=True))

    else:
        tasks = {}
        to_reschedule = {}
        due_dates_comming_up = {}
        progress = {}

    taskformset = add_tasks(request=request, internal=True)
    rescheduleform = rescheduler(request=request, internal=True)

    # if user_query.exists():
    if schedule_query.exists():
        daysserializer = DaysSerializer(schedule_query, many=True)
        schedule = {day['date']: {'quote': {task: hours for task, hours in json.loads(day['tasks_jsonDump']).items() if task in tasks}, 'extra_hours': float(day['extra_hours'])}
                    for day in daysserializer.data}
        if schedule:
            # TODO maybe integrate?
            for day, data in dict(schedule).items():
                if datetime.strptime(day, '%Y-%m-%d').date() - local_date < timedelta(-1):
                    schedule.pop(day)
                    continue

            # TODO remove latest
            latest = Days.objects.filter(
                user__user=request.user).latest('date')

            day_count = int((latest.date - local_date).days) + 1

            for single_date in (local_date + timedelta(n-1) for n in range(day_count)):
                if single_date.strftime('%Y-%m-%d') not in list(schedule.keys()):
                    schedule[single_date.strftime(
                        '%Y-%m-%d')] = {'quote': {'0': 0}}

            schedule = dict(sorted(schedule.items(),
                                   key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))

            # pprint.pprint(schedule)
            earliest_day = list(schedule.keys())[0]
            last_day = list(schedule.keys())[-1]

            previous_days(earliest_day, request.user, local_date)

            todays_todo = schedule[local_date.strftime(
                '%Y-%m-%d')]['quote'] if schedule[local_date.strftime('%Y-%m-%d')]['quote'] != {'0': 0} else {}
        else:
            todays_todo = {}
            last_day = 0
    else:
        schedule = {}
        todays_todo = {}
        last_day = 0

    return render(request, 'scheduler/dashboard.html', {
        'schedule': schedule,
        'tasks': tasks,
        'formset': taskformset,
        'userinfo': user_query,
        'todays_todo': todays_todo,
        'last_day': last_day,
        'upper_limit': user_query.max_week_end_work if user_query.max_week_end_work > user_query.max_week_day_work else user_query.max_week_day_work,
        'to_reschedule': to_reschedule,
        'reschedule_form': rescheduleform,
        'dues_comming_up': due_dates_comming_up,
        'progress': progress
    })


@login_required
def edit_tasks(request):
    TaskModelFormSet = modelformset_factory(
        TaskInfo, form=TaskForm, exclude=('user', 'id', 'modified_date', 'start_date', 'days_needed', 'to_reschedule'), extra=0)
    if request.method == "GET":
        formset = TaskModelFormSet(
            queryset=TaskInfo.objects.filter(user__user=request.user).order_by('due_date'))
        return render(request, 'scheduler/edit.html', {'formset': formset})

    else:
        formset = TaskModelFormSet(request.POST,
                                   queryset=TaskInfo.objects.filter(user__user=request.user))

        userinfo = UserInfo.objects.get(user=request.user)
        local_date = get_local_date(userinfo)

        if formset.is_valid():
            oldtasks = get_old_tasks(request, local_date)
            updated_tasks = {}
            newtask_cumulation = {}
            needs_redo = 0

            for form in formset:
                if form.has_changed():
                    # id = form.cleaned_data['id']
                    obj = form.save()
                    obj.total_hours = float(obj.total_hours) - (oldtasks[str(obj.id)][0] -
                                                                float(obj.hours_needed))
                    obj.save()
                    # print('id ', obj.id)
                    # algorithm is rerun only if any of these three are edited
                    if 'due_date' in form.changed_data or 'hours_needed' in form.changed_data or 'gradient' in form.changed_data:
                        needs_redo += 1
                        updated_tasks[str(obj.id)] = oldtasks.pop(str(obj.id))

                        if float(obj.hours_needed):
                            task = TaskModel(id=obj.id, due=getDateDelta(obj.due_date), work=float(obj.hours_needed),
                                             week_day_work=float(userinfo.week_day_work), days=0, gradient=obj.gradient, today=getDateDelta(local_date) + 1)
                            newtask_cumulation[(form.instance.pk, obj.task_name,
                                                getDateDelta(obj.due_date))] = task
                        else:
                            TaskInfo.objects.get(id=obj.id).delete()
            if needs_redo:
                n = 0
                for task, info in updated_tasks.items():
                    reschedule_range = {f'{n}': tuple(info[2])}
                    # info[2]
                    n -= 1
                process(request, userinfo, oldtasks,
                        newtask_cumulation, reschedule_range)
        return redirect('/scheduler/edit')


@ api_view(['GET', 'POST'])
def schedule(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            days = Days.objects.filter(
                user__user=request.user).order_by('date')
            daysserializer = DaysSerializer(days, many=True)
            result = {(day['date']): {'quote': {task: quotes for task, quotes in json.loads(day['tasks_jsonDump']).items()}, 'date': getDateDelta(day['date'])}
                      for day in daysserializer.data}
            return Response(result)


@ api_view(['GET', 'POST'])
def tasks(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            tasks = TaskInfo.objects.filter(user__user=request.user)
            taskinfoserializer = TaskInfoSerializer(tasks, many=True)
            result = {info['id']: [float(info['hours_needed']), info['gradient'], [(info['start_date'], getDateDelta(info['start_date'])), (info['due_date'], getDateDelta(info['due_date']))],
                                   (info['modified_date'], getDateDelta(info['modified_date']))] for info in taskinfoserializer.data}
            return Response(result)


@login_required
def userinfo(request):
    if request.method == 'POST':
        if UserInfo.objects.filter(user=request.user).exists():
            time_zone = UserInfo.objects.get(user=request.user).time_zone
            form = UserInfoForm(
                request.POST, instance=UserInfo.objects.get(user=request.user))
            if form.is_valid():
                a = form.save(commit=False)
                a.time_zone = time_zone
                a.save()

            return redirect('/scheduler/settings')
        else:
            form = UserInfoForm(request.POST)
            if form.is_valid():
                a = form.save(commit=False)
                a.user = request.user
                a.save()
                return HttpResponseRedirect('/scheduler/')
    else:
        if UserInfo.objects.filter(user=request.user).exists():
            user_not_complete = False
            form = UserInfoForm(
                instance=UserInfo.objects.get(user=request.user))
        else:
            user_not_complete = True
            form = UserInfoForm()
        return render(request, 'scheduler/user_info.html', {'form': form, 'user_not_complete': user_not_complete})
    # else:
    #     return redirect('/scheduler/')


# @login_required
# def settings(request):
#     if request.method == 'POST':
#         pass
#     else:
#         form
