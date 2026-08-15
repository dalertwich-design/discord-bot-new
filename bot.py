import os
import asyncio
import json
import random
import string
from datetime import datetime
import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from flask import Flask, render_template_string, request, make_response, jsonify
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
                reviews = json.load(f)
                for idx, rev in enumerate(reviews):
                    if 'likes' not in rev:
                        rev['likes'] = 0
                    if 'id' not in rev:
                        rev['id'] = idx
                return reviews
        except:
            pass
    return [
        {"id": 0, "username": "@daler", "rating": 5, "text": "Отличный магазин! Брал товар, всё пришло моментально, рекомендую!", "time": "2026-08-14 12:00:00", "likes": 12},
        {"id": 1, "username": "@user123", "rating": 4, "text": "Быстрая поддержка и честные цены. Буду брать еще.", "time": "2026-08-14 12:00:00", "likes": 5}
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

SITE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Art Shop — Отзывы</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #fdf8f2;
            color: #4a3525;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            min-height: 100vh;
        }
        h1 { color: #4a3525; margin-bottom: 10px; margin-top: 20px; }
        p.desc { color: #6b5141; margin-bottom: 25px; text-align: center; }
        
        /* Счетчик отзывов в правом верхнем углу */
        .reviews-counter-badge {
            position: absolute;
            top: 20px;
            right: 25px;
            background: #ffffff;
            border: 1px solid #e7d4c0;
            padding: 8px 16px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            color: #4a3525;
            box-shadow: 0 2px 5px rgba(0,0,0,0.03);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .rating-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 15px;
        }
        .rating {
            display: flex;
            flex-direction: row-reverse;
            justify-content: center;
            gap: 5px;
            margin: 10px 0 20px 0;
        }
        .rating input { display: none; }
        .rating label { cursor: pointer; color: #d1d5db; transition: color 0.2s; }
        .rating input:checked ~ label,
        .rating label:hover,
        .rating label:hover ~ label { color: #f59e0b; }
        .rating svg { width: 32px; height: 32px; fill: currentColor; }

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
            flex: 1; display: flex; align-items: center; justify-content: center; min-width: 140px;
            font-size: 14px; padding: 0.8rem 1.2rem; cursor: pointer; font-weight: 600; letter-spacing: 0.3px;
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
            margin-top: 15px;
        }
        
        input, textarea {
            width: 100%; padding: 12px; margin-top: 8px; margin-bottom: 15px;
            background-color: #fdf8f2; border: 1px solid #d4b59d; border-radius: 8px; color: #4a3525; box-sizing: border-box; text-align: left;
        }
        input::placeholder, textarea::placeholder { color: #a48c77; }
        
        button[type="submit"] {
            background-color: #bc6c25; color: white; padding: 12px 20px; border: none; border-radius: 8px;
            cursor: pointer; font-weight: bold; width: 100%; transition: background 0.2s;
            position: relative; min-height: 45px; display: flex; align-items: center; justify-content: center;
        }
        button[type="submit"]:hover { background-color: #9a541c; }

        /* Анимация загрузки (печеньки) */
        .loader {
            user-select: none;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 24px;
        }

        .cookie-icon {
            opacity: 0;
            fill: #fdf8f2;
            animation: loader 2s infinite alternate;
            width: 24px;
            height: 24px;
        }

        .cookie2 {
            width: 20px;
            height: 20px;
            margin-left: -8px;
            animation-delay: 0.25s;
        }

        .cookie3 {
            width: 16px;
            height: 16px;
            margin-left: -12px;
            animation-delay: 0.5s;
        }

        @keyframes loader {
            0% {
                opacity: 0;
                transform: translateY(0) translateX(30px) rotate(0deg);
            }
            10% {
                opacity: 0;
                transform: translateY(0) translateX(30px) rotate(0deg);
            }
            100% {
                opacity: 1;
                transform: translateY(-10px) translateX(0) rotate(360deg);
            }
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

        .Btn {
            width: 120px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            border: none;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.06);
            cursor: pointer;
            background-color: transparent;
            transition: transform 0.1s;
        }
        .Btn:active { transform: scale(0.96); }
        .leftContainer {
            width: 55%;
            height: 100%;
            background-color: #ccc;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: background-color 0.2s;
        }
        .leftContainer .like { color: white; font-weight: 600; font-size: 13px; }
        .likeCount {
            width: 45%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-weight: 600;
            font-size: 13px;
            position: relative;
            background-color: white;
            transition: color 0.2s;
        }
        .likeCount::before {
            height: 8px; width: 8px; position: absolute; content: "";
            background-color: rgb(255, 255, 255); transform: rotate(45deg); left: -4px;
        }

        .Btn.liked .leftContainer { background-color: rgb(238, 0, 0); }
        .Btn.liked .likeCount { color: rgb(238, 0, 0); }
        .Btn:not(.liked):hover .leftContainer { background-color: rgb(219, 0, 0); }
        .Btn:not(.liked):hover .likeCount { color: rgb(219, 0, 0); }

        .hidden { display: none !important; }
    </style>
</head>
<body>

    <!-- Счетчик отзывов в правом верхнем углу -->
    <div class="reviews-counter-badge">
        💬 Отзывов: <span style="color: #bc6c25;">{{ reviews|length }}</span>
    </div>

    <h1>⭐ Art Shop — Отзывы</h1>
    <p class="desc">Оставляйте отзывы по кодам подтверждения покупок.</p>

    <div class="glass-radio-group">
        <input type="radio" name="glass-nav" id="glass-write" {% if active_tab == 'write' %}checked{% endif %} onchange="switchTab('write')">
        <label for="glass-write">Оставить отзыв</label>
        
        <input type="radio" name="glass-nav" id="glass-reviews" {% if active_tab == 'reviews' %}checked{% endif %} onchange="switchTab('reviews')">
        <label for="glass-reviews">Список отзывов</label>

        <div class="glass-glider"></div>
    </div>

    <!-- ВКЛАДКА 1: Написать отзыв -->
    <div id="tab-write" class="section-content {% if active_tab == 'write' %}active{% endif %}">
        <div class="form-container">
            <h3 style="margin-top: 0; font-weight: bold; color: #4a3525;">Оставить отзыв</h3>
            
            {% if error %}
                <div style="background-color: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; color: #b91c1c; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">
                    {{ error }}
                </div>
            {% endif %}
            
            <form action="/add-review" method="POST" id="review-form" onsubmit="handleReviewSubmit(event)">
                <input type="hidden" name="active_tab" value="write">
                <label style="font-weight: 600;">Ваше имя / Discord:</label>
                <input type="text" name="username" placeholder="@username" required>
                
                <label style="font-weight: 600;">Код подтверждения покупки:</label>
                <input type="text" name="code" placeholder="Например: REV-XXXX" required>

                <label style="font-weight: 600; display: block; text-align: center; margin-bottom: 5px;">Ваша оценка:</label>
                <div class="rating-container">
                    <div class="rating">
                        <input type="radio" id="star5" name="rating" value="5"><label for="star5"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg></label>
                        <input type="radio" id="star4" name="rating" value="4"><label for="star4"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg></label>
                        <input type="radio" id="star3" name="rating" value="3"><label for="star3"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg></label>
                        <input type="radio" id="star2" name="rating" value="2"><label for="star2"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg></label>
                        <input type="radio" id="star1" name="rating" value="1" checked><label for="star1"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg></label>
                    </div>
                </div>

                <label style="font-weight: 600;">Ваш отзыв:</label>
                <textarea name="text" rows="4" placeholder="Напишите пару слов о магазине..." required></textarea>
                
                <button type="submit" id="submit-btn">
                    <span id="btn-text">Отправить отзыв</span>
                    <div id="btn-loader" class="loader hidden">
                        <svg class="cookie-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.78L8 11.5c0 .55.45 1 1 1 .83 0 1.5-.67 1.5-1.5 0-.28-.08-.54-.21-.76l1.29-1.29c.4.15.82.25 1.25.25 2.76 0 5-2.24 5-5 0-.43-.1-.85-.25-1.25L17 5.5c.22.13.48.21.76.21.83 0 1.5-.67 1.5-1.5 0-.55-.45-1-1-1-.28 0-.54.08-.76.21L16.2 2.21C15.01 2.07 13.79 2 12.5 2 7.81 2 4 5.81 4 10.5c0 .65.08 1.28.22 1.88L6 10.6v1.4c0 3.31 2.69 6 6 6 1.48 0 2.84-.55 3.88-1.45l1.41 1.41C15.88 19.34 14.5 19.93 13 19.93zM7.5 8C7.22 8 7 7.78 7 7.5S7.22 7 7.5 7 8 7.22 8 7.5 7.78 8 7.5 8zm3 2c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zm4-3c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zm-3 7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm4-3c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/></svg>
                        <svg class="cookie-icon cookie2" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.78L8 11.5c0 .55.45 1 1 1 .83 0 1.5-.67 1.5-1.5 0-.28-.08-.54-.21-.76l1.29-1.29c.4.15.82.25 1.25.25 2.76 0 5-2.24 5-5 0-.43-.1-.85-.25-1.25L17 5.5c.22.13.48.21.76.21.83 0 1.5-.67 1.5-1.5 0-.55-.45-1-1-1-.28 0-.54.08-.76.21L16.2 2.21C15.01 2.07 13.79 2 12.5 2 7.81 2 4 5.81 4 10.5c0 .65.08 1.28.22 1.88L6 10.6v1.4c0 3.31 2.69 6 6 6 1.48 0 2.84-.55 3.88-1.45l1.41 1.41C15.88 19.34 14.5 19.93 13 19.93zM7.5 8C7.22 8 7 7.78 7 7.5S7.22 7 7.5 7 8 7.22 8 7.5 7.78 8 7.5 8zm3 2c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zm4-3c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zm-3 7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm4-3c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1 z"/></svg>
                        <svg class="cookie-icon cookie3" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.78L8 11.5c0 .55.45 1 1 1 .83 0 1.5-.67 1.5-1.5 0-.28-.08-.54-.21-.76l1.29-1.29c.4.15.82.25 1.25.25 2.76 0 5-2.24 5-5 0-.43-.1-.85-.25-1.25L17 5.5c.22.13.48.21.76.21.83 0 1.5-.67 1.5-1.5 0-.55-.45-1-1-1-.28 0-.54.08-.76.21L16.2 2.21C15.01 2.07 13.79 2 12.5 2 7.81 2 4 5.81 4 10.5c0 .65.08 1.28.22 1.88L6 10.6v1.4c0 3.31 2.69 6 6 6 1.48 0 2.84-.55 3.88-1.45l1.41 1.41C15.88 19.34 14.5 19.93 13 19.93zM7.5 8C7.22 8 7 7.78 7 7.5S7.22 7 7.5 7 8 7.22 8 7.5 7.78 8 7.5 8zm3 2c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zm4-3c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zm-3 7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm4-3c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/></svg>
                    </div>
                </button>
            </form>
        </div>
    </div>

    <!-- ВКЛАДКА 2: Список отзывов -->
    <div id="tab-reviews" class="section-content {% if active_tab == 'reviews' %}active{% endif %}" style="gap: 25px; margin-top: 15px;">
        
        {% set total_reviews = reviews|length %}
        {% set ns = namespace(total_score=0) %}
        {% for r in reviews %}
            {% set ns.total_score = ns.total_score + (r.rating | int) %}
        {% endfor %}
        {% set avg = (ns.total_score / total_reviews) if total_reviews > 0 else 5 %}

        <div class="stats-banner w-4/5 max-w-[350px]">
            <div class="stats-emoji">{% if avg < 3 %}😢{% elif avg < 4.0 %}😐{% else %}😁{% endif %}</div>
            <div class="stats-info">
                <h3>Рейтинг: {{ "%.1f" | format(avg) }} / 5.0</h3>
                <p>{% if avg < 3 %}Есть над чем работать{% elif avg < 4.0 %}Нормально, но можем лучше{% else %}Отличные отзывы! ❤️{% endif %}</p>
            </div>
        </div>

        {% for review in reviews %}
        <div class="w-4/5 h-auto rounded-2xl bg-[#ffffff] border border-[#e7d4c0] p-6 max-w-[350px] text-[#4a3525] shadow-sm">
            <div style="display: flex; gap: 3px; margin-bottom: 8px;">
                {% for i in range(1, 6) %}
                    {% if i <= review.rating|int %}
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#ffc73a"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>
                    {% else %}
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="transparent" stroke="#ccc"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>
                    {% endif %}
                {% endfor %}
            </div>
            <h5 class="text-sm font-bold mb-2 text-[#5c4033]">{{ review.username }}</h5>
            <p class="w-full mb-4 text-sm text-[#6b5141]">{{ review.text }}</p>
            
            <div class="flex items-center justify-between w-full mt-2">
                <span class="text-xs text-[#a48c77]">{{ review.time }}</span>
                <button class="Btn" id="btn-like-{{ review.id }}" onclick="toggleLike('{{ review.id }}')">
                  <div class="leftContainer">
                    <svg viewBox="0 0 512 512" width="16" height="16" xmlns="http://www.w3.org/2000/svg"><path fill="white" d="M462.3 62.6C407.5 15.9 326 24.3 275.7 76.2L256 96.5l-19.7-20.3C186.1 24.3 104.5 15.9 49.7 62.6c-62.8 53.6-66.1 149.8-9.9 207.6l193.5 199.8c6.2 6.4 14.4 9.7 22.6 9.7s16.4-3.2 22.6-9.7L472 270.2c56.4-57.8 53.1-154-9.7-207.6zm-15.1 190.3L256 445.9 64.8 252.9c-40.8-41.9-43.1-110.5-5.7-154.5 38.3-43.9 104.5-47.5 147.2-7.5l27.9 28.7 27.9-28.7c42.7-40 108.9-36.4 147.2 7.5 37.4 44 35.1 112.6-5.7 154.5z"/></svg>
                    <span class="like">Like</span>
                  </div>
                  <div class="likeCount" id="like-count-{{ review.id }}">{{ review.likes }}</div>
                </button>
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", () => {
            {% for review in reviews %}
                if (localStorage.getItem('liked_review_{{ review.id }}') === 'true') {
                    const btn = document.getElementById('btn-like-{{ review.id }}');
                    if (btn) btn.classList.add('liked');
                }
            {% endfor %}
        });

        function switchTab(tabName) {
            document.getElementById('tab-write').classList.remove('active');
            document.getElementById('tab-reviews').classList.remove('active');
            
            if (tabName === 'write') {
                document.getElementById('tab-write').classList.add('active');
            } else if (tabName === 'reviews') {
                document.getElementById('tab-reviews').classList.add('active');
            }
        }

        function handleReviewSubmit(event) {
            event.preventDefault(); // Задерживаем отправку формы, чтобы показать анимацию
            
            const btn = document.getElementById('submit-btn');
            const btnText = document.getElementById('btn-text');
            const btnLoader = document.getElementById('btn-loader');
            const form = document.getElementById('review-form');
            
            // Скрываем текст, показываем печеньки и блокируем клики
            btnText.classList.add('hidden');
            btnLoader.classList.remove('hidden');
            btn.style.pointerEvents = 'none';
            
            // Ждем 2.5 секунды анимации загрузки, затем отправляем форму
            setTimeout(() => {
                form.submit();
            }, 2500);
        }

        function toggleLike(reviewId) {
            const isLiked = localStorage.getItem('liked_review_' + reviewId) === 'true';
            const action = isLiked ? 'unlike' : 'like';

            fetch('/like-review/' + reviewId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: action })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('like-count-' + reviewId).innerText = data.likes;
                    const btn = document.getElementById('btn-like-' + reviewId);
                    
                    if (action === 'like') {
                        localStorage.setItem('liked_review_' + reviewId, 'true');
                        btn.classList.add('liked');
                    } else {
                        localStorage.removeItem('liked_review_' + reviewId);
                        btn.classList.remove('liked');
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/reviews')
def reviews_page():
    active_tab = request.args.get('tab', 'reviews')
    error = request.args.get('error')
    
    resp = make_response(render_template_string(
        SITE_TEMPLATE, 
        reviews=load_reviews(), 
        active_tab=active_tab,
        error=error
    ))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/like-review/<int:review_id>', methods=['POST'])
def like_review(review_id):
    global REVIEWS_LIST
    REVIEWS_LIST = load_reviews()
    data = request.get_json() or {}
    action = data.get('action', 'like')

    for review in REVIEWS_LIST:
        if review.get('id') == review_id:
            current_likes = review.get('likes', 0)
            if action == 'like':
                review['likes'] = current_likes + 1
            else:
                review['likes'] = max(0, current_likes - 1)
            
            save_reviews(REVIEWS_LIST)
            return jsonify({"success": True, "likes": review['likes']})
            
    return jsonify({"success": False}), 404

@app.route('/add-review', methods=['POST'])
def add_review():
    username = request.form.get('username')
    code = request.form.get('code', '').strip()
    rating = request.form.get('rating', '5')
    text = request.form.get('text')
    
    reviews = load_reviews()
    codes = load_codes()

    if not username or not code or not text:
        return make_response(render_template_string(SITE_TEMPLATE, reviews=reviews, active_tab='write', error="Заполните все поля!"))
    
    if code not in codes:
        return make_response(render_template_string(SITE_TEMPLATE, reviews=reviews, active_tab='write', error="Ошибка: Неверный код подтверждения!"))
        
    if codes[code]:
        return make_response(render_template_string(SITE_TEMPLATE, reviews=reviews, active_tab='write', error="Ошибка: Этот код уже был использован!"))

    if len(text) < 3 or len(text) > 500:
        return make_response(render_template_string(SITE_TEMPLATE, reviews=reviews, active_tab='write', error="Ошибка: Отзыв от 3 до 500 символов."))

    codes[code] = True
    save_codes(codes)

    new_id = max([r.get('id', 0) for r in reviews], default=-1) + 1
    new_review = {
        "id": new_id,
        "username": username,
        "rating": int(rating),
        "text": text,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "likes": 0
    }
    reviews.insert(0, new_review)
    save_reviews(reviews)
    
    return make_response(render_template_string(SITE_TEMPLATE, reviews=reviews, active_tab='reviews'))

# --- Discord Bot код ---
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

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command(name="review", aliases=["отзывы"])
async def review_command(ctx):
    embed = discord.Embed(
        title="⭐ Отзывы о магазине Art Shop",
        description="Нажмите на кнопку ниже, чтобы открыть страницу с отзывами на нашем сайте!",
        color=discord.Color.purple()
    )
    
    view = View()
    view.add_item(Button(label="Смотреть на сайте", style=discord.ButtonStyle.link, url="https://discord-bot-new-production.up.railway.app/reviews"))
    
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
