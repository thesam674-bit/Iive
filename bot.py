import asyncio
import os
import aiosqlite
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID")) # Ensure OWNER_ID is an integer

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") # Get admin password from .env

DB = "database.db"

bot = Bot(token=TOKEN)

dp = Dispatcher()

ADMIN_USERS = set()
WAIT_CHANNEL = set()
WAIT_BIO = set()
WAIT_NAME = set()
WAIT_POST = set()

async def db_init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS usernames(
            username TEXT PRIMARY KEY
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        await db.commit()

async def save_setting(k,v):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings VALUES(?,?)",
            (k,v)
        )
        await db.commit()

async def get_setting(k):
    async with aiosqlite.connect(DB) as db:
        cur=await db.execute(
            "SELECT value FROM settings WHERE key=?",
            (k,)
        )
        x=await cur.fetchone()
        return x[0] if x else None

async def is_username_in_db(username):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT username FROM usernames WHERE username=?",
            (username,)
        )
        return await cur.fetchone() is not None

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
        [
        InlineKeyboardButton(
            text="📋 Username List",
            callback_data="show_list_0"
        )
        ],
        [
        InlineKeyboardButton(
            text="📊 Stats",
            callback_data="stats"
        )
        ],
        [
        InlineKeyboardButton(
            text="⚙️ Admin",
            callback_data="admin"
        )
        ]
        ]
    )

@dp.message(Command("start"))
async def start(m:Message):
    await m.answer(
        "👋 Welcome\n\nUse /help for commands"
    )

@dp.message(Command("help"))
async def help_cmd(m:Message):
    await m.answer(
"""
🆘 Commands

/add @username
/remove username

/list

/check username

/stats

/secure <password> (Admin access)
/admin (Admin panel)
"""
    )

@dp.message(Command("add"))
async def add(m:Message):
    args=m.text.split()
    if len(args)<2:
        return await m.answer(
            "Use /add @username"
        )

    u=args[1].replace("@","").lower()

    if await is_username_in_db(u):
        return await m.answer(f"⚠️ @{u} is already in your list.")

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO usernames VALUES(?)",
            (u,)
        )
        await db.commit()

    await m.answer(
        f"✅ @{u} saved"
    )

@dp.message(Command("remove"))
async def remove(m:Message):
    args=m.text.split()
    if len(args)<2:
        return

    u=args[1].replace("@","")

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "DELETE FROM usernames WHERE username=?",
            (u,)
        )
        await db.commit()

    await m.answer(
        f"🗑 @{u} removed"
    )

async def show_list(c,page):
    limit=10
    offset=page*limit

    async with aiosqlite.connect(DB) as db:
        cur=await db.execute(
            "SELECT username FROM usernames LIMIT ? OFFSET ?",
            (limit,offset)
        )
        rows=await cur.fetchall()

        cur=await db.execute(
            "SELECT COUNT(*) FROM usernames"
        )
        total=(await cur.fetchone())[0]

    if not rows:
        return await c.message.edit_text(
            "📭 No usernames saved",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="🔙 Menu", callback_data="back"),
                    InlineKeyboardButton(text="📊 Stats", callback_data="stats")
                ]]
            )
        )

    text=f"📋 Page {page+1}\n\n"

    for r in rows:
        text+=f"• @{r[0]}\n"

    keyboard_buttons = []
    nav_buttons = []

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Prev",
                callback_data=f"show_list_{page-1}"
            )
        )

    if offset + limit < total:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Next ➡️",
                callback_data=f"show_list_{page+1}"
            )
        )
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Menu", callback_data="back"),
        InlineKeyboardButton(text="📊 Stats", callback_data="stats")
    ])

    await c.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard_buttons
        )
    )

@dp.message(Command("list"))
async def list_cmd(m:Message):
    # Directly show the list when /list is called
    await show_list(m, 0)

@dp.callback_query(F.data.startswith("show_list_"))
async def list_page(c:CallbackQuery):
    page=int(c.data.split("_")[2])
    await show_list(c,page)

@dp.message(Command("check"))
async def check(m:Message):
    args=m.text.split()
    if len(args)<2:
        return await m.answer("Please provide a username to check.")

    u=args[1].replace("@","").lower()

    if await is_username_in_db(u):
        return await m.answer(f"✅ @{u} is already in your list.")

    try:
        await bot.get_chat("@"+u)
        await m.answer(
            f"❌ @{u} is taken on Telegram."
        )
    except Exception:
        await m.answer(
            f"✅ @{u} is available on Telegram."
        )

@dp.callback_query(F.data=="stats")
async def stats(c:CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        cur=await db.execute(
            "SELECT COUNT(*) FROM usernames"
        )
        x=(await cur.fetchone())[0]

    await c.message.edit_text(
        f"📊 Total usernames in list: {x}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Menu", callback_data="back"),
                InlineKeyboardButton(text="📋 Username List", callback_data="show_list_0")
            ]]
        )
    )

# SECRET ACCESS
@dp.message(Command("secure"))
async def secure(m:Message):
    args=m.text.split()

    if len(args)<2:
        return await m.answer("Please provide the admin password.")

    if m.from_user.id != OWNER_ID:
        return await m.answer("❌ Access denied. You are not the owner.")

    if args[1] != ADMIN_PASSWORD:
        return await m.answer("❌ Incorrect admin password.")

    ADMIN_USERS.add(
        m.from_user.id
    )

    await m.answer(
        "🔓 Admin unlocked\nUse /admin"
    )

@dp.message(Command("admin"))
async def admin(m:Message):
    if m.from_user.id not in ADMIN_USERS:
        return await m.answer(
            "❌ Access denied"
        )

    kb=InlineKeyboardMarkup(
        inline_keyboard=[
        [
        InlineKeyboardButton(
            text="📢 Add Channel",
            callback_data="add_channel"
        )
        ],
        [
        InlineKeyboardButton(
            text="🗑 Low Views Cleaner",
            callback_data="low"
        )
        ],
        [
        InlineKeyboardButton(
            text="🎨 Channel Settings",
            callback_data="settings"
        )
        ],
        [
        InlineKeyboardButton(
            text="📝 Update Channel Bio",
            callback_data="update_bio"
        )
        ],
        [
        InlineKeyboardButton(
            text="🖼️ Update Channel Photo",
            callback_data="update_photo"
        )
        ],
        [
        InlineKeyboardButton(
            text="✏️ Update Channel Name",
            callback_data="update_name"
        )
        ],
        [
        InlineKeyboardButton(
            text="📮 Send Post to Channel",
            callback_data="send_post"
        )
        ]
        ]
    )

    await m.answer(
        "👑 Owner Panel",
        reply_markup=kb
    )

@dp.callback_query(F.data=="add_channel")
async def add_channel(c:CallbackQuery):
    WAIT_CHANNEL.add(
        c.from_user.id
    )
    await c.message.answer(
        "Send channel username\nExample:\n@channel"
    )

@dp.message()
async def handle_all_messages(m:Message):
    if m.from_user.id in WAIT_CHANNEL:
        ch=m.text.replace("@","")
        await save_setting(
            "channel",
            ch
        )
        WAIT_CHANNEL.remove(
            m.from_user.id
        )
        await m.answer(
            f"✅ Channel added\n@{ch}"
        )
    elif m.from_user.id in WAIT_BIO:
        channel_username = await get_setting("channel")
        if not channel_username:
            await m.answer("⚠️ No channel added. Please add your channel first.")
            WAIT_BIO.remove(m.from_user.id)
            return
        try:
            await bot.set_chat_description(chat_id=f"@{channel_username}", description=m.text)
            await m.answer("✅ Channel bio updated successfully!")
        except Exception as e:
            await m.answer(f"❌ Failed to update channel bio: {e}")
        WAIT_BIO.remove(m.from_user.id)
    elif m.from_user.id in WAIT_NAME:
        channel_username = await get_setting("channel")
        if not channel_username:
            await m.answer("⚠️ No channel added. Please add your channel first.")
            WAIT_NAME.remove(m.from_user.id)
            return
        try:
            await bot.set_chat_title(chat_id=f"@{channel_username}", title=m.text)
            await m.answer("✅ Channel name updated successfully!")
        except Exception as e:
            await m.answer(f"❌ Failed to update channel name: {e}")
        WAIT_NAME.remove(m.from_user.id)
    elif m.from_user.id in WAIT_POST:
        channel_username = await get_setting("channel")
        if not channel_username:
            await m.answer("⚠️ No channel added. Please add your channel first.")
            WAIT_POST.remove(m.from_user.id)
            return
        try:
            if m.text:
                await bot.send_message(chat_id=f"@{channel_username}", text=m.text)
            elif m.photo:
                file_id = m.photo[-1].file_id
                await bot.send_photo(chat_id=f"@{channel_username}", photo=file_id, caption=m.caption)
            elif m.video:
                file_id = m.video.file_id
                await bot.send_video(chat_id=f"@{channel_username}", video=file_id, caption=m.caption)
            elif m.document:
                file_id = m.document.file_id
                await bot.send_document(chat_id=f"@{channel_username}", document=file_id, caption=m.caption)
            else:
                await m.answer("Unsupported message type for posting.")
            await m.answer("✅ Post sent to channel successfully!")
        except Exception as e:
            await m.answer(f"❌ Failed to send post to channel: {e}")
        WAIT_POST.remove(m.from_user.id)
    elif m.photo and m.from_user.id in ADMIN_USERS:
        # This handles photo updates for the channel
        channel_username = await get_setting("channel")
        if not channel_username:
            await m.answer("⚠️ No channel added. Please add your channel first.")
            return
        try:
            file_id = m.photo[-1].file_id
            # Download the photo to a temporary file
            file_info = await bot.get_file(file_id)
            downloaded_file = await bot.download_file(file_info.file_path)
            temp_photo_path = f"/tmp/{file_id}.jpg"
            with open(temp_photo_path, "wb") as f:
                f.write(downloaded_file.read())
            
            await bot.set_chat_photo(chat_id=f"@{channel_username}", photo=FSInputFile(temp_photo_path))
            await m.answer("✅ Channel photo updated successfully!")
            os.remove(temp_photo_path) # Clean up the temporary file
        except Exception as e:
            await m.answer(f"❌ Failed to update channel photo: {e}")
    else:
        # Default message handler if no specific state is active
        await m.answer("I don't understand that command. Use /help for available commands.")

@dp.callback_query(F.data=="low")
async def low(c:CallbackQuery):
    ch=await get_setting("channel")
    if not ch:
        return await c.message.edit_text(
            "⚠️ No channel added.\nPlease add your channel first."
        )
    await c.message.edit_text(
        f"🗑 Low Views Cleaner\n\nChannel: @{ch}"
    )

@dp.callback_query(F.data=="settings")
async def settings(c:CallbackQuery):
    ch=await get_setting("channel")
    if not ch:
        return await c.message.edit_text(
            "⚠️ Please add channel first."
        )
    await c.message.edit_text(
        f"🎨 Channel Settings\n\n@{ch}"
    )

@dp.callback_query(F.data=="update_bio")
async def update_bio(c:CallbackQuery):
    channel_username = await get_setting("channel")
    if not channel_username:
        return await c.message.edit_text("⚠️ No channel added. Please add your channel first.")
    WAIT_BIO.add(c.from_user.id)
    await c.message.answer("Please send the new channel bio text.")

@dp.callback_query(F.data=="update_photo")
async def update_photo(c:CallbackQuery):
    channel_username = await get_setting("channel")
    if not channel_username:
        return await c.message.edit_text("⚠️ No channel added. Please add your channel first.")
    await c.message.answer("Please send the new channel photo.")
    # The actual photo handling is in handle_all_messages with F.photo filter

@dp.callback_query(F.data=="update_name")
async def update_name(c:CallbackQuery):
    channel_username = await get_setting("channel")
    if not channel_username:
        return await c.message.edit_text("⚠️ No channel added. Please add your channel first.")
    WAIT_NAME.add(c.from_user.id)
    await c.message.answer("Please send the new channel name.")

@dp.callback_query(F.data=="send_post")
async def send_post(c:CallbackQuery):
    channel_username = await get_setting("channel")
    if not channel_username:
        return await c.message.edit_text("⚠️ No channel added. Please add your channel first.")
    WAIT_POST.add(c.from_user.id)
    await c.message.answer("Please send the message (text, photo, video, or document) you want to post to the channel.")

@dp.callback_query(F.data=="back")
async def back(c:CallbackQuery):
    await c.message.edit_text(
        "Menu",
        reply_markup=main_menu()
    )

async def main():
    await db_init()
    await bot.delete_webhook(
        drop_pending_updates=True
    )
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
    
