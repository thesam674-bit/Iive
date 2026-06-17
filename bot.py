import asyncio
from datetime import datetime

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DB = "usernames.db"

bot = Bot(TOKEN)
dp = Dispatcher()


def now():
    return datetime.now().strftime("%d %B %Y | %I:%M %p")


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


@dp.message(Command("start"))
async def start(m: Message):
    await m.answer(
        "🤖 Username Manager Bot\n\n/help"
    )


@dp.message(Command("help"))
async def help(m: Message):
    await m.answer("""
Commands:

/add @username
/list
/remove @username

/live @username
/tlist
/stop @username

/worth @username
/stats


Owner:

/clear
/deleteall
/users
/broadcast text
""")


@dp.message(Command("add"))
async def add(m: Message):

    users = m.text.split()[1:]

    if not users:
        return await m.answer("Use /add @username")

    async with aiosqlite.connect(DB) as db:

        for u in users:
            await db.execute(
            "INSERT OR IGNORE INTO usernames VALUES(?,?,0)",
            (
                u.replace("@",""),
                now()
            ))

        await db.commit()

    await m.answer("✅ Added")


@dp.message(Command("list"))
async def listing(m: Message):

    async with aiosqlite.connect(DB) as db:

        cur = await db.execute(
        "SELECT username,added FROM usernames"
        )

        rows = await cur.fetchall()


    if not rows:
        return await m.answer("Empty")

    text="📋 Username List\n\n"

    for i,r in enumerate(rows,1):

        text += f"""
{i}. @{r[0]}
Added: {r[1]}

"""

    await m.answer(text)



@dp.message(Command("remove"))
async def remove(m: Message):

    u=m.text.split()

    if len(u)<2:
        return

    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "DELETE FROM usernames WHERE username=?",
        (u[1].replace("@",""),))

        await db.commit()


    await m.answer("✅ Removed")



@dp.message(Command("live"))
async def live(m: Message):

    u=m.text.split()

    if len(u)<2:
        return

    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "UPDATE usernames SET tracking=1 WHERE username=?",
        (u[1].replace("@",""),))

        await db.commit()

    await m.answer("🔎 Tracking Started")



@dp.message(Command("tlist"))
async def tlist(m: Message):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT username,added FROM usernames WHERE tracking=1"
        )

        rows=await cur.fetchall()


    text="🔎 Tracking List\n\n"

    for r in rows:
        text+=f"@{r[0]}\nStarted: {r[1]}\n\n"

    await m.answer(text)



@dp.message(Command("stop"))
async def stop(m: Message):

    u=m.text.split()

    if len(u)<2:
        return

    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "UPDATE usernames SET tracking=0 WHERE username=?",
        (u[1].replace("@",""),))

        await db.commit()


    await m.answer("⛔ Stopped")



@dp.message(Command("worth"))
async def worth(m: Message):

    u=m.text.split()

    if len(u)<2:
        return

    name=u[1].replace("@","")

    await m.answer(f"""
💎 Username Worth

Username: @{name}

Length: {len(name)}

Market:
Check Fragment for live price
""")



@dp.message(Command("stats"))
async def stats(m: Message):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT COUNT(*) FROM usernames")

        total=await cur.fetchone()


    await m.answer(
    f"📊 Saved: {total[0]}"
    )



# OWNER

@dp.message(Command("clear"))
async def clear(m: Message):

    if not is_owner(m):
        return

    async with aiosqlite.connect(DB) as db:

        await db.execute("DELETE FROM usernames")
        await db.commit()

    await m.answer("🗑 Cleared")



@dp.message(Command("deleteall"))
async def deleteall(m: Message):

    if not is_owner(m):
        return

    await clear(m)



@dp.message(Command("users"))
async def users(m: Message):

    if not is_owner(m):
        return

    await m.answer("Owner command")



@dp.message(Command("broadcast"))
async def broadcast(m: Message):

    if not is_owner(m):
        return

    msg=m.text.replace("/broadcast","").strip()

    await m.answer(
    "✅ Broadcast:\n"+msg
    )



async def main():

    await init_db()

    await dp.start_polling(bot)



asyncio.run(main())
