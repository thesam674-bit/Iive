import asyncio
import os
import aiosqlite

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 8864002775

ADMIN_PASSWORD = "TG-Pro_9xA7_Channel_Manager_2026"

DB = "database.db"


bot = Bot(token=TOKEN)

dp = Dispatcher()


ADMIN_USERS = set()

WAIT_CHANNEL = set()



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



def menu():

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
            "📭 No usernames saved"
        )



    text=f"📋 Page {page+1}\n\n"


    for r in rows:

        text+=f"• @{r[0]}\n"



    btn=[]


    if page>0:

        btn.append(
        InlineKeyboardButton(
            text="⬅️ Prev",
            callback_data=f"show_list_{page-1}"
        ))


    if offset+limit < total:

        btn.append(
        InlineKeyboardButton(
            text="Next ➡️",
            callback_data=f"show_list_{page+1}"
        ))


    btn.append(
        InlineKeyboardButton(
            text="🔙 Menu",
            callback_data="back"
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
        "📋 List",
        reply_markup=menu()
    )



@dp.callback_query(F.data.startswith("show_list_"))
async def list_page(c:CallbackQuery):

    page=int(c.data.split("_")[2])

    await show_list(c,page)



@dp.message(Command("check"))
async def check(m:Message):

    args=m.text.split()

    if len(args)<2:
        return


    u=args[1].replace("@","")


    try:

        await bot.get_chat("@"+u)

        await m.answer(
            f"❌ @{u} is taken"
        )

    except:

        await m.answer(
            f"✅ @{u} is available"
        )



@dp.callback_query(F.data=="stats")
async def stats(c:CallbackQuery):

    async with aiosqlite.connect(DB) as db:

        cur=await db.execute(
            "SELECT COUNT(*) FROM usernames"
        )

        x=(await cur.fetchone())[0]


    await c.message.edit_text(
        f"📊 Total: {x}"
    )



# SECRET ACCESS

@dp.message(Command("secure"))
async def secure(m:Message):

    args=m.text.split()


    if len(args)<2:
        return


    if m.from_user.id != OWNER_ID:
        return


    if args[1] != ADMIN_PASSWORD:
        return


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
async def save_channel(m:Message):

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



@dp.callback_query(F.data=="back")
async def back(c:CallbackQuery):

    await c.message.edit_text(
        "Menu",
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
