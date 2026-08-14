import os
import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from discord.ui import View, Button, Select
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
        embed.set_footer(text="ID транзакции: UI-77-9X04-ART")
        await channel.send(embed=embed)

PRODUCTS = {
    "Discord": {"Nitro Full": "200$", "Nitro Basic": "100$", "Украшение": "50$"},
    "Telegram": {"Telegram Premium": "150$"},
    "Spotify": {"Spotify Premium": "120$"},
    "Роблокс": {"1000 Роблуксов": "80$", "5000 Роблуксов": "350$"},
    "КС ГО": {"Нож | Драконий коготь": "450$", "AWP | Азимов": "90$"},
    "ПАБГ": {"600 UC": "60$", "1800 UC": "170$"}
}

class InfoView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Заказать", style=discord.ButtonStyle.green, custom_id="btn_order")
    async def order_button(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "Оформление заказа")

    @discord.ui.button(label="Товары", style=discord.ButtonStyle.primary, custom_id="btn_products")
    async def products_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Выберите категорию товаров:", view=CategorySelectView(), ephemeral=True)

    @discord.ui.button(label="Админ", style=discord.ButtonStyle.secondary, custom_id="btn_admin")
    async def admin_button(self, interaction: discord.Interaction, button: Button):
        await create_ticket(interaction, "Обращение к администрации")

class CategorySelectView(View):
    def __init__(self):
        super().__init__(timeout=180)
        select = Select(
            placeholder="Выберите категорию...",
            options=[discord.SelectOption(label=cat, description=f"Каталог {cat}") for cat in PRODUCTS.keys()]
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        selected_cat = interaction.data["values"][0]
        items_text = "\n".join([f"• **{item}** — `{price}`" for item, price in PRODUCTS[selected_cat].items()])
        embed = discord.Embed(title=f"📦 Товары в категории: {selected_cat}", description=items_text, color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def create_ticket(interaction: discord.Interaction, reason: str):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="ТИКЕТЫ")
    if not category:
        category = await guild.create_category("ТИКЕТЫ")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    embed = discord.Embed(
        title="🛒 Меню заказа / Тикет",
        description=f"**Пользователь:** {interaction.user.mention}\n**Цель:** {reason}\n**Дата создания:** {current_time}",
        color=discord.Color.green()
    )
    
    view = TicketControlView(interaction.user.id)
    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Ваш тикет создан: {channel.mention}", ephemeral=True)

class TicketControlView(View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Закрыть тикет может только владелец!", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Тикет закрывается...")
        await asyncio.sleep(2)
        await interaction.channel.delete()

    @discord.ui.button(label="Карта", style=discord.ButtonStyle.primary, custom_id="show_card")
    async def show_card(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("💳 Реквизиты карты:", ephemeral=True)

    @discord.ui.button(label="Товары", style=discord.ButtonStyle.secondary, custom_id="show_prod_ticket")
    async def show_prod(self, interaction: discord.Interaction, button: Button):
        text = "📦 **Доступные товары:**\n"
        for cat, items in PRODUCTS.items():
            text += f"\n**{cat}**:\n" + "".join([f"  • {k}: {v}\n" for k, v in items.items()])
        await interaction.response.send_message(text, ephemeral=True)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command(name="info")
async def info_command(ctx):
    embed = discord.Embed(
        title="Art Shop",
        description="Добро пожаловать в наш премиум магазин, если желаете приобрести какой либо товар можете это оформить нажимая ниже кнопку.\nЕсли хотите обратится к администрации сделайте аналогичную действию.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=InfoView())

@bot.command(name="review", aliases=["отзывы"])
async def review_command(ctx):
    embed = discord.Embed(
        title="⭐ Отзывы о магазине Art Shop",
        description="Нажмите на кнопку ниже, чтобы открыть страницу с отзывами на нашем сайте!",
        color=discord.Color.purple()
    )
    
    view = View()
    # Замените ссылку ниже на адрес вашего приложения на Railway и добавьте /reviews в конце
    view.add_item(Button(label="Смотреть отзывы на сайте", style=discord.ButtonStyle.link, url="https://discord-bot-new-production.up.railway.app/reviews"))
    
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    @app.route('/reviews')
def reviews_page():
    return render_template('reviews.html')

Thread(target=run_flask).start()
bot.run(os.environ.get("DISCORD_TOKEN"))