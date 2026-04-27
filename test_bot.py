import os
import sys
import tempfile
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Устанавливаем временную БД для тестов
TEMP_DIR = tempfile.mkdtemp()
os.environ["DB_PATH"] = os.path.join(TEMP_DIR, "test_bot.db")

import main
import aiosqlite


class MockChat:
    def __init__(self, chat_id, chat_type="private"):
        self.id = chat_id
        self.type = chat_type


class MockUser:
    def __init__(self, user_id, first_name="User", is_bot=False):
        self.id = user_id
        self.first_name = first_name
        self.is_bot = is_bot


class MockMessage:
    def __init__(self, text, chat_id=123456, chat_type="private", from_user_id=None, from_user_name="User", reply_to=None):
        self.text = text
        self.chat = MockChat(chat_id, chat_type)
        self.reply_text = AsyncMock()
        self.from_user = MockUser(from_user_id if from_user_id is not None else chat_id, from_user_name)
        self.reply_to_message = reply_to


class MockUpdate:
    def __init__(self, text, chat_id=123456, chat_type="private", from_user_id=None, from_user_name="User", reply_to=None):
        self.message = MockMessage(text, chat_id, chat_type, from_user_id, from_user_name, reply_to)
        self.effective_chat = self.message.chat
        self.effective_user = self.message.from_user


class MockChatMember:
    def __init__(self, status):
        self.status = status


class MockChatMemberUpdated:
    def __init__(self, chat, old_status, new_status):
        self.chat = chat
        self.old_chat_member = MockChatMember(old_status)
        self.new_chat_member = MockChatMember(new_status)


class MockUpdateMember:
    def __init__(self, chat, old_status, new_status):
        self.my_chat_member = MockChatMemberUpdated(chat, old_status, new_status)
        self.effective_chat = chat


class MockContext:
    def __init__(self, args=None, member_count=2):
        self.args = args or []
        self.bot = MagicMock()
        self.bot.send_message = AsyncMock()
        self.bot.get_chat_member_count = AsyncMock(return_value=member_count)


class TestBotLogic(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await main.db.init()
        # Очищаем config и students перед каждым тестом
        async with aiosqlite.connect(os.environ["DB_PATH"]) as db_conn:
            await db_conn.execute("DELETE FROM config")
            await db_conn.execute("DELETE FROM students")
            await db_conn.execute("DELETE FROM transactions")
            await db_conn.commit()

    async def test_01_start_sets_admin(self):
        update = MockUpdate("/start", chat_id=320246687)
        context = MockContext()
        await main.start_handler(update, context)

        admin_id = await main.db.get_config("ADMIN_CHAT_ID")
        self.assertEqual(admin_id, "320246687")
        update.message.reply_text.assert_called_once()
        text = update.message.reply_text.call_args[0][0]
        self.assertIn("репетитором", text)

    async def test_02_start_already_admin(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("/start", chat_id=320246687)
        context = MockContext()
        await main.start_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Вы уже админ", text)

    async def test_03_myid_private(self):
        update = MockUpdate("/myid", chat_id=111222)
        context = MockContext()
        await main.myid_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("111222", text)

    async def test_04_myid_group(self):
        update = MockUpdate("/myid", chat_id=-123456789, chat_type="group", from_user_id=111222333)
        context = MockContext()
        await main.myid_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("-123456789", text)
        self.assertIn("addstudent", text)

    async def test_05_add_student_with_group(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("/addstudent", chat_id=320246687)
        context = MockContext(args=["111222333", "-987654321", "Анна"])
        await main.addstudent_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Анна", text)
        self.assertIn("-987654321", text)

        student = await main.db.find_student_by_chat("111222333")
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], "Анна")
        self.assertEqual(student["group_chat_id"], "-987654321")

    async def test_06_stats_shows_student(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна", "-987654321")
        update = MockUpdate("/stats", chat_id=320246687)
        context = MockContext()
        await main.stats_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Анна", text)
        self.assertIn("0 занятий", text)

    async def test_07_student_topup_private(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        update = MockUpdate("+4", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Пополнение", text)
        self.assertIn("4", text)

        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["bought"], 4)
        self.assertEqual(student["balance"], 4)

    async def test_08_group_topup_works(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна", "-987654321")
        update = MockUpdate("+4", chat_id=-987654321, chat_type="group", from_user_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Пополнение", text)
        self.assertIn("4", text)

        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["bought"], 4)
        self.assertEqual(student["balance"], 4)

    async def test_09_group_meet_charge(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна", "-987654321")
        # Пополняем
        await main.db.update_counters("111222333", "bought", 4)

        update = MockUpdate("meet.google.com/abc-defg-hij", chat_id=-987654321, chat_type="group", from_user_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Осталось", text)

        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["spent"], 1)
        self.assertEqual(student["balance"], 3)

    async def test_10_multiple_topup_and_meet(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна", "-987654321")
        await main.db.update_counters("111222333", "bought", 2)

        # Списываем в группе
        update = MockUpdate("meet.google.com/xxx", chat_id=-987654321, chat_type="group", from_user_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)

        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["bought"], 2)
        self.assertEqual(student["spent"], 1)
        self.assertEqual(student["balance"], 1)

    async def test_11_stats_after_activity(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна", "-987654321")
        await main.db.update_counters("111222333", "bought", 6)
        await main.db.update_counters("111222333", "spent", 2)

        update = MockUpdate("/stats", chat_id=320246687)
        context = MockContext()
        await main.stats_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Анна", text)
        self.assertIn("4 занятий", text)

    async def test_12_unregistered_user(self):
        update = MockUpdate("+5", chat_id=999888777)
        context = MockContext()
        await main.text_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("не зарегистрированы", text)

    async def test_13_group_auto_register(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        # Ученик пишет первое сообщение в новой группе
        update = MockUpdate("привет", chat_id=-999999999, chat_type="group", from_user_id=111222333, from_user_name="АвтоУченик")
        context = MockContext()
        await main.text_handler(update, context)

        # Ученик должен быть добавлен автоматически
        student = await main.db.find_student_by_group("-999999999")
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], "АвтоУченик")
        self.assertEqual(student["chat_id"], "111222333")

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("АвтоУченик", text)
        self.assertIn("добавлен автоматически", text)

    async def test_14_admin_unknown_command(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("какая-то ерунда", chat_id=320246687)
        context = MockContext()
        await main.text_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("админ", text)

    async def test_15_zero_balance_block(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Бедный", "-987654321")

        update = MockUpdate("meet.google.com/zero", chat_id=-987654321, chat_type="group", from_user_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("закончились", text)

        # Транзакция списания НЕ создается
        async with aiosqlite.connect(os.environ["DB_PATH"]) as db_conn:
            async with db_conn.execute("SELECT COUNT(*) FROM transactions") as cur:
                count = (await cur.fetchone())[0]
                self.assertEqual(count, 0)

    async def test_16_one_lesson_warning(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Предупреждаемый", "-987654321")
        await main.db.update_counters("111222333", "bought", 2)

        update = MockUpdate("meet.google.com/one-left", chat_id=-987654321, chat_type="group", from_user_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)

        # Должно быть 2 сообщения: основное + предупреждение
        self.assertEqual(update.message.reply_text.call_count, 2)
        texts = [call[0][0] for call in update.message.reply_text.call_args_list]
        self.assertTrue(any("Осталось" in t for t in texts))
        self.assertTrue(any("*1*" in t and "занятие" in t for t in texts))

    async def test_17_add_student_without_group(self):
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("/addstudent", chat_id=320246687)
        context = MockContext(args=["111222333", "БезГруппы"])
        await main.addstudent_handler(update, context)

        student = await main.db.find_student_by_chat("111222333")
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], "БезГруппы")
        self.assertIsNone(student["group_chat_id"])

    async def test_18_welcome_on_group_add(self):
        chat = MockChat(-987654321, "group")
        update = MockUpdateMember(chat, "left", "member")
        context = MockContext()
        await main.chat_member_handler(update, context)

        context.bot.send_message.assert_called_once()
        text = context.bot.send_message.call_args[0][1]
        self.assertIn("Привет", text)
        self.assertIn("Google Meet", text)

    # === EDGE CASES: пополнение ===

    async def test_19_no_plus_no_topup(self):
        """Число без плюса — не пополнение"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        await main.db.update_counters("111222333", "bought", 4)
        update = MockUpdate("У меня 4 занятия", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Не понял", text)
        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["bought"], 4)  # баланс не изменился

    async def test_20_date_not_topup(self):
        """Дата типа 17.05 — не пополнение"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        await main.db.update_counters("111222333", "bought", 4)
        update = MockUpdate("Занятие будет 17.05", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Не понял", text)
        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["bought"], 4)

    async def test_21_text_with_number_not_topup(self):
        """Число в середине текста — не пополнение"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        await main.db.update_counters("111222333", "bought", 4)
        update = MockUpdate("Я прошел 12 тестов", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Не понял", text)
        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["bought"], 4)

    async def test_22_plus_zero_not_topup(self):
        """+0 — не пополнение (ноль не в диапазоне)"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        await main.db.update_counters("111222333", "bought", 4)
        update = MockUpdate("+0", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Не понял", text)
        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["bought"], 4)

    async def test_23_plus_fifty_one_not_topup(self):
        """+51 — слишком много, не пополнение"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        await main.db.update_counters("111222333", "bought", 4)
        update = MockUpdate("+51", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Не понял", text)
        student = await main.db.find_student_by_chat("111222333")
        self.assertEqual(student["bought"], 4)

    async def test_24_plus_with_space(self):
        """+ 4 с пробелом — должно работать"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        update = MockUpdate("+ 4", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Пополнение", text)
        self.assertIn("4", text)

    async def test_25_empty_message(self):
        """Пустое сообщение — игнорируем"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        update = MockUpdate("", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        # Не падаем, молча игнорируем или отвечаем "не понял"
        # Достаточно проверить, что не упали
        self.assertTrue(True)

    async def test_26_only_emoji(self):
        """Только emoji — отвечаем Не понял"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        update = MockUpdate("👍🎉", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Не понял", text)

    async def test_27_stats_in_group_ignored(self):
        """/stats в группе — игнорируется"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна", "-987654321")
        update = MockUpdate("/stats", chat_id=-987654321, chat_type="group", from_user_id=320246687)
        context = MockContext()
        await main.stats_handler(update, context)
        update.message.reply_text.assert_not_called()

    async def test_28_meet_in_private_ignored(self):
        """Meet-ссылка в личке — игнорируется (не списываем)"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.add_student("111222333", "Анна")
        await main.db.update_counters("111222333", "bought", 4)
        update = MockUpdate("meet.google.com/abc", chat_id=111222333)
        context = MockContext()
        await main.text_handler(update, context)
        # В личке meet не списывается
        update.message.reply_text.assert_not_called()

    async def test_29_register_by_reply(self):
        """Админ отвечает reply /register на сообщение ученика"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        # Сообщение ученика
        student_msg = MockMessage("привет", chat_id=-987654321, chat_type="group", from_user_id=111222333, from_user_name="Вова")
        # Админ отвечает reply /register
        update = MockUpdate("/register", chat_id=-987654321, chat_type="group", from_user_id=320246687, reply_to=student_msg)
        context = MockContext()
        await main.register_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Вова", text)
        self.assertIn("добавлен", text)

        student = await main.db.find_student_by_group("-987654321")
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], "Вова")
        self.assertEqual(student["chat_id"], "111222333")

    async def test_30_register_without_reply(self):
        """/register без reply — инструкция"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("/register", chat_id=-987654321, chat_type="group", from_user_id=320246687)
        context = MockContext()
        await main.register_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Ответьте", text)

    async def test_31_admin_as_student_in_small_group(self):
        """В группе с 2 участниками админ = ученик (тестовый режим)"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("привет", chat_id=-987654321, chat_type="group", from_user_id=320246687, from_user_name="Влад")
        context = MockContext(member_count=2)
        await main.text_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Режим теста", text)
        self.assertIn("Влад", text)

        student = await main.db.find_student_by_group("-987654321")
        self.assertIsNotNone(student)
        self.assertEqual(student["name"], "Влад")
        self.assertEqual(student["chat_id"], "320246687")

    async def test_32_admin_not_student_in_large_group(self):
        """В группе с 3+ участниками админ НЕ является учеником"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("привет", chat_id=-987654321, chat_type="group", from_user_id=320246687)
        context = MockContext(member_count=5)
        await main.text_handler(update, context)

        update.message.reply_text.assert_not_called()
        student = await main.db.find_student_by_group("-987654321")
        self.assertIsNone(student)

    async def test_33_lang_change_to_en(self):
        """Админ меняет язык на английский"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("/lang", chat_id=320246687, from_user_id=320246687)
        context = MockContext(args=["en"])
        await main.lang_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("English", text)
        self.assertIn("changed", text)

        lang = await main.db.get_config("language")
        self.assertEqual(lang, "en")

    async def test_34_lang_change_back_to_ru(self):
        """Админ меняет язык обратно на русский"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.set_config("language", "en")
        update = MockUpdate("/lang", chat_id=320246687, from_user_id=320246687)
        context = MockContext(args=["ru"])
        await main.lang_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("Русский", text)

        lang = await main.db.get_config("language")
        self.assertEqual(lang, "ru")

    async def test_35_lang_affects_messages(self):
        """После смены языка на en сообщения на английском"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        await main.db.set_config("language", "en")
        update = MockUpdate("/start", chat_id=320246687, from_user_id=320246687)
        context = MockContext()
        await main.start_handler(update, context)

        text = update.message.reply_text.call_args[0][0]
        self.assertIn("admin", text.lower())
        self.assertNotIn("репетитором", text)

    async def test_36_lang_only_admin(self):
        """Не-админ не может менять язык"""
        await main.db.set_config("ADMIN_CHAT_ID", "320246687")
        update = MockUpdate("/lang", chat_id=111222333, from_user_id=111222333)
        context = MockContext(args=["en"])
        await main.lang_handler(update, context)
        update.message.reply_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
