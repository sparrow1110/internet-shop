from django.urls import path
from users import views

app_name = "users"

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name='login'),
    path("register/", views.UserRegisterView.as_view(), name='register'),
    path("logout/", views.logout, name='logout'),
    path("users-cart/", views.UserCartView.as_view(), name='users_cart'),
    path("profile/", views.UserProfileView.as_view(), name='profile'),
]