

from django.shortcuts import redirect


def index(response):
    return redirect('/accounts/login')
