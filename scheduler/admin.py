from django.contrib import admin

from .models import Days, TaskInfo, Tasks, UserInfo

# Register your models here.
admin.site.register(Tasks)
admin.site.register(TaskInfo)
admin.site.register(Days)
admin.site.register(UserInfo)
