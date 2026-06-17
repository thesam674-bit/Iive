import asyncio
import os
import aiosqlite
from datetime import datetime

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import Command


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DB = "usernames.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()


def date():
    return datetime.now().strftime("%d-%m-%Y %I:%M %p")


async def db_init():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS usernames(
        username TEXT PRIMARY KEY,
        added TEXT
        )
        """)
        await db.commit()


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


@dp.message(Command("start"))
async def start(m:Message):

    await m.answer(
        "👋 Welcome\n\nChoose option:",
        reply_markup=menu()
    )


@dp.message(Command("help"))
async def help_cmd(m:Message):

    await m.answer(
"""
🆘 Commands

/add @username
Add username

/list
Show all usernames

/check username
Check username status

/stats
Total count

/admin
Owner panel
"""
)


@dp.message(Command("add"))
async def add(m:Message):

    args=m.text.split()

    if len(args)<2:
        return await m.answer(
            "Use:\n/add @username"
        )

    username=args[1].replace("@","")


    async with aiosqlite.connect(DB) as db:

        await db.execute(
        """
        INSERT OR IGNORE INTO usernames
        VALUES (?,?)
        """,
        (username,date())
        )

        await db.commit()


    await m.answer(
        f"✅ Saved @{username}"
    )



async def show_list(c:CallbackQuery,page:int):

    limit=8
    offset=page*limit


    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        """
        SELECT username FROM usernames
        LIMIT ? OFFSET ?
        """,
        (limit,offset)
        )

        rows=await cur.fetchall()


        cur=await db.execute(
        "SELECT COUNT(*) FROM usernames"
        )

        total=(await cur.fetchone())[0]


    if not rows:
        return await c.answer(
            "Empty",
            show_alert=True
        )


    text=f"📋 Page {page+1}\n\n"

    for x in rows:
        text+=f"• @{x[0]}\n"



    buttons=[]


    if page>0:

        buttons.append(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"list_{page-1}"
        ))


    if offset+limit < total:

        buttons.append(
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"list_{page+1}"
        ))


    buttons.append(
        InlineKeyboardButton(
            text="🔙",
            callback_data="back"
        )
    )


    await c.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[buttons]
        )
    )



@dp.callback_query(F.data.startswith("list_"))
async def list_page(c:CallbackQuery):

    await show_list(
        c,
        int(c.data.split("_")[1])
    )



@dp.message(Command("list"))
async def list_cmd(m:Message):

    await m.answer(
        "Opening list...",
        reply_markup=menu()
    )



@dp.message(Command("check"))
async def check(m:Message):

    args=m.text.split()

    if len(args)<2:
        return await m.answer(
        "Use:\n/check username"
        )


    u=args[1].replace("@","")


    try:

        await bot.get_chat(
            "@"+u
        )

        await m.answer(
        f"❌ @{u} is taken"
        )


    except:

        await m.answer(
        f"✅ @{u} looks available"
        )



@dp.callback_query(F.data=="stats")
async def stats(c:CallbackQuery):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
        "SELECT COUNT(*) FROM usernames"
        )

        total=(await cur.fetchone())[0]


    await c.message.edit_text(
        f"📊 Total: {total}",
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
        [
        InlineKeyboardButton(
        text="🔙",
        callback_data="back")
        ]
        ])
    )



@dp.callback_query(F.data=="back")
async def back(c:CallbackQuery):

    await c.message.edit_text(
        "Choose option:",
        reply_markup=menu()
    )



@dp.message(Command("admin"))
async def admin(m:Message):

    if m.from_user.id != OWNER_ID:
        return await m.answer("❌ No Access")


    await m.answer(
        "🛠 Admin Panel\n\nComing controls ready",
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
