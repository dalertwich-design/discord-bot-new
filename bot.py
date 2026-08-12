import threading
import os
import discord
from discord.ext import commands
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Настройка Discord бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ID канала для уведомлений (можно указать или оставить пустым)
CHANNEL_ID = None  

@bot.event
async def on_ready():
    print(f'Бот авторизован как {bot.user}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/order', methods=['POST'])
def order():
    data = request.json
    product = data.get('product')
    price = data.get('price')
    discord_user = data.get('discord')

    print(f"Новый заказ: {product} за {price} от {discord_user}")

    # Отправка уведомления в Discord, если указан ID канала
    try:
        if CHANNEL_ID:
            import asyncio
            fut = asyncio.run_coroutine_threadsafe(
                send_discord_notification(product, price, discord_user), bot.loop
            )
            fut.result(timeout=5)
    except Exception as e:
        print(f"Ошибка отправки в Discord: {e}")

    return jsonify({"status": "success"})

async def send_discord_notification(product, price, discord_user):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"🚨 **Новый заказ!**\n👤 Покупатель: **{discord_user}**\n📦 Товар: **{product}**\n💰 Цена: **{price}**")

# Функция запуска веб-сервера Flask
def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Запускаем Discord бота
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("ОШИБКА: Токен Discord не найден в переменных окружения!")