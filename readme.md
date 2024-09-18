## gwkang
GNU/Weeb kang util bot

## Installation
```sh
sudo apt-get install python3-pip python3-venv
git clone https://github.com/GNUWeeb/gwkang.git
cd gwkang
mkdir venv && cd venv
python -m venv .
cd ..
./venv/bin/pip3 install -r requirements.txt
./venv/bin/python bot.py
```

nb: rename .env.example -> .env

## Feature
```
kang - kanging sticker into pack
unkang - unkanging sticker
fork - fork your own sticker
dbg - show json output
dfid - show file_id
packinfo - show sticker pack info
to_ts - turn into document

```

## license
MIT