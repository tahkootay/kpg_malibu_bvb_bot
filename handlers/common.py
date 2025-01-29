# handlers/common.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden, TelegramError
from datetime import datetime
import pytz

from database.database import Database
from config.config import BotConfig
from config.messages import Messages
from utils.validators import is_admin, parse_time_range, validate_session_time
from utils.logger import log_command
from utils.formatting import (
    format_players_list,
    format_reserve_list,
    create_session_buttons
)

class CommandHandler:
    """Base class for handling bot commands"""
    
    def __init__(self, database: Database, logger):
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
            log_command(
                self.logger,
                command,
                update.effective_user.id,
                update.effective_chat.id
            )

    async def update_session_message(self, context: ContextTypes.DEFAULT_TYPE, 
                                   session_id: int) -> None:
        """
        Update message with player list
        
        Args:
            context: bot context
            session_id: session ID
        """
        try:
            session = self.db.get_session(session_id)
            if not session or not session.message_id or not session.chat_id:
                self.logger.warning(f"Session {session_id} not found or missing message info")
                return

            players = self.db.get_session_players(session_id)
            reserve = self.db.get_session_reserve(session_id)
            
            # Define session number based on start time
            all_sessions = self.db.get_sessions_for_date(session.date)
            session_num = next(
                (i + 1 for i, s in enumerate(sorted(all_sessions, key=lambda x: x.time_start))
                 if s.id == session_id),
                1
            )
            
            message = self.messages.SESSION_TEMPLATE.format(
                date=session.date.strftime(self.config.FORMAT_SETTINGS['date_format']),
                session_num=session_num,
                start_time=session.time_start.strftime(
                    self.config.FORMAT_SETTINGS['time_format']
                ),
                end_time=session.time_end.strftime(
                    self.config.FORMAT_SETTINGS['time_format']
                ),
                max_players=session.max_players,
                players_list=format_players_list(players, session.max_players),
                reserve_list=format_reserve_list(reserve)
            )

            try:
                buttons = create_session_buttons(all_sessions)
                await context.bot.edit_message_text(
                    chat_id=session.chat_id,
                    message_id=session.message_id,
                    text=message,
                    parse_mode='HTML',
                    reply_markup=buttons,  # Добавляем кнопки при обновлении
                    disable_web_page_preview=True
                )
            except BadRequest as e:
                if "message is not modified" in str(e):
                    pass
                elif "message to edit not found" in str(e):
                    self.logger.error(
                        f"Message {session.message_id} not found in chat {session.chat_id}"
                    )
                else:
                    raise
            except Forbidden:
                self.logger.error(
                    f"Bot was blocked by user in chat {session.chat_id}"
                )
            except TelegramError as e:
                self.logger.error(
                    f"Failed to update message: {e}",
                    exc_info=True
                )
                try:
                    buttons = create_session_buttons(all_sessions)
                    new_message = await context.bot.send_message(
                        chat_id=session.chat_id,
                        text=message,
                        parse_mode='HTML',
                        reply_markup=buttons  # Добавляем кнопки при создании нового сообщения
                    )
                    self.db.update_session_message(
                        session_id,
                        new_message.message_id,
                        session.chat_id
                    )
                except TelegramError:
                    self.logger.error(
                        "Failed to send new message",
                        exc_info=True
                    )
                    
        except Exception as e:
            self.logger.error(
                f"Error in update_session_message: {e}",
                exc_info=True
            )

    async def refresh_sessions(self, update: Update, 
                             context: ContextTypes.DEFAULT_TYPE) -> None:
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
                await query.message.reply_text(
                    "❌ Failed to update lists"
                )