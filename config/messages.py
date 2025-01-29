# config/messages.py

class Messages:
    """
    Класс с шаблонами всех сообщений бота.
    Вынесен в отдельный файл для удобства редактирования и локализации.
    """
    
    # Шаблон списка игроков
    SESSION_TEMPLATE = """
Date: {date}

⏰ Session {session_num}: {start_time} – {end_time}
👥 Max Players: {max_players}
Players:  
{players_list}

Reserve:
{reserve_list}
"""
    
    # Сообщения об ошибках
    ERRORS = {
        'session_full': "Session is full. You've been added to reserve list.",
        'already_registered': "You are already registered for this session.",
        'not_registered': "You are not registered for this session.",
        'invalid_session': "Invalid session time.",
        'admin_only': "This command is for administrators only.",
        'invalid_format': "Invalid command format.",
        'bot_disabled': "Bot is currently disabled.",
    }
    
    # Сообщения об успешных действиях
    SUCCESS = {
        'player_added': "Successfully added to the session.",
        'player_removed': "Successfully removed from the session.",
        'moved_to_main': "You've been moved from reserve to main list!",
        'session_created': "New session created successfully.",
        'group_added': "Players have been added to the session.",
    }
    
    # Административные сообщения
    ADMIN = {
        'bot_enabled': "Bot has been enabled.",
        'bot_disabled': "Bot has been disabled.",
        'settings_updated': "Settings have been updated.",
        'player_removed_admin': "Player {} has been removed from the session.",
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
