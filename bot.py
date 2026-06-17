import asyncio
import os
from datetime import datetime

import aiosqlite
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OWNER = int(os.getenv("OWNER_ID"))

bot = Bot(TOKEN)
dp = Dispatcher()

DB = "usernames.db"


async def db():
    async with aiosqlite.connect(DB) as con:
        await con.execute("""
        CREATE TABLE IF NOT EXISTS names(
        username TEXT PRIMARY KEY,
        added TEXT,
        tracking INTEGER DEFAULT 0
        )
        """)
        await con.commit()


def time_now():
    return datetime.now().strftime("%d %B %Y | %I:%M %p")


def is_owner(m):
    return m.from_user.id == OWNER


@dp.message(Command("start"))
async def start(m:Message):
    await m.answer(
    "🤖 Username Manager Bot\n\n/help use karo"
    )


@dp.message(Command("help"))
async def help(m:Message):
    await m.answer("""
Commands:

/add @user
/list
/remove @user
/live @user
/tlist
/stop @user
/worth @user
/stats

Owner:
/clear
/broadcast text
/users
""")


@dp.message(Command("add"))
async def add(m:Message):
    users=m.text.split()[1:]

    if not users:
        return await m.answer("Use: /add @username")

    async with aiosqlite.connect(DB) as con:
        for u in users:
            await con.execute(
            "INSERT OR IGNORE INTO names VALUES(?,?,0)",
            (u.replace("@",""),time_now())
            )

        await con.commit()

    await m.answer("✅ Added usernames")


@dp.message(Command("list"))
async def list_cmd(m:Message):
    async with aiosqlite.connect(DB) as con:
        cur=await con.execute(
        "SELECT username,added FROM names")
        rows=await cur.fetchall()

    if not rows:
        return await m.answer("Empty")

    text="📋 List\n\n"

    for i,r in enumerate(rows,1):
        text+=f"{i}. @{r[0]}\nAdded: {r[1]}\n\n"

    text+="\nRemove: /remove @username"

    await m.answer(text)


@dp.message(Command("remove"))
async def remove(m:Message):
    u=m.text.split()

    if len(u)<2:
        return await m.answer("Use /remove @user")

    async with aiosqlite.connect(DB) as con:
        await con.execute(
        "DELETE FROM names WHERE username=?",
        (u[1].replace("@",""),))
        await con.commit()

    await m.answer("✅ Removed")


@dp.message(Command("live"))
async def live(m:Message):
    u=m.text.split()

    if len(u)<2:
        return await m.answer("Use /live @user")

    async with aiosqlite.connect(DB) as con:
        await con.execute(
        "UPDATE names SET tracking=1 WHERE username=?",
        (u[1].replace("@",""),))
        await con.commit()

    await m.answer("🔎 Tracking started")


@dp.message(Command("tlist"))
async def tlist(m:Message):
    async with aiosqlite.connect(DB) as con:
        cur=await con.execute(
        "SELECT username,added FROM names WHERE tracking=1")
        rows=await cur.fetchall()

    if not rows:
        return await m.answer("No tracking")

    text="🔎 Tracking\n\n"

    for r in rows:
        text+=f"@{r[0]}\nStarted: {r[1]}\n\n"

    await m.answer(text)


@dp.message(Command("stop"))
async def stop(m:Message):

    u=m.text.split()

    if len(u)<2:
        return

    async with aiosqlite.connect(DB) as con:
        await con.execute(
        "UPDATE names SET tracking=0 WHERE username=?",
        (u[1].replace("@",""),))
        await con.commit()

    await m.answer("⛔ Tracking stopped")


@dp.message(Command("worth"))
async def worth(m:Message):

    u=m.text.split()

    if len(u)<2:
        return

    name=u[1].replace("@","")

    score=max(1,10-len(name))

    await m.answer(f"""
💎 Username Analysis

@{name}

Length: {len(name)}
Score: {score}/10

Estimated:
Check Fragment market manually
""")


@dp.message(Command("stats"))
async def stats(m:Message):

    async with aiosqlite.connect(DB) as con:
        cur=await con.execute(
        "SELECT COUNT(*),SUM(tracking) FROM names")
        r=await cur.fetchone()

    await m.answer(
    f"📊 Stats\n\nSaved: {r[0]}\nTracking: {r[1] or 0}"
    )


# OWNER

@dp.message(Command("clear"))
async def clear(m:Message):

    if not is_owner(m):
        return

    async with aiosqlite.connect(DB) as con:
        await con.execute("DELETE FROM names")
        await con.commit()

    await m.answer("Database cleared")


@dp.message(Command("broadcast"))
async def broadcast(m:Message):

    if not is_owner(m):
        return

    await m.answer("Broadcast system ready")


async def main():
    await db()
    await dp.start_polling(bot)


asyncio.run(main())
