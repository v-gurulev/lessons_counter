import os
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, filters, ContextTypes
from db import get_db
from i18n import _, get_lang, LANG_NAMES

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
    lang = await get_lang()

    if not admin_id and is_private:
        await db.set_config("ADMIN_CHAT_ID", chat_id)
        await update.message.reply_text(
            _("start_admin_set", lang, chat_id=chat_id)
        )
        return

    if not admin_id:
        await update.message.reply_text(_("start_first_setup", lang))
        return

    if chat_id == admin_id and is_private:
        await update.message.reply_text(
            _("start_admin_already", lang, chat_id=chat_id)
        )
        return


async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)
    lang = await get_lang()

    if chat_id != admin_id or update.effective_chat.type != "private":
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            _("lang_current", lang, lang_name=LANG_NAMES.get(lang, lang))
        )
        return

    new_lang = args[0].lower()
    if new_lang not in ("ru", "en"):
        await update.message.reply_text(_("lang_usage", lang), parse_mode="Markdown")
        return

    await db.set_config("language", new_lang)
    await update.message.reply_text(
        _("lang_changed", new_lang, lang_name=LANG_NAMES.get(new_lang, new_lang))
    )


async def myid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    lang = await get_lang()

    if update.effective_chat.type in ("group", "supergroup"):
        await update.message.reply_text(
            _("myid_group", lang, chat_id=chat_id)
        )
    else:
        await update.message.reply_text(_("myid_private", lang, chat_id=chat_id))


async def addstudent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)
    lang = await get_lang()

    if chat_id != admin_id or update.effective_chat.type != "private":
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            _("addstudent_format", lang),
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
        group_text = f", группа: `{group_chat_id}`" if group_chat_id else ""
        await update.message.reply_text(
            _("addstudent_success", lang, name=name, student_chat_id=student_chat_id, group_text=group_text),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(_("addstudent_exists", lang))


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)
    lang = await get_lang()

    if chat_id != admin_id or update.effective_chat.type != "private":
        return

    students = await db.get_all_students()
    if not students:
        await update.message.reply_text(_("stats_empty", lang))
        return

    msg = _("stats_header", lang)
    for name, bought, spent, last in students:
        bal = (bought or 0) - (spent or 0)
        last = last or "—"
        msg += _("stats_row", lang, name=name, bal=bal, last=last)

    await update.message.reply_text(msg, parse_mode="Markdown")


async def deletestudent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)
    lang = await get_lang()

    if chat_id != admin_id or update.effective_chat.type != "private":
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            _("deletestudent_format", lang),
            parse_mode="Markdown"
        )
        return

    student_chat_id = args[0]
    success = await db.delete_student(student_chat_id)

    if success:
        await update.message.reply_text(
            _("deletestudent_success", lang, student_chat_id=student_chat_id),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(_("deletestudent_not_found", lang))


async def register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = await db.get_config("ADMIN_CHAT_ID")
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)
    lang = await get_lang()

    if user_id != admin_id:
        return

    if update.effective_chat.type not in ("group", "supergroup"):
        await update.message.reply_text(_("register_only_groups", lang))
        return

    if update.message.reply_to_message:
        student_user = update.message.reply_to_message.from_user
        if not student_user:
            await update.message.reply_text(_("register_no_user", lang))
            return
        if str(student_user.id) == admin_id:
            await update.message.reply_text(_("register_admin_self", lang))
            return
        if student_user.is_bot:
            await update.message.reply_text(_("register_bot", lang))
            return

        name = student_user.first_name or _("student_default_name", lang, default="Ученик")
        success = await db.add_student(str(student_user.id), name, chat_id)
        if success:
            await update.message.reply_text(_("register_success", lang, name=name))
        else:
            await update.message.reply_text(_("register_exists", lang))
        return

    await update.message.reply_text(_("register_instructions", lang))


async def chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.my_chat_member:
        return
    new_status = update.my_chat_member.new_chat_member.status
    old_status = update.my_chat_member.old_chat_member.status
    chat = update.my_chat_member.chat
    lang = await get_lang()

    if chat.type in ("group", "supergroup") and new_status in ("member", "administrator"):
        if old_status not in ("member", "administrator"):
            await context.bot.send_message(
                chat.id,
                _("welcome_group", lang)
            )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text or ""
    is_group = update.effective_chat.type in ("group", "supergroup")
    lang = await get_lang()

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
                    _("need_admin_setup", lang)
                )
            return

        if user_id == admin_id:
            try:
                member_count = await context.bot.get_chat_member_count(int(chat_id))
                if member_count <= 2:
                    name = update.effective_user.first_name or _("test_default_name", lang, default="Тест")
                    await db.add_student(user_id, name, chat_id)
                    await update.message.reply_text(
                        _("test_mode_admin", lang, name=name)
                    )
                    student = await db.find_student_by_group(chat_id)
                else:
                    if "meet.google.com" in text:
                        await update.message.reply_text(
                            _("need_register_meet", lang)
                        )
                    return
            except Exception:
                if "meet.google.com" in text:
                    await update.message.reply_text(
                        _("need_register_meet", lang)
                    )
                return

        elif user_id:
            name = update.effective_user.first_name or _("student_default_name", lang, default="Ученик")
            await db.add_student(user_id, name, chat_id)
            await update.message.reply_text(
                _("auto_register_success", lang, name=name),
                parse_mode="Markdown"
            )
            student = await db.find_student_by_group(chat_id)

    if not is_group and not student and chat_id != admin_id:
        await update.message.reply_text(_("not_registered", lang))
        return

    if not is_group and not student and chat_id == admin_id:
        await update.message.reply_text(
            _("admin_panel", lang, chat_id=chat_id),
            parse_mode="Markdown"
        )
        return

    # Списание: Meet (только в группе)
    if "meet.google.com" in text:
        if not is_group:
            return
        if not student:
            await update.message.reply_text(_("not_registered", lang))
            return

        if student["balance"] <= 0:
            await update.message.reply_text(_("meet_zero_balance", lang))
            if admin_id:
                await context.bot.send_message(
                    admin_id,
                    _("meet_zero_balance_admin", lang, name=student["name"]),
                    parse_mode="Markdown"
                )
            return

        await db.log_transaction(student["chat_id"], student["name"], _("log_charge", lang), 1, text)
        await db.update_counters(student["chat_id"], "spent", 1)
        await db.update_last_lesson(student["chat_id"])

        new_bal = student["balance"] - 1
        await update.message.reply_text(
            _("meet_success", lang, new_bal=new_bal),
            parse_mode="Markdown"
        )
        if admin_id:
            await context.bot.send_message(
                admin_id,
                _("meet_success_admin", lang, name=student["name"], new_bal=new_bal),
                parse_mode="Markdown"
            )

        if new_bal == 1:
            await update.message.reply_text(
                _("meet_one_left", lang),
                parse_mode="Markdown"
            )
            if admin_id:
                await context.bot.send_message(
                    admin_id,
                    _("meet_one_left_admin", lang, name=student["name"]),
                    parse_mode="Markdown"
                )
        return

    # Пополнение: +число (в личке или в группе)
    match = re.search(r"(?:^|\s)\+\s*(\d+)(?:\s|$)", text)
    if match:
        count = int(match.group(1))
        if 0 < count <= 50:
            if not student:
                await update.message.reply_text(_("topup_unregistered", lang))
                return

            await db.log_transaction(student["chat_id"], student["name"], _("log_topup", lang), count, text)
            await db.update_counters(student["chat_id"], "bought", count)

            new_bal = student["balance"] + count
            await update.message.reply_text(
                _("topup_success", lang, count=count, new_bal=new_bal),
                parse_mode="Markdown"
            )
            if admin_id:
                await context.bot.send_message(
                    admin_id,
                    _("topup_success_admin", lang, name=student["name"], count=count, new_bal=new_bal),
                    parse_mode="Markdown"
                )
            return

    if is_group:
        return

    await update.message.reply_text(
        _("unknown_command", lang),
        parse_mode="Markdown"
    )


# ==================== MAIN ====================

def main():
    TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
    PORT = int(os.environ.get("PORT", 8443))

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("lang", lang_handler))
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
            webhook_url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET
        )
    else:
        logger.info("Starting polling mode...")
        application.run_polling()


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(db.init())
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    main()
