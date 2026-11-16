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
                    text="💬 Обсудить проект",
                    callback_data=f"interest:{service_key}",
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
