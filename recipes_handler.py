import asyncio
import re
import aiohttp
import json
from googletrans import Translator

from aiogram import types


async def create_kb(result):
    a = json.dumps(result)
    categories = re.findall('"idCategory": "\d*", "strCategory": "\w*"', a)
    cats_dict = {}
    for i in range(0, len(categories)):
        categories[i] = categories[i].replace('"idCategory": "', '').replace('"strCategory": ', '').replace('"', '')
        category_number = re.split(', ', categories[i])[0]
        category_name = re.split(', ', categories[i])[1]
        cats_dict[category_name] = category_number
    a = list(cats_dict)
    kb = []
    i = 0
    while True:
        if len(a) > i + 5:
            kb.append([types.KeyboardButton(text=a[i+z]) for z in range(0, 5)])
            i = i + 5
        else:
            ost = len(a) - i
            kb.append([types.KeyboardButton(text=a[i+z]) for z in range(0, ost)])
            break
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard, cats_dict


async def pick_dishes(result):
    translator = Translator()
    dishes_name = re.findall('"strMeal": "[^"]*"', result)
    dishes_num = re.findall('"idMeal": "\d*"', result)
    dishes_dict = {}
    for i in range(0, len(dishes_name)):
        dishes_name[i] = dishes_name[i].replace('"strMeal": "', '"').replace('"', '')
        dishes_num[i] = dishes_num[i].replace('"idMeal": "', '').replace('"', '')
        dishes_dict[translator.translate(dishes_name[i], dest='ru').text] = dishes_num[i]
    return dishes_dict


async def func_request(session, link):
    async with session.get(url=link) as resp:
        return await resp.json()


async def final_answer(recipes_dict, rus_name):
    translator = Translator()

    answer = f"{rus_name}\n{translator.translate(recipes_dict['meals'][0]['strInstructions'], dest='ru').text}\n"
    ingridients = []
    for i in range(1, 21):
        if recipes_dict['meals'][0][f'strIngredient{i}']:
            if len(recipes_dict['meals'][0][f'strIngredient{i}']) > 2:
                ingridients.append(translator.translate(recipes_dict['meals'][0][f'strIngredient{i}'], dest='ru').text)
    answer = answer + '\nИнгридиенты:\n' + '\n'.join(map(str, ingridients))
    return answer
