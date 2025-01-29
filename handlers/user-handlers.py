# handlers/user_handlers.py

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from typing import List

from .common import CommandHandler
from database.models import PlayerStatus
from utils.formatting import format_players_list

class UserCommandHandler(CommandHandler):
    """Обработчик пользовательских команд"""

    async def help_command(self, update: Update, 
                          context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать справку по командам"""
        if not update.message:
            return
            
        await update.message.reply_text(self.messages.COMMANDS['help'])

        # Логируем команду
        self.log_command_usage(update, 'help')

    async def join_session(self, update: Update, 
                          context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды присоединения к сессии
        Пример: /join 14:00
        """
        if not update.message or not update.effective_user:
            return

        # Проверяем, включен ли бот
        if not self.db.is_bot_enabled():
            await update.message.reply_text(self.messages.ERRORS['bot_disabled'])
            return

        # Получаем время сессии из аргументов команды
        args = context.args
        if not args:
            await update.message.reply_text(
                "Please specify session time: /join HH:MM"
            )
            return

        session_time = args[0]
        today = datetime.now().date()
        
        # Находим сессию
        session = self.db.get_session_by_time(today, session_time)
        if not session:
            await update.message.reply_text(self.messages.ERRORS['invalid_session'])
            return

        # Проверяем, не зарегистрирован ли уже пользователь
        if self.db.is_player_registered(session.id, update.effective_user.id):
            await update.message.reply_text(
                self.messages.ERRORS['already_registered']
            )
            return

        # Добавляем игрока
        player = self.db.add_player(
            full_name=update.effective_user.full_name,
            telegram_id=update.effective_user.id
        )

        # Проверяем количество игроков в сессии
        current_players = self.db.get_session_players(session.id)
        status = PlayerStatus.MAIN if len(current_players) < session.max_players \
                else PlayerStatus.RESERVE

        # Регистрируем игрока
        self.db.register_player(session.id, player.id, status)

        # Отправляем сообщение об успехе
        message = (self.messages.SUCCESS['player_added'] if status == PlayerStatus.MAIN
                  else self.messages.ERRORS['session_full'])
        await update.message.reply_text(message)

        # Обновляем сообщение со списком
        await self.update_session_message(context, session.id)
        
        # Логируем команду
        self.log_command_usage(update, 'join')

    async def leave_session(self, update: Update, 
                           context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Обработчик команды выхода из сессии
        Пример: /leave 14:00
        """
        if not update.message or not update.effective_user:
            return

        # Проверяем, включен ли бот
        if not self.db.is_bot_enabled():
            await update.message.reply_text(self.messages.ERRORS['bot_disabled'])
            return

        args = context.args
        if not args:
            await update.message.reply_text(
                "Please specify session time: /leave HH:MM"
            )
            return

        session_time = args[0]
        today = datetime.now().date()
        
        # Находим сессию
        session = self.db.get_session_by_time(today, session_time)
        if not session:
            await update.message.reply_text(self.messages.ERRORS['invalid_session'])
            return

        # Проверяем регистрацию
        if not self.db.is_player_registered(session.id, update.effective_user.id):
            await update.message.reply_text(self.messages.ERRORS['not_registered'])
            return

        # Удаляем игрока из сессии
        self.db.unregister_player(session.id, update.effective_user.id)
        
        # Перемещаем игрока из резерва, если есть
        moved_player = self.db.move_reserve_to_main(session.id)
        
        await update.message.reply_text(self.messages.SUCCESS['player_removed'])
        
        # Если кто-то был перемещен из резерва, уведомляем его
        if moved_player and moved_player.telegram_id:
            try:
                await context.bot.send_message(
                    chat_id=moved_player.telegram_id,
                    text=self.messages.SUCCESS['moved_to_main']
                )
            except Exception as e:
                self.logger.error(f"Failed to notify player: {e}")
        
        # Обновляем сообщение со списком
        await self.update_session_message(context, session.id)
        
        # Логируем команду
        self.log_command_usage(update, 'leave')

    async def show_sessions(self, update: Update, 
                           context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Показать все сессии на сегодня
        Команда: /sessions
        """
        if not update.message:
            return

        # Проверяем, включен ли бот
        if not self.db.is_bot_enabled():
            await update.message.reply_text(self.messages.ERRORS['bot_disabled'])
            return

        today = datetime.now().date()
        sessions = self.db.get_sessions_for_date(today)
        
        if not sessions:
            await update.message.reply_text("No sessions available today.")
            return

        for session in sessions:
            players = self.db.get_session_players(session.id)
            reserve = self.db.get_session_reserve(session.id)
            
            message = self.messages.SESSION_TEMPLATE.format(
                date=today.strftime(self.config.FORMAT_SETTINGS['date_format']),
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
            
            await update.message.reply_text(message)
        
        # Логируем команду
        self.log_command_usage(update, 'sessions')
