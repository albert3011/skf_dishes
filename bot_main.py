import asyncio
import json
from random import choices
from aiogram import Bot, Dispatcher, types
import aiohttp
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from recipes_handler import create_kb, func_request, pick_dishes, final_answer
from token_data import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()


class TestInfo(StatesGroup):
    categories_info = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer('Здравствуйте! Воспользуйтесь командой /category_search_random для поиска рецептов.\nНапример, "/category_search_random 3" для получения трёх случайных рецептов.')


@dp.message(Command("category_search_random"))
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    """
    Принимаем команду category_search_random.
    Если с командой не отправлен аргумент - оповещаем об этом пользователя.
    Если аргумент отправлен:
    1 - С помощью функции func_request отправляем запрос по ссылке с категориями блюд
    2 - С помощью функции create_kb генерируем клавиатуру со всеми категориями и словарь со всеми категориями
    3 - Сохраняем кол-во блюд и словарь категорий в state data
    4 - Обновляем состояние в state state
    """
    if command.args is None:
        await message.answer("Укажите кол-во блюд, например:\n/category_search_random 4")
    else:
        async with aiohttp.ClientSession() as session:
            result = await func_request(session, 'https://www.themealdb.com/api/json/v1/1/categories.php')
        info = await create_kb(result)
        await state.set_data({'arg': int(command.args), 'cat_dict': info[1]})
        await state.set_state('waiting_category')
        await message.answer(f"Выбирайте категорию, чтобы получить случайные рецепты ({int(command.args)} шт.)", reply_markup=info[0])


@dp.message()
async def echo(message: types.Message, state: FSMContext):
    """
    Принимаем любые сообщения, определяем текущее состояние из state state.
    Если state = waiting_category:
    1 - Проверяем, верную ли пользователь выбрал категорию.
    2 - С помощью функции func_request отправляем запрос по ссылке со всеми блюдами выбранной категории
    3 - С помощью функции pick_dishes собираем словарь блюд и их номеров
    4 - Выбираем случайные блюда
    5 - Предлагаем их пользователю, с кнопкой на клавиатуре
    6 - Меняем состояние через state state
    7 - Сохраняем в state data случайно выбранные блюда и полный словарь блюд с их номерами
    Если state = waiting_recipes:
    1 - С помощью функции func_request отправляем запрос по ссылке на каждое блюдо с его рецептом
    2 - С помощью функции final_answer формируем полный рецепт на русском языке со списком ингридиентов
    3 - Отправляем пользователю отдельными сообщениями всю информацию.
    """
    curr_state = await state.get_state()
    if curr_state == 'waiting_category':
        data = await state.get_data()
        if message.text in data['cat_dict']:
            async with aiohttp.ClientSession() as session:
                result = await func_request(session, f'https://www.themealdb.com/api/json/v1/1/filter.php?c={message.text}')
            dishes_dict = await pick_dishes(json.dumps(result))
            random_list = choices(list(dishes_dict), k=data['arg'])
            answer = 'Как Вам такие варианты: ' + ', '.join(map(str, random_list))
            keyboard = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text='Покажи рецепты')]], resize_keyboard=True)
            await state.set_state('waiting_recipes')
            await state.set_data({'random_list': random_list, 'dishes_dict': dishes_dict})
            await message.answer(answer, reply_markup=keyboard)
        else:
            await message.answer(f'Категории {message.text} не существует.\nВоспользуйтесь кнопками для выбора категории.')
    elif curr_state == 'waiting_recipes':
        data = await state.get_data()
        random_list = data['random_list']
        dishes_dict = data['dishes_dict']
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(random_list)):
                result = await func_request(session, f'https://www.themealdb.com/api/json/v1/1/lookup.php?i={dishes_dict[random_list[i]]}')
                answer = await final_answer(result, random_list[i])
                await message.answer(answer)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
