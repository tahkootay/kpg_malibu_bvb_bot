# utils/formatting.py

from typing import List, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Player, Registration, Session

def create_remove_players_menu(sessions: List[Session]) -> InlineKeyboardMarkup:
    """Create menu for selecting session to remove players from"""
    keyboard = []
    
    # Buttons for each session
    session_row = []
    for session in sessions:
        time_str = session.time_start.strftime('%H:%M')
        session_row.append(
            InlineKeyboardButton(
                f"🕒 {time_str}",
                callback_data=f"select_session_{session.id}"
            )
        )
    keyboard.append(session_row)
    
    # Back button
    keyboard.append([
        InlineKeyboardButton(
            "« Back",
            callback_data="back_to_group_menu"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_session_players_menu(players: List[Tuple[Player, Registration]], 
                              reserve: List[Tuple[Player, Registration]],  # добавляем параметр
                              session_id: int,
                              current_user_id: int,
                              is_admin: bool) -> InlineKeyboardMarkup:
    """Create menu with player list for removal"""
    keyboard = []
    
    # Main list header
    if players:
        keyboard.append([InlineKeyboardButton("📋 Main list", callback_data="header_main")])
        
        # Group players by two in a row
        current_row = []
        for player, reg in players:
            # Allow removal if admin or if current user registered this player
            if is_admin or (reg.registered_by_id and reg.registered_by_id == current_user_id):
                current_row.append(
                    InlineKeyboardButton(
                        f"{player.full_name} ❌",
                        callback_data=f"remove_player_{session_id}_{player.id}"
                    )
                )
                
                if len(current_row) == 2:
                    keyboard.append(current_row)
                    current_row = []
        
        if current_row:  # Add remaining buttons
            keyboard.append(current_row)

    # Reserve list header and players
    if reserve:
        keyboard.append([InlineKeyboardButton("📋 Reserve list", callback_data="header_reserve")])
        
        current_row = []
        for player, reg in reserve:
            if is_admin or (reg.registered_by_id and reg.registered_by_id == current_user_id):
                current_row.append(
                    InlineKeyboardButton(
                        f"{player.full_name} ❌",
                        callback_data=f"remove_player_{session_id}_{player.id}"
                    )
                )
                
                if len(current_row) == 2:
                    keyboard.append(current_row)
                    current_row = []
        
        if current_row:
            keyboard.append(current_row)
    
    # Back button
    keyboard.append([
        InlineKeyboardButton(
            "« Back",
            callback_data="manage_groups"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_session_buttons(sessions: List[Session]) -> InlineKeyboardMarkup:
    """Create keyboard with buttons for all sessions"""
    keyboard = []
    
    # Join buttons for sessions in one row
    join_row = []
    for session in sessions:
        time_str = session.time_start.strftime('%H:%M')
        join_row.append(
            InlineKeyboardButton(
                f"✍️ {time_str}",
                callback_data=f"join_self_{session.id}"
            )
        )
    keyboard.append(join_row)
    
    # Cancel and Groups in one row
    keyboard.append([
        InlineKeyboardButton(
            "❌ Cancel my sign-up",
            callback_data="cancel_my_signup"
        ),
        InlineKeyboardButton(
            "👥 For groups",
            callback_data="group_menu"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_group_menu(sessions: List[Session]) -> InlineKeyboardMarkup:
    """Create keyboard for group registration"""
    keyboard = []
    
    # Group registration buttons in one row
    join_row = []
    for session in sessions:
        time_str = session.time_start.strftime('%H:%M')
        join_row.append(
            InlineKeyboardButton(
                f"✍️ {time_str}",
                callback_data=f"join_group_{session.id}"
            )
        )
    keyboard.append(join_row)
    
    # Cancel and Back in one row
    keyboard.append([
        InlineKeyboardButton(
            "❌ Cancel sign-up",
            callback_data="cancel_group_signup"
        ),
        InlineKeyboardButton(
            "« Back",
            callback_data="back_to_main"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)

def format_player_name(player: Player, registration: Registration) -> str:
    """Helper function to format player name with proper HTML formatting"""
    safe_name = player.full_name.replace('<', '&lt;').replace('>', '&gt;')
    
    # Basic player name
    if player.telegram_id:
        name = f'<a href="tg://user?id={player.telegram_id}">{safe_name}</a>'
    else:
        name = f"<b>{safe_name}</b>"
        
    # Add registrar info if exists
    if registration.registered_by_id:
        registrar = f'<a href="tg://user?id={registration.registered_by_id}">{registration.registered_by_name}</a>'
        name += f" (by {registrar})"
    
    return name

def format_players_list(players: List[Tuple[Player, Registration]], max_players: int) -> str:
    """Format the main players list with numbers"""
    number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    formatted_list = []
    
    # Convert list to dictionary for easier access
    players_dict = {idx: (player, reg) for idx, (player, reg) in enumerate(players)}
    
    for i in range(max_players):
        if i < len(number_emojis):
            if player_data := players_dict.get(i):
                player, reg = player_data
                name = format_player_name(player, reg)
                formatted_list.append(f"{number_emojis[i]} {name}")
            else:
                # Для пустых мест просто номер
                formatted_list.append(f"{number_emojis[i]}")
    
    return '\n'.join(formatted_list)

def format_reserve_list(players: List[Tuple[Player, Registration]]) -> str:
    """Format reserve list as comma-separated names"""
    if not players:
        return ""
        
    names = []
    for player, reg in players:
        name = format_player_name(player, reg)
        names.append(name)
    
    return ', '.join(names)