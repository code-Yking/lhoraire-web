from django import forms
from django.forms import ModelForm, fields
from django.forms.models import modelformset_factory
from .models import TaskInfo
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
        }

    # task_name = forms.CharField(label='Task Name', max_length=100)
    # work = forms.IntegerField(label='Hours')
    # due_date = forms.CharField(label='Due Date', max_length=20)
    # gradient = forms.CharField(label='Gradient', max_length=1, initial='+')
