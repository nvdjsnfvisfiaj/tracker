from html import escape
from typing import Tuple

from src.core import logger


def format_mint_message(data: dict) -> Tuple[str, str]:
    logger.debug(f"Formatting message for data: {data}")
    gift = data['gift']

    title = f"🆕 <b>{gift['title']} #{gift['num']}</b>\n"

    owner = gift.get('owner', {})
    owner_name = owner.get('first_name', '')
    username = owner.get('username') or (owner.get('usernames', []) or [None])[0]
    owner_id = owner.get('id')

    owner_text = escape(owner_name) or "???"
    owner_url = f"https://t.me/{username}" if username else f"tg://user?id={owner_id}" if owner_id else None

    owner_content = f"<a href='{owner_url}'>{owner_text}</a>" if owner_url else owner_text
    owner_line = f"<b>👤 Owner:</b> {owner_content}\n"

    attrs = gift['attributes']
    attributes = [
        f"<b>🎭 Model:</b> <code>{attrs[0]['name']}</code> ({attrs[0]['rarity']}%)",
        f"<b>🎨 Backdrop:</b> <code>{attrs[2]['name']}</code> ({attrs[2]['rarity']}%)",
        f"<b>🔮 Symbol:</b> <code>{attrs[1]['name']}</code> ({attrs[1]['rarity']}%)"
    ]

    stats = f"<b>📊 Availability:</b> {gift['availability_issued']:,}/{gift['availability_total']:,} issued"

    message = "\n".join([title, owner_line, *attributes, "", stats])
    nft_url = f"https://t.me/nft/{gift['title'].replace(' ', '')}-{gift['num']}"

    return message, nft_url
