import telebot
import json
import pymongo
from datetime import datetime, timezone

with open('config.json', encoding='utf-8') as f: 
    config = json.load(f) # type: dict

bot = telebot.TeleBot(config['token'])
CHANNEL = config['channel_id'] # Обязательна подписка
TO_CHANNEL = config['to_channel'] # Принимает в канал

client = pymongo.MongoClient('mongodb://localhost:27017/')
users = client.user.users
dino_owners = client.dinosaur.dino_owners

def get_delta(_id):
    create = _id.generation_time
    now = datetime.now(timezone.utc)
    delta = now - create
    return delta.seconds

def user_in_chat(userid, chatid = CHANNEL):
    statuss = ['creator', 'administrator', 'member']
    try:
        result = bot.get_chat_member(chat_id=chatid, user_id=userid)
    except Exception as e: return False

    if result.status in statuss: return result.status
    return False

def check(userid, lang):
    secs = 0
    in_chat = False
    in_bot = False

    user = users.find_one({"userid": userid}, {"_id": 1})
    dino = dino_owners.find_one({"owner_id": userid}, {"_id": 1}) not in [None, {}]
    markup_inline = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    if user:
        in_bot = True
        secs = get_delta(user['_id'])
        in_chat = user_in_chat(userid) != False

        if secs >= 10000 and dino and in_chat:

            if lang == 'ru':
                text = '❤️ Спасибо, что играете в бота, доступ к каналу открыт.\n🪙 Если остались вопросы -> @dinogochi_bugs'
            else:
                text = '❤️ Thanks for playing the bot, access to the channel is open.\n🪙 If you have any questions -> @dinogochi_bugs'
            
            markup_inline.add(
                telebot.types.InlineKeyboardButton(
                    text="🗝️", 
                    url='https://t.me/+iFBBwYBEnvgzMTZi'))
    
            bot.approve_chat_join_request(TO_CHANNEL, userid)
            bot.send_message(userid, text, reply_markup=markup_inline)
            return

    if lang == 'ru':
        text = '🎭 Доступ в канал для розыгрыша телеграм премиума доступен только игрокам.\n\n🎍 Для доступа вы должны владеть минимум одним динозавром, быть зарегестрированны в боте минимум 2 дня и иметь подписку на основной канал новостей.\n\n🪙 Если остались вопросы -> @dinogochi_bugs\n\nP.S. Перед тем как перепроверить всё, напишите /start, чтобы бот мог с вами общаться.\n\n'
        markup_inline.add(
            telebot.types.InlineKeyboardButton(
            text="🎋 Новостной канал", 
            url='https://t.me/DinoGochi'),

            telebot.types.InlineKeyboardButton(
            text="👑 Основной бот", 
            url='https://t.me/DinoGochi_bot'),

            telebot.types.InlineKeyboardButton(text="♻️ Перепроверить",
                    callback_data=f'recheck')
            )

    else:
        text = '🎭 Access to the channel for drawing premium telegrams is available only to players.\n\n🎍 To access it, you must own at least one dinosaur, be registered in the bot for at least 2 days and have a subscription to the main news channel.\n\n🪙 If you have any questions -> @dinogochi_bugs\n\nP.S. Before you double-check everything, write / start so that the bot can communicate with you.\n\n'
        markup_inline.add(
            telebot.types.InlineKeyboardButton(
            text="🎋 News Channel", 
            url='https://t.me/DinoGochi'),

            telebot.types.InlineKeyboardButton(
            text="👑 The main bot", 
            url='https://t.me/DinoGochi_bot'),

            telebot.types.InlineKeyboardButton(text="♻️ Check",
                    callback_data=f'recheck')
            )

    text_temp = f'🗝️ {in_bot} ⌚ {secs >= 172800} 💬 {in_chat} 🦕 {dino}'
    text_temp = text_temp.replace('True', '✅').replace('False', '❌')
    text += text_temp

    bot.send_message(userid, text, reply_markup=markup_inline)

@bot.chat_join_request_handler()
def application(message: telebot.types.ChatJoinRequest):
    lang = message.from_user.language_code
    check(message.from_user.id, lang)

@bot.callback_query_handler(func=lambda call: 
    call.data.startswith('recheck'))
def inv_callback(call: telebot.types.CallbackQuery):
    userid = call.from_user.id
    check(userid, call.from_user.language_code)


def run():
    print('start')
    bot.infinity_polling()
