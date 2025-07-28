from django.shortcuts import render
from goods.models import Categories, Products
# Create your views here.


def catalog(request, slug):
    if slug == "all":
        goods = Products.objects.all()
    else:
        goods = Products.objects.filter(category__slug=slug)
    categories = Categories.objects.all()
    context = {
        "title": "ModaHouse - Каталог",
        "goods": goods,
        "categories": categories
    }

    return render(request, "goods/catalog.html", context=context)


def product(request):
    return render(request, "goods/product.html")