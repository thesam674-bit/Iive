from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# SECRET ADMIN PASSWORD
ADMIN_KEY = "TG-Pro_9xA7_Channel_Manager_2026"


# ADMIN ACCESS COMMAND

@dp.message(Command("access"))
async def access(message: Message):

    args = message.text.split()

    if len(args) < 2:
        return await message.answer(
            "❌ Use:\n/access password"
        )


    password = args[1]


    if password != ADMIN_KEY:
        return await message.answer(
            "❌ Wrong password"
        )


    if message.from_user.id != 8864002775:
        return await message.answer(
            "❌ Access denied"
        )


    kb = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🗑 Low Views Delete",
                    callback_data="low_views"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎨 Channel Settings",
                    callback_data="channel_settings"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📋 Username Manage",
                    callback_data="username_manage"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="back"
                )
            ]

        ]
    )


    await message.answer(
        "🔐 Admin Panel Activated\n\n"
        "Welcome Owner 👑",
        reply_markup=kb
    )



# LOW VIEWS BUTTON

@dp.callback_query(F.data=="low_views")
async def low_views(call:CallbackQuery):

    await call.message.edit_text(
        "🗑 Low Views Cleaner\n\n"
        "Feature ready\n"
        "Set minimum views to delete posts."
        ,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Back",
                        callback_data="back"
                    )
                ]
            ]
        )
    )



# CHANNEL SETTINGS BUTTON

@dp.callback_query(F.data=="channel_settings")
async def channel_settings(call:CallbackQuery):

    await call.message.edit_text(
        "🎨 Channel Settings\n\n"
        "Options:\n\n"
        "📝 Change Name\n"
        "📄 Change Bio\n"
        "🖼 Change Photo",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Back",
                        callback_data="back"
                    )
                ]
            ]
        )
    )



# USERNAME MANAGE

@dp.callback_query(F.data=="username_manage")
async def username_manage(call:CallbackQuery):

    await call.message.edit_text(
        "📋 Username Manager\n\n"
        "Use:\n"
        "/add @username\n"
        "/remove username",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Back",
                        callback_data="back"
                    )
                ]
            ]
        )
    )
