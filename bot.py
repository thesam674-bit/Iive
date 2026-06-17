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
WAIT_SET_CHANNEL = set()
WAIT_BIO = set()
WAIT_NAME = set()
WAIT_POST = set()
WAIT_PHOTO = set()
WAIT_TARGETED_POST_CONTENT = {}
WAIT_TARGET_USERNAME_FOR_POST = {}

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

async def get_all_usernames(limit=None):
    async with aiosqlite.connect(DB) as db:
        if limit:
            cur = await db.execute("SELECT username FROM usernames LIMIT ?", (limit,))
        else:
            cur = await db.execute("SELECT username FROM usernames")
        return [row[0] for row in await cur.fetchall()]

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
        return await m.answer("Please provide a username to remove.")

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

async def show_list_content(target_message, page):
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
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Menu", callback_data="back"),
                InlineKeyboardButton(text="📊 Stats", callback_data="stats")
            ]]
        )
        if isinstance(target_message, Message):
            return await target_message.answer(
                "📭 No usernames saved",
                reply_markup=keyboard
            )
        else: # CallbackQuery
            return await target_message.message.edit_text(
                "📭 No usernames saved",
                reply_markup=keyboard
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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_buttons
    )

    if isinstance(target_message, Message):
        await target_message.answer(
            text,
            reply_markup=keyboard
        )
    else: # CallbackQuery
        await target_message.message.edit_text(
            text,
            reply_markup=keyboard
        )

@dp.message(Command("list"))
async def list_cmd(m:Message):
    await show_list_content(m, 0)

@dp.callback_query(F.data.startswith("show_list_"))
async def list_page(c:CallbackQuery):
    page=int(c.data.split("_")[2])
    await show_list_content(c,page)

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
            text="📢 Set Managed Channel",
            callback_data="set_managed_channel"
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
            text="📮 Send Post to Managed Channel", # Renamed for clarity
            callback_data="send_post_managed_channel"
        )
        ],
        [
        InlineKeyboardButton(
            text="🎯 Targeted Post to Users",
            callback_data="targeted_post_menu"
        )
        ]
        ]
    )

    await m.answer(
        "👑 Owner Panel",
        reply_markup=kb
    )

@dp.callback_query(F.data=="targeted_post_menu")
async def targeted_post_menu(c:CallbackQuery):
    if c.from_user.id not in ADMIN_USERS:
        return await c.message.answer("❌ Access denied")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="First 10 Users", callback_data="send_to_first_10"),
                InlineKeyboardButton(text="Specific User", callback_data="send_to_specific_user")
            ],
            [
                InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin")
            ]
        ]
    )
    await c.message.answer("Choose your target for the post:", reply_markup=kb)

@dp.callback_query(F.data=="send_to_first_10")
async def send_to_first_10_prompt(c:CallbackQuery):
    if c.from_user.id not in ADMIN_USERS:
        return await c.message.answer("❌ Access denied")
    
    users = await get_all_usernames(limit=10)
    if not users:
        return await c.message.answer("⚠️ No users in the list to send to.")

    WAIT_TARGETED_POST_CONTENT[c.from_user.id] = {"target_type": "first_10", "users": users}
    await c.message.answer("Please send the message (text, photo, video, or document) you want to post to the first 10 users.")

@dp.callback_query(F.data=="send_to_specific_user")
async def send_to_specific_user_prompt(c:CallbackQuery):
    if c.from_user.id not in ADMIN_USERS:
        return await c.message.answer("❌ Access denied")

    WAIT_TARGET_USERNAME_FOR_POST[c.from_user.id] = True
    await c.message.answer("Please send the username (without @) of the specific user you want to send the post to.")

@dp.callback_query(F.data=="set_managed_channel")
async def set_managed_channel(c:CallbackQuery):
    WAIT_SET_CHANNEL.add(
        c.from_user.id
    )
    await c.message.answer(
        "Please send the username of the channel you want to manage.\nExample:\n@your_channel_username"
    )

@dp.callback_query(F.data=="send_post_managed_channel")
async def send_post_managed_channel_prompt(c:CallbackQuery):
    channel_username = await get_setting("channel")
    if not channel_username:
        return await c.message.answer("⚠️ No channel set for management. Please set your channel first using the Admin Panel.")
    WAIT_POST.add(c.from_user.id)
    await c.message.answer("Please send the message (text, photo, video, or document) you want to post to the managed channel.")

@dp.message()
async def handle_all_messages(m:Message):
    user_id = m.from_user.id

    if user_id in WAIT_SET_CHANNEL:
        ch=m.text.replace("@","")
        await save_setting(
            "channel",
            ch
        )
        WAIT_SET_CHANNEL.remove(
            user_id
        )
        await m.answer(
            f"✅ Channel set for management: @{ch}"
        )
    elif user_id in WAIT_BIO:
        channel_username = await get_setting("channel")
        if not channel_username:
            await m.answer("⚠️ No channel set for management. Please set your channel first using the Admin Panel.")
            WAIT_BIO.remove(user_id)
            return
        try:
            await bot.set_chat_description(chat_id=f"@{channel_username}", description=m.text)
            await m.answer("✅ Channel bio updated successfully!")
        except Exception as e:
            await m.answer(f"❌ Failed to update channel bio: {e}")
        WAIT_BIO.remove(user_id)
    elif user_id in WAIT_NAME:
        channel_username = await get_setting("channel")
        if not channel_username:
            await m.answer("⚠️ No channel set for management. Please set your channel first using the Admin Panel.")
            WAIT_NAME.remove(user_id)
            return
        try:
            await bot.set_chat_title(chat_id=f"@{channel_username}", title=m.text)
            await m.answer("✅ Channel name updated successfully!")
        except Exception as e:
            await m.answer(f"❌ Failed to update channel name: {e}")
        WAIT_NAME.remove(user_id)
    elif user_id in WAIT_POST:
        channel_username = await get_setting("channel")
        if not channel_username:
            await m.answer("⚠️ No channel set for management. Please set your channel first using the Admin Panel.")
            WAIT_POST.remove(user_id)
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
            await m.answer("✅ Post sent to managed channel successfully!")
        except Exception as e:
            await m.answer(f"❌ Failed to send post to managed channel: {e}")
        WAIT_POST.remove(user_id)
    elif user_id in WAIT_PHOTO:
        channel_username = await get_setting("channel")
        if not channel_username:
            await m.answer("⚠️ No channel set for management. Please set your channel first using the Admin Panel.")
            WAIT_PHOTO.remove(user_id)
            return
        if m.photo:
            try:
                file_id = m.photo[-1].file_id
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
            await m.answer("Please send a photo to update the channel photo.")
        WAIT_PHOTO.remove(user_id)
    elif user_id in WAIT_TARGET_USERNAME_FOR_POST:
        target_username = m.text.replace("@","").lower()
        if not await is_username_in_db(target_username):
            await m.answer(f"⚠️ User @{target_username} is not in your list. Please add them first or choose another target.")
            del WAIT_TARGET_USERNAME_FOR_POST[user_id]
            return
        
        WAIT_TARGETED_POST_CONTENT[user_id] = {"target_type": "specific_user", "users": [target_username]}
        del WAIT_TARGET_USERNAME_FOR_POST[user_id]
        await m.answer(f"Target user set to @{target_username}. Please send the message (text, photo, video, or document) you want to post.")

    elif user_id in WAIT_TARGETED_POST_CONTENT:
        target_info = WAIT_TARGETED_POST_CONTENT.pop(user_id)
        target_type = target_info["target_type"]
        target_users = target_info["users"]
        
        success_count = 0
        fail_count = 0
        failed_users = []

        for username in target_users:
            try:
                # Get user's chat ID from username (this requires the bot to have interacted with the user before)
                # For simplicity, we'll assume the bot can send to usernames directly if they are public or bot has chatted.
                # In a real scenario, you might need to store user_id instead of username for direct messaging.
                if m.text:
                    await bot.send_message(chat_id=f"@{username}", text=m.text)
                elif m.photo:
                    file_id = m.photo[-1].file_id
                    await bot.send_photo(chat_id=f"@{username}", photo=file_id, caption=m.caption)
                elif m.video:
                    file_id = m.video.file_id
                    await bot.send_video(chat_id=f"@{username}", video=file_id, caption=m.caption)
                elif m.document:
                    file_id = m.document.file_id
                    await bot.send_document(chat_id=f"@{username}", document=file_id, caption=m.caption)
                else:
                    await m.answer(f"Unsupported message type for posting to @{username}.")
                    fail_count += 1
                    failed_users.append(username)
                    continue
                success_count += 1
            except Exception as e:
                fail_count += 1
                failed_users.append(username)
                print(f"Failed to send post to @{username}: {e}") # Log the error
        
        result_message = f"✅ Post sent to {success_count} user(s) successfully!\n"
        if fail_count > 0:
            result_message += f"❌ Failed to send to {fail_count} user(s): {', '.join([f'@{u}' for u in failed_users])}.\n(Note: Bot can only send to users it has previously interacted with or public channels/groups if it's an admin there.)"
        
        await m.answer(result_message)

    else:
        # Default message handler if no specific state is active
        if m.text and not m.text.startswith("/"): # Only respond to non-command text if not in a waiting state
            await m.answer("I don\'t understand that command. Use /help for available commands.")

@dp.callback_query(F.data=="low")
async def low(c:CallbackQuery):
    ch=await get_setting("channel")
    if not ch:
        return await c.message.answer(
            "⚠️ No channel set for management. Please set your channel first using the Admin Panel."
        )
    await c.message.edit_text(
        f"🗑 Low Views Cleaner\n\nChannel: @{ch}"
    )

@dp.callback_query(F.data=="settings")
async def settings(c:CallbackQuery):
    ch=await get_setting("channel")
    if not ch:
        return await c.message.answer(
            "⚠️ No channel set for management. Please set your channel first using the Admin Panel."
        )
    await c.message.edit_text(
        f"🎨 Channel Settings\n\n@{ch}"
    )

@dp.callback_query(F.data=="update_bio")
async def update_bio(c:CallbackQuery):
    channel_username = await get_setting("channel")
    if not channel_username:
        return await c.message.answer("⚠️ No channel set for management. Please set your channel first using the Admin Panel.")
    WAIT_BIO.add(c.from_user.id)
    await c.message.answer("Please send the new channel bio text.")

@dp.callback_query(F.data=="update_photo")
async def update_photo(c:CallbackQuery):
    channel_username = await get_setting("channel")
    if not channel_username:
        return await c.message.answer("⚠️ No channel set for management. Please set your channel first using the Admin Panel.")
    WAIT_PHOTO.add(c.from_user.id)
    await c.message.answer("Please send the new channel photo.")

@dp.callback_query(F.data=="update_name")
async def update_name(c:CallbackQuery):
    channel_username = await get_setting("channel")
    if not channel_username:
        return await c.message.answer("⚠️ No channel set for management. Please set your channel first using the Admin Panel.")
    WAIT_NAME.add(c.from_user.id)
    await c.message.answer("Please send the new channel name.")

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
