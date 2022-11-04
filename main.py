import logging
import fake_useragent
import time
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import math
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
import requests
import config
from bs4 import BeautifulSoup as bs
import datetime
from datetime import date as d
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
    s_add_homework_1 = State()
    s_starosta_note_1 = State()
    s_starosta_note_2 = State()
    s_starosta_note_3 = State()


async def f_delete_this_message(message):
    await bot.delete_message(message.chat.id, message.message_id)

async def get_user_status(user_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_status = cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,)).fetchone()[0]
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
            if message.text == '/start':
                await start_message_1(user_id, username)
            print("Проверка завершена! Пользователь одобрен ✅️!")
            return user_status
    conn.close()


@dp.message_handler(state=Form.s_username)
async def f_username(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['username'] = message.text
    await Form.next()
    await message.reply(f"<b>Введите пароль</b>")


@dp.message_handler(state=Form.s_password)
async def f_password(message: types.Message, state: FSMContext):
    async with state.proxy() as datas:
        ans = await bot.send_message(chat_id=message.chat.id, text='Загрузка...')
        datas['password'] = message.text
        url = 'https://lks.bmstu.ru/portal3/login?back=https://lks.bmstu.ru/portfolio'
        data = {
            'username': datas['username'],
            'password': datas['password'],
            '_eventId': 'submit'
        }
        s = requests.Session()
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
            # DOB = info[1].text
            # education_level = info[2].text
            course = info[3].text
            conn = sqlite3.connect('db.db', check_same_thread=False)
            cursor = conn.cursor()
            user_id = message.from_user.id
            username = message.from_user.username
            cursor.execute('INSERT INTO users (user_id, username, FIO, course, sub, sub_date, status, login, password) '
                           'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (user_id, username, name, course,
                            0, None, 1, datas['username'], datas['password']))
            await bot.edit_message_text(text='🏅  Вы успешно зарегистрированы  🏅', message_id=ans.message_id,
                                        chat_id=message.chat.id)
            conn.commit()
            conn.close()
            await state.reset_data()
            await state.finish()
            await start_message_1(user_id, username)
        except Exception as E:
            await bot.send_message(config.archive_chat_id,
                                   f'у вас ошибка блять *{E}* вот такая, иди исправляй сука тварь падла мразь')
            print(traceback.print_exc())
            await bot.send_message(message.chat.id,
                                   'Ты ввел неверный логин или пароль\n\nЕсли такая хрень написалась после успешной регистрации, то бля, не поленись и скинь мне че ты ввел')
            await state.reset_data()
            await state.finish()
            await f_user_verify(message.from_user.id, message.from_user.username, message)


@dp.message_handler(commands=['getmyid'])
async def getmyidbroshka(message):
    await message.answer(f"Твой айди: {message.from_user.id}")


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await f_user_verify(message.from_user.id, message.from_user.username, message)


async def start_message_1(user_id, username):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_status = await get_user_status(user_id)
    if user_status == 0:
        await bot.send_message(user_id, f'⛔️ ВЫ ЗАБАНЕНЫ'
                             f'\n\n   Ну а если вы просто не зарегистрированы, то обратитесь к старосте группы')
    elif user_status >= 1:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        info = cursor.fetchone()
        FIO = info[3]
        course = info[4]
        sub = info[5]
        sub_date = info[6]
        rez = cursor.execute("SELECT course FROM courses WHERE course=?", (course,)).fetchall()
        if not rez:
            cursor.execute(f'''INSERT INTO courses (course) VALUES ('{course}')''')
            conn.commit()
        key_start_message = InlineKeyboardMarkup()  # объявление клавиатуры
        b_timetable_today = InlineKeyboardButton('📆🟠 на сегодня', callback_data=f'c_timetable_now {1} {course}')
        b_timetable_tomorrow = InlineKeyboardButton('📆🟢 на завтра', callback_data=f'c_timetable_now {2} {course}')
        b_timetable_week = InlineKeyboardButton('📆🟣 на неделю', callback_data=f'c_timetable_now {3} {course}')
        b_setting = InlineKeyboardButton('⚙️ Настройки (не ворк)', callback_data='c_user_setting')
        key_start_message.row(b_timetable_today, b_timetable_tomorrow)  # добавление кнопки в клавиатуру
        key_start_message.row(b_timetable_week)
        key_start_message.row(b_setting)
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
async def f_timetable_week(message: types.Message, course, week_count):  # парсер расписания на неделю
    url = 'https://lks.bmstu.ru/schedule/list'
    b = bs(requests.get(url).text, 'lxml').find_all('a', class_="btn btn-primary text-nowrap")
    status = 0
    for i in b:
        if i.get_text(strip=True) == course:
            status = 1
            url = 'https://lks.bmstu.ru/' + i.get('href')
            b = bs(requests.get(url).text, 'lxml').find_all('div', class_='col-md-6 hidden-xs')
            string_build = "\n"
            for l, n in enumerate(b, start=1):
                if l >= 2:
                    string_build += f'—————————————————————————\n\n'
                string_build += f'''🗓    {n.find('strong').text}    🗓\n\n\n'''
                y = n.find_all('tr')
                for i, j in enumerate(y, start=1):
                    if i >= 3:
                        a = j.find('span')
                        if (a is not None) and (week_count == 0):
                            if (a.find_parent('td', class_='text-info')) or (a.find_parent('td', colspan='2')):
                                string_build += f"""🕰  {j.find('td', class_='bg-grey text-nowrap').text}\n{a.text}\n\n"""
                        if (a is not None) and (week_count == 1):
                            if (a.find_parent('td', class_='text-success')) or (a.find_parent('td', colspan='2')):
                                string_build += f"""🕰  {j.find('td', class_='bg-grey text-nowrap').text}\n{a.text}\n\n"""
            await message.answer(f"{string_build}")
            break

    if status == 0:
        await message.answer('\nОбратитесь к слабому создателю этого слабого бота (@m3k_unique)'
                             '\n\nНу и подпишитесь на мой канал @m3k_channel')


@dp.message_handler(commands=['homework'])
async def f_homework_panel_main_1(message: types.Message):
    await f_homework_panel_main(message)


async def f_homework_panel_main(message: types.Message):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_id = message.from_user.id
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))  # получаем статус из бд
    user_status = cursor.fetchone()[0]
    cursor.execute("SELECT course FROM users WHERE user_id=?", (user_id,))  # получаем группу
    course = cursor.fetchone()[0]
    homework_kol = cursor.execute("SELECT COUNT(*) FROM homework WHERE course=?", (course,)).fetchone()[0]
    if user_status >= 2:
        key_homework_panel = InlineKeyboardMarkup()
        b_add_homework = InlineKeyboardButton('Добавить домашнее задание', callback_data='c_add_homework')
        b_edit_homework = InlineKeyboardButton('Редактировать существующие', callback_data='c_edit_homework')
        b_check_homework = InlineKeyboardButton('Посмотреть домашнее задание', callback_data='c_check_homework')
        key_homework_panel.add(b_add_homework, b_edit_homework)
        key_homework_panel.add(b_check_homework)
        await message.answer("📔️   --- <b>ПАНЕЛЬ ДОМАШКИ</b> ---   📔️" +
                             f"\nДомашки в вашей группе: {str(homework_kol)}", reply_markup=key_homework_panel)
    elif user_status == 1:
        key_homework_panel = InlineKeyboardMarkup()
        b_check_homework = InlineKeyboardButton('Посмотреть домашнее задание', callback_data='c_check_homework')
        key_homework_panel.add(b_check_homework)
    else:
        await bot.send_message(message.chat.id, text='У вас недостаточно прав для просмотра команды')
    conn.close()


async def f_homework_edit(user_id, chat_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT course FROM users WHERE user_id=?", (user_id,))  # получаем группу
    course = cursor.fetchone()[0]
    cursor.execute("SELECT class FROM homework WHERE course=?", (course,))  # получаем все названия
    names_all = cursor.fetchall()
    names = []
    for i in names_all:
        if i[0] not in names:
            names.append(i[0])
    key_list_panel = InlineKeyboardMarkup()
    spisok = {j:InlineKeyboardButton(f'{i}', callback_data=f'c_reference {i}') for j, i in enumerate(names, start=1)}
    if len(spisok) > 5:
        key_list_panel.add(spisok[1],spisok[2],spisok[3])
        key_list_panel.add(spisok[4],spisok[5])
        key_list_panel.add(InlineKeyboardButton(f'Показать остальные дз', callback_data='c_next'))
        for i in range(1,6):
            spisok.pop(i)
    elif len(spisok) == 5:
        key_list_panel.add(spisok[1], spisok[2], spisok[3])
        key_list_panel.add(spisok[4], spisok[5])
    else:
        for i in range(1, len(spisok)+1):
            key_list_panel.add(spisok[i])
    #     todo
    # сделать показ остальных дз
    await bot.send_message(chat_id=chat_id, text='Выберете домашнее задание для редактирования',
                           reply_markup=key_list_panel)
    conn.close()


async def f_homework_edit_1(homework, user_id, chat_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT course FROM users WHERE user_id=?", (user_id,))  # получаем группу
    course = cursor.fetchone()[0]
    cursor.execute(
        f"SELECT text FROM homework WHERE (course LIKE '%{course}%') AND (class LIKE '%{homework}%')  ")  # текст дз
    text_all = cursor.fetchall()
    date_of_creation = cursor.execute(
        f"SELECT date_of_creation FROM homework WHERE (course LIKE '%{course}%') AND (class LIKE '%{homework}%')").fetchone()
    for i in range(len(text_all)):
        id_of_homework = cursor.execute(
            f"SELECT id FROM homework WHERE (course LIKE '%{course}%') AND (text LIKE '%{text_all[i][0]}%')").fetchone()
        await bot.send_message(chat_id, text=f'\n\n Задание по {homework} от {date_of_creation[0]}\n\n{text_all[i][0]}',
                               reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Редактировать',callback_data=f'c_edit_homework_1 {id_of_homework[0]}')))
    #     todo
    # сделать так, чтобы можно было лично для себя отмечать сделанные дз (это можно реализовать по уникальному id дз)
    # у дз сделать строку в бд, в которой будет количество людей, кто выполнил это дз, и типо если количество
    #  будет совпадать с количеством людей в группе, то все чистить и дз, и id
    conn.close()


async def f_homework_edit_2(id_of_homework, user_id, chat_id):
    await bot.send_message(chat_id, f'{id_of_homework[0]}')


@dp.message_handler(state='s_add_homework_1')  # надо доделать
async def homework_step_1(message: types.Message, state: FSMContext):
    with state.proxy() as data:
        data['class'] = message.text


async def f_timetable_today(message: types.Message, course, day_id, today, week_count):
    if day_id == '1':
        today = d.isoweekday(today)
    else:
        today = d.isoweekday(today) + 1
    url = 'https://lks.bmstu.ru/schedule/list'
    b = bs(requests.get(url).text, 'lxml').find_all('a', class_="btn btn-primary text-nowrap")
    status = 0
    for i in b:
        if i.get_text(strip=True) == course:
            status = 1
            url = 'https://lks.bmstu.ru/' + i.get('href')
            match today:
                case 1:
                    today = 'ПН'
                case 2:
                    today = 'ВТ'
                case 3:
                    today = 'СР'
                case 4:
                    today = 'ЧТ'
                case 5:
                    today = 'ПТ'
                case 6:
                    today = 'СБ'
                case 7:
                    break
            b = bs(requests.get(url).text, 'lxml').find(string=today).find_parent('table').find_all('tr')
            string_build = f"🗓    {today}    🗓\n\n"
            for i, j in enumerate(b, start=1):
                if i >= 3:
                    a = j.find('span')
                    if (a is not None) and (week_count == 0):
                        if (a.find_parent('td', class_='text-info')) or (a.find_parent('td', colspan='2')):
                            string_build += f"""🕰  {j.find('td', class_='bg-grey text-nowrap').text}\n{a.text}\n\n"""
                    elif (a is not None) and (week_count == 1):
                        if (a.find_parent('td', class_='text-success')) or (a.find_parent('td', colspan='2')):
                            string_build += f"""🕰  {j.find('td', class_='bg-grey text-nowrap').text}\n{a.text}\n\n"""
            await message.answer(f"{string_build}")
            break
    if status == 0:
        await message.answer(('\n\nЕсли все правильно, то обратитесь к создателю бота (ссылка на профиль в статусе)'))


@dp.message_handler(commands=['admin'])
async def f_admin_panel_main_1(message: types.Message):
    await f_admin_panel_main(message)  # я сделал это заранее, так надо, если захочешь узнать, спросишь


async def f_admin_panel_main(message: types.Message):
    user_id = message.from_user.id
    user_status = await f_user_verify(user_id, message.from_user.username, message)
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_kol = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    key_admin_panel = InlineKeyboardMarkup()
    b_search_user = InlineKeyboardButton('Поиск юзеров', callback_data='c_search_users')
    b_add_user = InlineKeyboardButton('Добавить юзера', callback_data='c_add_user')
    key_admin_panel.add(b_search_user)
    key_admin_panel.add(b_add_user)
    if user_status >= 5:
        await message.answer("⚜️--- <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b> ---⚜️" +
                             f"\nПользователей в боте: {str(user_kol)}", reply_markup=key_admin_panel)
    conn.close()


@dp.message_handler(state=Form.s_add_user)
async def f_add_user(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_user_id'] = message.text
    await message.answer("Введите ФИО")
    await Form.next()


@dp.message_handler(state=Form.s_add_user_2)
async def f_add_user_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_user_FIO'] = message.text
    await message.answer("Введите курс (группу (полное наименование))")
    await Form.next()


@dp.message_handler(state=Form.s_add_user_3)
async def f_add_user_3(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['add_user_course'] = message.text.upper()
    await message.answer("Подписка?"
                         "\n<code>0</code> - Нет подписки"
                         "\n<code>1</code> - Подписка активна")
    await Form.next()


@dp.message_handler(state=Form.s_add_user_4)
async def f_add_user_4(message: types.Message, state: FSMContext):
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
async def f_add_user_5(message: types.Message, state: FSMContext):
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
async def f_add_user_6(message: types.Message, state: FSMContext):
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


async def f_add_user_true(dati, chat_id, state: FSMContext):
    async with state.proxy() as data:
        if dati == '0':
            await bot.send_message(chat_id, 'Отменено успешно')
        else:
            conn = sqlite3.connect('db.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (user_id, username, FIO, course, sub, sub_date, status) '
                           'VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (data['add_user_id'], None, data['add_user_FIO'], data['add_user_course'],
                            data['add_user_sub'], data['add_user_sub_date'],
                            data['add_user_status']))  # добавление новой строки в бд
            conn.commit()
            await bot.send_message(chat_id, '✅ Сохранено!'
                                            f"\n\n<b> ID:</b> {data['add_user_id']}"
                                            f"\n<b> FIO:</b> {data['add_user_FIO']}"
                                            f"\n<b> Course:</b> {data['add_user_course']}"
                                            f"\n<b> Sub:</b> {data['add_user_sub']}"
                                            f"\n<b> Sub date:</b> {int(data['add_user_sub_date'])}"
                                            f"\n<b> Status:</b> {int(data['add_user_status'])}")
            conn.close()
    await state.finish()


@dp.message_handler(commands=['starosta'])
async def f_starosta_main_page_1(message: types.Message):
    user_status = await f_user_verify(message.from_user.id, message.from_user.username, message)
    if user_status == 3 or user_status >= 5:
        await f_starosta_main_page(user_status, message.from_user.id)


async def f_starosta_main_page(user_status, user_id):
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    user_course = cursor.execute("SELECT course FROM users WHERE user_id=?", (user_id,)).fetchone()[0]
    students_course_kol = cursor.execute(f"SELECT COUNT(*) FROM users WHERE course = '{user_course}'").fetchone()[0]
    if user_status == 3 or user_status >= 5:
        key_starosta_main_page = InlineKeyboardMarkup()
        b_starosta_user_info = InlineKeyboardButton('⬇️ ---Студенты--- ⬇️', callback_data='pass')
        b_start_menu = InlineKeyboardButton('🏡 Главное меню', callback_data=f'c_starosta {0}')
        b_starosta_announcment = InlineKeyboardButton('❗ Сделать объявление', callback_data=f'c_starosta {1}')
        b_starosta_search_user = InlineKeyboardButton('️🔎 Отметить (не сделано)', callback_data=f'c_starosta {2}')
        b_starosta_add_user = InlineKeyboardButton('➕ Добавить (не сделано)', callback_data=f'c_starosta {3}')
        b_starosta_del_user = InlineKeyboardButton('🗑 Удалить (не сделано)', callback_data=f'c_starosta {4}')
        # сюда надо добавить отметки присутствующих
        # todo

        key_starosta_main_page.add(b_starosta_announcment)
        key_starosta_main_page.add(b_starosta_user_info)
        key_starosta_main_page.add(b_starosta_search_user, b_starosta_add_user, b_starosta_del_user)
        key_starosta_main_page.add(b_start_menu)

        await bot.send_message(user_id, "💃 <b>Панель старосты</b> 💃"
                             f"\n\n◾️ <b>Студентов в группе:</b> <code>{str(students_course_kol)}</code>",
                             reply_markup=key_starosta_main_page)


async def f_starosta_main_page_2(user_id, reply):
    if reply == '1':  # обьявление
        key_cancel = InlineKeyboardMarkup()
        b_starosta_cancel = InlineKeyboardButton('🔙 Вернуться', callback_data=f'c_starosta cancel')
        key_cancel.add(b_starosta_cancel)
        await bot.send_message(user_id, 'Напишите объявление которое вы хотите сделать', reply_markup=key_cancel)
        await Form.s_starosta_announcement.set()
    elif reply == '2':  # отметить
        await Form.s_starosta_note_1.set()
    elif reply == '3':  # добавить
        pass
    elif reply == '4':  # удалить
        pass


@dp.message_handler(state=Form.s_starosta_announcement)
async def f_starosta_announcement(announcement: types.Message, state: FSMContext):
    user_id = announcement.from_user.id
    announcement = announcement.text
    conn = sqlite3.connect('db.db', check_same_thread=False)
    cursor = conn.cursor()
    course = cursor.execute('SELECT course FROM users WHERE user_id =?', (user_id,)).fetchone()[0]
    spisok_polupokerov = cursor.execute('SELECT user_id FROM users WHERE course =? AND status > 0',
                                        (course,)).fetchall()
    for i in spisok_polupokerov:
        if i[0] == user_id:
            await bot.send_message(user_id, f'✅  Сообщение было успешно доставлено.')
            await f_starosta_main_page(user_id, user_id)
        else:
            pass
            # todo тут просто надо раскомментировать при запуске бота
            # await bot.send_message(i[0], f'❗❗❗ Староста вещает ❗❗❗\n\n{announcement}')
    # todo
    # сделать кнопку (закрепить?), если человек нажмет, то бот закрепит сообщение
    conn.close()
    await state.finish()


# todo
# это для создания групп по интересам
# @dp.message_handler(commands=['test'])
# async def test(message: types.Message):
#     conn = sqlite3.connect('db.db')
#     user_id = message.from_user.id
#     cursor = conn.cursor()
#     check = cursor.execute('SELECT groups FROM users WHERE user_id =?', (user_id,)).fetchone()[0]
#     check = check.split('/split.,&!/')
#     if '1' in check:
#         print('ура, обьект найден')
#     await bot.send_message(user_id, f'{check}')
#     conn.close()


@dp.message_handler(state=Form.s_starosta_note_1)
async def f_starosta_note_1(message: types.Message, state: FSMContext):
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
async def f_starosta_note_2(message: types.Message, state: FSMContext):
    with state.proxy() as data:
        data['subject'] = message.text
        await message.answer("Напишите количество отсутствующих")
        await Form.next()


@dp.message_handler(state=Form.s_starosta_note_3)
async def f_starosta_note_3(message: types.Message, state: FSMContext):
    # todo
    with state.proxy() as data:
        print(data['subject'])


@dp.callback_query_handler(lambda call: True, state='*')
async def query_handler(query: types.CallbackQuery):
    if query.data.startswith('c_timetable_now'):
        user_status = await f_user_verify(query.from_user.id, query.from_user.username, query.message)
        if user_status != 0:
            day_id = query.data.split(' ')[1]
            course = query.data.split(' ')[2]
            start_time = d(2022, 8, 29)
            today = d.today()
            week_count = ((abs(today - start_time)).days // 7 + 1) % 2
            if (day_id == "1") or (day_id == "2"):
                await f_timetable_today(query.message, course, day_id, today, week_count)
            else:
                await f_timetable_week(query.message, course, week_count)
            await f_delete_this_message(query.message)
        else:
            pass

    elif query.data == 'c_add_user':
        user_status = await f_user_verify(query.from_user.id, query.from_user.username, query.message)
        if user_status >= 5:
            await f_delete_this_message(query.message)
            await query.message.answer("Введите ID")
            await Form.s_add_user.set()
        else:
            pass

    elif query.data == 'c_add_homework':
        await query.message.answer('Введите предмет')
        await f_delete_this_message(query.message)
        await Form.s_add_homework_1.set()

    elif query.data == 'c_edit_homework':

        await f_delete_this_message(query.message)
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        await f_homework_edit(user_id, chat_id)

    elif query.data.startswith('c_reference'):  # Это ссылка на редактирование дз
        await f_delete_this_message(query.message)
        homework = query.data.split(' ')[1]
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        await f_homework_edit_1(homework, user_id, chat_id)

    elif query.data.startswith('c_edit_homework_1'):  # редактирование дз
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        await f_delete_this_message(query.message)
        id_of_homework = query.data.split(' ')[1]
        await f_homework_edit_2(id_of_homework, user_id, chat_id)

    elif query.data == 'c_search_user':  # НЕДОДЕЛАНО, ТУТ НАДА ДОБАВЛЕНИЕ, УДАЛЕНИЕ И РЕДАКТИРОВАНИЕ УЧАСТНИКОВ ГРУППЫ
        #  todo
        pass

    elif query.data == 'c_next':
        await bot.send_message(query.message.chat.id, text=f'ты дурак :)\n\nдобавь сюда что-то (колбек _next)')

    elif query.data.startswith('c_starosta'):
        reply = query.data.split(' ')[1]
        user_id = query.from_user.id
        username = query.from_user.username
        user_status = await f_user_verify(user_id, username, query.message)
        if user_status >= 3:
            if reply == '0':
                await start_message_1(user_id, username)
                await f_delete_this_message(query.message)
            elif reply == 'cancel':
                user_id = query.from_user.id
                user_status = await get_user_status(user_id)
                await dp.current_state(user=user_id).finish()
                await f_starosta_main_page(user_status, query.from_user.id)
                await f_delete_this_message(query.message)
            else:
                await f_starosta_main_page_2(query.from_user.id, reply)
                await f_delete_this_message(query.message)

    elif query.data.startswith('c_add_user_true'):
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        await f_delete_this_message(query.message)
        dati = query.data.split(' ')[1]
        await f_add_user_true(dati, chat_id, dp.current_state(user=user_id))


    elif query.data == 'c_user_setting':
        await f_delete_this_message(query.message)


# А эта движуха отслеживает ошибки и не дает боту упасть, если будет ошибка отправит ее в чат архива
while True:
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as errors_logging:
        bot.send_message(config.archive_chat_id, "‼️ОШИБКА‼️" +
                         "\n\nТекст ошибки: " + str(errors_logging))
        print(errors_logging)
        pass
