from django.shortcuts import render

# Create your views here.


def catalog(request):
    context = {
        "title": "ModaHouse - Каталог"
    }
    return render(request, "goods/catalog.html", context=context)


def product(request):
    return render(request, "goods/product.html")