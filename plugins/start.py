# (©) t.me/Ahjin_Sprt
# Updated: smart force-sub – shows inline buttons ONLY for unjoined channels

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from config import (
    FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2,
    FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4,
    START_MSG, FORCE_MSG, CUSTOM_CAPTION, PROTECT_CONTENT,
    ADMINS
)
from helper_func import (
    decode, get_messages, encode,
    build_fsub_keyboard, get_unjoined_channels
)


# ── /start handler ────────────────────────────────────────────────────────────

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user = message.from_user
    user_id = user.id
    first_name = user.first_name or "User"

    # Check if any force-sub channels are configured
    fsub_active = any([
        FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2,
        FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4,
    ])

    # The payload after /start (e.g. /start <encoded_ids>)
    payload = message.command[1] if len(message.command) > 1 else ""

    if fsub_active:
        unjoined, keyboard = await build_fsub_keyboard(client, user_id, payload)
        if unjoined:
            # User hasn't joined one or more channels — show only the missing ones
            force_text = FORCE_MSG.format(first=first_name, id=user_id)
            await message.reply(
                text=force_text,
                reply_markup=keyboard,
                quote=True
            )
            return

    # ── User is subscribed (or no fsub configured) — serve the request ──────
    if not payload:
        # Plain /start with no file payload
        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("About", callback_data="about"),
                InlineKeyboardButton("Close", callback_data="close")
            ]
        ])
        await message.reply(
            text=START_MSG.format(first=first_name, id=user_id, mention=user.mention),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )
        return

    # Decode the file payload and send files
    try:
        base64_string = payload
        string = await decode(base64_string)
        argument = string.split("-")

        if len(argument) == 3:
            # Batch: "get-start-end"
            start = int(int(argument[1]) / abs(client.db_channel.id))
            end = int(int(argument[2]) / abs(client.db_channel.id))
            ids = range(start, end + 1) if start <= end else []
        elif len(argument) == 2:
            # Single: "get-id"
            ids = [int(int(argument[1]) / abs(client.db_channel.id))]
        else:
            return

        temp_msg = await message.reply("<b>Please wait...</b>")
        messages = await get_messages(client, list(ids))
        await temp_msg.delete()

        for msg in messages:
            caption = (
                CUSTOM_CAPTION.format(
                    previouscaption=msg.caption or "",
                    filename=msg.document.file_name if msg.document else ""
                )
                if CUSTOM_CAPTION and (msg.document or msg.photo or msg.video)
                else (msg.caption or "")
            )

            try:
                await msg.copy(
                    chat_id=user_id,
                    caption=caption,
                    protect_content=PROTECT_CONTENT
                )
                await asyncio.sleep(0.5)
            except Exception:
                await asyncio.sleep(1)

    except Exception as e:
        await message.reply("<b>Something went wrong. Please try again.</b>")


# ── ♻️ Try Again callback ─────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^check_subscription$"))
async def check_subscription_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    first_name = query.from_user.first_name or "User"

    unjoined, keyboard = await build_fsub_keyboard(client, user_id)

    if unjoined:
        # Still missing some channels – refresh the keyboard (only missing ones)
        await query.answer("❌ You haven't joined all required channels yet!", show_alert=True)
        force_text = FORCE_MSG.format(first=first_name, id=user_id)
        try:
            await query.message.edit_text(
                text=force_text,
                reply_markup=keyboard
            )
        except Exception:
            pass
    else:
        # Now fully subscribed
        await query.answer("✅ You're now subscribed! Send your link again.", show_alert=True)
        try:
            await query.message.delete()
        except Exception:
            pass


# ── About / Close callbacks ───────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^about$"))
async def about_callback(client: Client, query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "<b>Multi File Sharing Bot</b>\n\n"
        "Share multiple Telegram files via a single link.\n\n"
        "Powered by @NAKFLIXTV",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back", callback_data="home"),
             InlineKeyboardButton("Close", callback_data="close")]
        ])
    )


@Client.on_callback_query(filters.regex("^home$"))
async def home_callback(client: Client, query: CallbackQuery):
    await query.answer()
    user = query.from_user
    await query.message.edit_text(
        text=START_MSG.format(
            first=user.first_name or "User",
            id=user.id,
            mention=user.mention
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("About", callback_data="about"),
                InlineKeyboardButton("Close", callback_data="close")
            ]
        ]),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex("^close$"))
async def close_callback(client: Client, query: CallbackQuery):
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass
