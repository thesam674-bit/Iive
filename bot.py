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

DB = "data.db"


bot = Bot(token=TOKEN)

dp = Dispatcher()



async def init_db():

    async with aiosqlite.connect(DB) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS usernames(
            username TEXT PRIMARY KEY
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
                text="🔐 Admin",
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
🆘 Help

/add @username
/remove username

/list

/check username

/stats

/access password
"""
    )



@dp.message(Command("add"))
async def add(m:Message):

    args=m.text.split()

    if len(args)<2:
        return await m.answer(
            "Use /add @username"
        )


    username=args[1].replace("@","").lower()


    async with aiosqlite.connect(DB) as db:

        await db.execute(
            "INSERT OR IGNORE INTO usernames VALUES(?)",
            (username,)
        )

        await db.commit()


    await m.answer(
        f"✅ Added @{username}"
    )



@dp.message(Command("remove"))
async def remove(m:Message):

    args=m.text.split()

    if len(args)<2:
        return await m.answer(
            "Use /remove username"
        )


    username=args[1].replace("@","")


    async with aiosqlite.connect(DB) as db:

        await db.execute(
            "DELETE FROM usernames WHERE username=?",
            (username,)
        )

        await db.commit()


    await m.answer(
        f"🗑 Removed @{username}"
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

        return await c.answer(
            "No data",
            show_alert=True
        )


    text=f"📋 Page {page+1}\n\n"


    for x in rows:
        text += f"• @{x[0]}\n"



    btn=[]


    if page>0:

        btn.append(
            InlineKeyboardButton(
                text="⬅️ Back",
                callback_data=f"list_{page-1}"
            )
        )


    if offset+limit < total:

        btn.append(
            InlineKeyboardButton(
                text="Next ➡️",
                callback_data=f"list_{page+1}"
            )
        )



    await c.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[btn]
        )
    )



@dp.message(Command("list"))
async def list_cmd(m:Message):

    await m.answer(
        "📋 Username List",
        reply_markup=menu()
    )



@dp.callback_query(F.data.startswith("list_"))
async def list_btn(c:CallbackQuery):

    page=int(c.data.split("_")[1])

    await show_list(c,page)



@dp.message(Command("check"))
async def check(m:Message):

    args=m.text.split()

    if len(args)<2:
        return await m.answer(
            "Use /check username"
        )


    username=args[1].replace("@","")


    try:

        await bot.get_chat("@"+username)

        await m.answer(
            f"❌ @{username} Taken"
        )

    except:

        await m.answer(
            f"✅ @{username} Available"
        )



@dp.callback_query(F.data=="stats")
async def stats(c:CallbackQuery):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
            "SELECT COUNT(*) FROM usernames"
        )

        total=(await cur.fetchone())[0]


    await c.message.edit_text(
        f"📊 Total: {total}"
    )



@dp.callback_query(F.data=="admin")
async def admin_btn(c:CallbackQuery):

    await c.message.answer(
        "🔐 Use:\n/access password"
    )



@dp.message(Command("access"))
async def access(m:Message):

    args=m.text.split()


    if len(args)<2:

        return await m.answer(
            "Use /access password"
        )


    if m.from_user.id != OWNER_ID:

        return await m.answer(
            "❌ Denied"
        )


    if args[1] != ADMIN_PASSWORD:

        return await m.answer(
            "❌ Wrong password"
        )


    await m.answer(
        "👑 Owner Panel\n\n"
        "🗑 Low Views\n"
        "🎨 Channel Settings"
    )



async def main():

    await init_db()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)



if __name__=="__main__":

    asyncio.run(main())
