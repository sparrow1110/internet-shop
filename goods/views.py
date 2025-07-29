from django.core.paginator import Paginator
from django.shortcuts import render, get_list_or_404, get_object_or_404
from goods.models import Categories, Products


def catalog(request, category_slug):

    on_sale = request.GET.get("on_sale", None)
    order_by = request.GET.get("order_by", None)
    if category_slug == "all":
        goods = Products.objects.all()
    else:
        goods = Products.objects.filter(category__slug=category_slug)

    if on_sale:
        goods = goods.filter(discount__gt=0)

    if order_by and order_by != "default":
        goods = goods.order_by(order_by)
    paginator = Paginator(goods, 3)
    page = request.GET.get("page", 1)
    current_page = paginator.get_page(int(page))

    context = {
        "title": "ModaHouse - Каталог",
        "goods": current_page,
        "slug_url": category_slug
    }

    return render(request, "goods/catalog.html", context=context)


def product(request, product_slug):
    product = Products.objects.get(slug=product_slug)
    context = {
        "title": f"ModaHouse - {product.name}",
        "product": product,
    }

    return render(request, "goods/product.html", context)