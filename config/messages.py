# config/messages.py

class Messages:
    # Updated template with HTML support
    SESSION_TEMPLATE = """
<b>📅 Date:</b> {date}

<b>⏰ Session {session_num}:</b> <i>{start_time} – {end_time}</i>
👥 Max players: {max_players}
<b>Players:</b>  
{players_list}

<b>Reserve:</b> {reserve_list}
"""
    
    # Сообщения об ошибках
    ERRORS = {
        'session_full': "Session is full. You've been added to the reserve list.",
        'already_registered': "You are already registered for this session.",
        'not_registered': "You are not registered for this session.",
        'invalid_session': "Invalid session time.",
        'admin_only': "This command is for administrators only.",
        'invalid_format': "Invalid command format.",
        'bot_disabled': "Bot is currently disabled.",
        'update_failed': "Failed to update message. Please try again later.",
        'message_not_found': "Message not found. It might have been deleted.",
    }

    
    # Сообщения об успешных действиях
    SUCCESS = {
        'player_added': "Successfully added to the session.",
        'player_removed': "Successfully removed from the session.",
        'moved_to_main': "You've been moved from reserve to main list!",
        'session_created': "New session created successfully.",
        'group_added': "Players have been added to the session.",
        'list_updated': "✅ Lists updated",

    }
    
    # Административные сообщения
    ADMIN = {
        'bot_enabled': "Bot has been enabled.",
        'bot_disabled': "Bot has been disabled.",
        'settings_updated': "Settings have been updated.",
        'player_removed_admin': "Player {} has been removed from the session.",
    }
    
   # Добавляем сообщения для статусов сессии
    SESSION_STATUS = {
        'empty': "👥 No players",
        'few_players': "⚠️ Need more players",
        'ready': "✅ Session ready",
        'full': "🔒 Session full",
    }
    
    # Команды бота
    COMMANDS = {
        'help': """Available commands:
/join time - Join session (e.g., /join 14:00)
/leave time - Leave session
/sessions - Show today's sessions

Admin commands:
/create_session time_range max_players - Create new session
/add_players time player1, player2 - Add multiple players
/remove_player time player_name - Remove player
/toggle_bot [on|off] - Enable/disable bot
/stats [player_name] - Show statistics
""",
    }
