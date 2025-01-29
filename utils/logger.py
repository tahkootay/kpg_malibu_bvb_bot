# utils/logger.py

import logging
from typing import Optional
import os
from datetime import datetime

def setup_logger(name: str, log_file: Optional[str] = None, 
                level: int = logging.INFO) -> logging.Logger:
    """
    Настройка логгера
    
    Args:
        name: имя логгера
        log_file: путь к файлу логов (опционально)
        level: уровень логирования
    
    Returns:
        logging.Logger: настроенный логгер
    """
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Настраиваем формат
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Добавляем вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Если указан файл, добавляем запись в файл
    if log_file:
        # Создаем директорию для логов, если её нет
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_command(logger: logging.Logger, command: str, 
                user_id: int, chat_id: int) -> None:
    """
    Логирование использования команды
    
    Args:
        logger: логгер
        command: использованная команда
        user_id: ID пользователя
        chat_id: ID чата
    """
    logger.info(
        f"Command: {command} | User: {user_id} | Chat: {chat_id}"
    )
