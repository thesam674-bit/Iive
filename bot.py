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

DB = "usernames.db"


bot = Bot(token=TOKEN)
dp = Dispatcher()



# DATABASE

async def init_db():

    async with aiosqlite.connect(DB) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS usernames(
            username TEXT PRIMARY KEY,
            added TEXT
        )
        """)

        await db.commit()



# MAIN MENU

def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📋 Username List",
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
                    text="⚙️ Admin Panel",
                    callback_data="admin"
                )
            ]

        ]
    )



# START

@dp.message(Command("start"))
async def start(message:Message):

    await message.answer(
        "👋 Welcome\n\nUse /help for commands"
    )



# HELP

@dp.message(Command("help"))
async def help_cmd(message:Message):

    await message.answer(
"""
🆘 Commands

/add @username
Add username

/remove username
Remove username

/list
Show usernames

/check username
Check username

/stats
Total usernames

/admin
Owner panel
"""
    )



# ADD

@dp.message(Command("add"))
async def add(message:Message):

    args = message.text.split()

    if len(args)<2:
        return await message.answer(
            "Use:\n/add @username"
        )


    username=args[1].replace("@","").lower()


    async with aiosqlite.connect(DB) as db:

        await db.execute(
        "INSERT OR IGNORE INTO usernames VALUES(?,?)",
        (username,"saved")
        )

        await db.commit()


    await message.answer(
        f"✅ @{username} saved"
    )



# REMOVE

@dp.message(Command("remove"))
async def remove(message:Message):

    args=message.text.split()

    if len(args)<2:
        return await message.answer(
            "Use:\n/remove username"
        )


    username=args[1].replace("@","")


    async with aiosqlite.connect(DB) as db:

        await db.execute(
            "DELETE FROM usernames WHERE username=?",
            (username,)
        )

        await db.commit()


    await message.answer(
        f"🗑 @{username} removed"
    )



# LIST PAGINATION

async def show_list(call:CallbackQuery,page:int):

    limit=10
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

        return await call.answer(
            "No data",
            show_alert=True
        )



    text=f"📋 Username List\nPage {page+1}\n\n"


    for r in rows:

        text += f"• @{r[0]}\n"



    buttons=[]


    if page>0:

        buttons.append(
        InlineKeyboardButton(
            text="⬅️ Prev",
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
            text="🔙 Back",
            callback_data="back"
        )
    )



    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[buttons]
        )
    )



@dp.message(Command("list"))
async def list_cmd(message:Message):

    await message.answer(
        "📋 Open List",
        reply_markup=main_menu()
    )



@dp.callback_query(F.data.startswith("list_"))
async def list_callback(call:CallbackQuery):

    page=int(call.data.split("_")[1])

    await show_list(call,page)



# CHECK USERNAME

@dp.message(Command("check"))
async def check(message:Message):

    args=message.text.split()


    if len(args)<2:
        return await message.answer(
            "Use:\n/check username"
        )


    username=args[1].replace("@","")


    try:

        await bot.get_chat("@"+username)

        await message.answer(
            f"❌ @{username} is taken"
        )


    except:

        await message.answer(
            f"✅ @{username} available"
        )



# STATS

@dp.callback_query(F.data=="stats")
async def stats(call:CallbackQuery):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
            "SELECT COUNT(*) FROM usernames"
        )

        count=(await cur.fetchone())[0]


    await call.message.edit_text(
        f"📊 Total Usernames: {count}",
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[

        [
        InlineKeyboardButton(
            text="🔙 Back",
            callback_data="back"
        )
        ]

        ])
    )



# ADMIN

@dp.message(Command("admin"))
async def admin(message:Message):

    if message.from_user.id != OWNER_ID:

        return await message.answer(
            "❌ Access denied"
        )


    await message.answer(
        "🛠 Owner Panel",
        reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[

        [
        InlineKeyboardButton(
            text="🗑 Low Views Delete",
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
            text="🔙 Back",
            callback_data="back"
        )
        ]

        ])
    )



# BACK

@dp.callback_query(F.data=="back")
async def back(call:CallbackQuery):

    await call.message.edit_text(
        "Choose option:",
        reply_markup=main_menu()
    )



async def main():

    await init_db()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)



if __name__=="__main__":

    asyncio.run(main())
