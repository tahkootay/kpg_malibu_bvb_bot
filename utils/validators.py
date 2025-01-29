# utils/validators.py

from datetime import time
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Проверка, является ли пользователь администратором чата
    
    Args:
        update: объект обновления Telegram
        context: контекст бота
    
    Returns:
        bool: True если пользователь админ, иначе False
    """
    if not update.effective_chat or not update.effective_user:
        return False
        
    user = await context.bot.get_chat_member(
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id
    )
    return user.status in ['creator', 'administrator']

def parse_time_range(time_range: str) -> Optional[Tuple[time, time]]:
    """
    Парсинг временного диапазона (например, "14:00-16:00")
    
    Args:
        time_range: строка с временным диапазоном
    
    Returns:
        Optional[Tuple[time, time]]: кортеж (время_начала, время_окончания) или None
    """
    try:
        start_str, end_str = time_range.split('-')
        start_parts = start_str.strip().split(':')
        end_parts = end_str.strip().split(':')
        
        start_time = time(int(start_parts[0]), int(start_parts[1]))
        end_time = time(int(end_parts[0]), int(end_parts[1]))
        
        if start_time >= end_time:
            return None
            
        return start_time, end_time
    except (ValueError, IndexError):
        return None

def validate_session_time(time_str: str) -> bool:
    """
    Проверка формата времени сессии
    
    Args:
        time_str: строка со временем в формате HH:MM
    
    Returns:
        bool: True если формат правильный, иначе False
    """
    try:
        hours, minutes = map(int, time_str.split(':'))
        time(hours, minutes)
        return True
    except (ValueError, TypeError):
        return False
