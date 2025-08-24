import os
from pathlib import Path
from cachetools import TTLCache, cached
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import logging
from dotenv import load_dotenv
# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eshop.settings')
import django
django.setup()
from users.models import TelegramUser


# Настройка базового пути
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = os.getenv('BASE_URL')

# Кэш
products_cache = TTLCache(maxsize=100, ttl=300)
orders_cache = TTLCache(maxsize=100, ttl=100)

CATEGORIES = [
    {'name': 'Все товары', 'slug': 'all'},
    {'name': 'Кухня', 'slug': 'kuhnya'},
    {'name': 'Спальня', 'slug': 'spalnya'},
    {'name': 'Гостиная', 'slug': 'gostinnaya'},
    {'name': 'Офис', 'slug': 'ofis'},
    {'name': 'Декор', 'slug': 'dekor'},
]


def save_token(telegram_id, token):
    try:
        TelegramUser.objects.update_or_create(telegram_id=telegram_id, defaults={'token': token})
        logging.info(f"Token saved for telegram_id {telegram_id}")
    except Exception as e:
        logging.error(f"Error saving token for telegram_id {telegram_id}: {e}")


def get_token(telegram_id):
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        return user.token
    except TelegramUser.DoesNotExist:
        return None
    except Exception as e:
        logging.error(f"Error fetching token for telegram_id {telegram_id}: {e}")
        return None


def delete_token(telegram_id):
    try:
        TelegramUser.objects.filter(telegram_id=telegram_id).delete()
        logging.info(f"Token deleted for telegram_id {telegram_id}")
    except Exception as e:
        logging.error(f"Error deleting token for telegram_id {telegram_id}: {e}")


def create_main_keyboard(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Каталог"))
    token = get_token(chat_id)
    button_text = "Профиль" if token else "Войти"
    markup.add(KeyboardButton(button_text))
    return markup


def create_pagination_keyboard(data, category_slug, page):
    pagination_markup = InlineKeyboardMarkup(row_width=2)
    if data['previous'] and data['next']:
        pagination_markup.add(
            InlineKeyboardButton("◀️ Назад", callback_data=f"page_{category_slug}_{page - 1}"),
            InlineKeyboardButton("Вперед ▶️", callback_data=f"page_{category_slug}_{page + 1}")
        )
    elif data['previous']:
        pagination_markup.add(InlineKeyboardButton("◀️ Назад", callback_data=f"page_{category_slug}_{page - 1}"))
    elif data['next']:
        pagination_markup.add(InlineKeyboardButton("Вперед ▶️", callback_data=f"page_{category_slug}_{page + 1}"))
    return pagination_markup


def create_products_keyboard(products, page):
    message_text = f"Товары в категории (страница {page}):\n\n"
    product_buttons = []
    for product in products:
        message_text += f"{product['name']}\nЦена: {product['sell_price']} $\nОписание: {product['description'][:50]}...\n\n"
        product_buttons.append(KeyboardButton(f"Выбрать: {product['name']}"))

    choice_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    choice_markup.add(*product_buttons)
    choice_markup.add(KeyboardButton("Назад в каталог"))
    return choice_markup, message_text


def create_profile_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("Моя корзина"),
        KeyboardButton("Мои заказы"),
        KeyboardButton("Выйти"),
        KeyboardButton("Главное меню")
    )
    return markup


@cached(products_cache)
def get_products(category_slug, page):
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products/", params={'category_slug': category_slug, 'page': page})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Failed to fetch products for category {category_slug}, page {page}: {e}")
        return None


@cached(orders_cache)
def get_orders(token):
    try:
        headers = {'Authorization': f'Token {token}'}
        params = {'limit': 5}
        response = requests.get(f"{BASE_URL}/api/v1/orders/", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Failed to fetch orders: {e}")
        return None