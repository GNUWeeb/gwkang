from pyrogram import Client, filters
import os
import io
import tempfile
import shutil
import utilsfunc as fn
from pyrogram.raw.types import InputDocument
from pyrogram.raw.functions.stickers import RemoveStickerFromSet

from pyrogram.file_id import FileId

from pymongo import MongoClient
from dotenv import load_dotenv

g_dbctx = MongoClient(os.getenv("MONGO_URI"))
load_dotenv()

app = Client(
    "my_bot",
    api_id=os.getenv("API_ID"), api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("TOKEN"),
)


@app.on_message(filters.command(['dbg']))
async def test(client, msg):
    print(str(msg))
    dirpath = tempfile.mkdtemp()
    fulldirpath = dirpath + '/' + "ret.json"

    with open(fulldirpath, "w+") as dbgstr:
        dbgstr.write(str(msg))

    await client.send_document(document=fulldirpath, chat_id=msg.chat.id)

    shutil.rmtree(dirpath)
    
@app.on_message(filters.command(['dfid']))
async def testfid(client, msg):
    await msg.reply_text(fn.get_file_id(msg))
    

@app.on_message(filters.command(['dm']))
async def testfn(client, msg):
    dirpath = tempfile.mkdtemp()
    fulldirpath = dirpath + '/' + "ret.json"
    
    # start
    
    ret = await client.download_media(
        message=msg.reply_to_message,
        in_memory=True
    )
    
    print(ret)
    # end

    with open(fulldirpath, "w+") as dbgstr:
        dbgstr.write(str(ret))

    await client.send_document(document=fulldirpath, chat_id=msg.chat.id)

    shutil.rmtree(dirpath)
    
@app.on_message(filters.command(['kang']))
async def kangfunc(client, msg):
    database = g_dbctx["kangutils"]
    collection = database["stickerpack_state"]
    
    # find current sticker set
    dbquery = collection.find_one({'user_id': msg.from_user.id});
    
    sanitized_input = fn.sanitize_emoji(msg)
    if sanitized_input["err"] == 1:
        await msg.reply_text(sanitized_input["msg"])
        return;
    
    if msg.reply_to_message == None:
        await msg.reply_text("you must reply to another message")
        return;

    if dbquery == None:
        packraw = fn.genrand_stickerpack_name(msg)
        packname = packraw[0]
        packshort = packraw[1]
        
        try:
            ret = await client.create_sticker_set(
                title=packname, 
                short_name=packshort, 
                sticker=fn.get_file_id(msg),
                user_id=msg.from_user.id,
                emoji=sanitized_input["ret"]
            )
            
            collection.insert_one(
                {
                    'user_id': msg.from_user.id,
                    'current': packshort,
                    'len': 1
                }
            )
            
            await msg.reply_text(f"kanged!, here your sticker\n\n{"https://t.me/addstickers/" + ret.short_name}")
        except Exception as e:
            await msg.reply_text(e)
    else:
        packshort = dbquery["current"]
        
        try:
            ret = await client.add_sticker_to_set(
                
                set_short_name=packshort,
                sticker=fn.get_file_id(msg),
                user_id=msg.from_user.id,
                emoji=sanitized_input["ret"]
            )
            
            collection.update_one(
                {
                    'user_id': msg.from_user.id,
                },
                {
                    '$set': {
                        'len': dbquery["len"] + 1
                    }
                }
            )
            
            await msg.reply_text(f"kanged!, here your sticker\n\n{"https://t.me/addstickers/" + ret.short_name}")
        except Exception as e:
            await msg.reply_text(e)

@app.on_message(filters.command(['unkang']))
async def unkangfunc(client, msg):

    if msg.reply_to_message == None:
        await msg.reply_text("you must reply to another message")
        return;
    
    decoded = FileId.decode(fn.get_file_id(msg))

    await client.invoke(RemoveStickerFromSet(
        sticker=InputDocument(
        
                id=decoded.media_id,
                access_hash=decoded.access_hash,
                file_reference=decoded.file_reference
        )
    ))
    
    await msg.reply_text("sticker unkanged!")

app.run()
