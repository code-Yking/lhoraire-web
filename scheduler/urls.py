from django.urls import path

from . import views

app_name = 'scheduler'

urlpatterns = [
    path('create', views.get_name, name='create'),
    path('schedule', views.schedule, name='schedule'),
    path('tasks', views.tasks, name='tasks'),
    path('', views.index, name='index'),
    path('initial-info', views.userinfo, name='userinfo'),
    path('edit', views.edit_tasks, name='edit')
]
