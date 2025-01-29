# utils/formatting.py

from typing import List, Tuple
from database.models import Player, Registration

def format_players_list(players: List[Tuple[Player, Registration]], 
                       numbering: bool = True) -> str:
    """
    Форматирование списка игроков для отображения в сообщении
    
    Args:
        players: список кортежей (игрок, регистрация)
        numbering: использовать ли нумерацию (1️⃣, 2️⃣, etc.)
    
    Returns:
        str: отформатированный список игроков
    """
    if not players:
        return ""
        
    number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣']
    formatted_list = []
    
    for idx, (player, _) in enumerate(players):
        if numbering and idx < len(number_emojis):
            formatted_list.append(f"{number_emojis[idx]} {player.full_name}")
        else:
            formatted_list.append(f"• {player.full_name}")
    
    return '\n'.join(formatted_list)

def format_time_range(start_time: str, end_time: str) -> str:
    """
    Форматирование временного диапазона
    
    Args:
        start_time: время начала в формате HH:MM
        end_time: время окончания в формате HH:MM
    
    Returns:
        str: отформатированный временной диапазон
    """
    return f"{start_time} – {end_time}"
