import os
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, filters, ContextTypes
from db import get_db

DB_PATH = os.getenv("DB_PATH", "bot.db")

db = get_db()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ==================== HANDLERS ====================

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)
    is_private = update.effective_chat.type == "private"

    if not admin_id and is_private:
        await db.set_config("ADMIN_CHAT_ID", chat_id)
        await update.message.reply_text(
            "👨‍🏫 Вы назначены репетитором (админом).\n\n"
            "Команды:\n"
            "/addstudent [chat_id] [group_chat_id] [Имя] — добавить ученика\n"
            "/stats — сводка по всем ученикам\n"
            "/myid — узнать свой chat_id или ID группы\n\n"
            f"Чтобы протестировать, добавьте себя как ученика:\n"
            f"/addstudent {chat_id} ТестовыйУченик"
        )
        return

    if not admin_id:
        await update.message.reply_text("Напишите /start для первоначальной настройки.")
        return

    if chat_id == admin_id and is_private:
        await update.message.reply_text(
            "👨‍🏫 Вы уже админ.\n\n"
            "Команды:\n"
            "• /addstudent [chat_id] [group_chat_id] [Имя]\n"
            "• /stats\n"
            "• /myid\n\n"
            f"Чтобы протестировать как ученик, добавьте себя:\n"
            f"/addstudent {chat_id} Тест"
        )
        return


async def myid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if update.effective_chat.type in ("group", "supergroup"):
        await update.message.reply_text(
            f"ID этой группы: {chat_id}\n\n"
            f"Используйте его при добавлении ученика:\n"
            f"/addstudent [личный_chat_id] {chat_id} [Имя]"
        )
    else:
        await update.message.reply_text(f"Ваш chat_id: {chat_id}")


async def addstudent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)

    if chat_id != admin_id or update.effective_chat.type != "private":
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Формат: `/addstudent [chat_id] [group_chat_id] [Имя]`\n"
            "`group_chat_id` опционально (начинается с `-`)",
            parse_mode="Markdown"
        )
        return

    student_chat_id = args[0]
    group_chat_id = None
    name_start = 1

    if len(args) >= 3 and args[1].startswith("-"):
        group_chat_id = args[1]
        name_start = 2

    name = " ".join(args[name_start:])
    success = await db.add_student(student_chat_id, name, group_chat_id)

    if success:
        msg = f"✅ Ученик добавлен: *{name}* (личный ID: `{student_chat_id}`"
        if group_chat_id:
            msg += f", группа: `{group_chat_id}`"
        msg += ")"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Ученик с таким chat_id уже существует.")


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)

    if chat_id != admin_id or update.effective_chat.type != "private":
        return

    students = await db.get_all_students()
    if not students:
        await update.message.reply_text("📊 Учеников пока нет.")
        return

    msg = "📊 *Сводка по ученикам:*\n\n"
    for name, bought, spent, last in students:
        bal = (bought or 0) - (spent or 0)
        last = last or "—"
        msg += f"• *{name}*: {bal} занятий _(последнее: {last})_\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def deletestudent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)

    if chat_id != admin_id or update.effective_chat.type != "private":
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "❌ Формат: `/deletestudent [chat_id]`",
            parse_mode="Markdown"
        )
        return

    student_chat_id = args[0]
    success = await db.delete_student(student_chat_id)

    if success:
        await update.message.reply_text(f"✅ Ученик удалён (ID: `{student_chat_id}`)", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Ученик с таким chat_id не найден.")


async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)

    if user_id != admin_id:
        return

    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Эта команда работает только в группах.")
        return

    if update.message.reply_to_message:
        student_user = update.message.reply_to_message.from_user
        if not student_user:
            await update.message.reply_text("Не удалось определить ученика.")
            return
        if str(student_user.id) == admin_id:
            await update.message.reply_text("Нельзя зарегистрировать себя как ученика.")
            return
        if student_user.is_bot:
            await update.message.reply_text("Нельзя зарегистрировать бота как ученика.")
            return

        name = student_user.first_name or "Ученик"
        success = await db.add_student(str(student_user.id), name, chat_id)
        if success:
            await update.message.reply_text(f"✅ Ученик {name} добавлен!")
        else:
            await update.message.reply_text("⚠️ Ученик уже зарегистрирован.")
        return

    await update.message.reply_text(
        "📋 Чтобы зарегистрировать ученика:\n"
        "1. Найдите сообщение ученика в группе\n"
        "2. Ответьте на него этой командой: /register"
    )


async def chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.my_chat_member:
        return
    new_status = update.my_chat_member.new_chat_member.status
    old_status = update.my_chat_member.old_chat_member.status
    chat = update.my_chat_member.chat

    if chat.type in ("group", "supergroup") and new_status in ("member", "administrator"):
        if old_status not in ("member", "administrator"):
            await context.bot.send_message(
                chat.id,
                "👋 Привет! Я бот для учёта занятий.\n\n"
                "📋 Как работать:\n"
                "• Кидайте ссылку на Google Meet — я спишу занятие\n"
                "• Для пополнения баланса напишите: +4 (можно прямо здесь или в личку)\n"
                "• /myid — узнать ID этой группы\n\n"
                "✨ Ученик добавится автоматически при первом сообщении!"
            )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text or ""
    is_group = update.effective_chat.type in ("group", "supergroup")

    student = None
    if is_group:
        student = await db.find_student_by_group(chat_id)
    else:
        student = await db.find_student_by_chat(chat_id)

    admin_id = await db.get_config("ADMIN_CHAT_ID")
    user_id = str(update.effective_user.id) if update.effective_user else None

    # Группа без привязки — авто-регистрация или предупреждение
    if is_group and not student:
        if not admin_id:
            if "meet.google.com" in text or text.startswith("/"):
                await update.message.reply_text(
                    "⛔ Сначала назначьте админа. Напишите /start боту в личные сообщения."
                )
            return

        if user_id == admin_id:
            try:
                member_count = await context.bot.get_chat_member_count(int(chat_id))
                if member_count <= 2:
                    name = update.effective_user.first_name or "Тест"
                    await db.add_student(user_id, name, chat_id)
                    await update.message.reply_text(
                        f"✅ Режим теста: админ зарегистрирован как ученик {name}!"
                    )
                    student = await db.find_student_by_group(chat_id)
                else:
                    if "meet.google.com" in text:
                        await update.message.reply_text(
                            "⛔ Ученик ещё не зарегистрирован. Пусть ученик напишет что-нибудь в группу."
                        )
                    return
            except Exception:
                if "meet.google.com" in text:
                    await update.message.reply_text(
                        "⛔ Ученик ещё не зарегистрирован. Пусть ученик напишет что-нибудь в группу."
                    )
                return

        elif user_id:
            name = update.effective_user.first_name or "Ученик"
            await db.add_student(user_id, name, chat_id)
            await update.message.reply_text(
                f"✅ Ученик *{name}* добавлен автоматически!\n\n"
                f"💰 Пополнить баланс: отправьте *+4*\n"
                f"🔗 Meet-ссылка — спишет занятие",
                parse_mode="Markdown"
            )
            student = await db.find_student_by_group(chat_id)

    if not is_group and not student and chat_id != admin_id:
        await update.message.reply_text("⛔ Вы не зарегистрированы. Попросите репетитора добавить вас.")
        return

    if not is_group and not student and chat_id == admin_id:
        await update.message.reply_text(
            "ℹ️ Вы админ.\nКоманды: /addstudent, /stats, /myid\n\n"
            f"Чтобы протестировать как ученик, добавьте себя:\n"
            f"`/addstudent {chat_id} Тест`",
            parse_mode="Markdown"
        )
        return

    # Списание: Meet (только в группе)
    if "meet.google.com" in text:
        if not is_group:
            return
        if not student:
            await update.message.reply_text("⛔ Вы не зарегистрированы.")
            return

        if student["balance"] <= 0:
            await update.message.reply_text("⚠️ У вас закончились занятия! Пополните баланс.")
            if admin_id:
                await context.bot.send_message(
                    admin_id,
                    f"🚨 У ученика *{student['name']}* баланс = 0!",
                    parse_mode="Markdown"
                )
            return

        await db.log_transaction(student["chat_id"], student["name"], "списание", 1, text)
        await db.update_counters(student["chat_id"], "spent", 1)
        await db.update_last_lesson(student["chat_id"])

        new_bal = student["balance"] - 1
        await update.message.reply_text(
            f"✅ Урок начался и засчитан.\nОсталось занятий: *{new_bal}*",
            parse_mode="Markdown"
        )
        if admin_id:
            await context.bot.send_message(
                admin_id,
                f"📊 Ученик *{student['name']}* — проведен урок.\nОсталось: *{new_bal}*",
                parse_mode="Markdown"
            )

        if new_bal == 1:
            await update.message.reply_text(
                "⚠️ У вас осталось *1* занятие. Не забудьте пополнить баланс!",
                parse_mode="Markdown"
            )
            if admin_id:
                await context.bot.send_message(
                    admin_id,
                    f"🔔 У ученика *{student['name']}* осталось *1* занятие.",
                    parse_mode="Markdown"
                )
        return

    # Пополнение: +число (в личке или в группе)
    match = re.search(r"(?:^|\s)\+\s*(\d+)(?:\s|$)", text)
    if match:
        count = int(match.group(1))
        if 0 < count <= 50:
            if not student:
                await update.message.reply_text("⛔ Вы не зарегистрированы.")
                return

            await db.log_transaction(student["chat_id"], student["name"], "пополнение", count, text)
            await db.update_counters(student["chat_id"], "bought", count)

            new_bal = student["balance"] + count
            await update.message.reply_text(
                f"💰 Пополнение на *{count}* занятий.\nТекущий баланс: *{new_bal}*",
                parse_mode="Markdown"
            )
            if admin_id:
                await context.bot.send_message(
                    admin_id,
                    f"💰 Ученик *{student['name']}* пополнил баланс на *{count}*.\nВсего: *{new_bal}*",
                    parse_mode="Markdown"
                )
            return

    if is_group:
        return

    await update.message.reply_text(
        "🤔 Не понял команду.\n\n"
        "Отправьте число для пополнения (например: *+4* или *пакет 4*).\n"
        "Репетитор кидает ссылку на *Google Meet* — бот автоматически спишет занятие.",
        parse_mode="Markdown"
    )


# ==================== MAIN ====================

def main():
    TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    PORT = int(os.environ.get("PORT", 8443))

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("myid", myid_handler))
    application.add_handler(CommandHandler("addstudent", addstudent_handler))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("deletestudent", deletestudent_handler))
    application.add_handler(CommandHandler("register", register_handler))
    application.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    if WEBHOOK_URL:
        logger.info(f"Starting webhook on port {PORT}, URL: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL
        )
    else:
        logger.info("Starting polling mode...")
        application.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(db.init())
    main()
