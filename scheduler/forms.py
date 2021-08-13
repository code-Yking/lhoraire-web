from django import forms
from django.forms import ModelForm, fields
from .models import TaskInfo
from django.contrib.auth.decorators import login_required


class DateInput(forms.DateInput):
    input_type = 'date'


class TaskForm(ModelForm):
    class Meta:
        model = TaskInfo
        exclude = ['user']
        widgets = {
            'due_date': DateInput(),
        }
    # task_name = forms.CharField(label='Task Name', max_length=100)
    # work = forms.IntegerField(label='Hours')
    # due_date = forms.CharField(label='Due Date', max_length=20)
    # gradient = forms.CharField(label='Gradient', max_length=1, initial='+')
