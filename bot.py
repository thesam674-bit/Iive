import asyncio
import os
from datetime import datetime
import aiosqlite
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, 
    CallbackQuery, BotCommand
)
from aiogram.filters import Command, CommandObject

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
DB = "usernames.db"

bot = Bot(TOKEN)
dp = Dispatcher()

def now(): return datetime.now().strftime("%d %B %Y | %I:%M %p")

async def db_init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS usernames(
        username TEXT PRIMARY KEY, added TEXT, tracking INTEGER DEFAULT 0, views INTEGER DEFAULT 0
        )""")
        await db.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)")
        await db.commit()

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def admin_panel(m: Message):
    if m.from_user.id != OWNER_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧹 Cleanup Low Views", callback_data="admin_clean")],
        [InlineKeyboardButton(text="⚙️ Edit Settings", callback_data="admin_edit")]
    ])
    await m.answer("🛠 **PRO OWNER PANEL**\nManage your bot here.", reply_markup=kb)

@dp.callback_query(F.data == "admin_clean")
async def auto_clean(c: CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM usernames WHERE views < 5")
        await db.commit()
    await c.answer("✅ Cleanup Done: Deleted usernames with low views!", show_alert=True)

# --- PAGINATION ---
async def show_list(target, page):
    limit = 8
    offset = page * limit
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT username, views FROM usernames LIMIT ? OFFSET ?", (limit, offset)) as cur:
            rows = await cur.fetchall()
        async with db.execute("SELECT COUNT(*) FROM usernames") as cur:
            total = (await cur.fetchone())[0]

    if not rows: return await target.answer("List is empty!")

    text = f"📜 **USERNAME LIST | Page {page+1}**\n\n"
    for r in rows: text += f"• `@{r[0]}` | 👁 {r[1]} views\n"

    btn = []
    if page > 0: btn.append(InlineKeyboardButton(text="« Prev", callback_data=f"list_{page-1}"))
    if (offset + limit) < total: btn.append(InlineKeyboardButton(text="Next »", callback_data=f"list_{page+1}"))
    
    kb = InlineKeyboardMarkup(inline_keyboard=[btn])
    if isinstance(target, Message): await target.answer(text, reply_markup=kb, parse_mode="Markdown")
    else: await target.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("list"))
async def list_cmd(m: Message): await show_list(m, 0)

@dp.callback_query(F.data.startswith("list_"))
async def page_nav(c: CallbackQuery): await show_list(c, int(c.data.split("_")[1]))

# --- CORE COMMANDS ---
@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 List View", callback_data="list_0")],
        [InlineKeyboardButton(text="💡 Help", callback_data="help_menu")]
    ])
    await m.answer("🚀 **Username Manager Pro**\nSelect an option below.", reply_markup=kb)

@dp.message(Command("add"))
async def add(m: Message, command: CommandObject):
    if not command.args: return await m.answer("❌ Usage: `/add @username`")
    u = command.args.replace("@", "")
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO usernames (username, added) VALUES(?,?)", (u, now()))
        await db.commit()
    await m.answer(f"✅ Added: `@{u}`")

@dp.message(Command("check"))
async def check(m: Message, command: CommandObject):
    if not command.args: return await m.answer("Usage: `/check @username`")
    u = command.args.replace("@", "")
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT views FROM usernames WHERE username=?", (u,))
        row = await cur.fetchone()
    await m.answer(f"🔎 Status: **Found** ✅\n👁 Views: `{row[0]}`" if row else "❌ **Not Found**", parse_mode="Markdown")

@dp.message(Command("stats"))
async def stats(m: Message):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT COUNT(*) FROM usernames")
        count = (await cur.fetchone())[0]
    await m.answer(f"📊 **Total Database Count**: `{count}`", parse_mode="Markdown")

# --- MAIN ---
async def main():
    await db_init()
    await bot.set_my_commands([
        BotCommand(command="start", description="Start bot"),
        BotCommand(command="add", description="Add user"),
        BotCommand(command="list", description="View all"),
        BotCommand(command="check", description="Check availability"),
        BotCommand(command="admin", description="Admin Panel")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
