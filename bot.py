from pyrogram import Client, filters
import os
import io
import tempfile
import shutil

from pymongo import MongoClient
from dotenv import load_dotenv
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
    

app.run()
