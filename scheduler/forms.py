from django import forms


class TaskForm(forms.Form):
    task_name = forms.CharField(label='Task Name', max_length=100)
    work = forms.IntegerField(label='Hours')
    due_date = forms.CharField(label='Due Date', max_length=20)
    gradient = forms.CharField(label='Gradient', max_length=1, initial='+')
