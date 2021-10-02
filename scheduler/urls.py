from django.urls import path

from . import views

app_name = 'scheduler'

urlpatterns = [
    path('create', views.add_tasks, name='create'),
    path('schedule', views.schedule, name='schedule'),
    path('tasks', views.tasks, name='tasks'),
    path('', views.index, name='index'),
    path('initial-info', views.userinfo, name='userinfo'),
    path('edit', views.edit_tasks, name='edit'),
    path('rescheduler', views.rescheduler, name='rescheduler'),
    path('settings', views.userinfo, name='settings')
]
