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
    return datetime.now().strftime("%d %B %Y | %I:%M %p")

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
        BotCommand(command="start", description="Start bot"),
        BotCommand(command="help", description="Commands"),
        BotCommand(command="add", description="Add username"),
        BotCommand(command="list", description="Username list"),
        BotCommand(command="time", description="Added time"),
        BotCommand(command="remove", description="Remove username"),
        BotCommand(command="live", description="Track username"),
        BotCommand(command="tlist", description="Tracking list"),
        BotCommand(command="stop", description="Stop tracking"),
        BotCommand(command="worth", description="Username value"),
        BotCommand(command="stats", description="Bot stats")
    ])

@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="List", callback_data="list_0")],
        [InlineKeyboardButton(text="Stats", callback_data="stats")]
    ])
    await m.answer("Username Manager Pro\n\nUse /help", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "stats")
async def stats_callback(c: CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT COUNT(*) FROM usernames") as cur:
            r = await cur.fetchone()
    await c.answer(f"Total: {r[0]}", show_alert=True)

@dp.message(Command("help"))
async def help(m: Message):
    await m.answer("Username Manager Pro\n\n/add @user\n/list\n/time @user\n/remove @user\n/live @user\n/tlist\n/stop @user\n/worth @user\n/stats")

@dp.message(Command("add"))
async def add(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Use /add @username")
    async with aiosqlite.connect(DB) as db:
        for u in args[1:]:
            await db.execute("INSERT OR IGNORE INTO usernames VALUES(?,?,0)", (u.replace("@", ""), now()))
        await db.commit()
    await m.answer("Username saved.")

async def show_list(target, page):
    limit = 10
    offset = page * limit
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT username FROM usernames LIMIT ? OFFSET ?", (limit, offset)) as cur:
            rows = await cur.fetchall()
        async with db.execute("SELECT COUNT(*) FROM usernames") as cur:
            total = await cur.fetchone()

    if not rows:
        return await target.answer("List khaali hai.") if isinstance(target, Message) else await target.answer("List khaali hai.")

    text = f"Username List (Page {page+1})\n\n"
    for i, r in enumerate(rows, offset + 1):
        text += f"{i}. @{r[0]}\n"

    btn = []
    if page > 0: btn.append(InlineKeyboardButton(text="⬅️ Back", callback_data=f"list_{page-1}"))
    if (offset + limit) < total[0]: btn.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"list_{page+1}"))

    kb = InlineKeyboardMarkup(inline_keyboard=[btn] if btn else [])
    
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.edit_text(text, reply_markup=kb)
        await target.answer()

@dp.message(Command("list"))
async def list_cmd(m: Message):
    await show_list(m, 0)

@dp.callback_query(lambda c: c.data and c.data.startswith("list_"))
async def page_callback(c: CallbackQuery):
    await show_list(c, int(c.data.split("_")[1]))

@dp.message(Command("time"))
async def time_cmd(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Use /time @username")
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT added FROM usernames WHERE username=?", (args[1].replace("@", ""),)) as cur:
            r = await cur.fetchone()
    await m.answer(f"Added: {r[0]}" if r else "Not found.")

@dp.message(Command("remove"))
async def remove(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Use /remove @username")
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM usernames WHERE username=?", (args[1].replace("@", ""),))
        await db.commit()
    await m.answer("Removed.")

@dp.message(Command("live"))
async def live(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Use /live @username")
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE usernames SET tracking=1 WHERE username=?", (args[1].replace("@", ""),))
        await db.commit()
    await m.answer("Tracking started.")

@dp.message(Command("tlist"))
async def tlist(m: Message):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT username FROM usernames WHERE tracking=1") as cur:
            rows = await cur.fetchall()
    await m.answer("Tracking:\n" + "\n".join([f"@{x[0]}" for x in rows]) if rows else "No tracking.")

@dp.message(Command("stop"))
async def stop(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Use /stop @username")
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE usernames SET tracking=0 WHERE username=?", (args[1].replace("@", ""),))
        await db.commit()
    await m.answer("Stopped.")

@dp.message(Command("worth"))
async def worth(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Use /worth @username")
    await m.answer(f"@{args[1].replace('@','')} Value: Check market.")

@dp.message(Command("stats"))
async def stats(m: Message):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT COUNT(*) FROM usernames") as cur:
            r = await cur.fetchone()
    await m.answer(f"Total usernames: {r[0]}")

async def main():
    await db_init()
    await commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
