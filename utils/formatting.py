# utils/formatting.py

from typing import List, Tuple, Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Player, Registration, Session

# utils/formatting.py

from typing import List, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Player, Registration, Session

def format_players_list(players: List[Tuple[Player, Registration]], max_players: int) -> str:
    """Format the main players list with numbers"""
    number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    formatted_list = []
    
    # Convert list to dictionary for easier access
    players_dict = {idx: player for idx, (player, reg) in enumerate(players)}
    
    for i in range(max_players):
        if i < len(number_emojis):
            if player := players_dict.get(i):
                # Экранируем специальные символы в имени
                safe_name = player.full_name.replace('<', '&lt;').replace('>', '&gt;')
                if player.telegram_id:
                    name = f'<a href="tg://user?id={player.telegram_id}">{safe_name}</a>'
                else:
                    name = f"<b>{safe_name}</b>"
                formatted_list.append(f"{number_emojis[i]} {name}")
            else:
                # Добавляем пробел после номера для лучшей читаемости
                formatted_list.append(f"{number_emojis[i]} ▫️")
    
    return '\n'.join(formatted_list)

def format_reserve_list(players: List[Tuple[Player, Registration]]) -> str:
    """Format reserve list as comma-separated names"""
    if not players:
        return ""
        
    names = []
    for player, _ in players:
        if player.telegram_id:
            names.append(f'<a href="tg://user?id={player.telegram_id}">{player.full_name}</a>')
        else:
            names.append(player.full_name)
    
    return ', '.join(names)

def create_session_buttons(sessions: List[Session]) -> InlineKeyboardMarkup:
    """Create keyboard with buttons for all sessions"""
    keyboard = []
    
    # Join buttons for each session
    for session in sessions:
        time_str = session.time_start.strftime('%H:%M')
        keyboard.extend([
            [
                InlineKeyboardButton(
                    f"✍️ Join {time_str} session",
                    callback_data=f"join_menu_{session.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    f"❌ Leave {time_str} session",
                    callback_data=f"cancel_{session.id}"
                )
            ]
        ])
    
    return InlineKeyboardMarkup(keyboard)  # Убрали кнопку обновления

def create_join_menu(session_id: int, time_str: str) -> InlineKeyboardMarkup:
    """Create menu for joining types"""
    keyboard = [
        [
            InlineKeyboardButton(
                "✍️ Join myself", 
                callback_data=f"join_self_{session_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "👥 Register group", 
                callback_data=f"join_multiple_{session_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "« Back to sessions",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)