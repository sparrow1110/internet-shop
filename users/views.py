from django.shortcuts import render


def login(request):
    context = {
        'title': 'ModaHouse - Авторизация'
    }
    return render(request, "users/login.html", context)


def register(request):
    context = {
        'title': 'ModaHouse - Регистрация'
    }
    return render(request, "users/register.html", context)


def profile(request):
    context = {
        'title': 'ModaHouse - Профиль'
    }
    return render(request, "users/profile.html", context)


def logout(request):
    pass