import logging
import fake_useragent
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
import math
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from requests import get, Session
import config
from bs4 import BeautifulSoup as bs
from datetime import date as d
from datetime import timedelta
import sqlite3
import traceback

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.token, parse_mode='html')

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

l_sub_status = {0: "⛔ Not active",
                1: "✅ Active!"}

l_user_status = {0: "⛔ Бан",
                 1: "👨‍🎓 Студент",
                 2: "😎 Ответственный",
                 3: "💃 Староста",
                 4: "👨‍🏫 Преподаватель",
                 5: "🧑‍💻 Разраб",
                 6: "🤴 Бог", }

l_kniga_emoji = {0: "📕",
                 1: "📒",
                 2: "📗",
                 3: "📘",
                 4: "📙",
                 5: "📔"}


class Form(StatesGroup):
    s_username = State()
    s_password = State()
    s_add_user = State()
    s_add_user_2 = State()
    s_add_user_3 = State()
    s_add_user_4 = State()
    s_add_user_5 = State()
    s_add_user_6 = State()
    s_add_user_true = State()
    s_starosta_announcement = State()
    s_starosta_poll = State()
    s_starosta_poll_1 = State()
    s_starosta_poll_2 = State()
    s_add_homework_1 = State()
    s_starosta_note_1 = State()
    s_starosta_note_2 = State()
    s_starosta_note_3 = State()


class Poll(StatesGroup):
    poll_1 = State()
    poll_2 = State()
    poll_3 = State()
    poll_4 = State()
    poll_5 = State()
    poll_6 = State()
    poll_7 = State()
    poll_8 = State()
    poll_9 = State()
    poll_10 = State()
    poll_finish = State()


async def f_user_delete_true(user_id):
    key_del = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
    b_ = InlineKeyboardButton('⬇⬇⬇  Вы уверены?  ⬇⬇⬇', callback_data='pass')
    b_true = InlineKeyboardButton('🚮 ДА 🚮', callback_data='c_user_delete_true 1')
    b_false = InlineKeyboardButton('⛩ НЕТ ⛩', callback_data='c_user_delete_true 2')
    key_del.add(b_)
    key_del.add(b_true,b_false)
    await bot.send_message(user_id, 'ВЫ УВЕРЕНЫ???', reply_markup=key_del)



async def f_delete_this_message(message):
    await bot.delete_message(message.chat.id, message.message_id)


async def get_user_status(user_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_status = cursor.execute(f"SELECT status FROM users WHERE user_id ='{user_id}'").fetchone()[0]
    conn.close()
    return user_status


async def f_user_verify(user_id, username, message):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))  # поиск нужной записи
    rez = cursor.fetchall()  # привод в нормальный вид записей
    if not rez:  # если запись отсутствует то
        await bot.send_message(user_id, 'Для регистрации введите логин от личного кабинета студента')
        await Form.s_username.set()
    else:
        print("Пользователь найден в базе: " + str(username) + " || " + str(user_id))
        old_user_name = cursor.execute("SELECT username FROM users WHERE user_id=?", (user_id,)).fetchone()[0]
        fresh_user_name = username
        if old_user_name != fresh_user_name:
            await bot.send_message(config.archive_chat_id, f"❗️ Пользователь <code>{user_id}</code> сменил юзернейм!"
                                                           f"\n⚠️ Был @{old_user_name} стал @{fresh_user_name}")
            cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', (fresh_user_name, user_id))
            conn.commit()
        user_status = cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,)).fetchone()[0]
        if user_status == 0:
            print("Проверка завершена! Пользователь забанен ⛔️!")
        else:
            if message == '/start':
                await start_message_1(user_id)
            print("Проверка завершена! Пользователь одобрен ✅️!")
            return user_status
    conn.close()


@dp.message_handler(state=Form.s_username)
async def f_username(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['username'] = message.text
    await Form.next()
    await bot.send_message(message.from_user.id, f"<b>Введите пароль</b>")


@dp.message_handler(state=Form.s_password)
async def f_password(message: Message, state: FSMContext):
    async with state.proxy() as datas:
        ans = await bot.send_message(chat_id=message.chat.id, text='Загрузка...')
        datas['password'] = message.text
        url = 'https://lks.bmstu.ru/portal3/login?back=https://lks.bmstu.ru/portfolio'
        data = {
            'username': datas['username'],
            'password': datas['password'],
            '_eventId': 'submit'
        }
        s = Session()
        r = s.get(url)
        execution = r.text.split('<input type="hidden" name="execution" value="')[1].split('"/>')[0]
        data["execution"] = execution
        url = 'https://proxy.bmstu.ru:8443/cas/login?service=https%3A%2F%2Fproxy.bmstu.ru%3A8443%2Fcas%2Foauth2.0%2FcallbackAuthorize%3Fclient_name%3DCasOAuthClient%26client_id%3DEU'
        fake_user = fake_useragent.UserAgent().chrome
        headers = {
            'user-agent': fake_user
        }
        a = s.post(url, data=data, headers=headers)
        r = bs(a.text, 'lxml')
        try:
            name = [i for i in r.find(class_='card-title').text.split(' ') if i != '']
            name = [line.rstrip() for line in name]
            name = f'{name[0]} {name[1]} {name[2]}'
            info = r.find_all(class_='card-subtitle')
            DOB = info[1].text
            # education_level = info[2].text
            course = info[3].text
            conn = sqlite3.connect('db.db', check_same_thread=False)
            cursor = conn.cursor()
            user_id = message.from_user.id
            username = message.from_user.username
            rez = cursor.execute(f'SELECT user_id FROM users WHERE FIO=?', (name,)).fetchone()[0]
            username_1 = cursor.execute(f'SELECT username FROM users WHERE FIO=?', (name,)).fetchone()[0]
            if rez:
                cursor.execute(f'''UPDATE users SET user_id = ('{rez} {user_id}') WHERE FIO=?''', (name,))
                cursor.execute(f'''UPDATE users SET username = ('{username_1} {username}') WHERE FIO=?''', (name,))
            else:
                cursor.execute(
                    'INSERT INTO users (user_id, username, FIO, DOB, course, sub, sub_date, status, login, password) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (user_id, username, name, DOB, course,
                     0, None, 1, datas['username'], datas['password']))
            await bot.edit_message_text(text='🏅  Вы успешно зарегистрированы  🏅', message_id=ans.message_id,
                                        chat_id=message.chat.id)
            conn.commit()
            conn.close()
            await state.reset_data()
            await state.finish()
            await start_message_1(user_id)
        except Exception as E:
            print(traceback.print_exc())
            await bot.send_message(config.archive_chat_id,
                                   f'у вас ошибка блять *{E}* вот такая, иди исправляй сука тварь падла мразь')
            await bot.send_message(message.chat.id,
                                   'Ты ввел неверный логин или пароль\n\n'
                                   'Если такая хрень написалась после успешной регистрации, '
                                   'то бля, не поленись и скинь <a href="https://t.me/bmstu_support">мне</a> че ты ввел',
                                   disable_web_page_preview=True)
            await state.reset_data()
            await state.finish()
            await f_user_verify(message.from_user.id, message.from_user.username, '/start')


@dp.message_handler(commands=['getmyid'])
async def getmyidbroshka(message):
    await message.answer(f"Твой айди: {message.from_user.id}")


@dp.message_handler(commands=['start'])
async def start_message(message: Message):
    username = message.from_user.username
    user_id = message.from_user.id
    await f_user_verify(user_id, username, '/start')


async def start_message_1(user_id):
    user_status = await get_user_status(user_id)
    key_main = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
    b_timetable = InlineKeyboardButton('🗓 Посмотреть расписание', callback_data='c_main timetable')
    b_homework = InlineKeyboardButton('📃 Домашние задания', callback_data='c_main homework')
    b_starosta = InlineKeyboardButton('👨‍🏫 Панель старосты', callback_data='c_main starosta')
    b_admin = InlineKeyboardButton('🤖 Панель администратора', callback_data='c_main admin')
    b_account = InlineKeyboardButton('⚙ Аккаунт', callback_data='c_main account')
    key_main.add(b_timetable, b_homework)
    key_main.add(b_account)
    if user_status > 4:
        key_main.add(b_admin, b_starosta)
        await bot.send_message(user_id, " 🌍   ——— <b>ГЛАВНОЕ МЕНЮ</b> ———   🌍 ", reply_markup=key_main)
    elif user_status > 1:
        key_main.add(b_starosta)
        await bot.send_message(user_id, " 🌍   ——— <b>ГЛАВНОЕ МЕНЮ</b> ———   🌍 ", reply_markup=key_main)
    elif user_status > 0:
        await bot.send_message(user_id, " 🌍   ——— <b>ГЛАВНОЕ МЕНЮ</b> ———   🌍 ", reply_markup=key_main)
    else:
        await bot.send_message(user_id, f'⛔️ <b>ВЫ ЗАБАНЕНЫ</b>'
                                        f'\n\n   Ну а если вы просто не зарегистрированы, то обратитесь к старосте группы')


async def f_timetable_page(user_id):
    user_status = await get_user_status(user_id)
    if user_status > 0:
        conn = sqlite3.connect('db.db', check_same_thread=False)
        cursor = conn.cursor()
        course = cursor.execute(f"SELECT course FROM users WHERE user_id='{user_id}'").fetchone()[0]
        key_timetable = InlineKeyboardMarkup(resize_keyboard=True, selective=True)  # объявление клавиатуры
        b_back = InlineKeyboardButton('🏡 Главное меню', callback_data=f'c_back_to_menu')
        b_timetable_today = InlineKeyboardButton('🟠 на сегодня', callback_data=f'c_timetable_now {1} {course}')
        b_timetable_tomorrow = InlineKeyboardButton('🟢 на завтра', callback_data=f'c_timetable_now {2} {course}')
        b_timetable_week = InlineKeyboardButton('🟣 на неделю', callback_data=f'c_timetable_now {3} {course}')
        if d.isoweekday(d.today()) == 7:
            key_timetable.row(b_timetable_tomorrow, b_timetable_week)  # добавление кнопки в клавиатуру
        else:
            key_timetable.row(b_timetable_today, b_timetable_tomorrow)
            key_timetable.row(b_timetable_week)
        key_timetable.add(b_back)
        await bot.send_message(user_id, f'📆   ——— Расписание ———   📆', reply_markup=key_timetable)
        conn.close()


async def f_account_page(user_id, username):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_status = await get_user_status(user_id)
    if user_status > 0:
        cursor.execute(f"SELECT * FROM users WHERE user_id='{user_id}'")
        info = cursor.fetchone()
        FIO = info[3]
        course = info[5]
        sub = info[6]
        sub_date = info[7]
        rez = cursor.execute("SELECT course FROM courses WHERE course=?", (course,)).fetchall()
        if not rez:
            cursor.execute(f'''INSERT INTO courses (course) VALUES ('{course}')''')
            conn.commit()
        key_start_message = InlineKeyboardMarkup(resize_keyboard=True, selective=True)  # объявление клавиатуры
        b_back = InlineKeyboardButton('🏡️️ Главное меню', callback_data='c_back_to_menu')
        b_setting = InlineKeyboardButton('⚙ Настройки (не ворк)', callback_data='c_user_setting')
        b_delete = InlineKeyboardButton('🗑 Удалить аккаунт', callback_data='c_user_delete')
        key_start_message.add(b_setting, b_delete)
        key_start_message.add(b_back)
        if user_status != 0:
            await bot.send_message(user_id, f"Привет, {username}"
                                            f"\n\nПодписка: <b>{l_sub_status.get(sub)}</b>"
                                            f"\nАктивна до: <b>{sub_date}</b>"
                                            f"\n-----------------"
                                            f"\n💎 Информация о тебе 💎"
                                            f"\n<b>🆔 ID:</b> <code>{user_id}</code>"
                                            f"\n<b>📝 ФИО:</b> <code>{FIO}</code>"
                                            f"\n<b>👥 Курс:</b> <code>{course}</code>"
                                            f"\n<b>🧠 Статус:</b> <code>{l_user_status.get(user_status)}</code>",
                                   reply_markup=key_start_message)
        else:
            await bot.send_message(user_id, "⛔️ <b>Доступ запрещен</b>")
        conn.close()


@dp.message_handler(commands=['f'])
async def test(message):
    await message.answer(f"Сегодня: {d.today()}\n"
                         f"День недели: {d.isoweekday(d.today())}")


# todo
# подключиться к бд и проверить есть ли предмет в списке, если есть, то кнопка с дз
# если нет, то добавить предмет в бд и кнопка с дз
async def f_timetable_week(user_id, course, week_count):  # парсер расписания на неделю
    url = 'https://lks.bmstu.ru/schedule/list'
    b = bs(get(url).text, 'lxml').find_all('a', class_="btn btn-primary col-1 rounded schedule-indent")
    status = 0
    for i in b:
        if i.get_text(strip=True) == course:
            status = 1
            url = 'https://lks.bmstu.ru/' + i.get('href')
            b = bs(get(url).text, 'lxml').find_all('div', class_='col-lg-6 d-none d-md-block')
            string_build = "\n"
            for l, n in enumerate(b, start=1):
                if l >= 2:
                    string_build += f'—————————————————————————\n\n'
                string_build += f'''🗓    {n.find('strong').text}    🗓\n\n\n'''
                y = n.find_all('tr')
                for i, j in enumerate(y, start=1):
                    if i >= 3:
                        a = j.find('span')
                        if (a is not None) and (week_count == 0):  # чилситель
                            if (a.find_parent('td', class_='text-info-bold')) or (a.find_parent('td', colspan='2')):
                                string_build += f"""🕰  {j.find('td', class_='bg-grey text-nowrap').text}\n{a.text}\n\n"""
                        elif (a is not None) and (week_count == 1):  # знаменатель
                            if (a.find_parent('td', class_='text-primary')) or (a.find_parent('td', colspan='2')):
                                string_build += f"""🕰  {j.find('td', class_='bg-grey text-nowrap').text}\n{a.text}\n\n"""
            key_menu = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
            b_back = InlineKeyboardButton('🏡 Главное меню', callback_data=f'c_back_to_menu')
            key_menu.add(b_back)
            await bot.send_message(user_id, f"{string_build}", reply_markup=key_menu)
            break

    if status == 0:
        await bot.send_message(user_id,
                               '\nОбратитесь к <a href="https://t.me/bmstu_support">создателю</a> этого слабого'
                               ' бота', disable_web_page_preview=True)


async def f_homework_panel_main_0(user_id, username):
    user_status = await f_user_verify(user_id, username, ' ')
    if user_status > 0:
        await f_homework_panel_main(user_id, user_status)
    else:
        await bot.send_message(user_id, text='ВЫ ЗАБАНЕНЫ')


async def f_homework_panel_main(user_id, user_status):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"SELECT course FROM users WHERE user_id='{user_id}'")  # получаем группу
    course = cursor.fetchone()[0]
    homework_kol = cursor.execute("SELECT COUNT(*) FROM homework WHERE course=?", (course,)).fetchone()[0]
    key_homework_panel = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
    b_show_homework = InlineKeyboardButton('👁 Посмотреть домашние задания', callback_data='c_show_homework')
    b_back = InlineKeyboardButton('🏡️️ Главное меню', callback_data='c_back_to_menu')
    if user_status > 1:
        b_add_homework = InlineKeyboardButton('➕ Добавить домашнее задание', callback_data='c_add_homework')
        b_edit_homework = InlineKeyboardButton('✏ Редактировать существующие', callback_data='c_show_homework')
        key_homework_panel.add(b_add_homework, b_edit_homework)
    key_homework_panel.add(b_show_homework)
    key_homework_panel.add(b_back)
    await bot.send_message(user_id, "📔️   ——— <b>ПАНЕЛЬ ДОМАШКИ</b> ———   📔️" +
                           f"\nДомашки в вашей группе: {str(homework_kol)}", reply_markup=key_homework_panel)
    conn.close()


async def f_pagination(user_id, current_page, message_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT course FROM users WHERE user_id='{user_id}'")  # получаем группу
    course = cursor.fetchone()[0]
    cursor.execute("SELECT class FROM homework WHERE course=?", (course,))  # получаем все названия
    names_all = cursor.fetchall()
    names = []
    for i in names_all:
        if i[0] not in names:
            names.append(i[0])
    keybord = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
    keybord.row_width = 3
    spisok = {j: InlineKeyboardButton(f'{i}', callback_data=f'c_reference {i}') for j, i in enumerate(names, start=0)}
    full_length = len(spisok)
    last_page = math.ceil(full_length / 6)
    length = full_length - current_page * 6
    pass_ = InlineKeyboardButton(' ', callback_data='pass')
    back = InlineKeyboardButton('⬅', callback_data=f'c_pagination back {current_page}')
    page = InlineKeyboardButton(f'{current_page}/{last_page}', callback_data='pass')
    next = InlineKeyboardButton('➡', callback_data=f'c_pagination next {current_page}')
    if current_page == 1:
        for i in range(6, full_length):
            del spisok[i]
        keybord.add(*spisok.values())
        keybord.add(pass_, page, next)
    elif current_page == last_page:
        if full_length % 6 == 0:
            length = full_length - 6
        else:
            length = full_length - full_length // 6
        for i in range(0, length):
            spisok.pop(i)
        keybord.add(*spisok.values())
        keybord.add(back, page, pass_)
    else:
        for i in range(0, length):
            spisok.pop(i)
        for i in range(length + 6, full_length):
            spisok.pop(i)
        keybord.add(*spisok.values())
        keybord.add(back, page, next)

    await bot.edit_message_text(chat_id=user_id, message_id=message_id,
                                text='Выберете предмет', reply_markup=keybord)
    conn.close()


async def f_homework_page(user_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT course FROM users WHERE user_id='{user_id}'")
    course = cursor.fetchone()[0]
    cursor.execute("SELECT class FROM homework WHERE course=?", (course,))  # получаем все названия
    names_all = cursor.fetchall()
    names = []
    for i in names_all:
        if i[0] not in names:
            names.append(i[0])
    keybord = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
    keybord.row_width = 3
    spisok = {j: InlineKeyboardButton(f'{i}', callback_data=f'c_reference {i}') for j, i in enumerate(names, start=0)}
    length = len(spisok)
    pass_ = InlineKeyboardButton(' ', callback_data='pass')
    page = InlineKeyboardButton(f'1/{math.ceil(length / 6)}', callback_data='pass')
    next = InlineKeyboardButton('➡', callback_data=f'c_reference next {length}')
    if length <= 6:
        keybord.add(*spisok.values())
    else:
        length = length - length % 6
        for i in range(6, length - 1, -1):
            spisok.pop(i)
        keybord.add(*spisok.values())
        keybord.add(pass_, page, next)

    await bot.send_message(chat_id=user_id, text='Выберете предмет', reply_markup=keybord)
    conn.close()


async def f_homework_show(homework, user_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"SELECT status FROM users WHERE user_id='{user_id}'")
    user_status = cursor.fetchone()[0]
    cursor.execute(f"SELECT course FROM users WHERE user_id='{user_id}'")  # получаем группу
    course = cursor.fetchone()[0]
    cursor.execute(
        f"SELECT text FROM homework WHERE (course LIKE '%{course}%') AND (class LIKE '%{homework}%')  ")  # текст дз
    text_all = cursor.fetchall()
    date_of_creation = cursor.execute(
        f"SELECT date_of_creation FROM homework WHERE (course LIKE '%{course}%') AND (class LIKE '%{homework}%')").fetchone()
    for i in range(len(text_all)):
        id_of_homework = cursor.execute(
            f"SELECT id FROM homework WHERE (course LIKE '%{course}%') AND (text LIKE '%{text_all[i][0]}%')").fetchone()
        if user_status > 1:
            await bot.send_message(user_id,
                                   text=f'\n\n Задание по {homework} от {date_of_creation[0]}\n\n{text_all[i][0]}',
                                   reply_markup=InlineKeyboardMarkup(resize_keyboard=True, selective=True).add(
                                       InlineKeyboardButton('Редактировать',
                                                            callback_data=f'c_edit_homework_1 {id_of_homework[0]}')))
        elif user_status == 1:
            await bot.send_message(user_id,
                                   text=f'\n\n Задание по {homework} от {date_of_creation[0]}\n\n{text_all[i][0]}',
                                   reply_markup=InlineKeyboardMarkup(resize_keyboard=True, selective=True).add(
                                       InlineKeyboardButton))
    #     todo
    # сделать так, чтобы можно было лично для себя отмечать сделанные дз (это можно реализовать по уникальному id дз)
    # у дз сделать строку в бд, в которой будет количество людей, кто выполнил это дз, и типо если количество
    #  будет совпадать с количеством людей в группе, то все чистить и дз, и id
    conn.close()


async def f_homework_edit_1(id_of_homework, user_id):  # todo
    await bot.send_message(user_id, f'{id_of_homework[0]}')


@dp.message_handler(state='s_add_homework_1')  # todo надо доделать
async def homework_step_1(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['class'] = message.text


async def f_timetable_today(user_id, course, today, week_count):
    day = d.isoweekday(today)
    url = 'https://lks.bmstu.ru/schedule/list'
    b = bs(get(url).text, 'lxml').find_all('a', class_="btn btn-primary col-1 rounded schedule-indent")
    status = 0
    for i in b:
        if i.get_text(strip=True) == course:
            status = 1
            url = 'https://lks.bmstu.ru/' + i.get('href')
            match day:
                case 1:
                    day = 'ПН'
                case 2:
                    day = 'ВТ'
                case 3:
                    day = 'СР'
                case 4:
                    day = 'ЧТ'
                case 5:
                    day = 'ПТ'
                case 6:
                    day = 'СБ'
                case 7:
                    break
            b = bs(get(url).text, 'lxml').find(string=day).find_parent('table').find_all('tr')
            string_build = f"🗓    {day}    🗓\n\n"
            for i, j in enumerate(b, start=1):
                if i >= 3:
                    a = j.find('span')
                    if (a is not None) and (week_count == 0):  # числитель
                        if (a.find_parent('td', class_='text-info-bold')) or (a.find_parent('td', colspan='2')):
                            string_build += f"""🕰  {j.find('td', class_='bg-grey text-nowrap').text}\n{a.text}\n\n"""
                    elif (a is not None) and (week_count == 1):  # знаменатель
                        if (a.find_parent('td', class_='text-primary')) or (a.find_parent('td', colspan='2')):
                            string_build += f"""🕰  {j.find('td', class_='bg-grey text-nowrap').text}\n{a.text}\n\n"""
            key_menu = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
            b_back = InlineKeyboardButton('🏡 Главное меню', callback_data=f'c_back_to_menu')
            key_menu.add(b_back)
            await bot.send_message(user_id, f"{string_build}", reply_markup=key_menu)
            break
    if status == 0:
        await bot.send_message(user_id, 'вы забанены')


async def f_admin_panel_main(user_id, username):
    user_status = await f_user_verify(user_id, username, ' ')
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_kol = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    key_admin_panel = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
    b_search_user = InlineKeyboardButton('🔎 Поиск юзеров', callback_data='c_search_users')
    b_add_user = InlineKeyboardButton('➕ Добавить юзера', callback_data='c_add_user')
    b_back = InlineKeyboardButton('🏡 Главное меню', callback_data=f'c_back_to_menu')
    key_admin_panel.add(b_search_user)
    key_admin_panel.add(b_add_user)
    key_admin_panel.add(b_back)
    if user_status >= 5:
        await bot.send_message(user_id, "⚜   ——— <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b> ———   ⚜️" +
                               f"\n\nПользователей в боте: {str(user_kol)}", reply_markup=key_admin_panel)
    conn.close()


@dp.message_handler(state=Form.s_add_user)
async def f_add_user(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_user_id'] = message.text
    await message.answer("Введите ФИО")
    await Form.next()


@dp.message_handler(state=Form.s_add_user_2)
async def f_add_user_2(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_user_FIO'] = message.text
    await message.answer("Введите курс (группу (полное наименование))")
    await Form.next()


@dp.message_handler(state=Form.s_add_user_3)
async def f_add_user_3(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_user_course'] = message.text.upper()
    await message.answer("Подписка?"
                         "\n<code>0</code> - Нет подписки"
                         "\n<code>1</code> - Подписка активна")
    await Form.next()


@dp.message_handler(state=Form.s_add_user_4)
async def f_add_user_4(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_user_sub'] = message.text
        if data['add_user_sub'] == "1":
            await message.answer("До какого подписка? (пример: <code>2022-09-01</code>)")
            await Form.next()
        elif data['add_user_sub'] == "0":
            data['add_user_sub_date'] = 0
            await message.answer(f"Введите статус: "
                                 f"\n0 - ⛔ Бан"
                                 f"\n1 - 👨‍🎓 Студент"
                                 f"\n2 - 😎Ответственный"
                                 f"\n3 - 💃 Староста"
                                 f"\n4 - 👨‍🏫 Преподаватель")
            await Form.s_add_user_6.set()


@dp.message_handler(state=Form.s_add_user_5)
async def f_add_user_5(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if data['add_user_sub'] == '1':
            data['add_user_sub_date'] = message.text
            await message.answer(f"Введите статус: "
                                 f"\n0 - ⛔ Бан"
                                 f"\n1 - 👨‍🎓 Студент"
                                 f"\n2 - 😎Ответственный"
                                 f"\n3 - 💃 Староста"
                                 f"\n4 - 👨‍🏫 Преподаватель")

        await Form.next()


@dp.message_handler(state=Form.s_add_user_6)
async def f_add_user_6(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_user_status'] = message.text
        markup = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add(InlineKeyboardButton('Сохранить', callback_data=f'c_add_user_true {1}'))
        markup.add(InlineKeyboardButton('Отменить', callback_data=f'c_add_user_true {0}'))
        await message.answer("Проверьте введенную информацию:"
                             f"\n\n<b> ID:</b> {data['add_user_id']}"
                             f"\n<b> FIO:</b> {data['add_user_FIO']}"
                             f"\n<b> Course:</b> {data['add_user_course']}"
                             f"\n<b> Sub:</b> {int(data['add_user_sub'])}"
                             f"\n<b> Sub date:</b> {data['add_user_sub_date']}"
                             f"\n<b> Status:</b> {int(data['add_user_status'])}",
                             reply_markup=markup)


async def f_add_user_true(user_id, state: FSMContext):
    async with state.proxy() as data:
        conn = sqlite3.connect('db.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (user_id, username, FIO, course, sub, sub_date, status) '
                       'VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (data['add_user_id'], None, data['add_user_FIO'], data['add_user_course'],
                        data['add_user_sub'], data['add_user_sub_date'],
                        data['add_user_status']))  # добавление новой строки в бд
        conn.commit()
        await bot.send_message(user_id, '✅ Сохранено!'
                                        f"\n\n<b> ID:</b> {data['add_user_id']}"
                                        f"\n<b> FIO:</b> {data['add_user_FIO']}"
                                        f"\n<b> Course:</b> {data['add_user_course']}"
                                        f"\n<b> Sub:</b> {data['add_user_sub']}"
                                        f"\n<b> Sub date:</b> {int(data['add_user_sub_date'])}"
                                        f"\n<b> Status:</b> {int(data['add_user_status'])}")
        conn.close()
    await state.reset_data()
    await state.finish()


async def f_starosta_main_page_1(user_id, username):
    user_status = await f_user_verify(user_id, username, ' ')
    if user_status == 3 or user_status >= 5:
        await f_starosta_main_page(user_status, user_id)


async def f_starosta_main_page(user_status, user_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_course = cursor.execute(f"SELECT course FROM users WHERE user_id='{user_id}'").fetchone()[0]
    students_course_kol = cursor.execute(f"SELECT COUNT(*) FROM users WHERE course = '{user_course}'").fetchone()[0]
    if user_status == 3 or user_status >= 5:
        key_starosta_main_page = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
        b_starosta_user_info = InlineKeyboardButton('⬇   ——— Студенты ———   ⬇', callback_data='pass')
        b_starosta_user_back = InlineKeyboardButton('⬇   ——— Главное меню ———    ⬇', callback_data='pass')
        b_back = InlineKeyboardButton('🏡 Главное меню', callback_data=f'c_back_to_menu')
        b_starosta_announcment = InlineKeyboardButton('❗ Сделать объявление', callback_data=f'c_starosta {1}')
        b_starosta_poll = InlineKeyboardButton('📊 Создать опрос группы', callback_data=f'c_starosta {2}')
        b_starosta_search_user = InlineKeyboardButton('️🔎 Отметить (не сделано)', callback_data=f'c_starosta {3}')
        b_starosta_add_user = InlineKeyboardButton('➕ Добавить (не сделано)', callback_data=f'c_starosta {4}')
        b_starosta_del_user = InlineKeyboardButton('🗑 Удалить (не сделано)', callback_data=f'c_starosta {5}')
        # todo надо добавить назначение ответственных за дз

        key_starosta_main_page.add(b_starosta_user_info)
        key_starosta_main_page.add(b_starosta_announcment, b_starosta_poll)
        key_starosta_main_page.add(b_starosta_search_user, b_starosta_add_user, b_starosta_del_user)
        key_starosta_main_page.add(b_starosta_user_back)
        key_starosta_main_page.add(b_back)

        await bot.send_message(user_id, "💃 <b>Панель старосты</b> 💃"
                                        f"\n\n◾️ <b>Студентов в группе:</b> <code>{str(students_course_kol)}</code>",
                               reply_markup=key_starosta_main_page)


async def f_starosta_main_page_2(user_id, reply):
    key_starosta = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
    b_starosta_cancel = InlineKeyboardButton('🔙 Вернуться', callback_data=f'c_starosta cancel')
    key_starosta.add(b_starosta_cancel)
    if reply == '1':  # обьявление
        await bot.send_message(user_id, 'Введите объявление', reply_markup=key_starosta)
        await Form.s_starosta_announcement.set()
    elif reply == '2':  # сделать опрос группы
        await bot.send_message(user_id, 'Назовите опрос')
        await Form.s_starosta_poll.set()
    elif reply == '3':  # отметить
        pass
    elif reply == '4':  # добавить
        pass
    elif reply == '5':  # удалить
        pass


@dp.message_handler(state=Form.s_starosta_announcement)  # объявление
async def f_starosta_announcement(announcement: Message, state: FSMContext):
    user_id = announcement.from_user.id
    announcement = announcement.text
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    course = cursor.execute(f"SELECT course FROM users WHERE user_id='{user_id}'").fetchone()[0]
    spisok_polupokerov = [int(x) for x in cursor.execute(f"SELECT user_id FROM users WHERE (course='{course}') AND (status > 0)").fetchall()]
    for i in spisok_polupokerov:
        if i != user_id:
            await bot.send_message(i, f'❗❗❗ Староста вещает ❗❗❗\n\n{announcement}')
        else:
            await f_starosta_main_page(user_id, user_id)
            await bot.send_message(user_id, f'✅  Сообщение было успешно доставлено.')
    # todo
    # сделать кнопку (закрепить?), если человек нажмет, то бот закрепит сообщение
    conn.close()
    await state.finish()


@dp.message_handler(state=Form.s_starosta_poll)  # опрос
async def f_starosta_poll(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        key_poll = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
        b_poll_1 = InlineKeyboardButton('Много вариантов ответа, анонимный', callback_data=f'c_poll {1}')
        b_poll_2 = InlineKeyboardButton('Много вариантов ответа', callback_data=f'c_poll {2}')
        b_poll_3 = InlineKeyboardButton('Анонимный', callback_data=f'c_poll {3}')
        b_poll_4 = InlineKeyboardButton('Просто опрос', callback_data=f'c_poll {4}')
        key_poll.row(b_poll_1, b_poll_2)
        key_poll.row(b_poll_3, b_poll_4)
        data['name'] = poll.text
        await bot.send_message(poll.from_user.id, "Выберете вид опроса", reply_markup=key_poll)


async def f_starosta_poll_1(user_id):
    await bot.send_message(user_id, f'Введите количество вариантов ответа 2-10')
    await Form.s_starosta_poll_2.set()


@dp.message_handler(state=Form.s_starosta_poll_2)
async def f_starosta_poll_2(poll: Message, state: FSMContext):
    user_id = poll.from_user.id
    try:
        c = int(poll.text)
        if (c < 11) and (c > 1):
            async with state.proxy() as data:
                data['integer'] = poll.text
            await bot.send_message(user_id, f'Введите вариант ответа')
            await Poll.poll_1.set()
        else:
            await bot.send_message(user_id, f'В опросе может быть 2-10 вариантов')
            await Form.s_starosta_poll_1.set()
            await f_starosta_poll_1(poll.from_user.id)
    except:
        await bot.send_message(user_id, 'Введите число')
        await Form.s_starosta_poll_1.set()
        await f_starosta_poll_1(poll.from_user.id)


@dp.message_handler(state=Poll.poll_1)
async def f_poll_1(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        data['poll'] = f'''{poll.text}'''
        await bot.send_message(user_id, text='Введите следующий вариант ответа')
        await Poll.poll_2.set()


@dp.message_handler(state=Poll.poll_2)
async def f_poll_2(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        if int(data['integer']) == 2:
            string = poll.text
            await Poll.poll_finish.set()
            await f_poll_finsh(string, dp.current_state(user=user_id))
        else:
            data['poll'] = f'''{data['poll']}@#$0192{poll.text}'''
            await bot.send_message(user_id, f'Введите следующий вариант ответа')
            await Poll.poll_3.set()


@dp.message_handler(state=Poll.poll_3)
async def f_poll_3(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        if int(data['integer']) == 3:
            string = poll.text
            await Poll.poll_finish.set()
            await f_poll_finsh(string, dp.current_state(user=user_id))
        else:
            data['poll'] = f'''{data['poll']}@#$0192{poll.text}'''
            await bot.send_message(user_id, f'Введите следующий вариант ответа')
            await Poll.poll_4.set()


@dp.message_handler(state=Poll.poll_4)
async def f_poll_4(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        if int(data['integer']) == 4:
            string = poll.text
            await Poll.poll_finish.set()
            await f_poll_finsh(string, dp.current_state(user=user_id))
        else:
            data['poll'] = f'''{data['poll']}@#$0192{poll.text}'''
            await bot.send_message(user_id, f'Введите следующий вариант ответа')
            await Poll.poll_5.set()


@dp.message_handler(state=Poll.poll_5)
async def f_poll_5(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        if int(data['integer']) == 5:
            string = poll.text
            await Poll.poll_finish.set()
            await f_poll_finsh(string, dp.current_state(user=user_id))
        else:
            data['poll'] = f'''{data['poll']}@#$0192{poll.text}'''
            await bot.send_message(user_id, f'Введите следующий вариант ответа')
            await Poll.poll_6.set()


@dp.message_handler(state=Poll.poll_6)
async def f_poll_6(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        if int(data['integer']) == 6:
            string = poll.text
            await Poll.poll_finish.set()
            await f_poll_finsh(string, dp.current_state(user=user_id))
        else:
            data['poll'] = f'''{data['poll']}@#$0192{poll.text}'''
            await bot.send_message(user_id, f'Введите следующий вариант ответа')
            await Poll.poll_7.set()


@dp.message_handler(state=Poll.poll_7)
async def f_poll_7(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        if int(data['integer']) == 7:
            string = poll.text
            await Poll.poll_finish.set()
            await f_poll_finsh(string, dp.current_state(user=user_id))
        else:
            data['poll'] = f'''{data['poll']}@#$0192{poll.text}'''
            await bot.send_message(user_id, f'Введите следующий вариант ответа')
            await Poll.poll_8.set()


@dp.message_handler(state=Poll.poll_8)
async def f_poll_8(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        if int(data['integer']) == 8:
            string = poll.text
            await Poll.poll_finish.set()
            await f_poll_finsh(string, dp.current_state(user=user_id))
        else:
            data['poll'] = f'''{data['poll']}@#$0192{poll.text}'''
            await bot.send_message(user_id, f'Введите следующий вариант ответа')
            await Poll.poll_9.set()


@dp.message_handler(state=Poll.poll_9)
async def f_poll_9(poll: Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = poll.from_user.id
        if int(data['integer']) == 9:
            string = poll.text
            await Poll.poll_finish.set()
            await f_poll_finsh(string, dp.current_state(user=user_id))
        else:
            data['poll'] = f'''{data['poll']}@#$0192{poll.text}'''
            await bot.send_message(user_id, f'Введите следующий вариант ответа')
            await Poll.poll_10.set()


@dp.message_handler(state=Poll.poll_10)
async def f_poll_10(poll: Message, state: FSMContext):
        string = poll.text
        await Poll.poll_finish.set()
        await f_poll_finsh(string, dp.current_state(user=poll.from_user.id))


async def f_poll_finsh(string, state: FSMContext):
    async with state.proxy() as data:
        b_cancel = InlineKeyboardButton('Отменить и вернуться в главное меню', callback_data='c_cancel')
        data['poll'] = data['poll'] + '@#$0192' + string
        a = data['poll'].split('@#$0192')
        user_id = data['user_id']
        match int(data['reply']):
            case 1:
                mes = await bot.send_poll(user_id, data['name'], a, is_anonymous=True, allows_multiple_answers=True)
            case 2:
                mes = await bot.send_poll(user_id, data['name'], a, is_anonymous=False, allows_multiple_answers=True)
            case 3:
                mes = await bot.send_poll(user_id, data['name'], a, is_anonymous=True, allows_multiple_answers=False)
            case 4:
                mes = await bot.send_poll(user_id, data['name'], a, is_anonymous=False, allows_multiple_answers=False)
        mes_id = mes.message_id
        b_yes = InlineKeyboardButton('💌 Отправить', callback_data=f'poll yes {mes_id}')
        b_no = InlineKeyboardButton('🔄 Заполнить заново', callback_data=f'poll no {mes_id}')
        key_poll_finish = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
        key_poll_finish.add(b_yes, b_no)
        key_poll_finish.add(b_cancel)
        await bot.send_message(user_id, '✍ Проверьте правильность заполнения', reply_markup=key_poll_finish)
        await state.reset_data()
        await state.finish()


# todo
# это для создания групп по интересам
# @dp.message_handler(commands=['test'])
# async def test(message: Message):
#     conn = sqlite3.connect('db.db')
#     user_id = message.from_user.id
#     cursor = conn.cursor()
#     check = cursor.execute('SELECT groups FROM users WHERE user_id='{user_id}'").fetchone()[0]
#     check = check.split('/split.,&!/')
#     if '1' in check:
#         print('ура, обьект найден')
#     await bot.send_message(user_id, f'{check}')
#     conn.close()

@dp.message_handler(state=Form.s_starosta_note_1)
async def f_starosta_note_1(message: Message, state: FSMContext):
    await message.answer("Напишите предмет на котором вы сейчас")
    # todo
    # надо будет сделать кнопочки как только разберусь как из парсера нормально забирать предметы
    # надо написать хрень, которая дает кнопки по расписанию на сегодня (типо все сегодняшние предметы)
    # старосте надо просто написать фамилию отсутствующего, если 2 или больше челов с одной фамилией, то кнопки выбора
    # потом три кнопки (отменить, сохранить, вернуться назад)
    # в бд заносить список людей, кто отсутствует
    # количество отсутствующих
    await Form.next()


@dp.message_handler(state=Form.s_starosta_note_2)
async def f_starosta_note_2(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['subject'] = message.text
        await message.answer("Напишите количество отсутствующих")
        await Form.next()


@dp.message_handler(state=Form.s_starosta_note_3)
async def f_starosta_note_3(message: Message, state: FSMContext):
    # todo
    async with state.proxy() as data:
        print(data['subject'])


@dp.callback_query_handler(lambda call: True, state='*')
async def query_handler(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    username = call.from_user.username

    if call.data.startswith('c_main'):
        reply = call.data.split(' ')[1]
        if reply == 'timetable':
            await f_timetable_page(user_id)
        elif reply == 'homework':
            await f_homework_panel_main_0(user_id, username)
        elif reply == 'account':
            await f_account_page(user_id, username)
        elif reply == 'admin':
            await f_admin_panel_main(user_id, username)  # todo
        elif reply == 'starosta':
            await f_starosta_main_page_1(user_id, username)

    elif call.data == 'c_back_to_menu':
        await start_message_1(user_id)

    elif call.data.startswith('c_timetable_now'):
        user_status = await f_user_verify(user_id, username, ' ')
        if user_status != 0:
            day_id = call.data.split(' ')[1]
            course = call.data.split(' ')[2]
            start_time = d(2022, 8, 29)
            today = d.today()
            tomorrow = d.today() + timedelta(days=1)
            if (day_id == "1") or (day_id == "2"):
                if day_id == "2":
                    week_count = ((abs(tomorrow - start_time)).days // 7 + 1) % 2
                    await f_timetable_today(user_id, course, tomorrow, week_count)
                else:
                    week_count = ((abs(today - start_time)).days // 7 + 1) % 2
                    await f_timetable_today(user_id, course, today, week_count)
            else:
                if d.isoweekday(d.today()) == 7:
                    week_count = ((abs(tomorrow - start_time)).days // 7 + 1) % 2
                else:
                    week_count = ((abs(today - start_time)).days // 7 + 1) % 2
                await f_timetable_week(user_id, course, week_count)
        else:
            pass

    elif call.data == 'c_add_user':
        user_status = await f_user_verify(user_id, username, ' ')
        if user_status >= 5:
            await call.message.answer("Введите ID")
            await Form.s_add_user.set()
        else:
            pass

    elif call.data == 'c_add_homework':
        await call.message.answer('Введите предмет')
        await Form.s_add_homework_1.set()

    elif call.data == 'c_show_homework':
        await f_homework_page(user_id)

    elif call.data.startswith('c_reference'):  # Это ссылка на редактирование дз
        reply = call.data.split(' ')[1]
        user_status = await get_user_status(user_id)
        if reply == 'next':
            page = 2
            await f_pagination(user_id, page, call.message.message_id)
        else:
            if user_status > 1:
                await f_homework_show(reply, user_id)

    elif call.data.startswith('c_pagination'):
        reply = call.data.split(' ')[1]
        if reply == 'back':
            page = int(call.data.split(' ')[2]) - 1
            await f_pagination(user_id, page, call.message.message_id)
        elif reply == 'next':
            page = int(call.data.split(' ')[2]) + 1
            await f_pagination(user_id, page, call.message.message_id)

    elif call.data.startswith('c_edit_homework_1'):  # редактирование дз
        id_of_homework = call.data.split(' ')[1]
        await f_homework_edit_1(id_of_homework, user_id)

    elif call.data == 'c_search_user':  # НЕДОДЕЛАНО, ТУТ НАДА ДОБАВЛЕНИЕ, УДАЛЕНИЕ И РЕДАКТИРОВАНИЕ УЧАСТНИКОВ ГРУППЫ
        #  todo
        pass

    elif call.data == 'c_next':
        await bot.send_message(call.message.chat.id, text=f'ты дурак :)\n\nдобавь сюда что-то (колбек _next)')

    elif call.data.startswith('c_poll'):
        reply = call.data.split(' ')[1]
        async with state.proxy() as data:
            data['reply'] = reply
            data['user_id'] = user_id
            await Form.s_starosta_poll_1.set()
            await f_starosta_poll_1(user_id)

    elif call.data.startswith('poll'):
        reply = call.data.split(' ')[1]
        if reply == 'yes':
            message_id = int(call.data.split(' ')[2])
            conn = sqlite3.connect('db.db')
            cursor = conn.cursor()
            course = cursor.execute(f"SELECT course FROM users WHERE user_id='{user_id}'").fetchone()[0]
            spisok_polupokerov = [int(x[0]) for x in cursor.execute(f"SELECT user_id FROM users WHERE course='{course}'").fetchall()]
            k = 0
            for i in spisok_polupokerov:
                if i != user_id:
                    try:
                        await bot.forward_message(i, user_id, message_id, protect_content=True)
                        k += 1
                    except:
                        pass
            await bot.send_message(call.from_user.id, f'Успешно доставлено {k} людям')
            conn.close()
        elif reply == 'no':
            key_starosta = InlineKeyboardMarkup(resize_keyboard=True, selective=True)
            b_starosta_cancel = InlineKeyboardButton('🔙 Вернуться', callback_data=f'c_starosta cancel')
            key_starosta.add(b_starosta_cancel)
            await bot.send_message(user_id, 'Назовите опрос', reply_markup=key_starosta)
            await Form.s_starosta_poll.set()

    elif call.data == 'c_cancel':
        await dp.current_state(user=user_id).reset_data()
        await dp.current_state(user=user_id).finish()
        await start_message_1(user_id)

    elif call.data.startswith('c_starosta'):
        reply = call.data.split(' ')[1]
        user_status = await f_user_verify(user_id, username, ' ')
        if user_status >= 3:
            if reply == 'cancel':
                await dp.current_state(user=user_id).reset_data()
                await dp.current_state(user=user_id).finish()
                await bot.answer_callback_query(call.id, 'Отменено успешно', show_alert=False)
                await f_starosta_main_page(user_status, user_id)
            else:
                await f_starosta_main_page_2(user_id, reply)

    elif call.data.startswith('c_add_user_true'):
        user_id = call.from_user.id
        dati = call.data.split(' ')[1]
        if dati == '0':
            await dp.current_state(user=user_id).reset_data()
            await dp.current_state(user=user_id).finish()
            await bot.answer_callback_query(call.id, 'Отменено успешно', show_alert=False)
        else:
            await f_add_user_true(user_id, dp.current_state(user=user_id))

    elif call.data == 'c_user_setting':
        await bot.answer_callback_query(call.id, 'Данная функция находится в разработке')
        await start_message_1(user_id)

    elif call.data == 'c_user_delete':
        await f_user_delete_true(user_id)

    elif call.data.startswith('c_user_delete_true'):
        reply = call.data.split(' ')[1]
        if reply == '1':
            await bot.answer_callback_query(call.id, 'Аккаунт удален успешно')
            conn = sqlite3.connect('db.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM users WHERE user_id={user_id}')
            conn.commit()
            conn.close()
        else:
            await start_message_1(user_id)

    await f_delete_this_message(call.message)

# А эта движуха отслеживает ошибки и не дает боту упасть, если будет ошибка отправит ее в чат архива
while True:
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as errors_logging:
        bot.send_message(config.archive_chat_id, "‼️ОШИБКА‼️" +
                         "\n\nТекст ошибки: " + str(errors_logging))
        print(errors_logging)
        pass
