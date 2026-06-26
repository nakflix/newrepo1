import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2,
    FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4,
    FORCE_SUB_CHANNEL_1_NAME, FORCE_SUB_CHANNEL_2_NAME,
    FORCE_SUB_CHANNEL_3_NAME, FORCE_SUB_CHANNEL_4_NAME,
    ADMINS
)
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait


# Map channel_id → (invite_link_attr, custom_name_override)
FORCE_SUB_CHANNELS = [
    (FORCE_SUB_CHANNEL_1, "invitelink",  FORCE_SUB_CHANNEL_1_NAME),
    (FORCE_SUB_CHANNEL_2, "invitelink2", FORCE_SUB_CHANNEL_2_NAME),
    (FORCE_SUB_CHANNEL_3, "invitelink3", FORCE_SUB_CHANNEL_3_NAME),
    (FORCE_SUB_CHANNEL_4, "invitelink4", FORCE_SUB_CHANNEL_4_NAME),
]

MEMBER_STATUSES = (
    ChatMemberStatus.OWNER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.MEMBER,
)


async def get_unjoined_channels(client, user_id: int) -> list:
    """
    Returns a list of (channel_id, invite_link, display_name) tuples
    for every force-sub channel the user has NOT yet joined.
    Returns an empty list if the user is fully subscribed (or is an admin).
    """
    if user_id in ADMINS:
        return []

    unjoined = []
    for idx, (channel_id, link_attr, custom_name) in enumerate(FORCE_SUB_CHANNELS, start=1):
        if not channel_id:
            continue
        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in MEMBER_STATUSES:
                raise UserNotParticipant
        except UserNotParticipant:
            # Fetch invite link & display name
            invite_link = getattr(client, link_attr, None) or ""
            if custom_name:
                display_name = custom_name
            else:
                try:
                    chat = await client.get_chat(channel_id)
                    display_name = chat.title or f"Channel {idx}"
                except Exception:
                    display_name = f"Channel {idx}"
            unjoined.append((channel_id, invite_link, display_name))
        except Exception:
            # If we can't check (bot not in channel, etc.) treat as unjoined
            invite_link = getattr(client, link_attr, None) or ""
            display_name = custom_name or f"Channel {idx}"
            unjoined.append((channel_id, invite_link, display_name))

    return unjoined


async def build_fsub_keyboard(client, user_id: int, original_command: str = ""):
    """
    Builds an InlineKeyboardMarkup showing only the channels
    the user hasn't joined yet, plus a ♻️ Try Again button.

    Returns (unjoined_list, keyboard) where unjoined_list is empty if
    the user is fully subscribed (keyboard is None in that case).
    """
    unjoined = await get_unjoined_channels(client, user_id)
    if not unjoined:
        return [], None

    buttons = []
    for channel_id, invite_link, display_name in unjoined:
        if invite_link:
            buttons.append([InlineKeyboardButton(f"✅ Join {display_name}", url=invite_link)])

    # Try Again button — re-triggers the same start payload if available
    if original_command:
        buttons.append([InlineKeyboardButton("♻️ Try Again ♻️", url=f"https://t.me/me?start={original_command}")])
    else:
        buttons.append([InlineKeyboardButton("♻️ Try Again ♻️", callback_data="check_subscription")])

    return unjoined, InlineKeyboardMarkup(buttons)


# ── Legacy filter kept for backwards compatibility ──────────────────────────

async def is_subscribed(filter, client, update):
    """Simple boolean filter – True only when the user has joined ALL channels."""
    if not any([FORCE_SUB_CHANNEL_1, FORCE_SUB_CHANNEL_2,
                FORCE_SUB_CHANNEL_3, FORCE_SUB_CHANNEL_4]):
        return True

    user_id = update.from_user.id
    unjoined = await get_unjoined_channels(client, user_id)
    return len(unjoined) == 0


subscribed = filters.create(is_subscribed)


# ── Utility helpers (unchanged) ─────────────────────────────────────────────

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string


async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except Exception:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages


async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    return 0


def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time
