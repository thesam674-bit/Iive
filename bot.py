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

DB = "usernames.db"


bot = Bot(token=TOKEN)

dp = Dispatcher()



# DATABASE

async def db_init():

    async with aiosqlite.connect(DB) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS usernames(
            username TEXT PRIMARY KEY
        )
        """)

        await db.commit()



# MENU

def menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

        [
        InlineKeyboardButton(
            text="📋 List",
            callback_data="list_0"
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



# START

@dp.message(Command("start"))
async def start(m:Message):

    await m.answer(
        "👋 Welcome\n\nUse /help for commands"
    )



# HELP

@dp.message(Command("help"))
async def help_cmd(m:Message):

    await m.answer(
"""
🆘 Commands

/add @username
Add username

/remove username
Remove username

/list
Show list

/check username
Check username

/stats
Total count
"""
    )



# ADD

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
        f"✅ @{u} added"
    )



# REMOVE

@dp.message(Command("remove"))
async def remove(m:Message):

    args=m.text.split()

    if len(args)<2:
        return await m.answer(
            "Use /remove username"
        )


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



# LIST

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

        return await c.answer(
            "No data",
            show_alert=True
        )


    text=f"📋 Page {page+1}\n\n"


    for x in rows:

        text += f"• @{x[0]}\n"



    buttons=[]


    if page>0:

        buttons.append(
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=f"list_{page-1}"
        ))



    if offset+limit < total:

        buttons.append(
        InlineKeyboardButton(
            text="Next ➡️",
            callback_data=f"list_{page+1}"
        ))



    buttons.append(
    InlineKeyboardButton(
        text="🔙 Menu",
        callback_data="home"
    ))



    await c.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[buttons]
        )
    )



@dp.message(Command("list"))
async def list_cmd(m:Message):

    await m.answer(
        "📋 Username List",
        reply_markup=menu()
    )



@dp.callback_query(F.data.startswith("list_"))
async def list_page(c:CallbackQuery):

    page=int(c.data.split("_")[1])

    await show_list(c,page)



# CHECK

@dp.message(Command("check"))
async def check(m:Message):

    args=m.text.split()


    if len(args)<2:
        return await m.answer(
            "Use /check username"
        )


    u=args[1].replace("@","")


    try:

        await bot.get_chat("@"+u)

        await m.answer(
            f"❌ @{u} Taken"
        )

    except:

        await m.answer(
            f"✅ @{u} Available"
        )



# STATS

@dp.callback_query(F.data=="stats")
async def stats(c:CallbackQuery):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
            "SELECT COUNT(*) FROM usernames"
        )

        total=(await cur.fetchone())[0]


    await c.message.edit_text(
        f"📊 Total Usernames: {total}",
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
        [
        InlineKeyboardButton(
            text="🔙",
            callback_data="home"
        )
        ]
        ])
    )



# ADMIN BUTTON

@dp.callback_query(F.data=="admin")
async def admin_btn(c:CallbackQuery):

    await c.message.answer(
        "🔐"
    )



# SECRET OWNER LOGIN

@dp.message(Command("secure"))
async def secure(m:Message):

    args=m.text.split()


    if len(args)<2:
        return


    if m.from_user.id != OWNER_ID:
        return


    if args[1] != ADMIN_PASSWORD:
        return



    kb=InlineKeyboardMarkup(
        inline_keyboard=[

        [
        InlineKeyboardButton(
            text="🗑 Low Views Delete",
            callback_data="low"
        )
        ],

        [
        InlineKeyboardButton(
            text="🎨 Channel Customize",
            callback_data="custom"
        )
        ],

        [
        InlineKeyboardButton(
            text="📋 Username Manage",
            callback_data="manage"
        )
        ],

        [
        InlineKeyboardButton(
            text="📊 Bot Stats",
            callback_data="stats"
        )
        ]

        ]
    )


    await m.answer(
        "👑 Owner Panel",
        reply_markup=kb
    )



# BACK HOME

@dp.callback_query(F.data=="home")
async def home(c:CallbackQuery):

    await c.message.edit_text(
        "Choose option:",
        reply_markup=menu()
    )



async def main():

    await db_init()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)



if __name__=="__main__":

    asyncio.run(main())
