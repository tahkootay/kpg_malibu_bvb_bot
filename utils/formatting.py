# utils/formatting.py

from typing import List, Tuple
from database.models import Player, Registration
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def format_players_list(players: List[Tuple[Player, Registration]], max_players: int) -> str:
    """
    Форматирование списка игроков с пронумерованными пустыми местами
    """
    number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣']
    players_dict = {idx: player.full_name for idx, (player, _) in enumerate(players)}
    formatted_list = []
    
    for i in range(max_players):
        if i < len(number_emojis):
            name = players_dict.get(i, '')
            formatted_list.append(f"{number_emojis[i]} {name}")
    
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

def create_session_buttons(session_times: List[str]) -> InlineKeyboardMarkup:
    """Создание кнопок для записи на сессии"""
    keyboard = []
    
    # Кнопки записи для каждой сессии
    for time in session_times:
        keyboard.append([
            InlineKeyboardButton(
                f"Записаться на {time}",
                callback_data=f"join_menu_{time}"
            )
        ])
    
    # Кнопка отмены записи
    keyboard.append([
        InlineKeyboardButton(
            "Отменить запись",
            callback_data="cancel_registration"
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_join_menu(time: str) -> InlineKeyboardMarkup:
    """Меню выбора типа записи"""
    keyboard = [
        [
            InlineKeyboardButton("Себя", callback_data=f"join_self_{time}"),
            InlineKeyboardButton("Несколько человек", callback_data=f"join_multiple_{time}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
