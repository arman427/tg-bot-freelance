import asyncio
import html
import time
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from keyboards import get_services_kb, get_service_actions_kb, get_brief_kb
from services import SERVICES, PORTFOLIO

TOKEN = settings.BOT_TOKEN
dp = Dispatcher(storage=MemoryStorage())
last_request_time: dict[int, float] = {}
COOLDOWN_SECONDS = 180


class Brief(StatesGroup):
    task = State()
    budget = State()
    deadline = State()
    contact = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Здравствуйте, {html.escape(message.from_user.full_name)}\n\nВыберите интересующую вас услугу:",  # type: ignore
        reply_markup=get_services_kb(),
    )


@dp.callback_query(F.data.startswith("service:"))
async def show_service_handler(callback: CallbackQuery) -> None:
    key = callback.data.split(":")[1]  # type: ignore
    service = SERVICES[key]

    text = (
        f"{service['description']}\n\n"
        f"💰 <b>Стоимость:</b> {service['price']}\n"
        f"⏱ <b>Срок:</b> {service['duration']}\n\n"
        f"<i>Точную смету назову после короткого брифа.</i>"
    )

    await callback.message.edit_text(  # type: ignore
        text,
        reply_markup=get_service_actions_kb(key),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("portfolio:"))
async def show_portfolio_handler(callback: CallbackQuery, bot: Bot) -> None:
    key = callback.data.split(":")[1]  # type: ignore
    items = PORTFOLIO.get(key) or []

    if not items:
        await callback.answer("Примеры по этой услуге скоро добавлю", show_alert=True)
        return

    for item in items:
        if item["type"] == "photo":
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=item["value"],
                caption=item.get("caption"),
            )
        else:
            text = item["value"]
            if item.get("caption"):
                text = f"{item['caption']}\n{text}"
            await bot.send_message(chat_id=callback.from_user.id, text=text)

    await callback.answer()


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(  # type: ignore
        "Выберите интересующую вас услугу:",
        reply_markup=get_services_kb(),
    )
    await callback.answer()


QUESTIONS = {
    "task": "Шаг 1/4. Опишите задачу — что нужно сделать?",
    "budget": "Шаг 2/4. Какой бюджет? Если пока не знаете — так и напишите.",
    "deadline": "Шаг 3/4. Какие сроки?",
    "contact": "Шаг 4/4. Как с вами связаться? Телефон, @username или «сюда в Telegram».",
}
STEP_STATES = {
    "task": Brief.task,
    "budget": Brief.budget,
    "deadline": Brief.deadline,
    "contact": Brief.contact,
}
NEXT_STEP = {"task": "budget", "budget": "deadline", "deadline": "contact"}


async def ask_step(message: Message, state: FSMContext, step: str) -> None:
    await state.set_state(STEP_STATES[step])
    await message.answer(QUESTIONS[step], reply_markup=get_brief_kb(step))


async def send_brief(bot: Bot, message: Message, data: dict, contact: str) -> None:
    user = message.from_user
    now = time.time()
    last_time = last_request_time.get(user.id, 0)

    if (now - last_time) < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - last_time))
        await message.answer(
            f"Заявка уже отправлена. Повторно можно отправить через {remaining} сек."
        )
        return

    service_title = SERVICES[data["service_key"]]["title"]
    created_at = datetime.now(timezone(timedelta(hours=3))).strftime("%d.%m.%Y %H:%M")
    profile = (
        f"@{user.username}"
        if user.username
        else f'<a href="tg://user?id={user.id}">открыть профиль</a>'
    )

    admin_text = (
        f"🔥 <b>Новая заявка из бота!</b>\n\n"
        f"<b>Услуга:</b> {service_title}\n"
        f"<b>Дата:</b> {created_at}\n"
        f"<b>Задача:</b> {html.escape(data.get('task', '—'))}\n"
        f"<b>Бюджет:</b> {html.escape(data.get('budget', '—'))}\n"
        f"<b>Сроки:</b> {html.escape(data.get('deadline', '—'))}\n"
        f"<b>Связь:</b> {html.escape(contact)}\n"
        f"<b>Клиент:</b> {html.escape(user.full_name)}\n"
        f"<b>Профиль:</b> {profile}\n"
        f"<b>ID:</b> <code>{user.id}</code>"
    )

    await bot.send_message(chat_id=settings.ADMIN_ID, text=admin_text)
    last_request_time[user.id] = now

    await message.answer(
        f"Спасибо! Заявка по услуге <b>«{service_title}»</b> передана, скоро с вами свяжусь!\n\n"
        "Если интересует что-то ещё — выберите ниже:",
        reply_markup=get_services_kb(),
    )


@dp.callback_query(F.data.startswith("start_brief:"))
async def start_brief_handler(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":")[1]  # type: ignore
    await state.update_data(service_key=key)
    await state.set_state(Brief.task)
    await callback.message.edit_text(  # type: ignore
        QUESTIONS["task"], reply_markup=get_brief_kb("task")
    )
    await callback.answer()


@dp.message(Brief.task)
async def brief_task_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(task=message.text or "—")
    await ask_step(message, state, "budget")


@dp.message(Brief.budget)
async def brief_budget_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(budget=message.text or "—")
    await ask_step(message, state, "deadline")


@dp.message(Brief.deadline)
async def brief_deadline_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(deadline=message.text or "—")
    await ask_step(message, state, "contact")


@dp.message(Brief.contact)
async def brief_contact_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    await send_brief(bot, message, data, message.text or "сюда в Telegram")


@dp.callback_query(F.data.startswith("brief_skip:"))
async def brief_skip_handler(callback: CallbackQuery, state: FSMContext) -> None:
    step = callback.data.split(":")[1]  # type: ignore
    await state.update_data(**{step: "—"})

    next_step = NEXT_STEP.get(step)
    if next_step:
        await state.set_state(STEP_STATES[next_step])
        await callback.message.answer(  # type: ignore
            QUESTIONS[next_step], reply_markup=get_brief_kb(next_step)
        )
    await callback.answer()


@dp.callback_query(F.data == "brief_cancel")
async def brief_cancel_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(  # type: ignore
        "Ок, отменил. Выберите интересующую вас услугу:",
        reply_markup=get_services_kb(),
    )
    await callback.answer()


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
