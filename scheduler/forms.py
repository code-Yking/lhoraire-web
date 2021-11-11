from django import forms
from django.forms import ModelForm, fields
from django.forms import widgets
from django.forms.models import modelformset_factory
from django.forms.widgets import TextInput
from .models import TaskInfo, UserInfo
from django.forms import formset_factory

from datetime import date


class DateInput(forms.DateInput):
    input_type = "date"
    attrs = {"min": date.today().strftime("%Y-%m-%d")}


class TaskForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs) 
        self.auto_id = False

    default_data = {}

    class Meta:
        model = TaskInfo
        exclude = [
            "user",
            "modified_date",
            "start_date",
            "days_needed",
            "to_reschedule",
            "total_hours",
        ]
        widgets = {
            "due_date": TextInput(
                attrs={
                    "class": "datepicker",
                    "required": "True",
                    "autocomplete": "off",
                }
            ),
            "color": TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control-color",
                }
            ),
            "task_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Study Physics",
                    "required": "True",
                    "autocomplete": "off",
                }
            ),
            "task_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": "2",
                    "required": "True",
                    "autocomplete": "off",
                }
            ),
            "gradient": forms.Select(attrs={"class": "form-select"}),
            "hours_needed": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "required": "True",
                    "step": 0.01,
                    "min": "0",
                    "autocomplete": "off",
                }
            ),
            "days_needed": forms.TextInput(attrs={"class": "form-control"}),
            "total_hours": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
        }


class UserInfoForm(ModelForm):
    class Meta:
        model = UserInfo
        exclude = ["user"]
        widgets = {
            "time_zone": forms.Select(
                attrs={"class": "form-select", "id": "time_zone_select"}
            ),
            "week_day_work": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "1",
                    "step": 0.1,
                }
            ),
            "max_week_day_work": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "1",
                    "step": 0.1,
                }
            ),
            "week_end_work": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "1",
                    "step": 0.1,
                }
            ),
            "max_week_end_work": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "min": "1",
                    "step": 0.1,
                }
            ),
        }
        labels = {
            "week_day_work": "Number of Hours you can spend on a Weekday",
            "max_week_day_work": "Upper limit of Hours you can spend on a \
Weekday",
            "week_end_work": "Number of Hours you can spend on a Weekend day",
            "max_week_end_work": "Upper limit of Hours you can spend on a \
Weekend day",
        }


class ReschedulerDateForm(forms.Form):
    date = forms.CharField(
        widget=forms.TextInput(attrs={"type": "hidden", "name": "date"})
    )
    # to_date = forms.DateInput()
    extra_hours = forms.DecimalField(
        max_digits=4,
        decimal_places=2,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "type": "number",
                "min": "0",
                "step": 0.1,
            }
        ),
    )

    # class Meta:
    #     widgets = {
    #         'extra_hours': forms.TextInput(attrs={'class': 'form-control', 
    # 'type': 'number'}),
    #         'date': forms.TextInput(attrs={'type': 'hidden'}),
    #     }

    # task_name = forms.CharField(label='Task Name', max_length=100)
    # work = forms.IntegerField(label='Hours')
    # due_date = forms.CharField(label='Due Date', max_length=20)
    # gradient = forms.CharField(label='Gradient', max_length=1, initial='+')
