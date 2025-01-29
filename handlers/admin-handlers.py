# handlers/admin_handlers.py

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from typing import List

from .common import CommandHandler
from database.models import PlayerStatus
from utils.validators import parse_time_range

class AdminCommandHandler(CommandHandler):
    """Обработчик административных команд"""

    async def create_session(self, update: Update, 
                           context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Создание новой сессии
        Пример: /create_session 14:00-16:00 6
        """
        if not update.message:
            return

        if not await self.check_admin(update, context):
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /create_session TIME_RANGE MAX_PLAYERS\n"
                "Example: /create_session 14:00-16:00 6"
            )
            return

        time_range = args[0]
        try:
            max_players = int(args[1])
        except ValueError:
            await update.message.reply_text("Invalid number of players")
            return

        times = parse_time_range(time_range)
        if not times:
            await update.message.reply_text("Invalid time format")
            return

        start_time, end_time = times
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        # Создаем сессию
        session = self.db.create_session(
            date=tomorrow,
            time_start=start_time,
            time_end=end_time,
            max_players=max_players
        )

        # Отправляем сообщение со списком
        message = self.messages.SESSION_TEMPLATE.format(
            date=tomorrow.strftime(self.config.FORMAT_SETTINGS['date_format']),
            session_num='1',  # Можно добавить логику нумерации сессий
            start_time=start_time.strftime(
                self.config.FORMAT_SETTINGS['time_format']
            ),
            end_time=end_time.strftime(
                self.config.FORMAT_SETTINGS['time_format']
            ),
            max_players=max_players,
            players_list="",
            reserve_list=""
        )
        
        sent_message = await update.message.reply_text(message)
        
        # Сохраняем ID сообщения
        self.db.update_session_message(
            session.id, 
            sent_message.message_id,
            update.effective_chat.id
        )

        # Логируем команду
        self.log_command_usage(update, 'create_session')

    async def add_players(self, update: Update, 
                         context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Добавление группы игроков
        Пример: /add_players 14:00 Ivan, Peter, Elena
        """
        if not update.message:
            return

        if not await self.check_admin(update, context):
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /add_players TIME PLAYER1, PLAYER2, ...\n"
                "Example: /add_players 14:00 Ivan, Peter, Elena"
            )
            return

        session_time = args[0]
        players_str = ' '.join(args[1:])
        players_names = [name.strip() for name in players_str.split(',')]

        today = datetime.now().date()
        session = self.db.get_session_by_time(today, session_time)
        
        if not session:
            await update.message.reply_text(self.messages.ERRORS['invalid_session'])
            return

        # Добавляем каждого игрока
        for name in players_names:
            if not name:
                continue

            # Создаем временного пользователя
            player = self.db.add_player(
                full_name=name,
                telegram_id=None  # Для добавленных админом игроков без телеграм
            )

            # Проверяем количество игроков
            current_players = self.db.get_session_players(session.id)
            status = PlayerStatus.MAIN if len(current_players) < session.max_players \
                    else PlayerStatus.RESERVE

            # Регистрируем игрока
            self.db.register_player(session.id, player.id, status)

        await update.message.reply_text(self.messages.SUCCESS['group_added'])
        await self.update_session_message(context, session.id)

        # Логируем команду
        self.log_command_usage(update, 'add_players')

    async def remove_player(self, update: Update, 
                          context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Удаление игрока из сессии
        Пример: /remove_player 14:00 Ivan
        """
        if not update.message:
            return

        if not await self.check_admin(update, context):
            return

        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Usage: /remove_player TIME PLAYER_NAME\n"
                "Example: /remove_player 14:00 Ivan"
            )
            return

        session_time = args[0]
        player_name = ' '.join(args[1:])

        today = datetime.now().date()
        session = self.db.get_session_by_time(today, session_time)
        
        if not session:
            await update.message.reply_text(self.messages.ERRORS['invalid_session'])
            return

        # Удаляем игрока
        if self.db.remove_player_by_name(session.id, player_name):
            # Перемещаем игрока из резерва, если есть
            moved_player = self.db.move_reserve_to_main(session.id)
            await update.message.reply_text(
                self.messages.ADMIN['player_removed_admin'].format(player_name)
            )
            
            if moved_player and moved_player.telegram_id:
                # Уведомляем игрока, если он был перемещен из резерва
                try:
                    await context.bot.send_message(
                        chat_id=moved_player.telegram_id,
                        text=self.messages.SUCCESS['moved_to_main']
                    )
                except Exception as e:
                    self.logger.error(f"Failed to notify player: {e}")
            
            await self.update_session_message(context, session.id)
        else:
            await update.message.reply_text("Player not found in this session")

        # Логируем команду
        self.log_command_usage(update, 'remove_player')

    async def toggle_bot(self, update: Update, 
                        context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Включение/выключение бота
        Пример: /toggle_bot on
        """
        if not update.message:
            return

        if not await self.check_admin(update, context):
            return

        args = context.args
        if not args or args[0] not in ['on', 'off']:
            await update.message.reply_text(
                "Usage: /toggle_bot [on|off]"
            )
            return

        enabled = args[0] == 'on'
        self.db.set_bot_enabled(enabled)
        
        message = self.messages.ADMIN['bot_enabled'] if enabled \
                 else self.messages.ADMIN['bot_disabled']
        await update.message.reply_text(message)

        # Логируем команду
        self.log_command_usage(update, 'toggle_bot')

    async def show_stats(self, update: Update, 
                        context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Показать статистику посещений
        Пример: /stats или /stats Ivan
        """
        if not update.message:
            return

        if not await self.check_admin(update, context):
            return

        args = context.args
        player_name = ' '.join(args) if args else None

        if player_name:
            # Статистика конкретного игрока
            stats = self.db.get_player_stats(player_name)
            if not stats:
                await update.message.reply_text("Player not found")
                return

            message = f"Stats for {player_name}:\n"
            message += f"Total games: {stats['total_games']}\n"
            if stats['last_game']:
                message += f"Last game: {stats['last_game'].strftime('%Y-%m-%d')}\n"
            
        else:
            # Общая статистика
            stats = self.db.get_general_stats()
            message = "General statistics:\n"
            message += f"Total sessions: {stats['total_sessions']}\n"
            message += f"Total players: {stats['total_players']}\n"
            message += f"Active players: {stats['active_players']}\n"

        await update.message.reply_text(message)

        # Логируем команду
        self.log_command_usage(update, 'stats')
