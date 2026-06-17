import asyncio
import os
from datetime import datetime

import aiosqlite
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import Message, BotCommand
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



def is_owner(m):
    return m.from_user.id == OWNER_ID



async def init_db():

    async with aiosqlite.connect(DB) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS usernames(
            username TEXT PRIMARY KEY,
            added TEXT,
            tracking INTEGER DEFAULT 0
        )
        """)

        await db.commit()



async def set_commands():

    commands = [

        BotCommand(command="start",
        description="Start bot"),

        BotCommand(command="help",
        description="Commands list"),

        BotCommand(command="add",
        description="Add username"),

        BotCommand(command="list",
        description="Saved usernames"),

        BotCommand(command="remove",
        description="Remove username"),

        BotCommand(command="live",
        description="Start tracking"),

        BotCommand(command="tlist",
        description="Tracking list"),

        BotCommand(command="stop",
        description="Stop tracking"),

        BotCommand(command="worth",
        description="Username value"),

        BotCommand(command="stats",
        description="Bot stats"),

    ]

    await bot.set_my_commands(commands)





@dp.message(Command("start"))
async def start(m:Message):

    await m.answer(
"""Username Manager Pro

Use /help to view commands."""
    )





@dp.message(Command("help"))
async def help(m:Message):

    await m.answer("""
Username Manager Pro

Commands:

/add @username
Add usernames

/list
Saved usernames

/remove @username
Remove username

/live @username
Start tracking

/tlist
Tracking list

/stop @username
Stop tracking

/worth @username
Check value

/stats
Bot stats


Owner:

/clear
Clear data

/deleteall
Delete database

/broadcast text
Send message
""")





@dp.message(Command("add"))
async def add(m:Message):

    users = m.text.split()[1:]

    if not users:
        return await m.answer(
        "Use: /add @username"
        )


    async with aiosqlite.connect(DB) as db:

        for u in users:

            await db.execute(
            "INSERT OR IGNORE INTO usernames VALUES(?,?,0)",
            (
                u.replace("@",""),
                now()
            )
            )

        await db.commit()


    await m.answer(
    "Usernames added."
    )





@dp.message(Command("list"))
async def list_cmd(m:Message):

    async with aiosqlite.connect(DB) as db:

        cur = await db.execute(
        "SELECT username,added FROM usernames"
        )

        rows = await cur.fetchall()


    if not rows:
        return await m.answer(
        "No usernames found."
        )


    text="Saved Usernames\n\n"


    for i,r in enumerate(rows,1):

        text += f"""
{i}. @{r[0]}
Added: {r[1]}

"""


    await m.answer(text)





@dp.message(Command("remove"))
async def remove(m:Message):

    args=m.text.split()

    if len(args)<2:
        return


    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "DELETE FROM usernames WHERE username=?",
        (args[1].replace("@",""),)
        )

        await db.commit()


    await m.answer(
    "Username removed."
    )





@dp.message(Command("live"))
async def live(m:Message):

    args=m.text.split()

    if len(args)<2:
        return


    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "UPDATE usernames SET tracking=1 WHERE username=?",
        (args[1].replace("@",""),)
        )

        await db.commit()


    await m.answer(
    "Tracking started."
    )





@dp.message(Command("tlist"))
async def tlist(m:Message):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT username,added FROM usernames WHERE tracking=1"
        )

        rows=await cur.fetchall()


    if not rows:
        return await m.answer(
        "No tracking usernames."
        )


    text="Tracking List\n\n"

    for r in rows:

        text += f"""
@{r[0]}
Started: {r[1]}

"""


    await m.answer(text)





@dp.message(Command("stop"))
async def stop(m:Message):

    args=m.text.split()

    if len(args)<2:
        return


    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "UPDATE usernames SET tracking=0 WHERE username=?",
        (args[1].replace("@",""),)
        )

        await db.commit()


    await m.answer(
    "Tracking stopped."
    )





@dp.message(Command("worth"))
async def worth(m:Message):

    args=m.text.split()

    if len(args)<2:
        return


    u=args[1].replace("@","")

    score=100-len(u)*5

    if score<10:
        score=10


    await m.answer(f"""
Username Analysis

Username:
@{u}

Length:
{len(u)}

Score:
{score}/100

Type:
Premium estimate

Note:
Market value depends on Fragment demand.
""")





@dp.message(Command("stats"))
async def stats(m:Message):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT COUNT(*),SUM(tracking) FROM usernames"
        )

        r=await cur.fetchone()


    await m.answer(f"""
Bot Stats

Saved:
{r[0]}

Tracking:
{r[1] or 0}

Status:
Online
""")





# OWNER


@dp.message(Command("clear"))
async def clear(m:Message):

    if not is_owner(m):
        return

    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "DELETE FROM usernames"
        )

        await db.commit()


    await m.answer(
    "Database cleared."
    )




@dp.message(Command("deleteall"))
async def deleteall(m:Message):

    if not is_owner(m):
        return

    await clear(m)





@dp.message(Command("broadcast"))
async def broadcast(m:Message):

    if not is_owner(m):
        return

    msg=m.text.replace(
    "/broadcast",""
    ).strip()


    await m.answer(
    "Broadcast sent:\n"+msg
    )





async def main():

    await init_db()

    await set_commands()

    await dp.start_polling(bot)



asyncio.run(main())
