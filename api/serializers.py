
from rest_framework import serializers

from carts.models import Cart
from goods.models import Products
from orders.models import OrderItem, Order
from users.models import User


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ("pk", "name", "slug", "description", "image", "price", "discount", "sell_price", )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number'
        ]


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины (только чтение)"""
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.products_price()


class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'name', 'price', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.products_price()


class OrderListSerializer(serializers.ModelSerializer):
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'created_timestamp', 'payment_on_get', 'status', 'total_amount'
        ]

    def get_total_amount(self, obj):
        return obj.orderitem_set.total_price()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True, source='orderitem_set')
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'created_timestamp', 'requires_delivery',
            'delivery_address', 'payment_on_get', 'is_paid', 'status',
            'items', 'total_amount'
        ]

    def get_total_amount(self, obj):
        return obj.orderitem_set.total_price()
