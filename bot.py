import os
import asyncio
import json
import random
import string
from datetime import datetime
import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from flask import Flask, render_template_string, request, make_response
from threading import Thread

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')

REVIEWS_FILE = 'reviews.json'
CODES_FILE = 'codes.json'

def load_reviews():
    if os.path.exists(REVIEWS_FILE):
        try:
            with open(REVIEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return [
        {"username": "@daler", "rating": 5, "text": "Отличный магазин! Брал товар, всё пришло моментально, рекомендую!", "time": "2026-08-14 12:00:00"},
        {"username": "@user123", "rating": 4, "text": "Быстрая поддержка и честные цены. Буду брать еще.", "time": "2026-08-14 12:00:00"}
    ]

def save_reviews(reviews):
    with open(REVIEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=4)

def load_codes():
    if os.path.exists(CODES_FILE):
        try:
            with open(CODES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_codes(codes):
    with open(CODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(codes, f, ensure_ascii=False, indent=4)

REVIEWS_LIST = load_reviews()
PURCHASE_CODES = load_codes()

REVIEWS_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Отзывы — Art Shop</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #fdf8f2;
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
            background-color: #bc6c25;
            border: 1px solid #a45c1f;
            padding: 8px 16px;
            border-radius: 12px;
            font-weight: bold;
            color: #ffffff;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            font-size: 14px;
        }
        h1 { color: #4a3525; margin-bottom: 10px; margin-top: 20px; }
        p.desc { color: #6b5141; margin-bottom: 25px; text-align: center; }
        
        .rating-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 15px;
        }
        .rating {
            display: flex;
            flex-direction: row;
            gap: 0.3rem;
            --stroke: #666;
            --fill: #ffc73a;
        }
        .rating input {
            appearance: unset;
            display: none;
        }
        .rating label {
            cursor: pointer;
        }
        .rating svg {
            width: 2rem;
            height: 2rem;
            overflow: visible;
            fill: transparent;
            stroke: var(--stroke);
            stroke-linejoin: bevel;
            stroke-dasharray: 12;
            animation: idle 4s linear infinite;
            transition: stroke 0.2s, fill 0.5s;
        }
        @keyframes idle {
            from { stroke-dashoffset: 24; }
        }
        .rating label:hover svg,
        .rating label:hover ~ label svg,
        .rating input:checked ~ label svg {
            fill: var(--fill);
            stroke: var(--fill);
        }
        /* Подсветка звезд при выборе слева направо */
        .rating input:checked + label svg,
        .rating input:checked ~ label svg {
            fill: var(--fill);
            stroke: var(--fill);
        }
        /* Исправление порядка заполнения для стандартного выбора */
        .rating {
            display: flex;
            flex-direction: row-reverse;
        }
        .rating input:checked ~ label svg {
            transition: 0s;
            animation: yippee 0.75s backwards;
            fill: var(--fill);
            stroke: var(--fill);
            stroke-opacity: 0;
            stroke-dasharray: 0;
            stroke-linejoin: miter;
            stroke-width: 8px;
        }
        @keyframes yippee {
            0% { transform: scale(1); fill: var(--fill); fill-opacity: 0; stroke-opacity: 1; stroke: var(--stroke); stroke-dasharray: 10; stroke-width: 1px; stroke-linejoin: bevel; }
            30% { transform: scale(0); fill: var(--fill); fill-opacity: 0; stroke-opacity: 1; stroke: var(--stroke); stroke-dasharray: 10; stroke-width: 1px; stroke-linejoin: bevel; }
            30.1% { stroke: var(--fill); stroke-dasharray: 0; stroke-linejoin: miter; stroke-width: 8px; }
            60% { transform: scale(1.2); fill: var(--fill); }
        }

        .glass-radio-group {
            --bg: rgba(188, 108, 37, 0.15);
            --text: #4a3525;
            display: flex;
            position: relative;
            background: var(--bg);
            border-radius: 1rem;
            border: 1px solid #e7d4c0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            width: fit-content;
            margin-bottom: 20px;
        }
        .glass-radio-group input { display: none; }
        .glass-radio-group label {
            flex: 1; display: flex; align-items: center; justify-content: center; min-width: 100px;
            font-size: 14px; padding: 0.8rem 1.6rem; cursor: pointer; font-weight: 600; letter-spacing: 0.3px;
            color: var(--text); position: relative; z-index: 2; transition: color 0.3s ease-in-out;
        }
        .glass-glider {
            position: absolute; top: 0; bottom: 0; width: calc(100% / 2); border-radius: 1rem; z-index: 1;
            transition: transform 0.5s cubic-bezier(0.37, 1.95, 0.66, 0.56), background 0.4s ease-in-out;
        }
        #glass-write:checked ~ .glass-glider { transform: translateX(0%); background: #e7d4c0; }
        #glass-reviews:checked ~ .glass-glider { transform: translateX(100%); background: #e7d4c0; }
        .section-content { display: none; width: 100%; max-width: 600px; flex-direction: column; align-items: center; }
        .section-content.active { display: flex; }
        
        .form-container {
            background-color: #ffffff; 
            border: 1px solid #e7d4c0; 
            padding: 35px 25px 25px 25px; 
            border-radius: 16px;
            width: 100%; 
            margin-bottom: 20px; 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); 
            box-sizing: border-box; 
            text-align: left;
            color: #4a3525;
            position: relative;
            margin-top: 35px;
        }
        
        input, textarea {
            width: 100%; padding: 12px; margin-top: 8px; margin-bottom: 15px;
            background-color: #fdf8f2; border: 1px solid #d4b59d; border-radius: 8px; color: #4a3525; box-sizing: border-box; text-align: left;
        }
        input::placeholder, textarea::placeholder { color: #a48c77; }
        
        button[type="submit"] {
            background-color: #bc6c25; color: white; padding: 12px 20px; border: none; border-radius: 8px;
            cursor: pointer; font-weight: bold; width: 100%; transition: background 0.2s;
        }
        button[type="submit"]:hover { background-color: #9a541c; }

        .cookie-icon-top {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
        }

        .stats-banner {
            background: #ffffff;
            border: 1px solid #e7d4c0;
            padding: 15px 25px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.03);
            color: #4a3525;
        }
        .stats-emoji { font-size: 3rem; }
        .stats-info h3 { margin: 0; font-size: 18px; font-weight: bold; }
        .stats-info p { margin: 3px 0 0 0; font-size: 14px; color: #7c5c43; }

        .loader-container {
            display: flex; justify-content: center; align-items: center; height: 120px; position: relative; width: 100%;
        }
        .loader {
            --fill-color: #bc6c25; --shine-color: #bc6c2533; transform: scale(0.6); width: 100px; height: auto; position: relative; filter: drop-shadow(0 0 10px var(--shine-color));
        }
        .loader #pegtopone { position: absolute; animation: flowe-one 1s linear infinite; }
        .loader #pegtoptwo { position: absolute; opacity: 0; transform: scale(0) translateY(-200px) translateX(-100px); animation: flowe-two 1s linear infinite; animation-delay: 0.3s; }
        .loader #pegtopthree { position: absolute; opacity: 0; transform: scale(0) translateY(-200px) translateX(100px); animation: flowe-three 1s linear infinite; animation-delay: 0.6s; }
        @keyframes flowe-one { 0% { transform: scale(0.5) translateY(-200px); opacity: 0; } 25% { transform: scale(0.75) translateY(-100px); opacity: 1; } 50% { transform: scale(1) translateY(0px); opacity: 1; } 75% { transform: scale(0.5) translateY(50px); opacity: 1; } 100% { transform: scale(0) translateY(100px); opacity: 0; } }
        @keyframes flowe-two { 0% { transform: scale(0.5) rotateZ(-10deg) translateY(-200px) translateX(-100px); opacity: 0; } 25% { transform: scale(1) rotateZ(-5deg) translateY(-100px) translateX(-50px); opacity: 1; } 50% { transform: scale(1) rotateZ(0deg) translateY(0px) translateX(-25px); opacity: 1; } 75% { transform: scale(0.5) rotateZ(5deg) translateY(50px) translateX(0px); opacity: 1; } 100% { transform: scale(0) rotateZ(10deg) translateY(100px) translateX(25px); opacity: 0; } }
        @keyframes flowe-three { 0% { transform: scale(0.5) rotateZ(10deg) translateY(-200px) translateX(100px); opacity: 0; } 25% { transform: scale(1) rotateZ(5deg) translateY(-100px) translateX(50px); opacity: 1; } 50% { transform: scale(1) rotateZ(0deg) translateY(0px) translateX(25px); opacity: 1; } 75% { transform: scale(0.5) rotateZ(-5deg) translateY(50px) translateX(0px); opacity: 1; } 100% { transform: scale(0.5) rotateZ(-10deg) translateY(100px) translateX(-25px); opacity: 0; } }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="review-counter">💬 Отзывов: <span id="review-count-num">{{ reviews|length }}</span></div>
    <h1>⭐ Отзывы наших клиентов</h1>
    <p class="desc">Только реальные покупатели могут оставить отзыв, используя код подтверждения.</p>

    <div class="glass-radio-group">
        <input type="radio" name="glass-nav" id="glass-write" checked onchange="switchTab('write')">
        <label for="glass-write">Write</label>
        <input type="radio" name="glass-nav" id="glass-reviews" onchange="switchTab('reviews')">
        <label for="glass-reviews">Reviews</label>
        <div class="glass-glider"></div>
    </div>

    <!-- Секция 1: Написать отзыв -->
    <div id="tab-write" class="section-content active">
        <div class="form-container" id="form-card">
            <span class="cookie-icon-top">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" height="46" width="65">
                    <path stroke="#000" fill="#EAB789" d="M49.157 15.69L44.58.655l-12.422 1.96L21.044.654l-8.499 2.615-6.538 5.23-4.576 9.153v11.114l4.576 8.5 7.846 5.23 10.46 1.96 7.845-2.614 9.153 2.615 11.768-2.615 7.846-7.846 1.96-5.884.655-7.191-7.846-1.308-6.537-3.922z"></path>
                    <path fill="#9C6750" d="M32.286 3.749c-6.94 3.65-11.69 11.053-11.69 19.591 0 8.137 4.313 15.242 10.724 19.052a20.513 20.513 0 01-8.723 1.937c-11.598 0-21-9.626-21-21.5 0-11.875 9.402-21.5 21-21.5 3.495 0 6.79.874 9.689 2.42z" clip-rule="evenodd" fill-rule="evenodd"></path>
                    <path fill="#634647" d="M64.472 20.305a.954.954 0 00-1.172-.824 4.508 4.508 0 01-3.958-.934.953.953 0 00-1.076-.11c-.46.252-.977.383-1.502.382a3.154 3.154 0 01-2.97-2.11.954.954 0 00-.833-.634 4.54 4.54 0 01-4.205-4.507c.002-.23.022-.46.06-.687a.952.952 0 00-.213-.767 3.497 3.497 0 01-.614-3.5.953.953 0 00-.382-1.138 3.522 3.522 0 01-1.5-3.992.951.951 0 00-.762-1.227A22.611 22.611 0 0032.3 2.16 22.41 22.41 0 0022.657.001a22.654 22.654 0 109.648 43.15 22.644 22.644 0 0032.167-22.847zM22.657 43.4a20.746 20.746 0 110-41.493c2.566-.004 5.11.473 7.501 1.407a22.64 22.64 0 00.003 38.682 20.6 20.6 0 01-7.504 1.404zm19.286 0a20.746 20.746 0 112.131-41.384 5.417 5.417 0 001.918 4.635 5.346 5.346 0 00-.133 1.182A5.441 5.441 0 0046.879 11a5.804 5.804 0 00-.028.568 6.456 6.456 0 005.38 6.345 5.053 5.053 0 006.378 2.472 6.412 6.412 0 004.05 1.12 20.768 20.768 0 01-20.716 21.897z"></path>
                    <path fill="#644647" d="M54.962 34.3a17.719 17.719 0 01-2.602 2.378.954.954 0 001.14 1.53 19.637 19.637 0 002.884-2.634.955.955 0 00-1.422-1.274z"></path>
                    <path stroke-width="1.8" stroke="#644647" fill="#845556" d="M44.5 32.829c-.512 0-1.574.215-2 .5-.426.284-.342.263-.537.736a2.59 2.59 0 104.98.99c0-.686-.458-1.241-.943-1.726-.485-.486-.814-.5-1.5-.5zm-30.916-2.5c-.296 0-.912.134-1.159.311-.246.177-.197.164-.31.459a1.725 1.725 0 00-.086.932c.058.312.2.6.41.825.21.226.477.38.768.442.291.062.593.03.867-.092s.508-.329.673-.594a1.7 1.7 0 00.253-.896c0-.428-.266-.774-.547-1.076-.281-.302-.471-.31-.869-.311zm17.805-11.375c-.143-.492-.647-1.451-1.04-1.78-.392-.33-.348-.255-.857-.31a2.588 2.588 0 10.441 5.06c.66-.194 1.064-.788 1.395-1.39.33-.601.252-.92.06-1.58zm-22 2c-.143-.492-.647-1.451-1.04-1.78-.391-.33-.347-.255-.856-.31a2.589 2.589 0 10.44 5.06c.66-.194 1.064-.788 1.395-1.39.33-.601.252-.92.06-1.58Z"></path>
                </svg>
            </span>
            
            {% if error %}
                <div style="background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; color: #b91c1c; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">
                    {{ error }}
                </div>
            {% endif %}
            
            <form id="review-form" action="/add-review" method="POST" onsubmit="handleLoadingSubmit(event)">
                <label for="username" style="font-weight: 600;">Ваше имя / Discord:</label>
                <input type="text" id="username" name="username" placeholder="@username" required>
                
                <label for="code" style="font-weight: 600;">Код подтверждения покупки:</label>
                <input type="text" id="code" name="code" placeholder="Например: REV-XXXX" required>

                <label style="font-weight: 600; display: block; text-align: center; margin-bottom: 5px;">Ваша оценка:</label>
                <div class="rating-container">
                    <div class="rating">
                        <input type="radio" id="star-1" name="rating" value="1" />
                        <label for="star-1"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg></label>
                        <input type="radio" id="star-2" name="rating" value="2" />
                        <label for="star-2"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg></label>
                        <input type="radio" id="star-3" name="rating" value="3" />
                        <label for="star-3"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg></label>
                        <input type="radio" id="star-4" name="rating" value="4" />
                        <label for="star-4"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg></label>
                        <input type="radio" id="star-5" name="rating" value="5" checked />
                        <label for="star-5"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg></label>
                    </div>
                </div>

                <label for="text" style="font-weight: 600;">Ваш отзыв:</label>
                <textarea id="text" name="text" rows="4" placeholder="Напишите пару слов о магазине..." required></textarea>
                <button type="submit">Отправить отзыв</button>
            </form>

            <div id="cookie-loader-box" class="hidden loader-container">
                <div class="loader">
                    <div id="pegtopone"><svg xmlns="http://www.w3.org/2000/svg" fill="none" height="46" width="65"><path fill="#bc6c25" d="M49.157 15.69L44.58.655l-12.422 1.96L21.044.654l-8.499 2.615-6.538 5.23-4.576 9.153v11.114l4.576 8.5 7.846 5.23 10.46 1.96 7.845-2.614 9.153 2.615 11.768-2.615 7.846-7.846 1.96-5.884.655-7.191-7.846-1.308-6.537-3.922z"></path></svg></div>
                    <div id="pegtoptwo"><svg xmlns="http://www.w3.org/2000/svg" fill="none" height="46" width="65"><path fill="#bc6c25" d="M49.157 15.69L44.58.655l-12.422 1.96L21.044.654l-8.499 2.615-6.538 5.23-4.576 9.153v11.114l4.576 8.5 7.846 5.23 10.46 1.96 7.845-2.614 9.153 2.615 11.768-2.615 7.846-7.846 1.96-5.884.655-7.191-7.846-1.308-6.537-3.922z"></path></svg></div>
                    <div id="pegtopthree"><svg xmlns="http://www.w3.org/2000/svg" fill="none" height="46" width="65"><path fill="#bc6c25" d="M49.157 15.69L44.58.655l-12.422 1.96L21.044.654l-8.499 2.615-6.538 5.23-4.576 9.153v11.114l4.576 8.5 7.846 5.23 10.46 1.96 7.845-2.614 9.153 2.615 11.768-2.615 7.846-7.846 1.96-5.884.655-7.191-7.846-1.308-6.537-3.922z"></path></svg></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Секция 2: Список отзывов -->
    <div id="tab-reviews" class="section-content" style="gap: 25px; margin-top: 20px;">
        
        <!-- Динамический стикер-баннер общей оценки -->
        {% set total_reviews = reviews|length %}
        {% set ns = namespace(total_score=0) %}
        {% for r in reviews %}
            {% set ns.total_score = ns.total_score + (r.rating | int) %}
        {% endfor %}
        {% set avg = (ns.total_score / total_reviews) if total_reviews > 0 else 5 %}

        <div class="stats-banner w-4/5 max-w-[300px]">
            <div class="stats-emoji">
                {% if avg < 3 %}
                    😢
                {% elif avg < 4.0 %}
                    😐
                {% else %}
                    😁
                {% endif %}
            </div>
            <div class="stats-info">
                <h3>Рейтинг: {{ "%.1f" | format(avg) }} / 5.0</h3>
                <p>
                    {% if avg < 3 %} Нам есть над чем работать
                    {% elif avg < 4.0 %} Нормально, но можем лучше
                    {% else %} Отличные отзывы! Спасибо ❤️
                    {% endif %}
                </p>
            </div>
        </div>

        {% for review in reviews %}
        <div class="[--shadow:rgba(60,64,67,0.1)_0_1px_2px_0,rgba(60,64,67,0.05)_0_2px_6px_2px] w-4/5 h-auto rounded-2xl bg-[#ffffff] border border-[#e7d4c0] [box-shadow:var(--shadow)] max-w-[300px] text-[#4a3525]">
            <div class="flex flex-col items-center justify-between pt-9 px-6 pb-6 relative">
                <span class="relative mx-auto -mt-16 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" height="46" width="65">
                        <path stroke="#000" fill="#EAB789" d="M49.157 15.69L44.58.655l-12.422 1.96L21.044.654l-8.499 2.615-6.538 5.23-4.576 9.153v11.114l4.576 8.5 7.846 5.23 10.46 1.96 7.845-2.614 9.153 2.615 11.768-2.615 7.846-7.846 1.96-5.884.655-7.191-7.846-1.308-6.537-3.922z"></path>
                        <path fill="#9C6750" d="M32.286 3.749c-6.94 3.65-11.69 11.053-11.69 19.591 0 8.137 4.313 15.242 10.724 19.052a20.513 20.513 0 01-8.723 1.937c-11.598 0-21-9.626-21-21.5 0-11.875 9.402-21.5 21-21.5 3.495 0 6.79.874 9.689 2.42z" clip-rule="evenodd" fill-rule="evenodd"></path>
                        <path fill="#634647" d="M64.472 20.305a.954.954 0 00-1.172-.824 4.508 4.508 0 01-3.958-.934.953.953 0 00-1.076-.11c-.46.252-.977.383-1.502.382a3.154 3.154 0 01-2.97-2.11.954.954 0 00-.833-.634 4.54 4.54 0 01-4.205-4.507c.002-.23.022-.46.06-.687a.952.952 0 00-.213-.767 3.497 3.497 0 01-.614-3.5.953.953 0 00-.382-1.138 3.522 3.522 0 01-1.5-3.992.951.951 0 00-.762-1.227A22.611 22.611 0 0032.3 2.16 22.41 22.41 0 0022.657.001a22.654 22.654 0 109.648 43.15 22.644 22.644 0 0032.167-22.847zM22.657 43.4a20.746 20.746 0 110-41.493c2.566-.004 5.11.473 7.501 1.407a22.64 22.64 0 00.003 38.682 20.6 20.6 0 01-7.504 1.404zm19.286 0a20.746 20.746 0 112.131-41.384 5.417 5.417 0 001.918 4.635 5.346 5.346 0 00-.133 1.182A5.441 5.441 0 0046.879 11a5.804 5.804 0 00-.028.568 6.456 6.456 0 005.38 6.345 5.053 5.053 0 006.378 2.472 6.412 6.412 0 004.05 1.12 20.768 20.768 0 01-20.716 21.897z"></path>
                        <path fill="#644647" d="M54.962 34.3a17.719 17.719 0 01-2.602 2.378.954.954 0 001.14 1.53 19.637 19.637 0 002.884-2.634.955.955 0 00-1.422-1.274z"></path>
                        <path stroke-width="1.8" stroke="#644647" fill="#845556" d="M44.5 32.829c-.512 0-1.574.215-2 .5-.426.284-.342.263-.537.736a2.59 2.59 0 104.98.99c0-.686-.458-1.241-.943-1.726-.485-.486-.814-.5-1.5-.5zm-30.916-2.5c-.296 0-.912.134-1.159.311-.246.177-.197.164-.31.459a1.725 1.725 0 00-.086.932c.058.312.2.6.41.825.21.226.477.38.768.442.291.062.593.03.867-.092s.508-.329.673-.594a1.7 1.7 0 00.253-.896c0-.428-.266-.774-.547-1.076-.281-.302-.471-.31-.869-.311zm17.805-11.375c-.143-.492-.647-1.451-1.04-1.78-.392-.33-.348-.255-.857-.31a2.588 2.588 0 10.441 5.06c.66-.194 1.064-.788 1.395-1.39.33-.601.252-.92.06-1.58zm-22 2c-.143-.492-.647-1.451-1.04-1.78-.391-.33-.347-.255-.856-.31a2.589 2.589 0 10.44 5.06c.66-.194 1.064-.788 1.395-1.39.33-.601.252-.92.06-1.58Z"></path>
                    </svg>
                </span>
                
                <div style="display: flex; gap: 3px; margin-bottom: 8px;">
                    {% for i in range(1, 6) %}
                        {% if i <= review.rating|int %}
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="#ffc73a"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>
                        {% else %}
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="transparent" stroke="#ccc"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>
                        {% endif %}
                    {% endfor %}
                </div>

                <h5 class="text-sm font-bold mb-2 text-left mr-auto text-[#5c4033]">
                    {{ review.username }}
                </h5>
                <p class="w-full mb-4 text-sm text-justify text-[#6b5141]">
                    {{ review.text }}
                </p>
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
        
        function handleLoadingSubmit(event) {
            event.preventDefault();
            const form = event.target;
            form.classList.add('hidden');
            document.getElementById('cookie-loader-box').classList.remove('hidden');
            setTimeout(() => {
                form.submit();
            }, 1000);
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
    resp = make_response(render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/add-review', methods=['POST'])
def add_review():
    username = request.form.get('username')
    code = request.form.get('code', '').strip()
    rating = request.form.get('rating', '5')
    text = request.form.get('text')
    
    if not username or not code or not text:
        resp = make_response(render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, error="Заполните все поля!"))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp
    
    global PURCHASE_CODES
    PURCHASE_CODES = load_codes()
    
    if code not in PURCHASE_CODES:
        resp = make_response(render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, error="Ошибка: Неверный код подтверждения!"))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp
        
    if PURCHASE_CODES[code]:
        resp = make_response(render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, error="Ошибка: Этот код уже был использован!"))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp

    if len(text) < 3 or len(text) > 500:
        resp = make_response(render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST, error="Ошибка: Отзыв должен быть от 3 до 500 символов."))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp

    PURCHASE_CODES[code] = True
    save_codes(PURCHASE_CODES)

    now = datetime.now()
    new_review = {
        "username": username,
        "rating": int(rating),
        "text": text,
        "time": now.strftime("%Y-%m-%d %H:%M:%S")
    }
    REVIEWS_LIST.insert(0, new_review)
    save_reviews(REVIEWS_LIST)
    
    response = make_response(render_template_string(REVIEWS_TEMPLATE, reviews=REVIEWS_LIST))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/api/order', methods=['POST'])
def api_order():
    try:
        data = request.json
        bot.loop.create_task(send_receipt(data))
        return jsonify({"status": "success"})
    except Exception as e:
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

@bot.command(name="gen_code")
@commands.has_permissions(administrator=True)
async def gen_code_command(ctx, member: discord.Member):
    code = "REV-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    codes = load_codes()
    codes[code] = False
    save_codes(codes)
    
    try:
        await member.send(f"🎉 Спасибо за покупку в **Art Shop**!\nВаш одноразовый код для написания отзыва на сайте: `{code}`\nПерейдите на страницу отзывов и введите его в специальное поле.")
        await ctx.send(f"✅ Код `{code}` успешно сгенерирован и отправлен в ЛС пользователю {member.mention}!")
    except discord.Forbidden:
        await ctx.send(f"⚠️ Не удалось отправить ЛС пользователю {member.mention}. Вот его код: `{code}`")

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask).start()
bot.run(os.environ.get("DISCORD_TOKEN"))
