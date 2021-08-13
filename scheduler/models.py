from django.db import models
from django.conf import settings
# from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE
# Create your models here.


class TaskInfo(models.Model):
    task_name = models.CharField(max_length=50)
    task_description = models.TextField()
    due_date = models.DateField()
    hours_needed = models.DecimalField(decimal_places=2, max_digits=4)
    days_needed = models.DecimalField(
        decimal_places=2, max_digits=4, default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, default=None)

    def __str__(self):
        return self.task_name


class Tasks(models.Model):
    task = models.ForeignKey(TaskInfo, on_delete=CASCADE, default="")
    hours = models.DecimalField(decimal_places=4, max_digits=10, default=0)

    def __str__(self):
        return self.task.task_name


class Days(models.Model):
    date = models.DateField()
    tasks = models.ManyToManyField(Tasks)

    def __str__(self):
        return f'{self.date}'
