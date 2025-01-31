# handlers/user_handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from typing import List

try:
    from .common import CommandHandler
except ImportError:
    from handlers.common import CommandHandler

from database.models import PlayerStatus
from utils.formatting import (
    format_players_list, 
    format_reserve_list,  
    create_session_buttons, 
    create_group_menu,
    create_remove_players_menu,
    create_session_players_menu
)

class UserCommandHandler(CommandHandler):
    """Обработчик пользовательских команд"""

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        if not update.message:
            return
            
        if context.args and context.args[0] == "group_menu":
            # Show group management menu
            await update.message.reply_text(
                "Welcome to group management! Please select an action:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "➕ Register group",
                            callback_data="register_group"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Remove players",
                            callback_data="manage_groups"
                        )
                    ]
                ])
            )
            return
            
        # Default start message
        await update.message.reply_text(
            "Welcome! I'm a volleyball session management bot.\n"
            "Use me in the group chat to manage sessions."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать справку по командам"""
        if not update.message:
            return
            
        await update.message.reply_text(self.messages.COMMANDS['help'])
        self.log_command_usage(update, 'help')

    async def show_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать все сессии"""
        if not update.message:
            return

        if not self.db.is_bot_enabled():
            await update.message.reply_text(self.messages.ERRORS['bot_disabled'])
            return

        today = datetime.now().date()
        sessions = self.db.get_sessions_for_date(today)
        
        if not sessions:
            await update.message.reply_text("No sessions available today.")
            return

        full_message = f"<b>📅 Date:</b> {today.strftime(self.config.FORMAT_SETTINGS['date_format'])}\n\n"

        for i, session in enumerate(sessions, 1):
            players = self.db.get_session_players(session.id)
            reserve = self.db.get_session_reserve(session.id)
            
            session_message = f"""<b>⏰ Session {i}:</b> <i>{session.time_start.strftime(self.config.FORMAT_SETTINGS['time_format'])} – {session.time_end.strftime(self.config.FORMAT_SETTINGS['time_format'])}</i>
👥 Max players: {session.max_players}
<b>Players:</b>  
{format_players_list(players, session.max_players)}

<b>Reserve:</b>
{format_reserve_list(reserve)}

"""
            full_message += session_message

        await update.message.reply_text(
            text=full_message,
            parse_mode='HTML',
            reply_markup=create_session_buttons(sessions)
        )
        
        self.log_command_usage(update, 'sessions')

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button presses"""
        query = update.callback_query
        await query.answer()
        
        self.logger.info(f"Button pressed: {query.data}")
        
        # Special buttons handlers
        if query.data == "back_to_group_menu":
            await query.message.edit_text(
                "Welcome to group management! Please select an action:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "➕ Register group",
                            callback_data="register_group"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Remove players",
                            callback_data="manage_groups"
                        )
                    ]
                ])
            )
            return

        if query.data == "back_to_remove_menu":
            # Return to session selection for removal
            sessions = self.db.get_sessions_for_date(datetime.now().date() + timedelta(days=1))
            await query.message.edit_reply_markup(
                reply_markup=create_remove_players_menu(sessions)
            )
            return

        if query.data == "cancel_my_signup":
            sessions = self.db.get_sessions_for_date(datetime.now().date() + timedelta(days=1))
            user_id = update.effective_user.id
            self.logger.info(f"User {user_id} trying to cancel registration")

            for session in sessions:
                self.logger.info(f"Checking registration for session {session.id}")
                if self.db.is_player_registered(session.id, user_id):
                    self.logger.info(f"Found registration in session {session.id}")
                    await self.leave_session_by_id(update, context, session.id)
                    return
                else:
                    self.logger.info(f"No registration found in session {session.id}")

            self.logger.warning(f"User {user_id} not found in any sessions")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.messages.ERRORS['not_registered']
            )
            return

        if query.data == "group_menu":
            # Store chat_id where the group list is
            context.user_data['source_chat_id'] = update.effective_chat.id
            
            # Send message with link to private chat
            bot_username = (await context.bot.get_me()).username
            await query.message.reply_text(
                "To manage group registrations, please open private chat with the bot:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "Open private chat",
                        url=f"https://t.me/{bot_username}?start=group_menu"
                    )
                ]])
            )
            return

        # Handle /start deep linking
        if context.args and context.args[0] == "group_menu":
            await update.message.reply_text(
                "Welcome to group management! Please select an action:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Register group", callback_data="register_group")],
                    [InlineKeyboardButton("Remove players", callback_data="manage_groups")]
                ])
            )
            return

        # Handle group registration menu
        if query.data == "register_group":
                    source_chat_id = context.user_data.get('source_chat_id')
                    if not source_chat_id:
                        await query.message.reply_text("Please start from the group chat first")
                        return

                    sessions = self.db.get_sessions_for_date(datetime.now().date() + timedelta(days=1))
                    keyboard = []
                    # Кнопки для сессий
                    for session in sessions:
                        keyboard.append([
                            InlineKeyboardButton(
                                f"✍️ {session.time_start.strftime('%H:%M')}",
                                callback_data=f"private_group_join_{session.id}"
                            )
                        ])
                    # Добавляем кнопку Back
                    keyboard.append([
                        InlineKeyboardButton(
                            "« Back",
                            callback_data="back_to_group_menu"
                        )
                    ])
                    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
                    return

        # Handle manage groups menu
        if query.data == "manage_groups":
            source_chat_id = context.user_data.get('source_chat_id')
            if not source_chat_id:
                await query.message.reply_text("Please start from the group chat first")
                return

            sessions = self.db.get_sessions_for_date(datetime.now().date() + timedelta(days=1))
            keyboard = []
            for session in sessions:
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {session.time_start.strftime('%H:%M')}",
                        callback_data=f"private_manage_{session.id}"
                    )
                ])
            # Add back button
            keyboard.append([
                InlineKeyboardButton(
                    "« Back",
                    callback_data="back_to_group_menu"
                )
            ])
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Handle private group join
        if query.data.startswith("private_group_join_"):
            session_id = int(query.data.split('_')[-1])
            await query.message.reply_text("Please enter player names separated by commas")
            context.user_data['pending_multiple_join'] = {
                'session_id': session_id,
                'registrar_id': update.effective_user.id,
                'registrar_name': update.effective_user.full_name,
                'source_chat_id': context.user_data.get('source_chat_id')
            }
            return

        # Handle private manage session
        if query.data.startswith("private_manage_"):
            session_id = int(query.data.split('_')[-1])
            session = self.db.get_session(session_id)
            if not session:
                await query.message.reply_text("Session not found")
                return

            players = self.db.get_session_players(session_id)
            reserve = self.db.get_session_reserve(session_id)
            is_admin = await self.check_admin(update, context)
            
            await query.message.edit_reply_markup(
                reply_markup=create_session_players_menu(
                    players=players,
                    reserve=reserve,
                    session_id=session_id,
                    current_user_id=update.effective_user.id,
                    is_admin=is_admin
                )
            )
            return

        # Get session ID from callback_data for other actions
        data_parts = query.data.split('_')
        if len(data_parts) < 2:
            return

        action = data_parts[0]
        session_id = int(data_parts[-1])
        
        if action == 'join':
            if 'self' in data_parts:
                await self.join_session_by_id(update, context, session_id)
            elif 'group' in data_parts:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Please enter player names separated by commas"
                )
                context.user_data['pending_multiple_join'] = {
                    'session_id': session_id,
                    'registrar_id': update.effective_user.id,
                    'registrar_name': update.effective_user.full_name,
                    'source_chat_id': update.effective_chat.id
                }

        # Handle player removal
        if query.data == "back_to_remove_menu":
                    # Return to session selection for removal
                    sessions = self.db.get_sessions_for_date(datetime.now().date() + timedelta(days=1))
                    await query.message.edit_reply_markup(
                        reply_markup=create_remove_players_menu(sessions)
                    )
                    return

        if query.data.startswith("remove_player_"):
            # Remove selected player
            _, _, session_id, player_id = query.data.split('_')
            session_id = int(session_id)
            player_id = int(player_id)
            
            try:
                if self.db.remove_player_by_id(session_id, player_id):
                    self.logger.info("Player removed successfully")
                    
                    # Update the message with new keyboard
                    players = self.db.get_session_players(session_id)
                    reserve = self.db.get_session_reserve(session_id)  # Добавляем получение резерва
                    is_admin = await self.check_admin(update, context)
                    await query.message.edit_reply_markup(
                        reply_markup=create_session_players_menu(
                            players=players,
                            reserve=reserve,  # Добавляем параметр
                            session_id=session_id,
                            current_user_id=update.effective_user.id,
                            is_admin=is_admin
                        )
                    )
                    
                    # Update main session message
                    await self.update_session_message(context, session_id)
                    
                    # Move player from reserve if exists
                    moved_player = self.db.move_reserve_to_main(session_id)
                    if moved_player and moved_player.telegram_id:
                        try:
                            await context.bot.send_message(
                                chat_id=moved_player.telegram_id,
                                text=self.messages.SUCCESS['moved_to_main']
                            )
                        except Exception as e:
                            self.logger.error(f"Failed to notify player: {e}")
                            
            except Exception as e:
                self.logger.error(f"Error removing player: {e}")
                await query.message.reply_text("Error removing player. Please try again.")
            return

    async def join_session_by_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               session_id: int) -> None:
        """Add player to session by ID"""
        if not update.effective_user:
            return

        try:
            self.logger.info(f"Joining session {session_id} for user {update.effective_user.id}")

            if not self.db.is_bot_enabled():
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.messages.ERRORS['bot_disabled']
                )
                return

            session = self.db.get_session(session_id)
            if not session:
                self.logger.error(f"Session {session_id} not found")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.messages.ERRORS['invalid_session']
                )
                return

            # Check if already registered
            if self.db.is_player_registered(session_id, update.effective_user.id):
                self.logger.info(f"User {update.effective_user.id} already registered for session {session_id}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=self.messages.ERRORS['already_registered']
                )
                return

            # Check if already registered in any session of this day
            if not self.config.SESSION_SETTINGS['allow_multiple_sessions']:
                sessions = self.db.get_sessions_for_date(session.date)
                for s in sessions:
                    if self.db.is_player_registered(s.id, update.effective_user.id):
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="You are already registered for another session today"
                        )
                        return
            
            # Add player
            player = self.db.add_player(
                full_name=update.effective_user.full_name,
                telegram_id=update.effective_user.id
            )
            self.logger.info(f"Added player {player.id} to database")

            # Get current players count
            current_players = self.db.get_session_players(session_id)
            self.logger.info(f"Current players in session: {len(current_players)}, max: {session.max_players}")
            
            # Determine status based on current count
            status = PlayerStatus.MAIN if len(current_players) < session.max_players else PlayerStatus.RESERVE

            # Register player
            registration = self.db.register_player(
                session_id=session_id,
                player_id=player.id,
                status=status
            )
            self.logger.info(f"Registered player {player.id} with status {status}")

            # Send success message
            message = self.messages.SUCCESS['player_added'] if status == PlayerStatus.MAIN \
                     else self.messages.ERRORS['session_full']
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message
            )

            # Update session message
            self.logger.info("Updating session message")
            await self.update_session_message(context, session_id)
            
            # Log command
            self.log_command_usage(update, 'join')

        except Exception as e:
            self.logger.error(f"Error in join_session_by_id: {e}", exc_info=True)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="An error occurred while joining the session. Please try again."
            )

    async def leave_session_by_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                               session_id: int) -> None:
        """Leave session by ID"""
        if not update.effective_user:
            return

        self.logger.info(f"Attempting to leave session {session_id} for user {update.effective_user.id}")

        if not self.db.is_bot_enabled():
            await update.callback_query.message.reply_text(
                self.messages.ERRORS['bot_disabled']
            )
            return

        session = self.db.get_session(session_id)
        if not session:
            self.logger.error(f"Session {session_id} not found")
            await update.callback_query.message.reply_text(
                self.messages.ERRORS['invalid_session']
            )
            return

        is_registered = self.db.is_player_registered(session_id, update.effective_user.id)
        self.logger.info(f"Registration check for user {update.effective_user.id} in session {session_id}: {is_registered}")

        if not is_registered:
            await update.callback_query.message.reply_text(
                self.messages.ERRORS['not_registered']
            )
            return

        try:
            self.db.unregister_player(session_id, update.effective_user.id)
            self.logger.info(f"Successfully unregistered user {update.effective_user.id} from session {session_id}")
            
            moved_player = self.db.move_reserve_to_main(session_id)
            
            await update.callback_query.message.reply_text(
                self.messages.SUCCESS['player_removed']
            )
            
            if moved_player and moved_player.telegram_id:
                try:
                    await context.bot.send_message(
                        chat_id=moved_player.telegram_id,
                        text=self.messages.SUCCESS['moved_to_main']
                    )
                    self.logger.info(f"Notified player {moved_player.telegram_id} about moving to main list")
                except Exception as e:
                    self.logger.error(f"Failed to notify player: {e}")
            
            await self.update_session_message(context, session_id)
            self.log_command_usage(update, 'leave')
            
        except Exception as e:
            self.logger.error(f"Error in leave_session: {e}", exc_info=True)
            await update.callback_query.message.reply_text(
                "Error removing from session. Please try again."
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Обработка обычных сообщений"""
            if 'pending_multiple_join' in context.user_data:
                data = context.user_data['pending_multiple_join']
                session_id = data['session_id']
                registrar_id = data['registrar_id']
                registrar_name = data['registrar_name']
                source_chat_id = data.get('source_chat_id')
                del context.user_data['pending_multiple_join']
                
                players_names = [name.strip() for name in update.message.text.split(',')]
                
                session = self.db.get_session(session_id)
                if not session:
                    await update.message.reply_text(self.messages.ERRORS['invalid_session'])
                    return

                added_count = 0
                reserve_count = 0
                current_players = self.db.get_session_players(session_id)
                available_spots = session.max_players - len(current_players)

                for name in players_names:
                    if not name:
                        continue

                    # Create player
                    player = self.db.add_player(
                        full_name=name,
                        telegram_id=None  # Group players don't have telegram_id
                    )

                    # Determine status
                    status = PlayerStatus.MAIN if available_spots > 0 else PlayerStatus.RESERVE

                    # Register player
                    self.db.register_player(
                        session_id=session_id,
                        player_id=player.id,
                        status=status,
                        registered_by_id=registrar_id,
                        registered_by_name=registrar_name
                    )

                    if status == PlayerStatus.MAIN:
                        added_count += 1
                        available_spots -= 1
                    else:
                        reserve_count += 1

                # Send summary message
                message = f"Added {added_count} players to main list"
                if reserve_count > 0:
                    message += f" and {reserve_count} to reserve"
                await update.message.reply_text(message)
                
                # Update session message in source chat if it exists
                self.logger.info(f"Updating message in source chat: {source_chat_id}")
                if source_chat_id:
                    # Сначала обновим chat_id в сессии, если нужно
                    session = self.db.get_session(session_id)
                    if session.chat_id != source_chat_id:
                        self.db.update_session_message(session_id, session.message_id, source_chat_id)
                    await self.update_session_message(context, session_id)
                
                # Log command
                self.log_command_usage(update, 'add_group')