from datetime import datetime, date
from django.db import models
from django.conf import settings
# from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE

import pytz
# Create your models here.


class UserInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    time_zone = models.IntegerField(
        choices=list(enumerate(pytz.common_timezones)))

    week_day_work = models.DecimalField(decimal_places=2, max_digits=4)
    max_week_day_work = models.DecimalField(decimal_places=2, max_digits=4)

    week_end_work = models.DecimalField(decimal_places=2, max_digits=4)
    max_week_end_work = models.DecimalField(decimal_places=2, max_digits=4)

    def __str__(self) -> str:
        return self.user.username


class TaskInfo(models.Model):
    task_name = models.CharField(max_length=50)
    task_description = models.TextField(null=True)

    start_date = models.DateField(null=True)
    due_date = models.DateField()

    hours_needed = models.DecimalField(
        decimal_places=2, max_digits=4, default=10)
    days_needed = models.DecimalField(
        decimal_places=2, max_digits=4, default=0, null=True)

    gradient = models.CharField(max_length=1, default='+', choices=(
        ['+', 'Increasing'], ['-', 'Decreasing'], ['0', 'Roughly same']))

    to_reschedule = models.DecimalField(decimal_places=2, max_digits=4)

    modified_date = models.DateField(null=True)
    user = models.ForeignKey(UserInfo, on_delete=CASCADE, default="")

    color = models.CharField(max_length=10)

    def __str__(self):
        return self.task_name


class Tasks(models.Model):
    task = models.ForeignKey(TaskInfo, on_delete=CASCADE, default="")
    hours = models.DecimalField(decimal_places=4, max_digits=10, default=0)

    def __str__(self):
        return self.task.task_name


class Days(models.Model):
    date = models.DateField()
    # tasks = models.ManyToManyField(Tasks)

    tasks_jsonDump = models.CharField(max_length=481)
    user = models.ForeignKey(UserInfo, on_delete=CASCADE, default="")

    extra_hours = models.DecimalField(
        decimal_places=2, max_digits=4, default=0)

    def __str__(self):
        return f'{self.date}'
