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
import imgbbpy

from pyrogram.file_id import FileId

from pymongo import MongoClient
from dotenv import load_dotenv
from PIL import Image
import sys

from pool import run_in_thread

try:
    DEBUG_MODE = bool(sys.argv[1])
except IndexError:
    DEBUG_MODE = False

g_dbctx = MongoClient(os.getenv("MONGO_URI"))
load_dotenv()

app = Client(
    "my_bot",
    api_id=os.getenv("API_ID"), api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("TOKEN"),
)

@run_in_thread
def convert_to_gif(paths):
    os.system(f"./venv/bin/lottie_convert.py {paths} {paths}.gif")
    
async def show_debug_text(msg):
    await msg.reply_text("Debug mode enabled, sorry for the convenience. Try again later")

async def check_debug(msg):
    if DEBUG_MODE == True:
        if msg.from_user.id != int(os.getenv("AUTHOR_ID")):
            await show_debug_text(msg)
            return -1
        
@app.on_message(filters.command(['start']))
async def startfunc(client, msg):
    await msg.reply_text("Hello!")

@app.on_message(filters.command(['dbg']))
async def test(client, msg):
    if await check_debug(msg) ==  -1:
        return
    dirpath = tempfile.mkdtemp()
    fulldirpath = dirpath + '/' + "ret.json"

    with open(fulldirpath, "w+") as dbgstr:
        dbgstr.write(str(msg))

    await client.send_document(document=fulldirpath, chat_id=msg.chat.id)

    shutil.rmtree(dirpath)
    
@app.on_message(filters.command(['dfid']))
async def testfid(client, msg):
    if await check_debug(msg) ==  -1:
        return
    if msg.reply_to_message == None:
        await msg.reply_text("you must reply to another message")
        return;
    await msg.reply_text(fn.get_file_id(msg))
    

@app.on_message(filters.command(['dm']))
async def testfn(client, msg):
    if await check_debug(msg) ==  -1:
        return
    
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
        
        msgdata = await msg.reply_text(f"<a href='https://t.me/addstickers/{ret.short_name}'>Kanged!</a>")
        return [
            packshort, msgdata
        ]
    
    except pyroexception.bad_request_400.PeerIdInvalid as e:
        await msg.reply_text("Peer id invalid or not known yet, Please PM first")
        return -1
    
    except Exception as e:
        # await msg.reply_text(e)
        await fn.send_trace(e, msg)
        return -1
        
@app.on_message(filters.command(['kang']))
async def kangfunc(client, msg):
    if await check_debug(msg) ==  -1:
        return
    
    if msg.reply_to_message == None or msg.reply_to_message.sticker == None:
        await msg.reply_text("you must reply to another sticker, not a message")
        return;
    
    database = g_dbctx["kangutils"]
    collection = database["stickerpack_state"]
    
    # find current sticker set
    dbquery = collection.find_one({'user_id': msg.from_user.id});
    
    print(dbquery)
    
    sanitized_input = fn.sanitize_emoji(msg)
    if sanitized_input["err"] == 1:
        await msg.reply_text(sanitized_input["msg"])
        return;

    if dbquery == None:
        fnret = await create_new_stickerpack(client, msg, sanitized_input, collection)
        if fnret != -1:
            collection.insert_one(
                {
                    'user_id': msg.from_user.id,
                    'current': fnret[0]
                }
            )
            
            return fnret[1]
    else:
        packshort = dbquery["current"]
        
        try:
            ret = await client.add_sticker_to_set(
                
                set_short_name=packshort,
                sticker=fn.get_file_id(msg),
                user_id=msg.from_user.id,
                emoji=sanitized_input["ret"]
            )
            
            await fn.rename_sticker(packshort, client)

            msgret = await msg.reply_text(f"<a href='https://t.me/addstickers/{ret.short_name}'>Kanged!</a>")
            
            return msgret
        except (pyroexception.bad_request_400.StickersTooMuch, 
                pyroexception.bad_request_400.StickersetInvalid):
            fnret = await create_new_stickerpack(client, msg, sanitized_input, collection)
            
            if fnret != -1:
                collection.update_one(
                    {
                        'user_id': msg.from_user.id
                    }, 
                    {
                        '$set': {
                            'current': fnret[0]
                        }
                    }
                )
        except Exception as e:
            await fn.send_trace(e, msg)
            
# @app.on_message(filters.command(['kang2']))
# async def kang2func(client, msg):
#     if msg.reply_to_message == None:
#         await msg.reply_text("you must reply to sticker or photo")
#     else:
#         msgret = await to_tsfunc(client, msg)
        
#         print(msgret)
#         await msg.reply_text("test")

@app.on_message(filters.command(['unkang']))
async def unkangfunc(client, msg):
    if await check_debug(msg) ==  -1:
        return
    
    if msg.reply_to_message == None:
        await msg.reply_text("you must reply to another message")
        return;
    
    try:
        decoded = FileId.decode(fn.get_file_id(msg))
    except TypeError:
        await msg.reply_text("Invalid reply, can't detect media")
    except Exception as e:
        await fn.send_trace(e, msg)

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
    if await check_debug(msg) ==  -1:
        return
    
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
    await msg.reply_text(f"sticker <a href='https://t.me/addstickers/{packshort}'>forked!</a>")


@app.on_message(filters.command(['to_ts', 'ts']))
async def to_tsfunc(client, msg):
    if await check_debug(msg) ==  -1:
        return
    
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
    
    
    return await client.send_sticker(
        chat_id=msg.chat.id,
        sticker=iomem,
        reply_to_message_id=msg.reply_to_message.id
    )
    
    
@app.on_message(filters.command(['packinfo']))
async def packinfofunc(client, msg):
    if await check_debug(msg) ==  -1:
        return
    
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
    
@app.on_message(filters.command(['del']))
async def msgdel(client, msg):
    if await check_debug(msg) ==  -1:
        return
    
    await client.delete_messages(
        chat_id=msg.chat.id,
        message_ids=msg.reply_to_message.id
    )
    
    
@app.on_message(filters.command(['toimg']))
async def toimgfunc(client, msg):
    if await check_debug(msg) ==  -1:
        return

    if msg.reply_to_message == None or msg.reply_to_message.sticker == None:
        await msg.reply_text("you must reply to sticker")
        return;
    
    
    
    if msg.reply_to_message.sticker.is_animated == False and msg.reply_to_message.sticker.is_video == False:
        byteres = await client.download_media(msg.reply_to_message, in_memory=True)
        
        bytepng = io.BytesIO();
        im = Image.open(byteres)
        im.save(bytepng, "png")
        
        await client.send_photo(
            chat_id=msg.chat.id,
            photo=bytepng,
            reply_to_message_id=msg.reply_to_message.id
        )
    elif msg.reply_to_message.sticker.is_animated == False and msg.reply_to_message.sticker.is_video == True:
        webppath = await client.download_media(msg.reply_to_message, in_memory=True)

        
        await client.send_animation(
            chat_id=msg.chat.id,
            animation=webppath,
            reply_to_message_id=msg.reply_to_message.id
        )
        # print("end")
        
    elif msg.reply_to_message.sticker.is_animated == True and msg.reply_to_message.sticker.is_video == False:
        
        await msg.reply_text("please be patient, rendering your animation")
        animationpath = await client.download_media(msg.reply_to_message)
        
        await convert_to_gif(animationpath)
        
        await client.send_document(
            chat_id=msg.chat.id,
            document=animationpath + ".gif",
            reply_to_message_id=msg.reply_to_message.id
        )
        
        os.remove(animationpath)
        os.remove(animationpath + ".gif")
        # print("end")
        
@app.on_message(filters.command(['sauce']))
async def reverseimg(client, msg):
    if await check_debug(msg) ==  -1:
        return
    
    if msg.reply_to_message != None:
        if msg.reply_to_message.sticker != None or msg.reply_to_message.photo != None:
        
            byteres = await client.download_media(msg.reply_to_message)
            
            client = imgbbpy.AsyncClient(os.getenv("IMGBB_API"))
            image = await client.upload(file=byteres)
            
            formatstr = f"""<a href="https://saucenao.com/search.php?url={image.url}">saucenao</a><br>
<a href="https://lens.google.com/uploadbyurl?url={image.url}">google</a>"""
            await msg.reply_text(formatstr)
            os.remove(byteres)

    else:
        await msg.reply_text("you must reply to a sticker / image")
        return;
    
app.run()
