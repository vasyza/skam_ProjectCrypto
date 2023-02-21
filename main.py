import logging
import os

import mysql.connector
import numpy as np
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

import config
import const_messages
import keyboards
import static_functions

mysqli_host = "testcrypto.site"
mysqli_name = "u1929057_oreders_bd"
mysqli_login = "u1929057_default"
mysqli_password = "kHtnpSj78FBW6s1t"

def create_connection():
    connection = mysql.connector.connect(host=mysqli_host, user=mysqli_login, passwd=mysqli_password,
                                         database=mysqli_name)
    cursor = connection.cursor()
    return cursor, connection

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(config.BOT_TOKEN)
PICKLE_STORAGE = os.getenv('PICKLE_STORAGE', './db/fsm_storage.pickle')
JSON_STORAGE = os.getenv('JSON_STORAGE', './db/fsm_storage.json')
# storage = PickleStorage(PICKLE_STORAGE)
# storage = MemoryStorage()
storage = JSONStorage(JSON_STORAGE)
dp = Dispatcher(bot, storage=storage)


class States(StatesGroup):
    accept_rules = State('accept_rules')
    how_find = State('how_find', const_messages.how_find)
    experience = State('experience', const_messages.what_experience)
    time_work = State('time_work', const_messages.what_time)
    goals = State('goals', const_messages.what_goals)
    complete_request = State('complete_request')
    worker = State('worker')
    blocked = State('blocked')
    admin = State("admin")


@dp.message_handler(state=States.blocked)
async def process_blocked(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, const_messages.blocked)


@dp.message_handler(state=States.complete_request)
async def process_complete_request(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, const_messages.request_in_process)


@dp.message_handler(state=None)
async def process_none_state(message: types.Message, state: FSMContext):
    await States.accept_rules.set()
    markup = InlineKeyboardMarkup()
    btn_callback = InlineKeyboardButton('✅ Правила проекта приняты', callback_data='callback_accept_rules')
    await state.set_data({"username": message.from_user.username})
    markup.add(btn_callback)
    await message.answer(const_messages.start_message, reply_markup=markup)


@dp.message_handler(state=States.accept_rules)
async def process_accept(message: types.Message, state: FSMContext):
    markup = InlineKeyboardMarkup()
    btn_callback = InlineKeyboardButton('✅ Правила проекта приняты', callback_data='callback_accept_rules')
    markup.add(btn_callback)
    await message.answer(const_messages.start_message, reply_markup=markup)


@dp.message_handler(state=States.how_find)
async def process_find(message: types.Message, state: FSMContext):
    await state.update_data(how_find=message.text)
    await States.experience.set()
    await message.answer(const_messages.what_experience)


@dp.message_handler(state=States.experience)
async def process_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await States.time_work.set()
    await message.answer(const_messages.what_time)


@dp.message_handler(state=States.time_work)
async def process_time_work(message: types.Message, state: FSMContext):
    await state.update_data(time_work=message.text)
    await States.goals.set()
    await message.answer(const_messages.what_goals)


@dp.message_handler(state=States.goals)
async def process_goals(message: types.Message, state: FSMContext):
    await state.update_data(goals=message.text)
    await States.complete_request.set()
    complete_form = await state.get_data()
    await message.answer(const_messages.request_process)

    markup = InlineKeyboardMarkup()
    cancel = InlineKeyboardButton('Отклонить', callback_data=f'cancel{message.from_user.id}')
    accept = InlineKeyboardButton('Принять', callback_data=f'accept{message.from_user.id}')
    rewrite = InlineKeyboardButton('Заблокировать', callback_data=f'block{message.from_user.id}')
    fake_profit = InlineKeyboardButton('Fake Profit', callback_data=f'fake_profit')
    markup.add(accept)
    markup.add(cancel)
    markup.add(rewrite)
    markup.add(fake_profit)

    for admin_id in config.ADMIN_IDS:
        await bot.send_message(admin_id,
                               f"Новая анкета\nПользователь: @{message.from_user.username}\nКак узнали: {complete_form['how_find']}\nОпыт: {complete_form['experience']}\nВремя на работу: {complete_form['time_work']}\nЦель: {complete_form['goals']}",
                               reply_markup=markup)


@dp.message_handler(commands='start', state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await States.accept_rules.set()
        markup = InlineKeyboardMarkup()
        btn_callback = InlineKeyboardButton('✅ Правила проекта приняты', callback_data='callback_accept_rules')
        markup.add(btn_callback)
        await state.set_data({"username": message.from_user.username})
        await message.answer(const_messages.start_message, reply_markup=markup)
    else:
        await message.answer(text="Вы уже зарегистрированы", reply_markup=keyboards.get_worker_keyboard())


@dp.message_handler(commands='help', state='*')
async def cmd_help(message: types.Message):
    await message.answer("I can do a lot of things! Try sending me a message.")


@dp.message_handler(lambda m: m.text == "Мой профиль 👤", state=[States.worker, States.admin])
async def cmd_help(message: types.Message, state: FSMContext):
    data_user = await state.get_data()
    text_to_send = const_messages.user_profile.format(message.from_user.id, data_user['referral_code'], "Новичок",
                                                      sum(data_user['profits']), len(data_user['profits']),
                                                      static_functions.parse_timestamp(data_user['signup_date']),
                                                      "✅ Всё работает")
    await message.answer(
        text=text_to_send, parse_mode='Markdown')


@dp.message_handler(lambda m: m.text == "О проекте ℹ️", state=[States.worker, States.admin])
async def cmd_help(message: types.Message, state: FSMContext):
    # data_user = await state.get_data()
    statistics_state = dp.current_state(chat="statistics", user="statistics")
    statistics_data = await statistics_state.get_data()
    mean_profit = 0 if not statistics_data['profits'] else mean_profit if not np.isnan(
        mean_profit := np.mean(statistics_data['profits'])) else 0
    text_to_send = const_messages.about_project.format(config.date_open, len(statistics_data['profits']),
                                                       int(sum(statistics_data['profits'])),
                                                       int(mean_profit), config.support_id)
    await message.answer(
        text=text_to_send, parse_mode='Markdown')


@dp.message_handler(lambda m: m.text == "Как работать? ❓", state=[States.worker, States.admin])
async def cmd_help(message: types.Message, state: FSMContext):
    data_user = await state.get_data()
    text_to_send = const_messages.how_work.format(data_user['referral_code'], config.url_site,
                                                  config.url_site + f'?ref={data_user["referral_code"]}')
    await message.answer(
        text=text_to_send, parse_mode='Markdown')


@dp.callback_query_handler(lambda c: c.data == 'callback_accept_rules', state=States.accept_rules)
async def process_callback_accept_rules(callback_query: CallbackQuery, state: FSMContext):
    await States.how_find.set()
    await bot.send_message(chat_id=callback_query.from_user.id, text=const_messages.how_find)


@dp.callback_query_handler(lambda c: 'cancel' in c.data, state='*')
async def process_callback_accept_rules(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.data.replace('cancel', '')
    who_cancel = callback_query['from']
    user_state = dp.current_state(chat=user_id, user=user_id)
    await user_state.set_state('States:accept_rules')
    await bot.send_message(user_id,
                           const_messages.request_cancel.format(who_cancel['first_name'], who_cancel['username']),
                           parse_mode='Markdown', disable_web_page_preview=True)
    await callback_query.message.edit_text(callback_query.message.text + "\nСтатус: Отклонено")


@dp.callback_query_handler(lambda c: 'block' in c.data, state='*')
async def process_callback_accept_rules(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.data.replace('block', '')
    who_block = callback_query['from']
    user_state = dp.current_state(chat=user_id, user=user_id)
    await user_state.set_state('States:blocked')
    await bot.send_message(user_id, const_messages.request_block.format(who_block['first_name'], who_block['username']),
                           parse_mode='Markdown', disable_web_page_preview=True)
    await callback_query.message.edit_text(callback_query.message.text + "\nСтатус: Заблокирован")


@dp.callback_query_handler(lambda c: 'accept' in c.data, state='*')
async def process_callback_accept_rules(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.data.replace('accept', '')
    who_block = callback_query['from']
    user_state = dp.current_state(chat=user_id, user=user_id)
    referral_code = static_functions.generate_referral_code()
    user_data = await user_state.get_data()

    cursor, connection = create_connection()

    cursor.execute(f"INSERT INTO workers VALUES ('{referral_code}', '{user_id}');")
    connection.commit()

    await user_state.update_data(
        {'referral_code': referral_code, "profits": [], "profits_payed": [],
         'signup_date': static_functions.get_timestamp_now()})
    await user_state.set_state('States:worker')
    await bot.send_message(user_id,
                           const_messages.request_accept.format(who_block['first_name'], who_block['username']),
                           parse_mode='Markdown', disable_web_page_preview=True)
    await bot.send_message(user_id, const_messages.info_message.format(config.bot_to_work, config.channel_pay,
                                                                       config.channel_info, config.chat_url),
                           reply_markup=keyboards.get_worker_keyboard())
    await callback_query.message.edit_text(callback_query.message.text + "\nСтатус: Принят")


@dp.callback_query_handler(lambda c: 'ChangePayToDone' in c.data, state=States.admin)
async def process_callback_change_pay(callback_query: CallbackQuery, state: FSMContext):
    from_user = callback_query['from']

    profit_message_ = list(filter(lambda x: x, callback_query.message.text.split('\n')))
    worker_profit_value = int(profit_message_[-1].split(' ~ ')[-1].replace(" $", ""))

    markup = InlineKeyboardMarkup()
    btn_callback = InlineKeyboardButton('✅ Успешно выплачено', callback_data='not')
    markup.add(btn_callback)

    worker_id = callback_query.data.replace("ChangePayToDone", "")
    worker_state = dp.current_state(chat=worker_id, user=worker_id)
    worker_data = await worker_state.get_data()
    worker_data['profits_payed'].append(worker_profit_value)

    await worker_state.update_data(profits_payed=worker_data['profits_payed'])

    await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                        inline_message_id=callback_query.inline_message_id, reply_markup=markup)


@dp.callback_query_handler(lambda c: 'confirmPayTrue' in c.data, state="*")
async def process_callback_accept_rules(callback_query: CallbackQuery, state: FSMContext):
    from_user = callback_query['from']

    # todo: parse with regular
    # parsing
    list_of_profit_values = list(filter(lambda x: x, callback_query.message.text.split("\n")))
    profit_value_usdt = float(list_of_profit_values[3].split(" = ")[-1].replace(" USDT", ""))
    profit_value_crypt = list_of_profit_values[3].split(" = ")[0].replace("Сумма: ", "")

    worker_profit = static_functions.calculate_worker_profit(profit_value_usdt)
    worker_id = callback_query.data.replace('confirmPayTrue_', '')
    worker_state = dp.current_state(chat=worker_id, user=worker_id)
    worker_data = await worker_state.get_data()
    worker_data['profits'].append(worker_profit)
    worker_username = worker_data['username'].replace('_', r'\_')
    await worker_state.update_data(profits=worker_data['profits'])

    statistics_state = dp.current_state(chat="statistics", user="statistics")
    statistics_data = await statistics_state.get_data()
    statistics_data['profits'].append(profit_value_usdt)
    await statistics_state.update_data(profits=statistics_data['profits'])

    message_profit = const_messages.new_profit.format(profit_value_crypt,
                                                      int(profit_value_usdt),
                                                      f"@{worker_username}", worker_profit)
    await callback_query.message.edit_text(callback_query.message.text + "\n\nСтатус: ✅", parse_mode="HTML")

    await bot.send_message(worker_id, message_profit,
                           parse_mode="Markdown")

    markup = InlineKeyboardMarkup()
    btn_callback = InlineKeyboardButton('⏳ Выплата в процессе', callback_data=f'ChangePayToDone{worker_id}')
    markup.add(btn_callback)

    await bot.send_message(config.PROFITS_CHAT_ID,
                           message_profit,
                           reply_markup=markup, parse_mode="Markdown")


@dp.callback_query_handler(lambda c: 'confirmPayFalse' in c.data, state="*")
async def process_callback_accept_rules(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(callback_query.message.text + "\n\nСтатус: ❌", parse_mode="HTML")

    worker_id = callback_query.data.replace('confirmPayFalse_', '')
    await bot.send_message(worker_id, const_messages.new_profit_false.format(callback_query.from_user.first_name,
                                                                             callback_query.from_user.username),
                           parse_mode="Markdown", disable_web_page_preview=True)




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
