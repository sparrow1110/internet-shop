from django.urls import path

from api.views import *

urlpatterns = [
    path("api/v1/products/", ProductsListView.as_view()),
    path('api/v1/products/<int:pk>/', ProductDetailView.as_view()),
    path('api/v1/cart/', CartListView.as_view()),
    path('api/v1/orders/', OrdersListView.as_view()),
    path('api/v1/orders/<int:pk>/', OrderDetailView.as_view())
]