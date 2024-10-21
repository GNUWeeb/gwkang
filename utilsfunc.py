import traceback
from time import time
from dotenv import load_dotenv
import os
import emoji
import tempfile
import shutil
from pyrogram.types import Sticker
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.functions.stickers import RenameStickerSet
from pyrogram.raw.types import InputStickerSetShortName

load_dotenv()

def genrand_stickerpack_name(msg):
        cur_time = int(time());
        
        if msg.sender_chat != None:
            ret = [
                    f'Sticker {msg.sender_chat.title}',
                    f'a{str(msg.sender_chat.id)[1:]}_on_{cur_time}_by_{os.getenv("BOT_USERNAME")}',
            ]
            return ret
        
        if msg.from_user.last_name == None:
            ret = [
                    f'Sticker {msg.from_user.first_name}',
                    f'a{msg.from_user.id}_on_{cur_time}_by_{os.getenv("BOT_USERNAME")}',
            ]
        else:
            ret = [
                    f'Sticker {msg.from_user.first_name} {msg.from_user.last_name}',
                    f'a{msg.from_user.id}_on_{cur_time}_by_{os.getenv("BOT_USERNAME")}',
            ]
            
        return ret

def get_file_id(msg):
        if msg.reply_to_message.photo != None:
                return msg.reply_to_message.photo.file_id
        if msg.reply_to_message.animation != None:
                return msg.reply_to_message.animation.file_id
        if msg.reply_to_message.sticker != None:
                return msg.reply_to_message.sticker.file_id
        if msg.reply_to_message.document != None and msg.reply_to_message.document.mime_type == "video/webm":
                return msg.reply_to_message.document.file_id
        
def sanitize_emoji(msg):
    

    try:
        cur = msg.command[1]
        
        
        if emoji.is_emoji(msg.command[1]) == False:
            return {
                "err": 1,
                "msg": "You need emoji, not a chars",
                "ret": None
            }
        if emoji.emoji_count(msg.command[1]) > 1:
            return {
                "err": 1,
                "msg": "A custom emoji must be just 1 chars length",
                "ret": None
            }
        
    except IndexError:
        cur = "🗿"
        
    return {
        "err": 0,
        "msg": None,
        "ret": cur
    }
            

async def gen_file_report(client, msg, errstr):
    dirpath = tempfile.mkdtemp()
    fulldirpath = dirpath + '/' + "ret.json"
    
    with open(fulldirpath, "w+") as dbgstr:
        dbgstr.write(str(errstr))

    await client.send_document(document=fulldirpath, chat_id=msg.chat.id)

    shutil.rmtree(dirpath)
    
async def get_stickers(self, short_name):
    sticker_set = await self.invoke(
        GetStickerSet(stickerset=InputStickerSetShortName(short_name=short_name), hash=0)
    )
    
    return [
        await Sticker._parse(self, doc, {type(a): a for a in doc.attributes})
        for doc in sticker_set.documents
    ]
    
async def send_trace(e, msg):
    tb = traceback.format_exc()
    await msg.reply_text(str(tb))
    
def random_hex_string(length=2):
    return str(os.urandom(length).hex())

async def rename_sticker(shortname, client):
    randomized_hex = random_hex_string()
    
    data = await client.get_sticker_set(
        shortname
    )
    
    if data.title[0] == '#':
        formats = f"#{randomized_hex} {data.title[6:]}"

    else:
        formats = f"#{randomized_hex} {data.title}"

    sticker_set = await client.invoke(
        RenameStickerSet(stickerset=InputStickerSetShortName(short_name=data.short_name), title=formats)
    )