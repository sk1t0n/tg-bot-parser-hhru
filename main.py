import os
from typing import Dict, List

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import get_new_configured_app

import parser_hhru
import config
from utils import get_params

WEBHOOK_HOST = os.environ['WEBHOOK_HOST']
WEBHOOK_PATH = '' if WEBHOOK_HOST[-1] == '/' else '/'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

TG_BOT_TOKEN = os.environ['TG_BOT_TOKEN']

bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher(bot)

filters = {
    config.PARAM_HHRU_QUERY: '',
    config.PARAM_HHRU_EXP: get_params.experience['1-3'],
    config.PARAM_HHRU_AREA: get_params.areas['Krasnodar'],
    config.PARAM_HHRU_PAGE: 0
}


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    start_message = '''
Welcome.
The bot can return a pdf with job vacancies at the search query.
For help with bot commands, send /help
'''
    await message.reply(start_message)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_message = '''
Available commands:
/select_exp - set the work experience
/select_area - set the city to search
'''
    await message.reply(help_message)


def get_keyboard_markup(
    items: List[Dict[str, str]]
) -> List[types.InlineKeyboardButton]:
    """
    Returns the list of buttons.

    items: list of dictionaries with keys
        text    - button text
        cb_data - the data for processing the clicking on this button  # noqa
    """
    markup = types.InlineKeyboardMarkup()
    for item in items:
        btn = types.InlineKeyboardButton(
            text=item['text'],
            callback_data=item['cb_data']
        )
        markup.add(btn)
    return markup


@dp.message_handler(commands=['select_exp'])
async def set_work_experience(message: types.Message):
    items = [
        {'text': key, 'cb_data': f'exp_{value}'}
        for key, value in get_params.experience.items()
    ]
    markup = get_keyboard_markup(items)
    await message.reply('Select the work experience', reply_markup=markup)


@dp.callback_query_handler(
    lambda call: call.message and call.data.startswith('exp_'))
async def cb_handler_exp(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)

    global filters
    filters[config.PARAM_HHRU_EXP] = query.data.split('exp_')[1]
    await bot.send_message(query.message.chat.id, 'Success')


@dp.message_handler(commands=['select_area'])
async def set_area(message: types.Message):
    areas = [
        {'text': key, 'cb_data': f'area_{value}'}
        for key, value in get_params.areas.items()
    ]
    markup = get_keyboard_markup(areas)
    await message.reply('Select the city to search', reply_markup=markup)


@dp.callback_query_handler(
    lambda call: call.message and call.data.startswith('area_'))
async def cb_handler_area(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)

    global filters
    filters[config.PARAM_HHRU_AREA] = query.data.split('area_')[1]
    await bot.send_message(query.message.chat.id, 'Success')


def check_search_query(query: str) -> bool:
    """Checking for a valid search query."""
    if query.startswith('/'):
        return False
    return True


@dp.callback_query_handler(
    lambda call: call.message and call.data == 'load_more')
async def cb_handler_load_more(query: types.CallbackQuery):
    """Loads the next page with vacancies and send pdf."""
    await bot.answer_callback_query(query.id)

    global filters
    filters[config.PARAM_HHRU_PAGE] += 1
    page = filters[config.PARAM_HHRU_PAGE]
    filename = f'vacancies{page}.pdf'
    parser = parser_hhru.AsyncParser(filters)
    result = await parser.save_pdf(filename)
    if result[0]:
        markup = get_keyboard_markup([{
            'text': 'Load More', 'cb_data': 'load_more'
        }])
        with open(filename, 'rb') as pdf:
            await bot.send_document(
                query.message.chat.id, pdf, reply_markup=markup)
    else:
        await bot.send_message(query.message.chat.id, result[1])


@dp.message_handler()
async def send_pdf_with_vacancies(message: types.Message):
    """Loads the first page with vacancies and send pdf."""
    global filters
    filters[config.PARAM_HHRU_QUERY] = message.text
    filters[config.PARAM_HHRU_PAGE] = 0
    if not check_search_query(message.text):
        return await bot.send_message(message.chat.id, 'Invalid search query')

    parser = parser_hhru.AsyncParser(filters)
    filename = 'vacancies0.pdf'
    result = await parser.save_pdf(filename)
    if result[0]:
        markup = get_keyboard_markup([{
            'text': 'Load More', 'cb_data': 'load_more'
        }])
        with open(filename, 'rb') as pdf:
            await bot.send_document(
                message.chat.id, pdf, reply_markup=markup)
    else:
        await bot.send_message(message.chat.id, result[1])


app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
