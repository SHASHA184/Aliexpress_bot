import logging
import os
from datetime import datetime, timedelta, timezone
import asyncio
import pytz

from config import *
from aiogram import Bot, Dispatcher, types
from aiogram.types.update import Update
from loader import dp, bot
from aiogram.utils.markdown import link, hlink
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher.filters import Text, IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import TerminatedByOtherGetUpdates
import pymysql

id_chat = os.environ['chat_id']
admin = os.environ['admin_id']


class Log_in(StatesGroup):
    enter_code = State()


async def kick_user(user_id):
    if user_id != admin:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            await asyncio.sleep(300)
            tzkiev = pytz.timezone('Europe/Kiev')
            time = datetime.now(tzkiev).strftime('%H:%M')
            check_user = "SELECT id FROM users WHERE id = (%s) AND action = (%s) AND time = (%s)"
            cursor.execute(check_user, (user_id, 1, time))
            check = cursor.fetchone()
            print(check)
            if check:
                await bot.kick_chat_member(id_chat, user_id)


# @dp.message_handler(content_types='photo')
# async def get_blob(message: types.Message):
#     # await bot.send_photo(chat_id=message.from_user.id,
#     #                      photo='AgACAgIAAxkBAAMDYkBzF9a7yIFJTdIiTwx1-tGok_sAAru9MRvujQlK00zjuJHkvC8BAAMCAAN5AAMjBA')
#     raw = message.photo[-1].file_id
#     print(raw)





@dp.message_handler(chat_id=id_chat)
async def add_time(message: types.Message):
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    with connection.cursor() as cursor:
        tzkiev = pytz.timezone('Europe/Kiev')
        time = datetime.now(tzkiev) + timedelta(minutes=5)
        insert = "INSERT INTO users (`id`, `name`, `action`, `time`) VALUES " \
                 "(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE `name` = %s, `time`= %s"
        t = (int(message.from_user.id), message.from_user.full_name, 1, time.strftime('%H:%M'),
             str(message.from_user.full_name), time.strftime('%H:%M'))
        cursor.execute(insert, t)
        connection.commit()
        asyncio.create_task(kick_user(message.from_user.id))


@dp.message_handler(commands='start')
async def start(message: types.Message):
    print(os.environ)
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    with connection.cursor() as cursor:
        # insert = "SHOW COLUMNS FROM users"
        # col = cursor.execute(insert)
        # print(col)

        select_last_10_id = "SELECT * FROM goods ORDER BY RAND() LIMIT 10"
        cursor.execute(select_last_10_id)
        info = cursor.fetchall()
        for i in range(len(info)):
            name = info[i]['name']
            description = info[i]['description']
            photo = info[i]['photo']
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Посмотреть', description))
            await bot.send_photo(chat_id=message.from_user.id, photo=photo, caption=name, reply_markup=kb)
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton(text='Ввести промокод', callback_data='enter_code'))
        await message.answer(text='Это все товары доступные обычному пользоваетелю.\n'
                                  'Введите промокод и пароль чтобы увидеть больше', reply_markup=kb)


@dp.callback_query_handler(text='enter_code')
async def enter_code(call: types.CallbackQuery):
    await bot.send_message(chat_id=call.from_user.id, text='Введите код')
    await Log_in.enter_code.set()


@dp.message_handler(state=Log_in.enter_code)
async def result(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
    code_input = message.text
    if code_input != code:
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton(text='Попробовать ещё', callback_data='enter_code'))
        await message.answer(text='Неправильный код', reply_markup=kb)
    else:
        for i in range(0, 2):
            await bot.delete_message(message.from_user.id, message.message_id - i)
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            check_user = "SELECT id FROM users WHERE id = (%s)"
            cursor.execute(check_user, message.from_user.id)
            check = cursor.fetchone()
            print(check)
            if check is None:
                bt = InlineKeyboardButton(text='Одобрить', callback_data='accept')
                bt1 = InlineKeyboardButton(text='Отклонить', callback_data='cancel')
                kb = InlineKeyboardMarkup(row_width=1).add(bt, bt1)
                await bot.send_message(chat_id=654937013, text=f"""Пользователь - {message.from_user.full_name},
id - {message.from_user.id}""", reply_markup=kb)
            else:
                link = await bot.create_chat_invite_link(chat_id=id_chat)
                print(link.invite_link)
                kb = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Войти в чат", url=link.invite_link))
                check_user = "SELECT id FROM users WHERE id = (%s) AND action = (%s)"
                cursor.execute(check_user, (message.from_user.id, 1))
                await bot.unban_chat_member(id_chat, message.from_user.id)
                # await bot.set_chat_permissions(permissions=)
                tzkiev = pytz.timezone('Europe/Kiev')
                time = datetime.now(tzkiev) + timedelta(minutes=5)
                insert = "INSERT INTO users (`id`, `name`, `action`, `time`) VALUES " \
                         "(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE `name` = %s, `time`= %s"
                t = (int(message.from_user.id), message.from_user.full_name, 1, time.strftime('%H:%M'),
                     str(message.from_user.full_name), time.strftime('%H:%M'))
                cursor.execute(insert, t)
                connection.commit()
                asyncio.create_task(kick_user(message.from_user.id))
                await bot.send_message(chat_id=message.from_user.id,
                                       text=f"Можете вступить по ссылке ниже(сообщение будет удалено через 5 секунд)",
                                       reply_markup=kb)
                for i in range(4, 0, -1):
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=message.message_id + 1,
                                                text=f"Можете вступить по ссылке ниже(сообщение будет удалено через {i} секунд)",
                                                reply_markup=kb)
                    await asyncio.sleep(1)
                await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id + 1)
                await bot.revoke_chat_invite_link(chat_id=id_chat, invite_link=link.invite_link)


@dp.callback_query_handler(text='accept')
async def accept(call: types.CallbackQuery):
    name = call.message.text.replace(' ', '').split('-')[1].split(',')[0]
    user_id = call.message.text.replace(' ', '').split('-')[2]
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    with connection.cursor() as cursor:
        insert = "INSERT INTO users (`id`, `name`, `action`) VALUES (%s, %s, %s)"
        cursor.execute(insert, (user_id, name, 1))
        connection.commit()
        await bot.send_message(user_id, "Вы приняты в канал")


if __name__ == '__main__':
    executor.start_polling(dp)
