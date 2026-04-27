from db import get_db

db = get_db()

TRANSLATIONS = {
    "ru": {
        "start_admin_set": (
            "👨‍🏫 Вы назначены репетитором (админом).\n\n"
            "Команды:\n"
            "/addstudent [chat_id] [group_chat_id] [Имя] — добавить ученика\n"
            "/stats — сводка по всем ученикам\n"
            "/myid — узнать свой chat_id или ID группы\n\n"
            "Чтобы протестировать, добавьте себя как ученика:\n"
            "/addstudent {chat_id} ТестовыйУченик"
        ),
        "start_first_setup": "Напишите /start для первоначальной настройки.",
        "start_admin_already": (
            "👨‍🏫 Вы уже админ.\n\n"
            "Команды:\n"
            "• /addstudent [chat_id] [group_chat_id] [Имя]\n"
            "• /stats\n"
            "• /myid\n\n"
            "Чтобы протестировать как ученик, добавьте себя:\n"
            "/addstudent {chat_id} Тест"
        ),
        "myid_private": "Ваш chat_id: {chat_id}",
        "myid_group": (
            "ID этой группы: {chat_id}\n\n"
            "Используйте его при добавлении ученика:\n"
            "/addstudent [личный_chat_id] {chat_id} [Имя]"
        ),
        "addstudent_format": (
            "❌ Формат: `/addstudent [chat_id] [group_chat_id] [Имя]`\n"
            "`group_chat_id` опционально (начинается с `-`)"
        ),
        "addstudent_success": "✅ Ученик добавлен: *{name}* (личный ID: `{student_chat_id}`{group_text})",
        "addstudent_exists": "⚠️ Ученик с таким chat_id уже существует.",
        "stats_empty": "📊 Учеников пока нет.",
        "stats_header": "📊 *Сводка по ученикам:*\n\n",
        "stats_row": "• *{name}*: {bal} занятий _(последнее: {last})_\n",
        "deletestudent_format": "❌ Формат: `/deletestudent [chat_id]`",
        "deletestudent_success": "✅ Ученик удалён (ID: `{student_chat_id}`)",
        "deletestudent_not_found": "⚠️ Ученик с таким chat_id не найден.",
        "register_only_groups": "Эта команда работает только в группах.",
        "register_no_user": "Не удалось определить ученика.",
        "register_admin_self": "Нельзя зарегистрировать себя как ученика.",
        "register_bot": "Нельзя зарегистрировать бота как ученика.",
        "register_success": "✅ Ученик {name} добавлен!",
        "register_exists": "⚠️ Ученик уже зарегистрирован.",
        "register_instructions": (
            "📋 Чтобы зарегистрировать ученика:\n"
            "1. Найдите сообщение ученика в группе\n"
            "2. Ответьте на него этой командой: /register"
        ),
        "welcome_group": (
            "👋 Привет! Я бот для учёта занятий.\n\n"
            "📋 Как работать:\n"
            "• Кидайте ссылку на Google Meet — я спишу занятие\n"
            "• Для пополнения баланса напишите: +4 (можно прямо здесь или в личку)\n"
            "• /myid — узнать ID этой группы\n\n"
            "✨ Ученик добавится автоматически при первом сообщении!"
        ),
        "need_admin_setup": "⛔ Сначала назначьте админа. Напишите /start боту в личные сообщения.",
        "need_register_meet": "⛔ Ученик ещё не зарегистрирован. Пусть ученик напишет что-нибудь в группу.",
        "test_mode_admin": "✅ Режим теста: админ зарегистрирован как ученик {name}!",
        "auto_register_success": (
            "✅ Ученик *{name}* добавлен автоматически!\n\n"
            "💰 Пополнить баланс: отправьте *+4*\n"
            "🔗 Meet-ссылка — спишет занятие"
        ),
        "not_registered": "⛔ Вы не зарегистрированы. Попросите репетитора добавить вас.",
        "admin_panel": (
            "ℹ️ Вы админ.\n"
            "Команды: /addstudent, /stats, /myid\n\n"
            "Чтобы протестировать как ученик, добавьте себя:\n"
            "`/addstudent {chat_id} Тест`"
        ),
        "meet_zero_balance": "⚠️ У вас закончились занятия! Пополните баланс.",
        "meet_zero_balance_admin": "🚨 У ученика *{name}* баланс = 0!",
        "meet_success": "✅ Урок начался и засчитан.\nОсталось занятий: *{new_bal}*",
        "meet_success_admin": "📊 Ученик *{name}* — проведен урок.\nОсталось: *{new_bal}*",
        "meet_one_left": "⚠️ У вас осталось *1* занятие. Не забудьте пополнить баланс!",
        "meet_one_left_admin": "🔔 У ученика *{name}* осталось *1* занятие.",
        "topup_success": "💰 Пополнение на *{count}* занятий.\nТекущий баланс: *{new_bal}*",
        "topup_success_admin": "💰 Ученик *{name}* пополнил баланс на *{count}*.\nВсего: *{new_bal}*",
        "topup_unregistered": "⛔ Вы не зарегистрированы.",
        "unknown_command": (
            "🤔 Не понял команду.\n\n"
            "Отправьте число для пополнения (например: *+4* или *пакет 4*).\n"
            "Репетитор кидает ссылку на *Google Meet* — бот автоматически спишет занятие."
        ),
        "lang_changed": "✅ Язык изменён на {lang_name}.",
        "lang_current": "🌐 Текущий язык: {lang_name}.\nИспользуйте /lang ru или /lang en",
        "lang_usage": "🌐 Использование: `/lang ru` или `/lang en`",
        "log_topup": "пополнение",
        "log_charge": "списание",
    },
    "en": {
        "start_admin_set": (
            "👨‍🏫 You have been set as tutor (admin).\n\n"
            "Commands:\n"
            "/addstudent [chat_id] [group_chat_id] [Name] — add a student\n"
            "/stats — summary for all students\n"
            "/myid — get your chat_id or group ID\n\n"
            "To test, add yourself as a student:\n"
            "/addstudent {chat_id} TestStudent"
        ),
        "start_first_setup": "Send /start for initial setup.",
        "start_admin_already": (
            "👨‍🏫 You are already admin.\n\n"
            "Commands:\n"
            "• /addstudent [chat_id] [group_chat_id] [Name]\n"
            "• /stats\n"
            "• /myid\n\n"
            "To test as a student, add yourself:\n"
            "/addstudent {chat_id} Test"
        ),
        "myid_private": "Your chat_id: {chat_id}",
        "myid_group": (
            "ID of this group: {chat_id}\n\n"
            "Use it when adding a student:\n"
            "/addstudent [personal_chat_id] {chat_id} [Name]"
        ),
        "addstudent_format": (
            "❌ Format: `/addstudent [chat_id] [group_chat_id] [Name]`\n"
            "`group_chat_id` is optional (starts with `-`)"
        ),
        "addstudent_success": "✅ Student added: *{name}* (personal ID: `{student_chat_id}`{group_text})",
        "addstudent_exists": "⚠️ A student with this chat_id already exists.",
        "stats_empty": "📊 No students yet.",
        "stats_header": "📊 *Student summary:*\n\n",
        "stats_row": "• *{name}*: {bal} lessons _(last: {last})_\n",
        "deletestudent_format": "❌ Format: `/deletestudent [chat_id]`",
        "deletestudent_success": "✅ Student removed (ID: `{student_chat_id}`)",
        "deletestudent_not_found": "⚠️ Student with this chat_id not found.",
        "register_only_groups": "This command works only in groups.",
        "register_no_user": "Could not identify the student.",
        "register_admin_self": "You cannot register yourself as a student.",
        "register_bot": "You cannot register a bot as a student.",
        "register_success": "✅ Student {name} added!",
        "register_exists": "⚠️ Student already registered.",
        "register_instructions": (
            "📋 To register a student:\n"
            "1. Find the student's message in the group\n"
            "2. Reply to it with this command: /register"
        ),
        "welcome_group": (
            "👋 Hello! I'm a lesson counter bot.\n\n"
            "📋 How it works:\n"
            "• Send a Google Meet link — I'll deduct a lesson\n"
            "• To top up balance write: +4 (here or in private)\n"
            "• /myid — get this group's ID\n\n"
            "✨ A student will be added automatically on first message!"
        ),
        "need_admin_setup": "⛔ Please set an admin first. Send /start to the bot in a private message.",
        "need_register_meet": "⛔ Student is not registered yet. Ask them to send any message in the group.",
        "test_mode_admin": "✅ Test mode: admin registered as student {name}!",
        "auto_register_success": (
            "✅ Student *{name}* added automatically!\n\n"
            "💰 Top up balance: send *+4*\n"
            "🔗 Meet link — deducts a lesson"
        ),
        "not_registered": "⛔ You are not registered. Ask your tutor to add you.",
        "admin_panel": (
            "ℹ️ You are admin.\n"
            "Commands: /addstudent, /stats, /myid\n\n"
            "To test as a student, add yourself:\n"
            "`/addstudent {chat_id} Test`"
        ),
        "meet_zero_balance": "⚠️ You have no lessons left! Please top up your balance.",
        "meet_zero_balance_admin": "🚨 Student *{name}* has balance = 0!",
        "meet_success": "✅ Lesson started and counted.\nLessons left: *{new_bal}*",
        "meet_success_admin": "📊 Student *{name}* — lesson conducted.\nLeft: *{new_bal}*",
        "meet_one_left": "⚠️ You have *1* lesson left. Don't forget to top up!",
        "meet_one_left_admin": "🔔 Student *{name}* has *1* lesson left.",
        "topup_success": "💰 Topped up by *{count}* lessons.\nCurrent balance: *{new_bal}*",
        "topup_success_admin": "💰 Student *{name}* topped up balance by *{count}*.\nTotal: *{new_bal}*",
        "topup_unregistered": "⛔ You are not registered.",
        "unknown_command": (
            "🤔 Didn't understand the command.\n\n"
            "Send a number to top up (e.g. *+4* or *package 4*).\n"
            "Tutor sends a *Google Meet* link — the bot will automatically deduct a lesson."
        ),
        "lang_changed": "✅ Language changed to {lang_name}.",
        "lang_current": "🌐 Current language: {lang_name}.\nUse /lang ru or /lang en",
        "lang_usage": "🌐 Usage: `/lang ru` or `/lang en`",
        "log_topup": "topup",
        "log_charge": "charge",
    },
}

LANG_NAMES = {"ru": "Русский", "en": "English"}


def _(key: str, lang: str = "ru", **kwargs) -> str:
    """Get translated text by key."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
    return text.format(**kwargs)


async def get_lang() -> str:
    """Get current language from database (defaults to ru)."""
    val = await db.get_config("language")
    return val if val in TRANSLATIONS else "ru"
