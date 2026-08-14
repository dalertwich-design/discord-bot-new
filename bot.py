import os
import asyncio
import json
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from flask import Flask, render_template_string, request, jsonify, make_response
from threading import Thread

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')

# Файл для сохранения отзывов
REVIEWS_FILE = 'reviews.json'

def load_reviews():
    if os.path.exists(REVIEWS_FILE):
        try:
            with open(REVIEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return [
        {"username": "@daler", "text": "Отличный магазин! Брал товар, всё пришло моментально, рекомендую!", "time": "2026-08-14 12:00:00"},
        {"username": "@user123", "text": "Быстрая поддержка и честные цены. Буду брать еще.", "time": "2026-08-14 12:00:00"}
    ]

def save_reviews(reviews):
    with open(REVIEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=4)

REVIEWS_LIST = load_reviews()

# Шаблон страницы: белый текст везде, песочный фон у блоков формы и карточек
REVIEWS_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Отзывы — Art Shop</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #0f172a;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            min-height: 100vh;
        }
        .review-counter {
            position: absolute;
            top: 20px;
            right: 30px;
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 8px 16px;
            border-radius: 12px;
            font-weight: bold;
            color: #ffffff;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            font-size: 14px;
        }
        h1 { color: #ffffff; margin-bottom: 10px; margin-top: 20px; }
        p.desc { color: #ffffff; margin-bottom: 25px; text-align: center; opacity: 0.9; }
        .glass-radio-group {
            --bg: rgba(255, 255, 255, 0.06);
            --text: #ffffff;
            display: flex;
            position: relative;
            background: var(--bg);
            border-radius: 1rem;
            backdrop-filter: blur(12px);
            box-shadow: inset 1px 1px 4px rgba(255, 255, 255, 0.2), inset -1px -1px 6px rgba(0, 0, 0, 0.3), 0 4px 12px rgba(0, 0, 0, 0.15);
            overflow: hidden;
            width: fit-content;
            margin-bottom: 40px;
        }
        .glass-radio-group input { display: none; }
        .glass-radio-group label {
            flex: 1; display: flex; align-items: center; justify-content: center; min-width: 100px;
            font-size: 14px; padding: 0.8rem 1.6rem; cursor: pointer; font-weight: 600; letter-spacing: 0.3px;
            color: var(--text); position: relative; z-index: 2; transition: color 0.3s ease-in-out;
        }
        .glass-radio-group label:hover { color: #ffffff; opacity: 1; }
        .glass-radio-group input:checked + label { color: #ffffff; }
        .glass-glider {
            position: absolute; top: 0; bottom: 0; width: calc(100% / 2); border-radius: 1rem; z-index: 1;
            transition: transform 0.5s cubic-bezier(0.37, 1.95, 0.66, 0.56), background 0.4s ease-in-out, box-shadow 0.4s ease-in-out;
        }
        #glass-write:checked ~ .glass-glider {
            transform: translateX(0%);
            background: linear-gradient(135deg, #c0c0c055, #e0e0e0);
            box-shadow: 0 0 18px rgba(192, 192, 192, 0.5), 0 0 10px rgba(255, 255, 255, 0.4) inset;
        }
        #glass-reviews:checked ~ .glass-glider {
            transform: translateX(100%);
            background: linear-gradient(135deg, #e7d4c055, #e7d4c0);
            box-shadow: 0 0 18px rgba(231, 212, 192, 0.5), 0 0 10px rgba(255, 255, 255, 0.4) inset;
        }
        .section-content { display: none; width: 100%; max-width: 600px; flex-direction: column; align-items: center; }
        .section-content.active { display: flex; }
        
        /* Блоки формы и ограничения теперь с песочным фоном в стиле печеньки */
        .form-container, .cooldown-box {
            background-color: #fdf8f2; 
            border: 1px solid #e7d4c0; 
            padding: 25px; 
            border-radius: 16px;
            width: 100%; 
            margin-bottom: 20px; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); 
            box-sizing: border-box; 
            text-align: center;
            color: #4a3525;
        }
        .cooldown-box h3 { color: #d97706; margin-top: 0; margin-bottom: 10px; }
        .cooldown-box p { color: #6b5141; margin: 0; }
        
        input, textarea {
            width: 100%; padding: 12px; margin-top: 8px; margin-bottom: 15px;
            background-color: #ffffff; border: 1px solid #d4b59d; border-radius: 8px; color: #4a3525; box-sizing: border-box; text-align: left;
        }
        input::placeholder, textarea::placeholder { color: #a48c77; }
        
        button[type="submit"] {
            background-color: #bc6c25; color: white; padding: 12px 20px; border: none; border-radius: 8px;
            cursor: pointer; font-weight: bold; width: 100%; transition: background 0.2s;
        }
        button[type="submit"]:hover { background-color: #9a541c; }
    </style>
</head>
<body>
    <div class="review-counter">💬 Отзывов: <span id="review-count-num">{{ reviews|length }}</span></div>
    <h1>⭐ Отзывы наших клиентов</h1>
    <p class="desc">Поделитесь своим мнением о магазине или почитайте другие отзывы.</p>

    <div class="glass-radio-group">
        <input type="radio" name="glass-nav" id="glass-write" checked onchange="switchTab('write')">
        <label for="glass-write">Write</label>
        <input type="radio" name="glass-nav" id="glass-reviews" onchange="switchTab('reviews')">
        <label for="glass-reviews">Reviews</label>
        <div class="glass-glider"></div>
    </div>

    <!-- Секция 1: Написать отзыв -->
    <div id="tab-write" class="section-content active">
        {% if has_cooldown %}
            <div class="cooldown-box">
                <h3>⏳ Ограничение 24 часа</h3>
                <p>Вы уже оставили отзыв. Следующий отзыв можно будет написать через 24 часа.</p>
            </div>
        {% else %}
            <div class="form-container" style="text-align: left;">
                {% if error %}
                    <div style="background-color: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; color: #b91c1c; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">
                        {{ error }}
                    </div>
                {% endif %}
                <form action="/add-review" method="POST">
                    <label for="username" style="color: #4a3525; font-weight: 600;">Ваше имя / Discord:</label>
                    <input type="text" id="username" name="username" placeholder="@username" required>
                    <label for="text" style="color: #4a3525; font-weight: 600;">Ваш отзыв:</label>
                    <textarea id="text" name="text" rows="4" placeholder="Напишите пару слов о магазине..." required></textarea>
                    <button type="submit">Отправить отзыв</button>
                </form>
            </div>
        {% endif %}
    </div>

    <!-- Секция 2: Список отзывов (карточки с цветом печеньки) -->
    <div id="tab-reviews" class="section-content" style="gap: 40px; margin-top: 40px;">
        {% for review in reviews %}
        <div class="[--shadow:rgba(60,64,67,0.3)_0_1px_2px_0,rgba(60,64,67,0.15)_0_2px_6px_2px] w-4/5 h-auto rounded-2xl bg-[#fdf8f2] border border-[#e7d4c0] [box-shadow:var(--shadow)] max-w-[300px] text-[#4a3525]">
            <div class="flex flex-col items-center justify-between pt-9 px-6 pb-6 relative">
                <!-- Иконка печеньки сверху -->
                <span class="relative mx-auto -mt-16 mb-6">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" height="46" width="65">
                        <path stroke="#000" fill="#EAB789" d="M49.157 15.69L44.58.655l-12.422 1.96L21.044.654l-8.499 2.615-6.538 5.23-4.576 9.153v11.114l4.576 8.5 7.846 5.23 10.46 1.96 7.845-2.614 9.153 2.615 11.768-2.615 7.846-7.846 1.96-5.884.655-7.191-7.846-1.308-6.537-3.922z"></path>
                        <path fill="#9C6750" d="M32.286 3.749c-6.94 3.65-11.69 11.053-11.69 19.591 0 8.137 4.313 15.242 10.724 19.052a20.513 20.513 0 01-8.723 1.937c-11.598 0-21-9.626-21-21.5 0-11.875 9.402-21.5 21-21.5 3.495 0 6.79.874 9.689 2.42z" clip-rule="evenodd" fill-rule="evenodd"></path>
                        <path fill="#634647" d="M64.472 20.305a.954.954 0 00-1.172-.824 4.508 4.508 0 01-3.958-.934.953.953 0 00-1.076-.11c-.46.252-.977.383-1.502.382a3.154 3.154 0 01-2.97-2.11.954.954 0 00-.833-.634 4.54 4.54 0 01-4.205-4.507c.002-.23.022-.46.06-.687a.952.952 0 00-.213-.767 3.497 3.497 0 01-.614-3.5.953.953 0 00-.382-1.138 3.522 3.522 0 01-1.5-3.992.951.951 0 00-.762-1.227A22.611 22.611 0 0032.3 2.16 22.41 22.41 0 0022.657.001a22.654 22.654 0 109.648 43.15 22.644 22.644 0 0032.167-22.847zM22.657 43.4a20.746 20.746 0 110-41.493c2.566-.004 5.11.473 7.501 1.407a22.64 22.64 0 00.003 38.682 20.6 20.6 0 01-7.504 1.404zm19.286 0a20.746 20.746 0 112.131-41.384 5.417 5.417 0 001.918 4.635 5.346 5.346 0 00-.133 1.182A5.441 5.441 0 0046.879 11a5.804 5.804 0 00-.028.568 6.456 6.456 0 005.38 6.345 5.053 5.053 0 006.378 2.472 6.412 6.412 0 004.05 1.12 20.768 20.768 0 01-20.716 21.897z"></path>
                        <path fill="#644647" d="M54.962 34.3a17.719 17.719 0 01-2.602 2.378.954.954 0 001.14 1.53 19.637 19.637 0 002.884-2.634.955.955 0 00-1.422-1.274z"></path>
                        <path stroke-width="1.8" stroke="#644647" fill="#845556" d="M44.5 32.829c-.512 0-1.574.215-2 .5-.426.284-.342.263-.537.736a2.59 2.59 0 104.98.99c0-.686-.458-1.241-.943-1.726-.485-.486-.814-.5-1.5-.5zm-30.916-2.5c-.296 0-.912.134-1.159.311-.246.177-.197.164-.31.459a1.725 1.725 0 00-.086.932c.058.312.2.6.41.825.21.226.477.38.768.442.291.062.593.03.867-.092s.508-.329.673-.594a1.7 1.7 0 00.253-.896c0-.428-.266-.774-.547-1.076-.281-.302-.471-.31-.869-.311zm17.805-11.375c-.143-.492-.647-1.451-1.04-1.78-.392-.33-.348-.255-.857-.31a2.588 2.588 0 10.441 5.06c.66-.194 1.064-.788 1.395-1.39.33-.601.252-.92.06-1.58zm-22 2c-.143-.492-.647-1.451-1.04-1.78-.391-.33-.347-.255-.856-.31a2.589 2.589 0 10.44 5.06c.66-.194 1.064-.788 1.395-1.39.33-.601.252-.92.06-1.58Z"></path>
                    </svg>
                </span>

                <!-- Ник пользователя -->
                <h5 class="text-sm font-bold mb-2 text-left mr-auto text-[#5c4033]">
                    {{ review.username }}
                </h5>

                <!-- Текст отзыва -->
                <p class="w-full mb-4 text-sm text-justify text-[#6b5141]">
                    {{ review.text }}
                </p>

                <!-- Время отзыва -->
                <span class="text-xs text-[#a48c77] mr-auto mt-2">
                    {{ review.time }}
                </span>
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        function switchTab(tabName) {
            document.getElementById('tab-write').classList.remove('active');
            document.getElementById('tab-reviews').classList.remove('active');
            if (tabName === 'write') {
                document.getElementById('tab-write').classList.add('active');
            } else {
                document.getElementById('tab-reviews').classList.add('active');
            }
        }
        {% if error %}
            document.getElementById('glass-write').checked = true;
            switchTab('write');
        {% endif %}
    </script>
</body>
</html>
"""

@app.route('/reviews')
def reviews_page():
    has_cooldown = request.cookies.get('review_sent') is not None
    return render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, has_cooldown=has_cooldown)

@app.route('/add-review', methods=['POST'])
def add_review():
    if request.cookies.get('review_sent'):
        return render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, has_cooldown=True, error="⏳ Действует ограничение 24 часа!")

    username = request.form.get('username')
    text = request.form.get('text')
    
    if not username or not text:
        return render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, has_cooldown=False, error="Заполните все поля!")
    
    if len(text) < 3 or len(text) > 500:
        return render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, has_cooldown=False, error="Ошибка: Отзыв должен быть от 3 до 500 символов.")

    now = datetime.now()
    new_review = {
        "username": username,
        "text": text,
        "time": now.strftime("%Y-%m-%d %H:%M:%S")
    }
    REVIEWS_LIST.insert(0, new_review)
    save_reviews(REVIEWS_LIST)
    
    response = make_response(render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, has_cooldown=True))
    response.set_cookie('review_sent', 'true', max_age=86400)
    return response

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
    view.add_item(Button(label="Смотреть отзывы на сайте", style=discord.ButtonStyle.link, url="https://discord-bot-new-production.up.railway.app/reviews"))
    
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask).start()
bot.run(os.environ.get("DISCORD_TOKEN"))
