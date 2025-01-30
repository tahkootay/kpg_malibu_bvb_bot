# handlers/admin_handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from typing import List

try:
    from .common import CommandHandler
except ImportError:
    from handlers.common import CommandHandler

from database.models import PlayerStatus
from utils.validators import parse_time_range
from utils.formatting import (
    format_players_list, 
    format_reserve_list, 
    create_session_buttons
)
class AdminCommandHandler(CommandHandler):  
    # Теперь методы базового класса доступны через self
    """Handler for admin commands"""

 # handlers/admin_handlers.py

    async def create_session(self, update: Update, 
                          context: ContextTypes.DEFAULT_TYPE) -> None:
        """Create new sessions list for tomorrow"""
        if not update.message:
            return

        if not await self.check_admin(update, context):
            return

        tomorrow = datetime.now().date() + timedelta(days=1)

        # Check if sessions list already exists
        if self.db.has_sessions_for_date(tomorrow):
            await update.message.reply_text(
                f"Sessions list for {tomorrow.strftime(self.config.FORMAT_SETTINGS['date_format'])} already exists!"
            )
            return

        sessions_to_create = []
        # If no arguments, create default sessions
        if not context.args:
            sessions_to_create = [
                ("14:00-16:00", 6),  # First session: 14-16, 6 players
                ("16:00-18:00", 8)   # Second session: 16-18, 8 players
            ]
        else:
            # Parse arguments for specified sessions
            time_ranges = context.args[0].split(',')
            for time_range in time_ranges:
                time_range = time_range.strip()
                max_players = 8 if time_range.startswith('16:') else 6
                sessions_to_create.append((time_range, max_players))

        created_sessions = []
        # Create each session
        for time_range, max_players in sessions_to_create:
            times = parse_time_range(time_range)
            if not times:
                await update.message.reply_text(f"Invalid time format: {time_range}")
                continue

            start_time, end_time = times
            
            session = self.db.create_session(
                date=tomorrow,
                time_start=start_time,
                time_end=end_time,
                max_players=max_players
            )
            created_sessions.append(session)

        # Add date header once
        full_message = f"<b>📅 Date:</b> {tomorrow.strftime(self.config.FORMAT_SETTINGS['date_format'])}\n\n"
        
        # Add each session without date
        for i, session in enumerate(created_sessions, 1):
            session_message = f"""<b>⏰ Session {i}:</b> <i>{session.time_start.strftime(self.config.FORMAT_SETTINGS['time_format'])} – {session.time_end.strftime(self.config.FORMAT_SETTINGS['time_format'])}</i>
👥 Max players: {session.max_players}
<b>Players:</b>  
{format_players_list([], session.max_players)}

<b>Reserve:</b>
{format_reserve_list([])}\n\n"""

            full_message += session_message

        # Send message with sessions and buttons
        buttons = create_session_buttons(created_sessions)
        sent_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=full_message,
            reply_markup=buttons,
            parse_mode='HTML'
        )

        # Save message ID for all sessions
        for session in created_sessions:
            self.db.update_session_message(
                session.id, 
                sent_message.message_id,
                update.effective_chat.id
            )

        # Log command
        self.logger.info(f"Updated message info for session {session.id}: message_id={sent_message.message_id}, chat_id={update.effective_chat.id}")
        self.log_command_usage(update, 'create_session')

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
