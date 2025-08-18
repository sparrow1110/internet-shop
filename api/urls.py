from django.urls import path

from api.views import ProductsListView, ProductDetailView
from goods import views


urlpatterns = [
    path("api/v1/products/", ProductsListView.as_view()),
    path('api/v1/products/<int:pk>/', ProductDetailView.as_view())
]