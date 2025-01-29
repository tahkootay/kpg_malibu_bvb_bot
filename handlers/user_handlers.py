# handlers/user_handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from typing import List

from .common import CommandHandler
from database.models import PlayerStatus
from utils.formatting import format_players_list, create_session_buttons, create_join_menu

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

    async def show_sessions(self, update: Update, 
                           context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать все сессии"""
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

        # Создаем одно сообщение со всеми сессиями
        full_message = f"Sessions for {today.strftime(self.config.FORMAT_SETTINGS['date_format'])}:\n\n"

        for session in sessions:
            players = self.db.get_session_players(session.id)
            reserve = self.db.get_session_reserve(session.id)
            
            session_message = self.messages.SESSION_TEMPLATE.format(
                date="",
                session_num='',
                start_time=session.time_start.strftime(
                    self.config.FORMAT_SETTINGS['time_format']
                ),
                end_time=session.time_end.strftime(
                    self.config.FORMAT_SETTINGS['time_format']
                ),
                max_players=session.max_players,
                players_list=format_players_list(players, session.max_players),
                reserve_list=format_players_list(reserve, False)
            )
            full_message += session_message + "\n"

        # Отправляем сообщение с кнопками
        await update.message.reply_text(
            text=full_message,
            reply_markup=create_session_buttons(sessions)
        )
        
        # Логируем команду
        self.log_command_usage(update, 'sessions')

    # В файле handlers/user_handlers.py

    async def button_handler(self, update: Update, 
                           context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button presses"""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_main":
            # Return to main menu
            sessions = self.db.get_sessions_for_date(datetime.now().date())
            await query.message.edit_reply_markup(
                reply_markup=create_session_buttons(sessions)
            )
            return

        if query.data == "cancel_registration":
            # Show sessions for cancellation
            sessions = self.db.get_sessions_for_date(datetime.now().date())
            time_buttons = []
            for session in sessions:
                time_str = session.time_start.strftime('%H:%M')
                time_buttons.append([
                    InlineKeyboardButton(
                        f"Cancel {time_str} registration",
                        callback_data=f"cancel_{session.id}"
                    )
                ])
            time_buttons.append([
                InlineKeyboardButton(
                    "« Back",
                    callback_data="back_to_main"
                )
            ])
            await query.message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup(time_buttons)
            )
            return

        if query.data == "refresh_sessions":
            # Handle refresh button
            await self.refresh_sessions(update, context)
            return
            
        # Get session ID from callback_data for other actions
        data_parts = query.data.split('_')
        action = data_parts[0]
        
        if action in ['join', 'cancel']:
            session_id = int(data_parts[-1])
            
            if query.data.startswith('join_menu_'):
                # Show join type menu
                time_str = self.db.get_session(session_id).time_start.strftime('%H:%M')
                await query.message.edit_reply_markup(
                    reply_markup=create_join_menu(session_id, time_str)
                )
                
            elif query.data.startswith('join_self_'):
                # Register single player
                await self.join_session_by_id(update, context, session_id)
                
            elif query.data.startswith('join_multiple_'):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Please enter player names separated by commas"
                )
                context.user_data['pending_multiple_join'] = session_id
                
            elif action == 'cancel':
                await self.leave_session_by_id(update, context, session_id)

    async def join_session_by_id(self, update: Update, 
                               context: ContextTypes.DEFAULT_TYPE,
                               session_id: int) -> None:
        """Add player to session by ID"""
        if not update.effective_user:
            return

        # Check if bot is enabled
        if not self.db.is_bot_enabled():
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.messages.ERRORS['bot_disabled']
            )
            return

        session = self.db.get_session(session_id)
        if not session:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.messages.ERRORS['invalid_session']
            )
            return

        # Check if already registered
        if self.db.is_player_registered(session_id, update.effective_user.id):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.messages.ERRORS['already_registered']
            )
            return

        # Add player
        player = self.db.add_player(
            full_name=update.effective_user.full_name,
            telegram_id=update.effective_user.id
        )

        # Check current players count
        current_players = self.db.get_session_players(session_id)
        status = PlayerStatus.MAIN if len(current_players) < session.max_players \
                else PlayerStatus.RESERVE

        # Register player
        self.db.register_player(session_id, player.id, status)

        # Send success message
        message = self.messages.SUCCESS['player_added'] if status == PlayerStatus.MAIN \
                 else self.messages.ERRORS['session_full']
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message
        )

        # Update session message
        await self.update_session_message(context, session_id)
        
        # Log command
        self.log_command_usage(update, 'join')

    async def add_multiple_players(self, update: Update, 
                                 context: ContextTypes.DEFAULT_TYPE,
                                 session_id: int,
                                 players_names: List[str]) -> None:
        """Add multiple players to session"""
        session = self.db.get_session(session_id)
        if not session:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.messages.ERRORS['invalid_session']
            )
            return

        # Add each player
        for name in players_names:
            name = name.strip()
            if not name:
                continue

            # Create temporary user
            player = self.db.add_player(
                full_name=name,
                telegram_id=None
            )

            # Check players count
            current_players = self.db.get_session_players(session_id)
            status = PlayerStatus.MAIN if len(current_players) < session.max_players \
                    else PlayerStatus.RESERVE

            # Register player
            self.db.register_player(session_id, player.id, status)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.messages.SUCCESS['group_added']
        )
        
        # Update session message
        await self.update_session_message(context, session_id)

    async def leave_session_by_id(self, update: Update, 
                                context: ContextTypes.DEFAULT_TYPE,
                                session_id: int) -> None:
        """
        Выход из сессии по её ID
        
        Args:
            update: объект обновления Telegram
            context: контекст бота
            session_id: ID сессии
        """
        if not update.effective_user:
            return

        # Проверяем, включен ли бот
        if not self.db.is_bot_enabled():
            await update.callback_query.message.reply_text(
                self.messages.ERRORS['bot_disabled']
            )
            return

        session = self.db.get_session(session_id)
        if not session:
            await update.callback_query.message.reply_text(
                self.messages.ERRORS['invalid_session']
            )
            return

        # Проверяем регистрацию
        if not self.db.is_player_registered(session_id, update.effective_user.id):
            await update.callback_query.message.reply_text(
                self.messages.ERRORS['not_registered']
            )
            return

        # Удаляем игрока из сессии
        self.db.unregister_player(session_id, update.effective_user.id)
        
        # Перемещаем игрока из резерва, если есть
        moved_player = self.db.move_reserve_to_main(session_id)
        
        await update.callback_query.message.reply_text(
            self.messages.SUCCESS['player_removed']
        )
        
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
        await self.update_session_message(context, session_id)
        
        # Логируем команду
        self.log_command_usage(update, 'leave')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка обычных сообщений"""
        if 'pending_multiple_join' in context.user_data:
            session_id = context.user_data['pending_multiple_join']
            del context.user_data['pending_multiple_join']
            
            players_names = [name.strip() for name in update.message.text.split(',')]
            await self.add_multiple_players(update, context, session_id, players_names)
