from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Create your views here.


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('scheduler:userinfo')
        # else:
        #     messages.error(request, 'Insert valid credentials')
        #     return redirect('/accounts/signup')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/accounts.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('/scheduler')
        else:
            messages.error(request, 'Username or Password not correct')
            return redirect('/accounts/login')

    elif request.user.is_authenticated:
        return redirect('scheduler:index')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/accounts.html', {'form': form})


def logout_view(request):
    # if request.method == 'POST':
    logout(request)
    return redirect('/accounts/login')
