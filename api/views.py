from django.http import Http404
from django.shortcuts import render
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from api.serializers import ProductSerializer
from goods.models import Products
from goods.utils import q_search


# Create your views here.
class ProductsListPagination(PageNumberPagination):
    page_size = 3


class ProductsListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    queryset = Products.objects.all()
    pagination_class = ProductsListPagination

    def get_queryset(self):
        category_slug = self.request.GET.get("category_slug")
        on_sale = self.request.GET.get("on_sale")
        order_by = self.request.GET.get("order_by")
        query = self.request.GET.get("q")

        if query:
            goods = q_search(query)
        elif category_slug == "all" or not category_slug:
            goods = super().get_queryset()
        else:
            goods = super().get_queryset().filter(category__slug=category_slug)
            if not goods:
                raise Http404()

        if on_sale:
            goods = goods.filter(discount__gt=0)

        if order_by and order_by != "default":
            goods = goods.order_by(order_by)
        return goods


