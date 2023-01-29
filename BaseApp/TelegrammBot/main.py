import openai
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

token = '6180872940:AAE9Wl6ZYjGg4o8T37OyAEdQsF3T_tKNYfA'
openai.api_key = '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'

bot = Bot(token)
dp = Dispatcher(bot)


@dp.message_handler()
async def send(message: types.Message):
    response = openai.Completion.create(
        model="code-davinci-002",
        prompt=message.text,
        temperature=0,
        max_tokens=64,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    await message.answer(response['choices'][0]['text'])


executor.start_polling(dp, skip_updates=True)
