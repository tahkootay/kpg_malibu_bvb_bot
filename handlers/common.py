# handlers/common.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden, TelegramError
from datetime import datetime
import logging

from database.database import Database
from config.config import BotConfig
from config.messages import Messages
from database.models import PlayerStatus
from utils.validators import is_admin
from utils.formatting import format_players_list, format_reserve_list, create_session_buttons

class CommandHandler:
    """Base class for handling bot commands"""
    
    def __init__(self, database: Database, logger):
        """Initialize base handler"""
        self.db = database
        self.config = BotConfig
        self.messages = Messages
        self.logger = logger

    async def check_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check admin rights with error message"""
        if not await is_admin(update, context):
            if update.message:
                await update.message.reply_text(self.messages.ERRORS['admin_only'])
            return False
        return True

    def log_command_usage(self, update: Update, command: str) -> None:
        """Log command usage"""
        if update.effective_user and update.effective_chat:
            self.logger.info(
                f"Command: {command} | "
                f"User: {update.effective_user.id} | "
                f"Chat: {update.effective_chat.id}"
            )

    async def update_session_message(self, context: ContextTypes.DEFAULT_TYPE, session_id: int) -> None:
        """
        Update the sessions list message
        """
        try:
            # Первая проверка - валидность контекста
            if not context or not context.bot:
                self.logger.error("Invalid context or bot instance")
                return

            # Get current session
            session = self.db.get_session(session_id)
            self.logger.info(f"Updating session {session_id}, message_id: {session.message_id}, chat_id: {session.chat_id}")
            
            if not session or not session.message_id or not session.chat_id:
                self.logger.warning(f"Session {session_id} not found or missing message info")
                return

            # Get all sessions for the same date
            all_sessions = self.db.get_sessions_for_date(session.date)
            if not all_sessions:
                self.logger.error("No sessions found for update")
                return

            self.logger.info(f"Found {len(all_sessions)} sessions for date {session.date}")

            # Sort sessions by start time
            all_sessions.sort(key=lambda x: x.time_start)

            # Format the full list message
            full_message = f"<b>📅 Date:</b> {session.date.strftime(self.config.FORMAT_SETTINGS['date_format'])}\n\n"

            for i, curr_session in enumerate(all_sessions, 1):
                # Get players and reserve for current session
                curr_players = self.db.get_session_players(curr_session.id)
                curr_reserve = self.db.get_session_reserve(curr_session.id)
                
                self.logger.info(f"Session {curr_session.id}: {len(curr_players)} players, {len(curr_reserve)} in reserve")

                session_text = f"""<b>⏰ Session {i}:</b> <i>{curr_session.time_start.strftime(self.config.FORMAT_SETTINGS['time_format'])} – {curr_session.time_end.strftime(self.config.FORMAT_SETTINGS['time_format'])}</i>
👥 Max players: {curr_session.max_players}
<b>Players:</b>  
{format_players_list(curr_players, curr_session.max_players)}

<b>Reserve:</b>
{format_reserve_list(curr_reserve)}

"""
                full_message += session_text

            # Вторая проверка - валидность сообщения
            if not full_message or not full_message.strip():
                self.logger.error("Empty message content")
                return

            # Update the message with all sessions
            try:
                buttons = create_session_buttons(all_sessions)
                self.logger.info(f"Updating message {session.message_id} in chat {session.chat_id}")
                
                # Добавляем проверку валидности HTML перед отправкой
                if not all(tag in full_message for tag in ['</b>', '</i>']):
                    self.logger.error("Invalid HTML formatting in message")
                    self.logger.debug(f"Message content: {full_message}")
                    return
                    
                await context.bot.edit_message_text(
                    chat_id=session.chat_id,
                    message_id=session.message_id,
                    text=full_message,
                    parse_mode='HTML',
                    reply_markup=buttons
                )
                self.logger.info("Sessions list updated successfully")
                
            except BadRequest as e:
                if "message is not modified" in str(e):
                    self.logger.info("Message content hasn't changed")
                elif "message to edit not found" in str(e):
                    self.logger.error(f"Message {session.message_id} not found in chat {session.chat_id}")
                else:
                    self.logger.error(f"Bad request error: {str(e)}")
                    raise
            except Forbidden:
                self.logger.error(f"Bot was blocked by user in chat {session.chat_id}")
            except TelegramError as e:
                self.logger.error(f"Failed to update message: {e}", exc_info=True)
                    
        except Exception as e:
            self.logger.error(f"Error in update_session_message: {e}", exc_info=True)

    async def refresh_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Refresh all active sessions"""
        query = update.callback_query
        if query:
            await query.answer()
        
        try:
            today = datetime.now().date()
            sessions = self.db.get_sessions_for_date(today)
            
            for session in sessions:
                await self.update_session_message(context, session.id)
                
            if query:
                await query.message.reply_text(
                    "✅ Lists updated",
                    reply_to_message_id=query.message.message_id
                )
        except Exception as e:
            self.logger.error(f"Error refreshing sessions: {e}", exc_info=True)
            if query:
                await query.message.reply_text("❌ Failed to update lists")