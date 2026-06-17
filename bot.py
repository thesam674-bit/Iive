import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# --- CONFIG ---
TOKEN = "YOUR_BOT_TOKEN_HERE"
OWNER_ID = 123456789 # Apni ID yahan daalo
DB = "usernames.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DB INIT ---
async def db_init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS usernames(username TEXT PRIMARY KEY, views INTEGER DEFAULT 0)")
        await db.commit()

# --- START WITH LANGUAGE SELECTOR ---
@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇮🇳 Hindi", callback_data="lang_hi"), 
         InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
    ])
    await m.answer("🚀 **Welcome to Username Pro**\nSelect your language to continue:", reply_markup=kb)

# --- LANGUAGE & MAIN MENU ---
@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(c: CallbackQuery):
    lang = c.data.split("_")[1]
    text = "नमस्ते! आप अब हिंदी मोड में हैं।" if lang == "hi" else "Hello! You are now in English mode."
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 List", callback_data="list_0")],
        [InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_menu")]
    ])
    await c.message.edit_text(f"{text}\n\nSelect an action:", reply_markup=kb)
    await c.answer()

# --- PAGINATION (FIXED) ---
async def show_list(c: CallbackQuery, page: int):
    limit = 5
    offset = page * limit
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT username FROM usernames LIMIT ? OFFSET ?", (limit, offset))
        rows = await cur.fetchall()
        cur_total = await db.execute("SELECT count(*) FROM usernames")
        total = (await cur_total.fetchone())[0]

    if not rows: return await c.answer("No users!")
    
    text = f"📜 **Page {page+1}**\n" + "\n".join([f"• @{r[0]}" for r in rows])
    btns = []
    if page > 0: btns.append(InlineKeyboardButton(text="« Prev", callback_data=f"list_{page-1}"))
    if (offset + limit) < total: btns.append(InlineKeyboardButton(text="Next »", callback_data=f"list_{page+1}"))
    
    await c.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[btns]))

@dp.callback_query(F.data.startswith("list_"))
async def nav_list(c: CallbackQuery):
    await show_list(c, int(c.data.split("_")[1]))

# --- ADMIN PANEL ---
@dp.callback_query(F.data == "admin_menu")
async def admin(c: CallbackQuery):
    if c.from_user.id != OWNER_ID: return await c.answer("❌ Access Denied!")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧹 Clear Low Views", callback_data="admin_clean")]
    ])
    await c.message.edit_text("🛠 **Admin Panel**", reply_markup=kb)

@dp.callback_query(F.data == "admin_clean")
async def admin_clean(c: CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM usernames WHERE views < 10")
        await db.commit()
    await c.answer("✅ Cleaned!", show_alert=True)

# --- RUN ---
async def main():
    await db_init()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
