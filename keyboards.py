from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_worker_keyboard():
    worker_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    my_profile = KeyboardButton("Мой профиль 👤")
    how_work = KeyboardButton("Как работать? ❓")
    about_project = KeyboardButton("О проекте ℹ️")
    worker_keyboard.add(my_profile, how_work)
    worker_keyboard.add(about_project)
    return worker_keyboard
