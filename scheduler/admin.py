from django.contrib import admin

from .models import Days, TaskInfo, Tasks

# Register your models here.
admin.site.register(Tasks)
admin.site.register(TaskInfo)
admin.site.register(Days)
