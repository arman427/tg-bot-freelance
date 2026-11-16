import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import settings
from keyboards import get_services_kb, get_service_actions_kb
from services import SERVICES

import time

TOKEN = settings.BOT_TOKEN
dp = Dispatcher()
last_request_time: dict[int, float] = {}
COOLDOWN_SECONDS = 180


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Здравствуйте, {message.from_user.full_name}\n\nВыберите интересующую вас услугу:",  # type: ignore
        reply_markup=get_services_kb(),
    )


@dp.callback_query(F.data.startswith("service:"))
async def show_service_handler(callback: CallbackQuery) -> None:
    key = callback.data.split(":")[1]  # type: ignore

    await callback.message.edit_text(  # type: ignore
        SERVICES[key]["description"],
        reply_markup=get_service_actions_kb(key),
    )
    await callback.answer()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(  # type: ignore
        "Выберите интересующую вас услугу:",
        reply_markup=get_services_kb(),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("interest:"))
async def send_message_to_me(callback: CallbackQuery, bot: Bot) -> None:
    key = callback.data.split(":")[1]  # type: ignore
    service_title = SERVICES[key]["title"]
    user = callback.from_user

    now = time.time()

    last_time = last_request_time.get(user.id, 0)

    if (now - last_time) < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - last_time))
        await callback.answer(
            f"Заявка уже отправлена. Повторно можно отправить через {remaining} сек.",
            show_alert=True,
        )
        return

    contact = (
        f"@{user.username}"
        if user.username
        else f'<a href="tg://user?id={user.id}">открыть профиль</a>'
    )

    admin_text = (
        f"🔥 <b>Новая заявка из бота!</b>\n\n"
        f"<b>Услуга:</b> {service_title}\n"
        f"<b>Клиент:</b> {user.full_name}\n"
        f"<b>Контакт:</b> {contact}\n"
        f"<b>ID:</b> <code>{user.id}</code>"
    )

    await bot.send_message(chat_id=settings.ADMIN_ID, text=admin_text)

    last_request_time[user.id] = now

    await callback.message.edit_text(  # type: ignore
        f"Заявка по услуге <b>«{service_title}»</b> передана, скоро с вами свяжусь!\n\n"
        f"Если интересует что-то ещё — выберите ниже:",
        reply_markup=get_services_kb(),
    )
    await callback.answer("Заявка отправлена!")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
