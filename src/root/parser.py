import asyncio

from pyrogram import raw

from src.core import telegram_client, logger


def format_user_info(user) -> dict:
    info = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": getattr(user, 'last_name', '') or None,
        "username": getattr(user, 'username', None),
        "premium": user.premium,
        "verified": user.verified
    }

    if user.phone:
        info["phone"] = f"+{user.phone}"

    if hasattr(user, 'usernames'):
        active_usernames = [u.username for u in user.usernames if u.active]
        if active_usernames:
            info["usernames"] = active_usernames

    return {k: v for k, v in info.items() if v is not None}


def format_gift_data(result) -> dict:
    gift = result.gift
    data = {
        "gift": {
            "title": gift.title,
            "num": gift.num,
            "id": str(gift.id),
            "availability_issued": gift.availability_issued,
            "availability_total": gift.availability_total,
            "attributes": []
        }
    }

    for attr in gift.attributes:
        if not hasattr(attr, 'name') or not hasattr(attr, 'rarity_permille'):
            continue

        attr_data = {
            "name": attr.name,
            "rarity": round(attr.rarity_permille / 10, 1)
        }
        data["gift"]["attributes"].append(attr_data)

    if hasattr(gift, 'owner_name') and gift.owner_name:
        data["gift"]["owner"] = {"first_name": gift.owner_name}
    elif hasattr(gift, 'owner_id') and gift.owner_id and result.users:
        user = result.users[0]
        data["gift"]["owner"] = format_user_info(user)

    return data


async def parse_gift(url: str) -> dict:
    try:
        await asyncio.sleep(3)
        slug = url.split('/')[-1]
        result = await telegram_client.invoke(
            raw.functions.payments.GetUniqueStarGift(slug=slug)
        )
        return format_gift_data(result)
    except Exception as e:
        if "STARGIFT_SLUG_INVALID" in str(e):
            logger.debug(f"Invalid slug: {url}")
        else:
            logger.error(f"Error parsing gift {url}: {e}")
        return {"error": str(e)}
