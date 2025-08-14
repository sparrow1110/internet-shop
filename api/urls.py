from django.urls import path

from api.views import ProductsListView
from goods import views


urlpatterns = [
    path("api/v1/products/", ProductsListView.as_view())
]