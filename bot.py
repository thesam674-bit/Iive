import asyncio
import os
from datetime import datetime

import aiosqlite
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    BotCommand
)
from aiogram.filters import Command


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DB = "usernames.db"


bot = Bot(TOKEN)
dp = Dispatcher()



def now():
    return datetime.now().strftime(
        "%d %B %Y | %I:%M %p"
    )



def owner(m):
    return m.from_user.id == OWNER_ID



async def db_init():

    async with aiosqlite.connect(DB) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS usernames(
        username TEXT PRIMARY KEY,
        added TEXT,
        tracking INTEGER DEFAULT 0
        )
        """)

        await db.commit()



async def commands():

    await bot.set_my_commands([
        BotCommand("start","Start bot"),
        BotCommand("help","Commands"),
        BotCommand("add","Add username"),
        BotCommand("list","Username list"),
        BotCommand("time","Added time"),
        BotCommand("remove","Remove username"),
        BotCommand("live","Track username"),
        BotCommand("tlist","Tracking list"),
        BotCommand("stop","Stop tracking"),
        BotCommand("worth","Username value"),
        BotCommand("stats","Bot stats")
    ])





@dp.message(Command("start"))
async def start(m:Message):

    kb = InlineKeyboardMarkup(
    inline_keyboard=[

        [
        InlineKeyboardButton(
        text="List",
        callback_data="list_0")
        ],

        [
        InlineKeyboardButton(
        text="Stats",
        callback_data="stats")
        ]

    ])

    await m.answer(
    "Username Manager Pro\n\nUse /help",
    reply_markup=kb
    )





@dp.message(Command("help"))
async def help(m:Message):

    await m.answer("""
Username Manager Pro

/add @user
Add username

/list
View usernames

/time @user
Added date

/remove @user
Remove

/live @user
Start tracking

/tlist
Tracking list

/stop @user
Stop tracking

/worth @user
Value check

/stats
Statistics
""")





@dp.message(Command("add"))
async def add(m:Message):

    users=m.text.split()[1:]

    if not users:
        return await m.answer(
        "Use /add @username"
        )


    async with aiosqlite.connect(DB) as db:

        for u in users:

            await db.execute(
            "INSERT OR IGNORE INTO usernames VALUES(?,?,0)",
            (
            u.replace("@",""),
            now()
            ))

        await db.commit()


    await m.answer(
    "Username saved."
    )






async def show_list(target,page):

    limit=10
    offset=page*limit


    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT username FROM usernames LIMIT ? OFFSET ?",
        (limit,offset)
        )

        rows=await cur.fetchall()


        cur=await db.execute(
        "SELECT COUNT(*) FROM usernames"
        )

        total=await cur.fetchone()



    if not rows:
        return


    text=f"Username List\nPage {page+1}\n\n"


    for i,r in enumerate(rows,offset+1):

        text+=f"{i}. @{r[0]}\n"



    btn=[]


    if page>0:

        btn.append(
        InlineKeyboardButton(
        text="Back",
        callback_data=f"list_{page-1}"
        ))


    if offset+limit < total[0]:

        btn.append(
        InlineKeyboardButton(
        text="Next",
        callback_data=f"list_{page+1}"
        ))



    kb=InlineKeyboardMarkup(
    inline_keyboard=[btn]
    )


    if isinstance(target,Message):

        await target.answer(
        text,
        reply_markup=kb
        )

    else:

        await target.message.edit_text(
        text,
        reply_markup=kb
        )





@dp.message(Command("list"))
async def list_cmd(m:Message):

    await show_list(m,0)





@dp.callback_query(lambda c:c.data.startswith("list_"))
async def page(c:CallbackQuery):

    await show_list(
    c,
    int(c.data.split("_")[1])
    )





@dp.message(Command("time"))
async def time_cmd(m:Message):

    u=m.text.split()[1].replace("@","")


    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT added FROM usernames WHERE username=?",
        (u,)
        )

        r=await cur.fetchone()


    if not r:
        return await m.answer(
        "Not found."
        )


    await m.answer(
    f"@{u}\nAdded:\n{r[0]}"
    )





@dp.message(Command("remove"))
async def remove(m:Message):

    u=m.text.split()[1].replace("@","")


    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "DELETE FROM usernames WHERE username=?",
        (u,)
        )

        await db.commit()


    await m.answer(
    "Removed."
    )





@dp.message(Command("live"))
async def live(m:Message):

    u=m.text.split()[1].replace("@","")


    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "UPDATE usernames SET tracking=1 WHERE username=?",
        (u,)
        )

        await db.commit()


    await m.answer(
    "Tracking started."
    )





@dp.message(Command("tlist"))
async def tlist(m:Message):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT username FROM usernames WHERE tracking=1"
        )

        rows=await cur.fetchall()


    text="Tracking\n\n"

    for x in rows:
        text+=f"@{x[0]}\n"


    await m.answer(text)





@dp.message(Command("stop"))
async def stop(m:Message):

    u=m.text.split()[1].replace("@","")


    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "UPDATE usernames SET tracking=0 WHERE username=?",
        (u,)
        )

        await db.commit()


    await m.answer(
    "Stopped."
    )





@dp.message(Command("worth"))
async def worth(m:Message):

    u=m.text.split()[1].replace("@","")

    await m.answer(f"""
Username:
@{u}

Length:
{len(u)}

Estimate:
Based on rarity

Fragment:
Check market listings
""")





@dp.message(Command("stats"))
async def stats(m:Message):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT COUNT(*) FROM usernames"
        )

        r=await cur.fetchone()


    await m.answer(
    f"Saved usernames: {r[0]}"
    )





async def main():

    await db_init()

    await commands()

    await dp.start_polling(bot)



asyncio.run(main())
