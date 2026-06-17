import asyncio
import os
import aiosqlite

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.filters import Command


load_dotenv()


TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 8864002775

ADMIN_PASSWORD = "TG-Pro_9xA7_Channel_Manager_2026"


DB = "bot.db"


bot = Bot(token=TOKEN)

dp = Dispatcher()


ADMIN_USERS = set()



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



async def get_setting(key):

    async with aiosqlite.connect(DB) as db:

        cur = await db.execute(
            "SELECT value FROM settings WHERE key=?",
            (key,)
        )

        data = await cur.fetchone()

        return data[0] if data else None



async def save_setting(key,value):

    async with aiosqlite.connect(DB) as db:

        await db.execute(
            "INSERT OR REPLACE INTO settings VALUES(?,?)",
            (key,value)
        )

        await db.commit()



def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

        [
        InlineKeyboardButton(
            text="📋 Username List",
            callback_data="list"
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



@dp.message(Command("stats"))
async def stats(m:Message):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
            "SELECT COUNT(*) FROM usernames"
        )

        total=(await cur.fetchone())[0]


    await m.answer(
        f"📊 Total usernames: {total}"
    )



# SECRET LOGIN

@dp.message(Command("secure"))
async def secure(m:Message):


    args=m.text.split()


    if len(args)<2:
        return


    if m.from_user.id != OWNER_ID:
        return


    if args[1] != ADMIN_PASSWORD:
        return


    ADMIN_USERS.add(m.from_user.id)


    await m.answer(
        "🔓 Admin access unlocked\n\n"
        "Use /admin now"
    )



# ADMIN

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
        ]

        ]
    )



    await m.answer(
        "👑 Owner Dashboard\n\n"
        "Select action:",
        reply_markup=kb
    )



# ADD CHANNEL

@dp.callback_query(F.data=="add_channel")
async def add_channel(c:CallbackQuery):

    await c.message.edit_text(
        "📢 Send channel username:\n\n"
        "Example:\n@mychannel"
    )


    dp.message.register(save_channel)



async def save_channel(m:Message):

    if m.from_user.id not in ADMIN_USERS:
        return


    channel=m.text.replace("@","")


    await save_setting(
        "channel",
        channel
    )


    await m.answer(
        f"✅ Channel added\n@{channel}"
    )



# LOW VIEWS

@dp.callback_query(F.data=="low")
async def low(c:CallbackQuery):

    channel=await get_setting("channel")


    if not channel:

        return await c.message.edit_text(
            "⚠️ No channel added.\n\n"
            "Please add channel first."
        )


    await c.message.edit_text(
        "🗑 Low Views Cleaner\n\n"
        f"Channel: @{channel}\n\n"
        "Ready to manage posts."
    )



# SETTINGS

@dp.callback_query(F.data=="settings")
async def settings(c:CallbackQuery):

    channel=await get_setting("channel")


    if not channel:

        return await c.message.edit_text(
            "⚠️ Please add channel first."
        )


    await c.message.edit_text(
        "🎨 Channel Settings\n\n"
        "📝 Change Name\n"
        "📄 Change Bio\n"
        "🖼 Change Photo"
    )



async def main():

    await db_init()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)



if __name__=="__main__":

    asyncio.run(main())
