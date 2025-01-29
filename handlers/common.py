# handlers/common.py

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, time
from typing import Optional, Tuple

from database.database import Database
from config.config import BotConfig
from config.messages import Messages
from utils.validators import is_admin, parse_time_range, validate_session_time
from utils.logger import log_command
from utils.formatting import format_players_list

class CommandHandler:
    """Базовый класс для обработки команд бота"""
    
    def __init__(self, database: Database, logger):
        """
        Инициализация обработчика команд
        
        Args:
            database: объект базы данных
            logger: настроенный логгер
        """
        self.db = database
        self.config = BotConfig
        self.messages = Messages
        self.logger = logger

    async def check_admin(self, update: Update, 
                         context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Проверка прав администратора с отправкой сообщения об ошибке
        
        Args:
            update: объект обновления от Telegram
            context: контекст бота
        
        Returns:
            bool: True если пользователь админ, иначе False
        """
        if not await is_admin(update, context):
            if update.message:
                await update.message.reply_text(self.messages.ERRORS['admin_only'])
            return False
        return True

    async def update_session_message(self, context: ContextTypes.DEFAULT_TYPE, 
                                   session_id: int) -> None:
        """
        Обновление сообщения со списком игроков
        
        Args:
            context: контекст бота
            session_id: ID сессии
        """
        try:
            session = self.db.get_session(session_id)
            if not session or not session.message_id or not session.chat_id:
                return

            players = self.db.get_session_players(session_id)
            reserve = self.db.get_session_reserve(session_id)
            
            message = self.messages.SESSION_TEMPLATE.format(
                date=session.date.strftime(self.config.FORMAT_SETTINGS['date_format']),
                session_num='1',  # Можно добавить логику нумерации сессий
                start_time=session.time_start.strftime(
                    self.config.FORMAT_SETTINGS['time_format']
                ),
                end_time=session.time_end.strftime(
                    self.config.FORMAT_SETTINGS['time_format']
                ),
                max_players=session.max_players,
                players_list=format_players_list(players),
                reserve_list=format_players_list(reserve, numbering=False)
            )

            await context.bot.edit_message_text(
                chat_id=session.chat_id,
                message_id=session.message_id,
                text=message
            )
        except Exception as e:
            self.logger.error(f"Error updating message: {e}", exc_info=True)

    def log_command_usage(self, update: Update, command: str) -> None:
        """
        Логирование использования команды
        
        Args:
            update: объект обновления от Telegram
            command: использованная команда
        """
        if update.effective_user and update.effective_chat:
            log_command(
                self.logger,
                command,
                update.effective_user.id,
                update.effective_chat.id
            )
