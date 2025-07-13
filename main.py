
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
import asyncio

API_TOKEN = '7957692959:AAGYNF8vHZaHanfSIxjc-l3rtxBALhJ6PDE'
GROUP_CHAT_ID = -1002682478434

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

order_cb = CallbackData("order", "action", "user_id")

class OrderHookah(StatesGroup):
    strength = State()
    addon = State()
    flavor = State()
    phone = State()
    comment = State()

class Review(StatesGroup):
    writing = State()

def cancel_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Отменить заказ")
    return kb

def main_menu_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Заказать кальян", "Меню и цены")
    kb.add("Оставить отзыв")
    return kb

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu_keyboard())

@dp.message_handler(lambda m: m.text == "🔙 В главное меню")
async def back_to_main(message: types.Message):
    await start(message)

@dp.message_handler(lambda m: m.text == "Меню и цены")
async def send_menu(message: types.Message):
    with open("menu.jpg", "rb") as photo:
        await message.answer_photo(photo, caption="Наше меню и цены:")

@dp.message_handler(lambda m: m.text == "Заказать кальян")
async def order_start(message: types.Message):
    await message.answer("Вы выбрали: Кальян на чаше — 3000₽", reply_markup=cancel_keyboard())
    await message.answer("Оцените крепость от 1 до 10:")
    await OrderHookah.strength.set()

@dp.message_handler(state=OrderHookah.strength)
async def get_addon(message: types.Message, state: FSMContext):
    await state.update_data(strength=message.text)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Молоко (+200₽)", "Вино (+400₽)", "Абсент (+500₽)", "Без добавок")
    await message.answer("Выберите одну добавку:", reply_markup=keyboard)
    await OrderHookah.addon.set()

@dp.message_handler(state=OrderHookah.addon)
async def get_flavor(message: types.Message, state: FSMContext):
    addon_text = message.text
    addon_price = 0
    if "Молоко" in addon_text:
        addon_price = 200
    elif "Вино" in addon_text:
        addon_price = 400
    elif "Абсент" in addon_text:
        addon_price = 500

    await state.update_data(addon=addon_text, addon_price=addon_price)
    await message.answer("Введите вкусовые предпочтения (например: мята + арбуз):", reply_markup=cancel_keyboard())
    await OrderHookah.flavor.set()

@dp.message_handler(state=OrderHookah.flavor)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(flavor=message.text)
    await message.answer("Введите контактный номер телефона (мы свяжемся с вами через WhatsApp):", reply_markup=cancel_keyboard())
    await OrderHookah.phone.set()

@dp.message_handler(state=OrderHookah.phone)
async def ask_comment(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Комментарий (необязательно). Если нечего добавить, отправьте «-».", reply_markup=cancel_keyboard())
    await OrderHookah.comment.set()

@dp.message_handler(state=OrderHookah.comment)
async def finish_order(message: types.Message, state: FSMContext):
    comment = message.text if message.text.strip() != "-" else "Без комментариев"
    await state.update_data(comment=comment)
    data = await state.get_data()

    base_price = 3000
    total_price = base_price + data.get('addon_price', 0)
    username = f"@{message.from_user.username}" if message.from_user.username else "Не указано"

    user_message = (
        f"Ваш заказ принят!\n\n"
        f"Чаша: {base_price}₽\n"
        f"Крепость: {data['strength']}\n"
        f"Добавка: {data['addon']} (+{data['addon_price']}₽)\n"
        f"Вкусы: {data['flavor']}\n"
        f"Телефон: {data['phone']}\n"
        f"Комментарий: {data['comment']}\n"
        f"Итого: {total_price}₽\n\n"
        f"Способы оплаты: наличные, переводом."
    )
    await message.answer(user_message, reply_markup=main_menu_keyboard())
    await state.finish()

    group_message = (
        f"Новый заказ кальяна:\n"
        f"Гость: {username}\n"
        f"Чаша: 3000₽\n"
        f"Крепость: {data['strength']}\n"
        f"Добавка: {data['addon']} (+{data['addon_price']}₽)\n"
        f"Вкусы: {data['flavor']}\n"
        f"Телефон: {data['phone']}\n"
        f"Комментарий: {data['comment']}\n"
        f"Итого: {total_price}₽\n"
        f"Способы оплаты: наличные, переводом."
    )

    confirm_keyboard = types.InlineKeyboardMarkup()
    confirm_keyboard.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=order_cb.new(action="confirm", user_id=message.from_user.id)),
        types.InlineKeyboardButton("❌ Отменить", callback_data=order_cb.new(action="cancel", user_id=message.from_user.id)),
    )

    await bot.send_message(GROUP_CHAT_ID, group_message, reply_markup=confirm_keyboard)

    async def send_review_request(user_id):
        await asyncio.sleep(3600)
        try:
            await bot.send_message(user_id, "🙏 Спасибо за заказ! Хотите оставить отзыв? Нажмите «Оставить отзыв» в главном меню 💬")
        except Exception as e:
            print(f"Ошибка при отправке отзыва: {e}")

    asyncio.create_task(send_review_request(message.from_user.id))

@dp.callback_query_handler(order_cb.filter())
async def handle_order_action(callback: types.CallbackQuery, callback_data: dict):
    action = callback_data['action']
    user_id = int(callback_data['user_id'])

    if action == "confirm":
        await bot.send_message(user_id, "✅ Ваш заказ подтверждён! Скоро к вам подойдут.")
        await callback.message.edit_reply_markup()
        await callback.message.edit_text(callback.message.text + "\n\nСтатус: ✅ Подтверждён")
        await callback.answer("Заказ подтверждён.")
    elif action == "cancel":
        await bot.send_message(user_id, "❌ Ваш заказ был отменён. Вы можете сделать новый.")
        await callback.message.edit_reply_markup()
        await callback.message.edit_text(callback.message.text + "\n\nСтатус: ❌ Отменён")
        await callback.answer("Заказ отменён.")

@dp.message_handler(lambda m: m.text == "❌ Отменить заказ", state="*")
async def cancel_any_state(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Действие отменено.", reply_markup=main_menu_keyboard())

@dp.message_handler(lambda m: m.text == "Оставить отзыв")
async def leave_review(message: types.Message):
    await message.answer("✍️ Напишите свой отзыв. Мы отправим его в командный чат:", reply_markup=cancel_keyboard())
    await Review.writing.set()

@dp.message_handler(state=Review.writing)
async def handle_review_text(message: types.Message, state: FSMContext):
    username = f"@{message.from_user.username}" if message.from_user.username else "Не указано"
    text = f"📝 Новый отзыв от {username}:\n\n{message.text}"
    await bot.send_message(GROUP_CHAT_ID, text)
    await message.answer("Спасибо за ваш отзыв! 🙏", reply_markup=main_menu_keyboard())
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
