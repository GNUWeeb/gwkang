import aiohttp
import asyncio

async def main():
        fd = open("aa.cc", "rb");
        
        mail_gun_data = {
                "file": fd
        }
        
        async with aiohttp.ClientSession() as session:
                with aiohttp.MultipartWriter("form-data") as mp:
                        for key, value in mail_gun_data.items():
                                part = mp.append(value)
                                part.set_content_disposition('form-data', name=key)
                        resp = await session.post(
                                "https://0x0.st/",
                                data=mp,
                        )
                        
                        print(await resp.text())

asyncio.run(main())
