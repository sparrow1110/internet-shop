
from rest_framework import serializers

from goods.models import Products


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ("pk", "name", "slug", "description", "image", "price", "discount", "sell_price", )