from time import time
from dotenv import load_dotenv
import os

load_dotenv()

def genrand_stickerpack_name(msg):
        cur_time = int(time());
        return [
                f'sticker {msg.from_user.id} on {cur_time}',
                f'a{msg.from_user.id}_on_{cur_time}_by_{os.getenv("BOT_USERNAME")}',
        ]

def get_file_id(msg):
        if msg.reply_to_message.photo != None:
                return msg.reply_to_message.photo.file_id
        if msg.reply_to_message.animation != None:
                return msg.reply_to_message.animation.file_id
        if msg.reply_to_message.sticker != None:
                return msg.reply_to_message.sticker.file_id