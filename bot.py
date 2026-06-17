import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# --- CONFIG ---
TOKEN = "YOUR_BOT_TOKEN_HERE"
OWNER_ID = 123456789  # Apna ID yahan dalein
DB = "usernames.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DB INIT ---
async def db_init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS usernames(username TEXT PRIMARY KEY, views INTEGER DEFAULT 0)")
        await db.commit()

# --- PAGINATION LOGIC ---
async def get_list_kb(page: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT count(*) FROM usernames")
        total = (await cur.fetchone())[0]
    
    btns = []
    if page > 0: btns.append(InlineKeyboardButton(text="« Prev", callback_data=f"list_{page-1}"))
    btns.append(InlineKeyboardButton(text=f"Page {page+1}", callback_data="none"))
    if (page + 1) * 5 < total: btns.append(InlineKeyboardButton(text="Next »", callback_data=f"list_{page+1}"))
    
    return InlineKeyboardMarkup(inline_keyboard=[btns])

# --- COMMANDS ---
@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 List View", callback_data="list_0")],
        [InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_menu")]
    ])
    await m.answer("🚀 **Username Manager Pro**\nSelect an option below:", reply_markup=kb)

@dp.message(Command("add"))
async def add(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Usage: /add @username")
    u = args[1].replace("@", "")
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO usernames (username) VALUES(?)", (u,))
        await db.commit()
    await m.answer(f"✅ @{u} added!")

@dp.message(Command("check"))
async def check(m: Message):
    args = m.text.split()
    if len(args) < 2: return await m.answer("Usage: /check @username")
    u = args[1].replace("@", "")
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT views FROM usernames WHERE username=?", (u,))
        row = await cur.fetchone()
    await m.answer(f"🔎 @{u} | Views: {row[0]}" if row else "❌ Not found.")

# --- CALLBACKS ---
@dp.callback_query(F.data.startswith("list_"))
async def list_nav(c: CallbackQuery):
    page = int(c.data.split("_")[1])
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT username FROM usernames LIMIT 5 OFFSET ?", (page*5,))
        rows = await cur.fetchall()
    
    text = "📜 **Usernames List:**\n\n" + "\n".join([f"• @{r[0]}" for r in rows])
    await c.message.edit_text(text, reply_markup=await get_list_kb(page))
    await c.answer()

@dp.callback_query(F.data == "admin_menu")
async def admin(c: CallbackQuery):
    if c.from_user.id != OWNER_ID: return await c.answer("Access Denied!")
    await c.message.edit_text("🛠 **Admin Panel**\nAuto-Cleanup enabled.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🧹 Clean Low Views", callback_data="clean")]]))

# --- RUN ---
async def main():
    await db_init()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
