from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Tasks(models.Model):
    task_name = models.CharField(max_length=50)
    task_description = models.TextField()
    due_date = models.DateTimeField()
    hours_needed = models.DecimalField(decimal_places=2, max_digits=4)

    days_needed = models.DecimalField(decimal_places=2, max_digits=4)
    # user = models.ForeignKey(User, default=None)

    def __str__(self):
        return self.task_name
