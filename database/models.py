# database/models.py

from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import Optional

class PlayerStatus(Enum):
    """Статус игрока в сессии"""
    MAIN = "main"       # В основном составе
    RESERVE = "reserve" # В резерве

@dataclass
class Player:
    """Модель данных игрока"""
    id: int
    full_name: str
    telegram_id: Optional[int]
    created_at: datetime

@dataclass
class Session:
    """Модель данных игровой сессии"""
    id: int
    date: datetime
    time_start: time
    time_end: time
    max_players: int
    message_id: Optional[int] = None
    chat_id: Optional[int] = None
    
@dataclass
class Registration:
    """Модель данных регистрации на игру"""
    id: int
    session_id: int
    player_id: int
    status: PlayerStatus
    registration_time: datetime
