from django import forms
from django.forms import ModelForm, fields
from django.forms import widgets
from django.forms.models import modelformset_factory
from django.forms.widgets import TextInput
from .models import TaskInfo, UserInfo
from django.forms import formset_factory

from datetime import date


class DateInput(forms.DateInput):
    input_type = 'date'
    attrs = {"min": date.today().strftime("%Y-%m-%d")}


class TaskForm(ModelForm):
    default_data = {}

    class Meta:
        model = TaskInfo
        exclude = ['user', 'modified_date',
                   'start_date', 'days_needed', 'to_reschedule']
        widgets = {
            'due_date': TextInput(attrs={"id": "datepicker", "required": "True"}),
            'color': TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            'task_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Study Physics', "required": "True"}),
            'task_description': forms.Textarea(attrs={'class': 'form-control', 'rows': '2', "required": "True"}),
            'gradient': forms.Select(attrs={'class': 'form-select'}),
            'hours_needed': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'required': 'True', 'step': 0.5}),
            'days_needed': forms.TextInput(attrs={'class': 'form-control'})
        }


class UserInfoForm(ModelForm):
    class Meta:
        model = UserInfo
        exclude = ['user']
        widgets = {
            'time_zone': forms.Select(attrs={'class': 'form-select', 'id': 'time_zone_select'}),
            'week_day_work': forms.TextInput(attrs={'class': 'form-control', 'type': 'number'}),
            'max_week_day_work': forms.TextInput(attrs={'class': 'form-control', 'type': 'number'}),
            'week_end_work': forms.TextInput(attrs={'class': 'form-control', 'type': 'number'}),
            'max_week_end_work': forms.TextInput(attrs={'class': 'form-control', 'type': 'number'})
        }
        labels = {
            'week_day_work': "No of Hours you can spend on a Weekday",
            'max_week_day_work': "Upper limit of Hours you can spend on a Weekday",
            'week_end_work': "No of Hours you can spend on a Weekend day",
            'max_week_end_work': "Upper limit of Hours you can spend on a Weekend day",
        }


class ReschedulerDateForm(forms.Form):
    date = forms.CharField(widget=forms.TextInput(
        attrs={'type': 'hidden', 'name': 'date'}))
    # to_date = forms.DateInput()
    extra_hours = forms.DecimalField(max_digits=4, decimal_places=2, widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'number'}))

    # class Meta:
    #     widgets = {
    #         'extra_hours': forms.TextInput(attrs={'class': 'form-control', 'type': 'number'}),
    #         'date': forms.TextInput(attrs={'type': 'hidden'}),
    #     }

    # task_name = forms.CharField(label='Task Name', max_length=100)
    # work = forms.IntegerField(label='Hours')
    # due_date = forms.CharField(label='Due Date', max_length=20)
    # gradient = forms.CharField(label='Gradient', max_length=1, initial='+')
