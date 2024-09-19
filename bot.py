from pyrogram import Client, filters
import os
import io
import tempfile
import shutil
import utilsfunc as fn
from pyrogram.raw.types import InputDocument
from pyrogram.raw.functions.stickers import RemoveStickerFromSet
import pyrogram.errors.exceptions as pyroexception
import pyrogram.enums as pyroenum

from pyrogram.file_id import FileId

from pymongo import MongoClient
from dotenv import load_dotenv
from PIL import Image

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
    if msg.reply_to_message == None:
        await msg.reply_text("you must reply to another message")
        return;
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
    
async def create_new_stickerpack(client, msg, sanitized_input, collection):
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
                'current': packshort
            }
        )
        
        await msg.reply_text(f"kanged!, here your sticker\n\n{"https://t.me/addstickers/" + ret.short_name}")
    except Exception as e:
        await msg.reply_text(e)
    
@app.on_message(filters.command(['kang']))
async def kangfunc(client, msg):
    if msg.reply_to_message == None or msg.reply_to_message.sticker == None:
        await msg.reply_text("you must reply to another sticker, not a message")
        return;
    
    database = g_dbctx["kangutils"]
    collection = database["stickerpack_state"]
    
    # find current sticker set
    dbquery = collection.find_one({'user_id': msg.from_user.id});
    
    sanitized_input = fn.sanitize_emoji(msg)
    if sanitized_input["err"] == 1:
        await msg.reply_text(sanitized_input["msg"])
        return;

    if dbquery == None:
        await create_new_stickerpack(client, msg, sanitized_input, collection)
    else:
        packshort = dbquery["current"]
        
        try:
            ret = await client.add_sticker_to_set(
                
                set_short_name=packshort,
                sticker=fn.get_file_id(msg),
                user_id=msg.from_user.id,
                emoji=sanitized_input["ret"]
            )
        
            await msg.reply_text(f"kanged!, here your sticker\n\n{"https://t.me/addstickers/" + ret.short_name}")
        except pyroexception.bad_request_400.StickersTooMuch:
            await create_new_stickerpack(client, msg, sanitized_input, collection)
        except Exception as e:
            await msg.reply_text(e)

@app.on_message(filters.command(['unkang']))
async def unkangfunc(client, msg):

    if msg.reply_to_message == None:
        await msg.reply_text("you must reply to another message")
        return;
    
    decoded = FileId.decode(fn.get_file_id(msg))

    try:
        await client.invoke(RemoveStickerFromSet(
            sticker=InputDocument(
            
                    id=decoded.media_id,
                    access_hash=decoded.access_hash,
                    file_reference=decoded.file_reference
            )
        ))
        
        await msg.reply_text("sticker unkanged!")
    except pyroexception.bad_request_400.StickersetInvalid:
        await msg.reply_text("This sticker is not yours, can't unkang. make sure you do /fork then /unkang")
    
@app.on_message(filters.command(['fork']))
async def forkfunc(client, msg):
    
    if msg.reply_to_message == None or msg.reply_to_message.sticker == None:
        await msg.reply_text("you must reply to another sticker")
        return;
    
    await msg.reply_text("Processing... It's takes a littebit of time.")
    await client.send_chat_action(
        chat_id=msg.chat.id,
        action=pyroenum.ChatAction.TYPING
    )
    
    is_first = True
    
    packraw = fn.genrand_stickerpack_name(msg)
    packname = packraw[0]
    packshort = packraw[1]
    
    # stickerset = await fn.get_stickers(client, msg.reply_to_message.sticker.set_name)
    for s in await fn.get_stickers(client, msg.reply_to_message.sticker.set_name):
        print(f"forking: {s.file_id} {packshort}")
        if is_first == True:
            await client.create_sticker_set(
                title=packname, 
                short_name=packshort, 
                sticker=s.file_id,
                user_id=msg.from_user.id,
                emoji=s.emoji
            )
            
            is_first = False
        else:
            try:
                await client.add_sticker_to_set(
                    set_short_name=packshort, 
                    sticker=s.file_id,
                    user_id=msg.from_user.id,
                    emoji=s.emoji
                )
            except:
                print(f"err forking: {s.file_id} {packshort}")
    # print(stickerset)
    await msg.reply_text(f"sticker forked!, <a href='https://t.me/addstickers/{packshort}'>link</a>")


@app.on_message(filters.command(['to_ts']))
async def to_tsfunc(client, msg):
    if msg.reply_to_message == None or msg.reply_to_message.photo == None:
        await msg.reply_text("you must reply to photo")
        return;
    
    bytesio_ret = await client.download_media(
        message=msg.reply_to_message,
        in_memory=True
    )
    
    size = 512, 512
    
    iomem = io.BytesIO()
    iomem.name = "rand.webp"
    
    image = Image.open(bytesio_ret)
    image = image.convert('RGB')
    image = image.resize((512, 512), Image.Resampling.LANCZOS)

    image.save(iomem, 'webp')
    
    
    await client.send_sticker(
        chat_id=msg.chat.id,
        sticker=iomem,
        reply_to_message_id=msg.reply_to_message.id
    )
    
    
@app.on_message(filters.command(['packinfo']))
async def packinfofunc(client, msg):
    if msg.reply_to_message == None or msg.reply_to_message.sticker == None:
        await msg.reply_text("you must reply to sticker")
        return;
    
    data = await client.get_sticker_set(
        msg.reply_to_message.sticker.set_name
    )
    
    await msg.reply_text(
        f"id: {data.id}\n" + 
        f"title: {data.title}\n" + 
        f"short_name: {data.short_name}\n" + 
        f"total: {data.count}\n"
    )
    
app.run()
