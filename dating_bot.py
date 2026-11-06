import os
import sqlite3
import telebot
from telebot import types

# Yahan double quotes ke andar apna asli Telegram Bot Token daal do:
TOKEN = ​ "9010254570:AAEYN45jLFXS0Soh1ZVxsiKy160JSrCA2NE"
bot = telebot.TeleBot(TOKEN)

# Database connection setup
conn = sqlite3.connect("dating_users.db", check_same_thread=False)
cursor = conn.cursor()

# Table creation for users
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        looking_for TEXT,
        bio TEXT
    )
"""
)
conn.commit()


@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Register Profile", "Find Matches")
    bot.send_message(
        message.chat.id,
        "Welcome to Telegram Dating Bot! 💖\nApni profile banane ke liye 'Register Profile' par click karein.",
        reply_markup=markup,
    )


@bot.message_handler(
    func=lambda message: message.text in ["Register Profile", "Find Matches"]
)
def handle_menu(message):
    if message.text == "Register Profile":
        msg = bot.send_message(message.chat.id, "Apna pura naam batayein:")
        bot.register_next_step_handler(msg, process_name)
    elif message.text == "Find Matches":
        show_matches(message)


def process_name(message):
    name = message.text
    msg = bot.send_message(message.chat.id, "Aapki umar (age) kitni hai?")
    bot.register_next_step_handler(msg, process_age, name)


def process_age(message, name):
    try:
        age = int(message.text)
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, one_time_keyboard=True
        )
        markup.add("Male", "Female")
        msg = bot.send_message(
            message.chat.id, "Aapka gender kya hai?", reply_markup=markup
        )
        bot.register_next_step_handler(msg, process_gender, name, age)
    except ValueError:
        msg = bot.send_message(
            message.chat.id, "Kripya sahi number me umar (age) likhein:"
        )
        bot.register_next_step_handler(msg, process_age, name)


def process_gender(message, name, age):
    gender = message.text
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    markup.add("Male", "Female", "Everyone")
    msg = bot.send_message(
        message.chat.id, "Aap kise dhoondh rahe hain?", reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_looking, name, age, gender)


def process_looking(message, name, age, gender):
    looking_for = message.text
    msg = bot.send_message(
        message.chat.id,
        "Apne baare me thoda sa kuch likhein (Bio):",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(
        msg, process_bio, name, age, gender, looking_for
    )


def process_bio(message, name, age, gender, looking_for):
    bio = message.text
    user_id = message.from_user.id

    cursor.execute(
        """
        INSERT OR REPLACE INTO users (user_id, name, age, gender, looking_for, bio)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (user_id, name, age, gender, looking_for, bio),
    )
    conn.commit()

    bot.send_message(
        message.chat.id,
        "🎉 Aapki profile safaltapoorvak save ho gayi hai!\nAb aap 'Find Matches' par click karke log dekh sakte hain.",
    )


def show_matches(message):
    user_id = message.from_user.id
    cursor.execute("SELECT looking_for FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        bot.send_message(
            message.chat.id,
            "Pehle apni profile register karein! Type /start",
        )
        return

    looking_for = row[0]
    if looking_for == "Everyone":
        cursor.execute(
            "SELECT name, age, bio FROM users WHERE user_id != ?", (user_id,)
        )
    else:
        cursor.execute(
            "SELECT name, age, bio FROM users WHERE gender = ? AND user_id != ?",
            (looking_for, user_id),
        )

    matches = cursor.fetchall()
    if not matches:
        bot.send_message(
            message.chat.id,
            "Filhal koi naye matches available nahi hain. Thodi der baad koshish karein!",
        )
        return

    for match in matches:
        profile_text = f"💖 **Match Found!**\n\nName: {match[0]}\nAge: {match[1]}\nBio: {match[2]}"
        bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
