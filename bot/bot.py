import os
from datetime import datetime
import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from bot.bot_utils import (
    save_token, get_token, delete_token, create_main_keyboard,
    create_pagination_keyboard, create_products_keyboard, create_profile_keyboard,
    get_products, get_orders, BASE_URL, BASE_DIR, CATEGORIES
)
import logging
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MEDIA_ROOT = BASE_DIR / 'media'
BOT_TOKEN = os.environ['BOT_TOKEN']
bot = telebot.TeleBot(BOT_TOKEN)


user_states = {}


def ensure_user_state(chat_id):
    if chat_id not in user_states:
        user_states[chat_id] = {}
        logging.info(f"Initialized user_states for user {chat_id}")


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    markup = create_main_keyboard(message.chat.id)
    bot.send_message(message.chat.id, "🏬 Добро пожаловать в ModaHouse! Нажмите 'Каталог' для просмотра товаров.",
                     reply_markup=markup)
    logging.info(f"User {message.chat.id} started bot")


@bot.message_handler(commands=['catalog'])
def show_categories(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(cat['name']) for cat in CATEGORIES]
    markup.add(*buttons)
    markup.add(KeyboardButton('Главное меню'))
    bot_message = bot.send_message(chat_id, "Выберите категорию:", reply_markup=markup)
    user_states[chat_id] = {'last_message_ids': [bot_message.message_id]}
    logging.info(f"Displayed categories for user {chat_id}")


def show_products(chat_id, category_slug, page=1):
    user_states[chat_id] = {'category_slug': category_slug, 'page': page, 'last_message_ids': [], 'last_products': []}

    data = get_products(category_slug, page)
    if not data:
        bot.send_message(chat_id, "❌ Ошибка загрузки товаров. Попробуйте позже.")
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
        bot.send_message(chat_id, "❌ Ошибка загрузки данных товара. Попробуйте позже.")
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
        bot.send_message(chat_id, f"❌ Ошибка загрузки изображения: {str(e)}")
        logging.error(f"Failed to send product {pk} image: {e}")

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Вернуться к списку товаров"))
    bot.send_message(chat_id, "Нажмите кнопку ниже, чтобы вернуться к списку товаров:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Войти")
def request_login(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    token = get_token(chat_id)
    if token:
        bot.send_message(chat_id, "Вы уже авторизованы.")
        return
    user_states[chat_id] = {'state': 'awaiting_credentials'}
    bot.send_message(chat_id, "Введите логин и пароль через пробел (например: user123 password123):")
    logging.info(f"User {chat_id} requested login")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'awaiting_credentials')
def handle_credentials(message):
    chat_id = message.chat.id
    try:
        login, password = message.text.split()
    except ValueError:
        bot.send_message(chat_id, "❌ Пожалуйста, введите логин и пароль через пробел.")
        return

    try:
        response = requests.post(f"{BASE_URL}/auth/token/login/", json={'username': login, 'password': password})
        response.raise_for_status()
        data = response.json()
        token = data.get('auth_token')
        if token:
            save_token(chat_id, token)
            user_states[chat_id] = {}  # Очищаем состояние
            keyboard = create_main_keyboard(chat_id)
            bot.send_message(chat_id, "✅ Авторизация успешна!", reply_markup=keyboard)
            logging.info(f"User {chat_id} logged in successfully")
        else:
            bot.send_message(chat_id, "❌ Ошибка авторизации. Проверьте логин и пароль.")
            logging.error(f"Login failed for user {chat_id}: no token in response")
    except Exception as e:
        bot.send_message(chat_id, "❌ Ошибка авторизации. Попробуйте еще раз.")
        logging.error(f"Login error for user {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "Профиль")
def show_profile(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    token = get_token(chat_id)
    if not token:
        bot.send_message(chat_id, "❌ Вы не авторизованы. Нажмите 'Войти' для авторизации.")
        return

    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(f"{BASE_URL}/auth/users/me/", headers=headers)
        response.raise_for_status()
        user_data = response.json()
        profile_text = (
            f"👤 Профиль пользователя:\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👩‍💼 Имя пользователя: {user_data['username']}\n"
            f"📧 Email: {user_data['email']}\n"
            f"🧑 Имя: {user_data['first_name']}\n"
            f"👪 Фамилия: {user_data['last_name']}"
        )
        markup = create_profile_keyboard()
        bot.send_message(chat_id, profile_text, reply_markup=markup)
        logging.info(f"Displayed profile for user {chat_id}")
    except Exception as e:
        bot.send_message(chat_id, "❌ Ошибка загрузки профиля. Попробуйте позже.")
        logging.error(f"Profile fetch error for user {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "Моя корзина")
def show_cart(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    token = get_token(chat_id)
    if not token:
        bot.send_message(chat_id, "❌ Вы не авторизованы. Нажмите 'Войти' для авторизации.")
        return

    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(f"{BASE_URL}/api/v1/cart/", headers=headers)
        response.raise_for_status()
        cart_data = response.json()
        items = cart_data.get('items', [])
        total_quantity = cart_data.get('total_quantity', 0)
        total_amount = cart_data.get('total_amount', 0)

        if not items:
            bot.send_message(chat_id, "🛒 Ваша корзина пуста.")
            return

        message_text = "🛒 Ваша корзина:\n\n"
        for item in items:
            product = item['product']
            message_text += (
                f"🛍 Товар: {product['name']}\n"
                f"  Количество: {item['quantity']} x {product['sell_price']} $ = {item['total_price']} $\n\n"
            )
        message_text += f"➡️ Итого: {total_quantity} товар(а) на сумму {total_amount} $"

        markup = create_profile_keyboard()
        bot.send_message(chat_id, message_text, reply_markup=markup)
        logging.info(f"Displayed cart for user {chat_id}")
    except Exception as e:
        bot.send_message(chat_id, "❌ Ошибка загрузки корзины. Попробуйте позже.")
        logging.error(f"Cart fetch error for user {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "Мои заказы")
def show_orders(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    token = get_token(chat_id)
    if not token:
        bot.send_message(chat_id, "❌ Вы не авторизованы. Нажмите 'Войти' для авторизации.")
        return

    try:
        orders = get_orders(token)
        if not orders:
            bot.send_message(chat_id, "📋 У вас нет заказов.")
            return

        message_text = "📋 Последние 5 заказов:\n\n"
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        for order in orders:
            date = datetime.fromisoformat(order['created_timestamp'].replace('Z', '+00:00')).strftime('%d.%m.%Y %H:%M')
            message_text += (
                f"📦 Заказ №{order['id']}\n"
                f"📅 Дата создания: {date}\n"
                f"✅ Статус: {order['status']}\n"
                f"💳 Способ оплаты: {'При получении' if order['payment_on_get'] else 'Онлайн'}\n"
                f"💲 Общая стоимость: {order['total_amount']} $\n\n"
            )
            markup.add(KeyboardButton(f"Заказ №{order['id']}"))

        markup.add(KeyboardButton("Назад в профиль"), KeyboardButton("Главное меню"))

        message = bot.send_message(chat_id, message_text, reply_markup=markup)
        user_states[chat_id]['last_message_ids'] = [message.message_id]
        logging.info(f"Displayed orders for user {chat_id}")
    except Exception as e:
        bot.send_message(chat_id, "❌ Ошибка загрузки заказов. Попробуйте позже.")
        logging.error(f"Orders fetch error for user {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text.startswith("Заказ №"))
def show_order_details(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    token = get_token(chat_id)
    if not token:
        bot.send_message(chat_id, "❌ Вы не авторизованы. Нажмите 'Войти' для авторизации.")
        return

    order_id = message.text.split("Заказ №")[1]
    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.get(f"{BASE_URL}/api/v1/orders/{order_id}/", headers=headers)
        response.raise_for_status()
        order = response.json()
        date = datetime.fromisoformat(order['created_timestamp'].replace('Z', '+00:00')).strftime('%d.%m.%Y %H:%M')
        message_text = (
            f"📦 Детали заказа №{order['id']}:\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📅 Дата создания: {date}\n"
            f"🚚 Требуется доставка: {'Да' if order['requires_delivery'] else 'Нет'}\n"
            f"🏠 Адрес доставки: {order['delivery_address'] or 'Не указан'}\n"
            f"💳 Способ оплаты: {'При получении' if order['payment_on_get'] else 'Онлайн'}\n"
            f"✅ Оплачено: {'Да' if order['is_paid'] else 'Нет'}\n"
            f"📋 Статус: {order['status']}\n"
            f"💲 Общая сумма: {order['total_amount']} $\n\n"
            f"🛍 Товары:\n"
        )
        for item in order['items']:
            message_text += (
                f"- {item['name']}\n"
                f"  {item['quantity']} x {item['price']} $ = {item['total_price']} $\n\n"
            )

        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(KeyboardButton("Назад в профиль"), KeyboardButton("Главное меню"))
        bot.send_message(chat_id, message_text, reply_markup=markup)
        logging.info(f"Displayed order {order_id} details for user {chat_id}")
    except Exception as e:
        bot.send_message(chat_id, "❌ Ошибка загрузки деталей заказа. Попробуйте позже.")
        logging.error(f"Order {order_id} fetch error for user {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "Назад в профиль")
def back_to_profile(message):
    show_profile(message)


@bot.message_handler(func=lambda message: message.text == "Выйти")
def logout(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    token = get_token(chat_id)
    if not token:
        bot.send_message(chat_id, "Вы не авторизованы.")
        return

    try:
        headers = {'Authorization': f'Token {token}'}
        response = requests.post(f"{BASE_URL}/auth/token/logout/", headers=headers)
        response.raise_for_status()
        delete_token(chat_id)
        keyboard = create_main_keyboard(chat_id)
        bot.send_message(chat_id, "Вы успешно вышли из системы.", reply_markup=keyboard)
        logging.info(f"User {chat_id} logged out")
    except Exception as e:
        bot.send_message(chat_id, "❌ Ошибка при выходе. Попробуйте позже.")
        logging.error(f"Logout error for user {chat_id}: {e}")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    ensure_user_state(chat_id)
    if message.text == "Каталог":
        show_categories(message)
    elif message.text == "Назад в каталог":
        user_states[chat_id]['last_products'] = []
        show_categories(message)
    elif message.text == "Вернуться к списку товаров":
        if chat_id in user_states:
            state = user_states[chat_id]
            show_products(chat_id, state['category_slug'], state['page'])
    elif message.text == "Главное меню":
        keyboard = create_main_keyboard(chat_id)
        bot.send_message(chat_id, "🏠 Вы вернулись в главное меню.", reply_markup=keyboard)
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
    else:
        bot.send_message(chat_id, "❌ Неизвестная команда. Выберите действие из меню.")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    ensure_user_state(chat_id)
    if call.data.startswith("page_"):
        parts = call.data.split('_')
        slug = parts[1]
        page = int(parts[2])
        if chat_id in user_states and 'last_message_ids' in user_states[chat_id]:
            for message_id in user_states[chat_id]['last_message_ids']:
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception as e:
                    logging.error(f"Failed to delete message {message_id}: {e}")
        show_products(chat_id, slug, page)
        bot.answer_callback_query(call.id)
        logging.info(f"User {chat_id} navigated to page {page} in category {slug}")


if __name__ == '__main__':
    logging.info("Starting bot")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Ошибка в работе бота: {e}")

