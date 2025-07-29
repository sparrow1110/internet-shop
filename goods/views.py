from django.shortcuts import render, get_list_or_404
from goods.models import Categories, Products
# Create your views here.


def catalog(request, category_slug):
    if category_slug == "all":
        goods = Products.objects.all()
    else:
        goods = get_list_or_404(Products, category__slug=category_slug)
    context = {
        "title": "ModaHouse - Каталог",
        "goods": goods,
    }

    return render(request, "goods/catalog.html", context=context)


def product(request, product_slug):
    product = Products.objects.get(slug=product_slug)
    context = {
        "title": f"ModaHouse - {product.name}",
        "product": product,
    }

    return render(request, "goods/product.html", context)