from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services import SERVICES


def get_services_kb() -> InlineKeyboardMarkup:
    buttons = []

    for key, data in SERVICES.items():
        buttons.append(
            [InlineKeyboardButton(text=data["title"], callback_data=f"service:{key}")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_service_actions_kb(service_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖼 Примеры работ",
                    callback_data=f"portfolio:{service_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Обсудить проект",
                    callback_data=f"start_brief:{service_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к услугам",
                    callback_data="back_to_menu",
                )
            ],
        ]
    )


def get_brief_kb(step: str) -> InlineKeyboardMarkup:
    buttons = []

    if step != "contact":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data=f"brief_skip:{step}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="✖️ Отменить",
                callback_data="brief_cancel",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
