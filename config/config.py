# config/config.py

from datetime import time
import os
from typing import Dict, List, Tuple

class BotConfig:
    """
    Основной класс конфигурации бота.
    Содержит все настройки, которые могут потребоваться для работы бота.
    """
    
    # Токен бота (должен быть установлен через переменную окружения)
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Настройки базы данных
    DATABASE = {
        'name': 'kpg_malibu_bvb.db',
        'path': 'database/'
    }
    
    # Стандартные временные слоты для игр
    DEFAULT_SESSIONS: List[Tuple[time, time]] = [
        (time(14, 0), time(16, 0)),  # 14:00 - 16:00
        (time(16, 0), time(18, 0))   # 16:00 - 18:00
    ]
    
    # Дополнительные слоты, которые могут быть активированы
    ADDITIONAL_SESSIONS: List[Tuple[time, time]] = [
        (time(12, 0), time(14, 0))   # 12:00 - 14:00
    ]
    
    # Время автоматической публикации списка (19:00)
    AUTOPOST_TIME: time = time(19, 0)
    
    # Настройки игровых сессий
    SESSION_SETTINGS = {
        'default_max_players': 6,  # Стандартное максимальное количество игроков
        'min_players': 4,         # Минимальное количество игроков для игры
    }
    
    # Форматирование сообщений
    FORMAT_SETTINGS = {
        'date_format': '%d %B, %A',  # Например: "29 January, Wednesday"
        'time_format': '%H:%M',      # Например: "14:00"
    }
