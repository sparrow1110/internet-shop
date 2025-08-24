from django.http import Http404
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.serializers import ProductSerializer, CartSerializer, OrderListSerializer, OrderDetailSerializer
from carts.models import Cart
from goods.models import Products
from goods.utils import q_search
from orders.models import Order


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


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Products.objects.all()
    lookup_field = 'pk'


class CartListView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related('product')

    def get_serializer_class(self):
        return CartSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Используем методы из CartQueryset
        total_quantity = queryset.total_quantity()
        total_amount = queryset.total_price()

        # Формируем ответ вручную
        response_data = {
            'items': serializer.data,
            'total_quantity': total_quantity,
            'total_amount': total_amount
        }

        return Response(response_data)


class OrdersListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user).order_by('-created_timestamp')  # Сортировка по дате
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
                if limit > 0:
                    queryset = queryset[:limit]
            except ValueError:
                pass  # Игнорируем некорректный limit
        return queryset


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('orderitem_set__product')

