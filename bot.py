import os
import discord
from discord.ext import commands
from flask import Flask, render_template, request, jsonify
from threading import Thread

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/order', methods=['POST'])
def api_order():
    try:
        data = request.json
        print("Получены данные заказа:", data)
        bot.loop.create_task(send_receipt(data))
        return jsonify({"status": "success"})
    except Exception as e:
        print("Ошибка в api_order:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

async def send_receipt(data):
    channel_id = 1339521364708687875 
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(title="🧾 ART SHOP — DIGITAL RECEIPT", color=0x8b5cf6)
        embed.description = "Спасибо за покупку в нашем магазине! Ваш заказ успешно оформлен."
        embed.add_field(name="🛒 Выбранный товар", value=data.get('product', 'Товар'), inline=False)
        embed.add_field(name="👤 Покупатель", value=data.get('discord', 'User'), inline=True)
        embed.add_field(name="💰 Стоимость", value=data.get('price', '0$'), inline=True)
        embed.set_footer(text=f"ID транзакции: UI-77-9X04-ART")
        await channel.send(embed=embed)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')

Thread(target=run_flask).start()
bot.run(os.environ.get("DISCORD_TOKEN"))