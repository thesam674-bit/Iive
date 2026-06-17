import asyncio
import os
from datetime import datetime
import aiosqlite
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand
from aiogram.filters import Command

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
DB = "usernames.db"

bot = Bot(TOKEN)
dp = Dispatcher()

# --- DATABASE SETUP ---
async def db_init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS usernames(username TEXT PRIMARY KEY, added TEXT, tracking INTEGER DEFAULT 0, views INTEGER DEFAULT 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)")
        await db.commit()

# --- ADMIN PANEL LOGIC ---
@dp.message(Command("admin"))
async def admin_panel(m: Message):
    if m.from_user.id != OWNER_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧹 Auto-Cleanup (Low Views)", callback_data="admin_clean")],
        [InlineKeyboardButton(text="⚙️ Edit Settings", callback_data="admin_edit")]
    ])
    await m.answer("🛠 **PRO OWNER PANEL**\nManage bot and database here.", reply_markup=kb)

@dp.callback_query(F.data == "admin_clean")
async def auto_clean(c: CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM usernames WHERE views < 10")
        await db.commit()
    await c.answer("✅ Low view items cleaned!", show_alert=True)

# --- PAGINATION LOGIC ---
async def show_list(c: CallbackQuery, page: int):
    limit = 8
    offset = page * limit
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT username, views FROM usernames LIMIT ? OFFSET ?", (limit, offset)) as cur:
            rows = await cur.fetchall()
        async with db.execute("SELECT COUNT(*) FROM usernames") as cur:
            total = (await cur.fetchone())[0]

    if not rows: return await c.answer("List empty!")
    text = f"📜 **USERNAME LIST | Page {page+1}**\n\n" + "\n".join([f"• @{r[0]} | 👁 {r[1]} views" for r in rows])
    btns = []
    if page > 0: btns.append(InlineKeyboardButton(text="« Prev", callback_data=f"list_{page-1}"))
    if (offset + limit) < total: btns.append(InlineKeyboardButton(text="Next »", callback_data=f"list_{page+1}"))
    await c.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[btns]))

@dp.callback_query(F.data.startswith("list_"))
async def list_nav(c: CallbackQuery):
    await show_list(c, int(c.data.split("_")[1]))

# --- COMMANDS ---
@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 List", callback_data="list_0"), InlineKeyboardButton(text="💡 Help", callback_data="help")],
        [InlineKeyboardButton(text="🔎 Check", callback_data="check_cmd")]
    ])
    await m.answer("🚀 **Welcome to Pro Username Manager**\nManage your assets with ease.", reply_markup=kb)

@dp.message(Command("add"))
async def add(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Usage: `/add @username`")
    u = args[1].replace("@", "")
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO usernames (username, added) VALUES(?,?)", (u, now()))
        await db.commit()
    await m.answer(f"✅ `@{u}` added!")

@dp.message(Command("check"))
async def check(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Usage: `/check @username`")
    u = args[1].replace("@", "")
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT views FROM usernames WHERE username=?", (u,))
        row = await cur.fetchone()
    await m.answer(f"🔎 Status: **Found** ✅\n👁 Views: `{row[0]}`" if row else "❌ **Not Found**")

@dp.message(Command("stats"))
async def stats(m: Message):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT COUNT(*) FROM usernames")
        count = (await cur.fetchone())[0]
    await m.answer(f"📊 **Total Database Count**: `{count}`")

# --- APP START ---
async def main():
    await db_init()
    print("Bot is running...")
    await dp.start_polling(bot)

def now(): return datetime.now().strftime("%d-%m-%Y")

if __name__ == "__main__":
    asyncio.run(main())
    
