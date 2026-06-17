import asyncio
import aiosqlite
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE") # Bot token environment variable se ya default
OWNER_ID = int(os.getenv("OWNER_ID", "123456789")) # Owner ID environment variable se ya default
DB = "usernames.db"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=TOKEN, parse_mode="MarkdownV2")
dp = Dispatcher()

# --- DB INIT ---
async def db_init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS usernames(username TEXT PRIMARY KEY, views INTEGER DEFAULT 0)")
        await db.commit()
    logging.info("Database initialized.")

# --- PAGINATION LOGIC ---
async def get_list_kb(page: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT count(*) FROM usernames")
        total = (await cur.fetchone())[0]
    
    btns = []
    if page > 0: btns.append(InlineKeyboardButton(text="« Prev", callback_data=f"list_{page-1}"))
    
    # Display current page number, but make it non-interactive
    btns.append(InlineKeyboardButton(text=f"Page {page+1}", callback_data="ignore_me")) 
    
    if (page + 1) * 5 < total: btns.append(InlineKeyboardButton(text="Next »", callback_data=f"list_{page+1}"))
    
    return InlineKeyboardMarkup(inline_keyboard=[btns])

# --- COMMANDS ---
@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 List View", callback_data="list_0")],
        [InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_menu")]
    ])
    await m.answer("🚀 \*\*Username Manager Pro\*\*\nSelect an option below:", reply_markup=kb)
    logging.info(f"User {m.from_user.id} started the bot.")

@dp.message(Command("add"))
async def add(m: Message):
    if m.from_user.id != OWNER_ID: 
        await m.answer("Access Denied\!")
        logging.warning(f"User {m.from_user.id} tried to use /add command without owner privileges.")
        return

    args = m.text.split()
    if len(args) < 2: 
        await m.answer("Usage: `/add @username`")
        return
    u = args[1].replace("@", "")
    try:
        async with aiosqlite.connect(DB) as db:
            await db.execute("INSERT OR IGNORE INTO usernames (username) VALUES(?)", (u,))
            await db.commit()
        await m.answer(f"✅ @{u} added\!")
        logging.info(f"Username @{u} added by {m.from_user.id}.")
    except Exception as e:
        await m.answer(f"❌ Error adding username: {e}")
        logging.error(f"Error adding username @{u}: {e}")

@dp.message(Command("check"))
async def check(m: Message):
    args = m.text.split()
    if len(args) < 2: 
        await m.answer("Usage: `/check @username`")
        return
    u = args[1].replace("@", "")
    try:
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute("SELECT views FROM usernames WHERE username=?", (u,))
            row = await cur.fetchone()
        if row:
            await m.answer(f"🔎 @{u} \| Views: {row[0]}")
            logging.info(f"User {m.from_user.id} checked @{u}. Views: {row[0]}")
        else:
            await m.answer("❌ Not found\.")
            logging.info(f"User {m.from_user.id} checked @{u}, but not found.")
    except Exception as e:
        await m.answer(f"❌ Error checking username: {e}")
        logging.error(f"Error checking username @{u}: {e}")

# --- CALLBACKS ---
@dp.callback_query(F.data.startswith("list_"))
async def list_nav(c: CallbackQuery):
    page = int(c.data.split("_")[1])
    try:
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute("SELECT username FROM usernames LIMIT 5 OFFSET ?", (page*5,))
            rows = await cur.fetchall()
        
        if rows:
            text = "📜 \*\*Usernames List:\*\*\n\n" + "\n".join([f"• @{r[0]}" for r in rows])
        else:
            text = "📜 \*\*Usernames List:\*\*\n\nNo usernames found on this page\."

        await c.message.edit_text(text, reply_markup=await get_list_kb(page))
        await c.answer()
        logging.info(f"User {c.from_user.id} navigated to list page {page}.")
    except Exception as e:
        await c.message.edit_text(f"❌ Error fetching list: {e}")
        await c.answer("Error fetching list!")
        logging.error(f"Error fetching list for user {c.from_user.id}: {e}")

@dp.callback_query(F.data == "admin_menu")
async def admin(c: CallbackQuery):
    if c.from_user.id != OWNER_ID: 
        await c.answer("Access Denied\!")
        logging.warning(f"User {c.from_user.id} tried to access admin panel without owner privileges.")
        return
    await c.message.edit_text("🛠 \*\*Admin Panel\*\*\nAuto\-Cleanup enabled\.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🧹 Clean Low Views", callback_data="clean")]]))
    await c.answer()
    logging.info(f"Owner {c.from_user.id} accessed admin panel.")

@dp.callback_query(F.data == "clean")
async def clean_low_views(c: CallbackQuery):
    if c.from_user.id != OWNER_ID: 
        await c.answer("Access Denied\!")
        logging.warning(f"User {c.from_user.id} tried to use clean function without owner privileges.")
        return
    try:
        async with aiosqlite.connect(DB) as db:
            cur = await db.execute("DELETE FROM usernames WHERE views = 0")
            deleted_count = cur.rowcount
            await db.commit()
        await c.message.edit_text(f"✅ Cleaned {deleted_count} usernames with 0 views\.")
        await c.answer(f"Cleaned {deleted_count} usernames\.")
        logging.info(f"Owner {c.from_user.id} cleaned {deleted_count} usernames with 0 views.")
    except Exception as e:
        await c.message.edit_text(f"❌ Error cleaning usernames: {e}")
        await c.answer("Error cleaning usernames!")
        logging.error(f"Error cleaning usernames for owner {c.from_user.id}: {e}")

@dp.callback_query(F.data == "ignore_me")
async def ignore_callback(c: CallbackQuery):
    # This callback is for non-interactive buttons like the page number in pagination
    await c.answer()

# --- RUN ---
async def main():
    await db_init()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Check if TOKEN and OWNER_ID are set
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        logging.error("BOT_TOKEN environment variable not set or is default. Please set it.")
        print("Error: BOT_TOKEN environment variable not set or is default. Please set it.")
        exit(1)
    if OWNER_ID == 123456789:
        logging.warning("OWNER_ID environment variable not set or is default. Please set it to your Telegram user ID.")
        print("Warning: OWNER_ID environment variable not set or is default. Please set it to your Telegram user ID.")

    asyncio.run(main())
    
