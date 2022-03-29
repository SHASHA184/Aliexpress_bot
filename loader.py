import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
TG_TOKEN = '5220382982:AAGCiLG91ntNIqBOpI4jWiHmYJe1zdR_Nl0'
bot = Bot(token=TG_TOKEN, parse_mode=types.ParseMode.HTML)
dp: Dispatcher = Dispatcher(bot, storage=MemoryStorage())