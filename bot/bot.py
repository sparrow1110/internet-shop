import telebot
from cachetools import TTLCache, cached
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import logging
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.getenv('BOT_TOKEN')
BASE_URL = os.getenv('BASE_URL')

# Путь к папке media в корне проекта
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = BASE_DIR / 'media'  # Папка media в корне проекта

# Кэш для данных о товарах (хранит до 100 записей, TTL = 5 минут)
products_cache = TTLCache(maxsize=100, ttl=300)

CATEGORIES = [
    {'name': 'Все товары', 'slug': 'all'},
    {'name': 'Кухня', 'slug': 'kuhnya'},
    {'name': 'Спальня', 'slug': 'spalnya'},
    {'name': 'Гостиная', 'slug': 'gostinnaya'},
    {'name': 'Офис', 'slug': 'ofis'},
    {'name': 'Декор', 'slug': 'dekor'},
]

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище состояния пользователя
user_states = {}


def create_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Каталог"))
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


@bot.message_handler(commands=['start'])
def start(message):
    markup = create_main_keyboard()
    bot.send_message(message.chat.id, "Добро пожаловать в ModaHouse! Нажмите 'Каталог' для просмотра товаров.",
                     reply_markup=markup)
    logging.info(f"User {message.chat.id} started bot")


@bot.message_handler(commands=['catalog'])
def show_categories(message):
    chat_id = message.chat.id
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(cat['name']) for cat in CATEGORIES]
    markup.add(*buttons)
    markup.add(KeyboardButton('Главное меню'))
    bot_message = bot.send_message(chat_id, "Выберите категорию:", reply_markup=markup)
    user_states[chat_id] = {'last_message_ids': [bot_message.message_id]}
    logging.info(f"Displayed categories for user {chat_id}")


@cached(products_cache)
def get_products(category_slug, page):
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products/", params={'category_slug': category_slug, 'page': page})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Failed to fetch products for category {category_slug}, page {page}: {e}")
        return None


def show_products(chat_id, category_slug, page=1):
    user_states[chat_id] = {'category_slug': category_slug, 'page': page, 'last_message_ids': [], 'last_products': []}

    data = get_products(category_slug, page)
    if not data:
        bot.send_message(chat_id, "Ошибка загрузки товаров. Попробуйте позже.")
        return

    products = data['results']

    if not products:
        message = bot.send_message(chat_id, "Товары не найдены.")
        user_states[chat_id]['last_message_ids'] = [message.message_id]
        logging.info(f"No products found for category {category_slug}, page {page}")
        return

    pagination_markup = create_pagination_keyboard(data, category_slug, page)
    choice_markup, message_text = create_products_keyboard(products, page)

    user_states[chat_id]['last_products'].extend(products)

    products_message = bot.send_message(chat_id, message_text, reply_markup=pagination_markup)
    choice_message = bot.send_message(chat_id, "Выберите товар или вернитесь в каталог:", reply_markup=choice_markup)
    user_states[chat_id]['last_message_ids'] = [products_message.message_id, choice_message.message_id]
    logging.info(f"Displayed products for category {category_slug}, page {page} for user {chat_id}")


def show_product_details(chat_id, pk):
    try:
        response = requests.get(f"{BASE_URL}/api/v1/products/{pk}/")
        response.raise_for_status()
    except Exception as e:
        bot.send_message(chat_id, "Ошибка загрузки данных товара. Попробуйте позже.")
        logging.error(f"Failed to fetch product {pk}: {e}")
        return

    product = response.json()
    sell_price = product['sell_price'] if float(product['discount']) > 0.0 else product['price']
    caption = f"{product['name']}\nЦена: {sell_price} $\nОписание: {product['description']}"

    try:
        if product['image']:
            parsed_url = urlparse(product['image'])
            image_path = parsed_url.path.split('/media/', 1)[-1]
            full_image_path = MEDIA_ROOT / image_path
            logging.info(f"Attempting to send local image: {full_image_path}")

            if os.path.exists(full_image_path):
                with open(full_image_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=caption)
                logging.info(f"Sent local photo for product {pk} to user {chat_id}")
            else:
                not_found_image_path = BASE_DIR / 'static' / 'images' / 'Not found image.png'
                with open(not_found_image_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=caption)
                logging.info(f"Sent not-found image for product {pk} to user {chat_id}")
        else:
            bot.send_message(chat_id, f"{caption}\n(Изображение отсутствует)")
            logging.info(f"Sent text for product {pk} (no image) to user {chat_id}")
    except Exception as e:
        bot.send_message(chat_id, f"Ошибка загрузки изображения: {str(e)}")
        logging.error(f"Failed to send product {pk} image: {e}")

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Вернуться к списку товаров"))
    bot.send_message(chat_id, "Нажмите кнопку ниже, чтобы вернуться к списку товаров:", reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if message.text == "Каталог":
        show_categories(message)
    elif message.text == "Назад в каталог":
        user_states[chat_id]['last_products'] = []
        show_categories(message)
    elif message.text == "Вернуться к списку товаров":
        # Восстанавливаем предыдущее состояние
        if chat_id in user_states:
            state = user_states[chat_id]
            show_products(chat_id, state['category_slug'], state['page'])
    elif message.text == "Главное меню":
        keyboard = create_main_keyboard()
        bot.send_message(message.chat.id, "Вы вернулись в главное меню.", reply_markup=keyboard)
    elif message.text in [cat['name'] for cat in CATEGORIES]:
        category = next((cat for cat in CATEGORIES if cat['name'] == message.text), None)
        if category:
            show_products(chat_id, category['slug'], 1)
            logging.info(f"User {chat_id} selected category: {category['name']}")
    elif message.text.startswith("Выбрать: "):
        try:
            product_name = message.text.split("Выбрать: ")[1]
            if chat_id in user_states and 'last_products' in user_states[chat_id]:
                product = next((p for p in user_states[chat_id]['last_products']
                                if p['name'] == product_name), None)
                if product:
                    show_product_details(chat_id, product['pk'])
                    logging.info(f"User {chat_id} selected product {product['pk']}")
        except Exception as e:
            bot.send_message(chat_id, f"Ошибка выбора товара: {str(e)}")
            logging.error(f"Error in product selection for user {chat_id}: {e}")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data.startswith("page_"):
        print(call.data)
        parts = call.data.split('_')
        slug = parts[1]
        page = int(parts[2])
        if chat_id in user_states and 'last_message_ids' in user_states[chat_id]:
            for message_id in user_states[chat_id]['last_message_ids']:
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception as e:
                    logging.error(f"Failed to delete message {message_id}: {e}")
        print(slug, page)
        show_products(chat_id, slug, page)
        bot.answer_callback_query(call.id)
        logging.info(f"User {chat_id} navigated to page {page} in category {slug}")


if __name__ == '__main__':
    logging.info("Starting bot")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Ошибка в работе бота: {e}")
