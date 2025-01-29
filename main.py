# main.py

import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    JobQueue,
)

from config.config import BotConfig
from database.database import Database
from handlers.user_handlers import UserCommandHandler
from handlers.admin_handlers import AdminCommandHandler
from utils.logger import setup_logger

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logger = setup_logger(
    'kpg_malibu_bvb',
    'logs/bot.log',
    logging.INFO
)

class VolleyballBot:
    """Основной класс бота"""
    
    def __init__(self):
        """Инициализация бота"""
        self.db = Database(f"{BotConfig.DATABASE['path']}{BotConfig.DATABASE['name']}")
        self.user_handler = UserCommandHandler(self.db, logger)
        self.admin_handler = AdminCommandHandler(self.db, logger)

    async def create_daily_sessions(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Создание ежедневных сессий"""
        try:
            chat_id = context.job.data['chat_id']
            logger.info(f"Creating daily sessions for chat {chat_id}")
            
            tomorrow = datetime.now().date() + timedelta(days=1)
            
            # Создаем стандартные сессии
            for start_time, end_time in BotConfig.DEFAULT_SESSIONS:
                session = self.db.create_session(
                    date=tomorrow,
                    time_start=start_time,
                    time_end=end_time,
                    max_players=BotConfig.SESSION_SETTINGS['default_max_players']
                )
                
                # Создаем сообщение для сессии
                message = self.user_handler.messages.SESSION_TEMPLATE.format(
                    date=tomorrow.strftime(BotConfig.FORMAT_SETTINGS['date_format']),
                    session_num='1',
                    start_time=start_time.strftime(
                        BotConfig.FORMAT_SETTINGS['time_format']
                    ),
                    end_time=end_time.strftime(
                        BotConfig.FORMAT_SETTINGS['time_format']
                    ),
                    max_players=BotConfig.SESSION_SETTINGS['default_max_players'],
                    players_list="",
                    reserve_list=""
                )
                
                # Отправляем сообщение в чат
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
                
                # Сохраняем ID сообщения
                self.db.update_session_message(
                    session.id,
                    sent_message.message_id,
                    chat_id
                )
                
            logger.info("Daily sessions created successfully")
        except Exception as e:
            logger.error(f"Error creating daily sessions: {e}", exc_info=True)

    def run(self):
        """Запуск бота"""
        try:
            # Создаем приложение
            application = Application.builder().token(BotConfig.TOKEN).build()

            # Регистрируем обработчики пользовательских команд
            application.add_handler(CommandHandler("help", self.user_handler.help_command))
            application.add_handler(CommandHandler("join", self.user_handler.join_session))
            application.add_handler(CommandHandler("leave", self.user_handler.leave_session))
            application.add_handler(CommandHandler("sessions", self.user_handler.show_sessions))

            # Регистрируем обработчики административных команд
            application.add_handler(CommandHandler("create_session", self.admin_handler.create_session))
            application.add_handler(CommandHandler("add_players", self.admin_handler.add_players))
            application.add_handler(CommandHandler("remove_player", self.admin_handler.remove_player))
            application.add_handler(CommandHandler("toggle_bot", self.admin_handler.toggle_bot))
            application.add_handler(CommandHandler("stats", self.admin_handler.show_stats))

            # Настраиваем ежедневную публикацию списков
            job_queue = application.job_queue
            
            # Задача будет выполняться каждый день в указанное время
            job_queue.run_daily(
                self.create_daily_sessions,
                time=BotConfig.AUTOPOST_TIME,
                days=(0, 1, 2, 3, 4, 5, 6),  # Все дни недели
                data={'chat_id': os.getenv('TELEGRAM_CHAT_ID')}  # ID чата из конфигурации
            )

            logger.info("Bot started")
            
            # Запускаем бота
            application.run_polling()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}", exc_info=True)
            raise

if __name__ == '__main__':
    bot = VolleyballBot()
    bot.run()
