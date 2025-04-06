import json
import asyncio
from datetime import datetime, timedelta
from random import choice
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from motor.motor_asyncio import AsyncIOMotorClient

# Загрузка конфигурации
with open('config.json', encoding='utf-8') as f: config = json.load(f)

bot = Bot(token=config['token'])
dp = Dispatcher()

CHANNEL = config['channel_id']
TO_CHANNEL = config['to_channel']

client = AsyncIOMotorClient(
    f'mongodb://{config["db_user"]}:{config["db_password"]}@mongo:27017/'
)
users = client.user.users
dino_owners = client.dinosaur.dino_owners
save_reward = client.other.save_reward

lvl_app = config['lvl']

async def user_in_chat(userid, chatid=CHANNEL):
    statuss = ['creator', 'administrator', 'member']
    try:
        result = await bot.get_chat_member(chat_id=chatid, user_id=userid)
        return result.status if result.status in statuss else False
    except Exception:
        return False

async def check(userid, lang):
    in_chat = False
    in_bot = False
    lvl = 0
    inline_keyboard = []

    user = await users.find_one({"userid": userid}, {"_id": 1, 'lvl': 1})
    dino = await dino_owners.find_one({"owner_id": userid}, {"_id": 1}) is not None

    if user:
        lvl = user["lvl"]
        in_bot = True
        in_chat = await user_in_chat(userid) is not False

        if lvl >= lvl_app and dino and in_chat:
            text = (
                '❤️ Спасибо, что играете в бота, доступ к каналу открыт.\n🪙 Если остались вопросы -> @AS1AW'
                if lang == 'ru' else
                '❤️ Thanks for playing the bot, access to the channel is open.\n🪙 If you have any questions -> @AS1AW'
            )
            
            inline_keyboard = [[
                InlineKeyboardButton(
                    text="🗝️",
                    url=config['url_to_channel']
                )
            ]]

            await bot.approve_chat_join_request(TO_CHANNEL, userid)
            await save_reward.insert_one({'userid': userid, 'lvl': lvl, 'lang': lang})
            await bot.send_message(userid, text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard))
            return

    text = (
        f'🎭 Доступ в канал для розыгрыша телеграм премиума доступен только игрокам.\n\n🎍 Для доступа вы должны владеть минимум одним динозавром, иметь {lvl_app} уровень, быть подписаны  на основной канал новостей.\n\n🪙 Если остались вопросы -> @AS1AW\n\nP.S. Перед тем как перепроверить всё, напишите /start, чтобы бот мог с вами общаться.\n\n'
        if lang == 'ru' else
        f'🎭 Access to the channel for drawing premium telegrams is available only to players.\n\n🎍For access, you must own at least one dinosaur, have a {lvl_app} level, and be subscribed to the main news channel.\n\n🪙 If you have any questions -> @AS1AW\n\nP.S. Before you double-check everything, write / start so that the bot can communicate with you.\n\n'
    )

    inline_keyboard.append([
        InlineKeyboardButton(
            text="🎋 Новостной канал" if lang == 'ru' else "🎋 News Channel",
            url='https://t.me/DinoGochi'
        ),
        InlineKeyboardButton(
            text="👑 Основной бот" if lang == 'ru' else "👑 The main bot",
            url='https://t.me/DinoGochi_bot'
        )])
    inline_keyboard.append([
        InlineKeyboardButton(
            text="♻️ Перепроверить" if lang == 'ru' else "♻️ Check",
            callback_data='recheck'
        )
    ])

    text_temp = f'🗝️ {in_bot} 🎲 {lvl} / {lvl_app} 💬 {in_chat} 🦕 {dino}'
    text_temp = text_temp.replace('True', '✅').replace('False', '❌')
    text += text_temp

    await bot.send_message(userid, text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard))

@dp.chat_join_request(lambda message: True)
async def application(message: types.ChatJoinRequest):
    print(f"Join request from {message.from_user.id}")

    userid = message.from_user.id
    lang = message.from_user.language_code

    await check(message.from_user.id, lang)

@dp.callback_query(lambda call: call.data.startswith('recheck'))
async def inv_callback(call: types.CallbackQuery):
    userid = call.from_user.id
    lang = call.from_user.language_code

    try:
        await check(userid, call.from_user.language_code)
    except Exception as e:
        print(f"Error in recheck callback: {e}")
        if not 'USER_ALREADY_PARTICIPANT' in str(e):
            if lang == 'ru':
                await call.answer('❌ Бот не может отправить сообщение, напишите /start и повторите попытку', show_alert=True)
            else:
                await call.answer('❌ The bot cannot send a message, write /start and try again', show_alert=True)


@dp.message(Command(commands=['random']))
async def random1(message: types.Message):
    userid = message.from_user.id

    if userid in config['admins']:
        data = save_reward.find({})
        l_data = await data.to_list(length=100)

        rand = choice(l_data)
        await bot.send_message(userid, f'{rand}')

async def daily_check():
    while True:
        now = datetime.now()
        next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_time = (next_run - now).total_seconds()

        print(f"Daily check started at {datetime.now()}")
        len_users = await save_reward.count_documents({})
        print(f"Total users: {len_users}")

        async for user in save_reward.find({}):
            userid = user["userid"]
            lang = user.get("lang", "ru")
            
            print('Checking user:', userid)

            try:
                in_chat = await user_in_chat(userid)
                dino = await dino_owners.find_one({"owner_id": userid}, {"_id": 1}) is not None
                lvl = user.get("lvl", 0)
                
                print(f"User {userid} - in_chat: {in_chat}, dino: {dino}, lvl: {lvl}")

                if not (in_chat and dino and lvl >= lvl_app):
                    text = (
                        '❌ Вы больше не соответствуете условиям для доступа к каналу.\n\n🎍 Для доступа вы должны владеть минимум одним динозавром, иметь {lvl_app} уровень, быть подписаны на основной канал новостей.'
                        if lang == 'ru' else
                        '❌ You no longer meet the conditions for access to the channel.\n\n🎍 To access, you must own at least one dinosaur, have a {lvl_app} level, and be subscribed to the main news channel.'
                    ).format(lvl_app=lvl_app)

                    await bot.ban_chat_member(TO_CHANNEL, userid, 31)
                    await save_reward.delete_many({'userid': userid})
                    await bot.unban_chat_member(TO_CHANNEL, userid)

                    await bot.send_message(userid, text)

            except Exception as e:
                print(f"Error checking user {userid}: {e}") 
                continue

        print(f"Daily check completed at {datetime.now()}")
        await asyncio.sleep(sleep_time)

def run():
    print('Initializing...')

    loop = asyncio.get_event_loop()
    print('Looping')

    loop.create_task(daily_check())
    print('Daily check task started')

    print('Start!')
    loop.run_until_complete(dp.start_polling(bot, skip_updates=True))
