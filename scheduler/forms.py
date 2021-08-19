from django import forms
from django.forms import ModelForm, fields
from django.forms.models import modelformset_factory
from django.forms.widgets import TextInput
from .models import TaskInfo, UserInfo
from django.forms import formset_factory


class DateInput(forms.DateInput):
    input_type = 'date'


TaskModelFormSet = modelformset_factory(
    TaskInfo, exclude=('user',), widgets={'due_date': DateInput()})


class TaskForm(ModelForm):
    class Meta:
        model = TaskInfo
        exclude = ['user', 'modified_date', 'start_date']
        widgets = {
            'due_date': DateInput(),
            'color': TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            'task_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Study Physics'}),
            'task_description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'gradient': forms.Select(attrs={'class': 'form-select'}),
        }


class UserInfoForm(ModelForm):
    class Meta:
        model = UserInfo
        exclude = ['user']
        widgets = {
            'time_zone': forms.Select(attrs={'class': 'form-select'}),
            'week_day_work': forms.TextInput(attrs={'class': 'form-control', 'type': 'number'})
        }

    # task_name = forms.CharField(label='Task Name', max_length=100)
    # work = forms.IntegerField(label='Hours')
    # due_date = forms.CharField(label='Due Date', max_length=20)
    # gradient = forms.CharField(label='Gradient', max_length=1, initial='+')
