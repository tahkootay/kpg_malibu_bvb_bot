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

# В models.py добавляем методы в класс Session:

@dataclass
class Session:
    """Model for game session"""
    id: int
    date: datetime
    time_start: time
    time_end: time
    max_players: int
    message_id: Optional[int] = None
    chat_id: Optional[int] = None

    def __eq__(self, other):
        if not isinstance(other, Session):
            return NotImplemented
        return (self.date == other.date and 
                self.time_start == other.time_start)

    def __lt__(self, other):
        if not isinstance(other, Session):
            return NotImplemented
        if self.date != other.date:
            return self.date < other.date
        return self.time_start < other.time_start
    
@dataclass
class Registration:
    """Модель данных регистрации на игру"""
    id: int
    session_id: int
    player_id: int
    status: PlayerStatus
    registration_time: datetime
