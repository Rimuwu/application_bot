import telebot
import json
import pymongo
from datetime import datetime, timezone

with open('config.json', encoding='utf-8') as f: 
    config = json.load(f) # type: dict

bot = telebot.TeleBot(config['token'])
CHANNEL = config['channel_id']

client = pymongo.MongoClient('mongodb://localhost:27017/')
users = client.users.users
dino_owners = client.dinosur.dino_owners

def get_delta(_id):
    create = _id.generation_time
    now = datetime.now(timezone.utc)
    delta = now - create
    return delta

def user_in_chat(userid, chatid = CHANNEL):
    statuss = ['creator', 'administrator', 'member']
    try:
        result = bot.get_chat_member(chat_id=chatid, user_id=userid)
    except Exception as e: return False

    if result.status in statuss: return result.status
    return False

def check(message):
    lang = message.from_user.language_code
    user = users.find_one({"userid": message.from_user.id}, {"_id": 1})
    dino = dino_owners.find_one({"userowner_idid": message.from_user.id}, {"_id": 1})

    if user:
        secs = get_delta(user['_id'])
        if secs >= 172_800 and dino and user_in_chat(message.from_user.id):
            bot.approve_chat_join_request(CHANNEL, message.from_user.id)
            
            if lang == 'ru':
                text = '🎭 Доступ в канал для розыгрыша телеграм премиума доступен только игрокам. Для доступа вы должны владеть минимум одним динозавром, быть зарегестрированным 2 дня и быть подписаны на основной канал новостей.'
                
            bot.approve_chat_join_request(message.chat.id)

@bot.chat_join_request_handler()
def application(message: telebot.types.ChatJoinRequest):
    lang = message.from_user.language_code

    # bot.send_message(message.from_user.id, "Hello, my friend!")
    # bot.approve_chat_join_request(message.chat.id)

    check(message)


def run():
    bot.infinity_polling(allowed_updates = telebot.util.update_types)
    
    # Не забыть вставить id основного канала новостей
