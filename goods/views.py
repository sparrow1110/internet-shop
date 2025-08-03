from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render, get_list_or_404, get_object_or_404
from goods.models import Categories, Products
from goods.utils import q_search


def catalog(request, category_slug=None):
    on_sale = request.GET.get("on_sale", None)
    order_by = request.GET.get("order_by", None)
    query = request.GET.get("q", None)

    if category_slug == "all":
        category_name = "Все товары"
        goods = Products.objects.all()
    elif query:
        category_name = ""
        goods = q_search(query)
    else:
        category = get_object_or_404(Categories, slug=category_slug)
        category_name = category.name
        goods = Products.objects.filter(category=category)
        if not goods.exists():
            raise Http404()

    if on_sale:
        goods = goods.filter(discount__gt=0)

    if order_by and order_by != "default":
        goods = goods.order_by(order_by)
    paginator = Paginator(goods, 3)
    page = request.GET.get("page", 1)
    current_page = paginator.get_page(int(page))

    context = {
        "title": f"ModaHouse - {category_name}",
        "goods": current_page,
        "slug_url": category_slug,
        "category": category_name
    }

    return render(request, "goods/catalog.html", context=context)


def product(request, product_slug):
    product = Products.objects.get(slug=product_slug)
    context = {
        "title": f"ModaHouse - {product.name}",
        "product": product,
    }

    return render(request, "goods/product.html", context)