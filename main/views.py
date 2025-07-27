from django.shortcuts import render

# Create your views here.


def index(request):
    context = {
        "title": "ModaHouse - Главная",
        "content": "Магазин мебели ModaHouse"
    }
    return render(request, "main/index.html", context=context)


def about(request):
    context = {
        "title": "ModaHouse - О нас",
        "content": "О нас",
        "text_on_page": "Мы создаём мебель, которая превращает ваш дом в уютное и стильное пространство, "
                        "где каждая деталь продумана для комфорта и вдохновения.",
    }
    return render(request, "main/about.html", context=context)