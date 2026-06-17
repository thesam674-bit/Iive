import asyncio
import os
from datetime import datetime
import aiosqlite
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
DB = "usernames.db"

bot = Bot(TOKEN)
dp = Dispatcher()

# --- HELPER ---
def now(): return datetime.now().strftime("%d %B %Y | %I:%M %p")

# --- DB INIT ---
async def db_init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS usernames(username TEXT PRIMARY KEY, added TEXT, views INTEGER DEFAULT 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)")
        await db.commit()

# --- START (Language Selection) ---
@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇮🇳 Hindi", callback_data="lang_hi"), 
         InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
    ])
    await m.answer("🚀 **Welcome to Username Pro**\nSelect your language:", reply_markup=kb)

@dp.callback_query(F.data.startswith("lang_"))
async def main_menu(c: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 User List", callback_data="list_0")],
        [InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")]
    ])
    await c.message.edit_text("✅ **Main Menu**\nManage usernames efficiently.", reply_markup=kb)

# --- LIST & PAGINATION (Pro) ---
async def show_list(c: CallbackQuery, page: int):
    limit = 8
    offset = page * limit
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT username, views FROM usernames LIMIT ? OFFSET ?", (limit, offset))
        rows = await cur.fetchall()
        total = (await db.execute("SELECT count(*) FROM usernames")).fetchone()[0]

    if not rows: return await c.answer("No users!")
    
    text = f"📜 **User List - Page {page+1}**\n\n" + "\n".join([f"• `@{r[0]}` | 👁 {r[1]} views" for r in rows])
    btns = []
    if page > 0: btns.append(InlineKeyboardButton(text="« Prev", callback_data=f"list_{page-1}"))
    if (offset + limit) < total: btns.append(InlineKeyboardButton(text="Next »", callback_data=f"list_{page+1}"))
    
    await c.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[btns]), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("list_"))
async def nav(c: CallbackQuery): await show_list(c, int(c.data.split("_")[1]))

# --- ADMIN PANEL (Fixed & Pro) ---
@dp.callback_query(F.data == "admin_panel")
async def admin(c: CallbackQuery):
    if c.from_user.id != OWNER_ID: return await c.answer("❌ Access Denied!", show_alert=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧹 Auto-Cleanup (Low Views)", callback_data="clean_low")],
        [InlineKeyboardButton(text="📢 Broadcast Message", callback_data="broadcast")],
        [InlineKeyboardButton(text="« Back", callback_data="list_0")]
    ])
    await c.message.edit_text("🛠 **Owner Control Panel**", reply_markup=kb)

@dp.callback_query(F.data == "clean_low")
async def clean(c: CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM usernames WHERE views < 10")
        await db.commit()
    await c.answer("✅ Low views cleared!", show_alert=True)

# --- RUN ---
async def main():
    await db_init()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
