from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    image = models.ImageField(upload_to="users_images", blank=True, null=True, verbose_name="Аватар")
    phone_number = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = 'user'
        verbose_name = "Пользователя"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True, primary_key=True)
    token = models.CharField(max_length=255)

    class Meta:
        db_table = 'telegram_user'
        verbose_name = "Telegram-пользователя"
        verbose_name_plural = "Telegram-пользователи"

    def __str__(self):
        return f"TelegramUser {self.telegram_id}"