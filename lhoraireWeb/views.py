

from django.shortcuts import redirect, render


def index(request):
    if request.user.is_authenticated:
        return redirect('/scheduler')
    else:
        return render(request, 'home.html', {})
