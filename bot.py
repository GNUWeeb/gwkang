from pyrogram import Client, filters
import os
import io
import tempfile
import shutil
import utilsfunc as fn

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

app.run()
