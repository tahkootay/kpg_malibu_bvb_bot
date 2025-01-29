# database/database.py

import sqlite3
from datetime import datetime, date, time
from typing import List, Optional, Tuple
from .models import Player, Session, Registration, PlayerStatus

class Database:
    """Класс для работы с базой данных."""
    
    def __init__(self, db_path: str):
        """
        Инициализация соединения с базой данных
        
        Args:
            db_path: путь к файлу базы данных
        """
        self.db_path = db_path
        self.create_tables()
    
    def create_tables(self) -> None:
        """Создание необходимых таблиц в базе данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица игроков
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    telegram_id INTEGER UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица сессий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    time_start TIME NOT NULL,
                    time_end TIME NOT NULL,
                    max_players INTEGER NOT NULL,
                    message_id INTEGER,
                    chat_id INTEGER
                )
            ''')
            
            # Таблица регистраций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id),
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            ''')
            
            # Таблица настроек
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            conn.commit()

    def add_player(self, full_name: str, telegram_id: Optional[int] = None) -> Player:
        """
        Добавление нового игрока или получение существующего
        
        Args:
            full_name: полное имя игрока
            telegram_id: ID пользователя в Telegram (опционально)
            
        Returns:
            Player: объект игрока
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if telegram_id:
                # Проверяем, существует ли игрок
                cursor.execute(
                    'SELECT * FROM players WHERE telegram_id = ?',
                    (telegram_id,)
                )
                player = cursor.fetchone()
                
                if player:
                    return Player(
                        id=player[0],
                        full_name=player[1],
                        telegram_id=player[2],
                        created_at=datetime.fromisoformat(player[3])
                    )
            
            # Создаем нового игрока
            cursor.execute(
                'INSERT INTO players (full_name, telegram_id) VALUES (?, ?)',
                (full_name, telegram_id)
            )
            
            return Player(
                id=cursor.lastrowid,
                full_name=full_name,
                telegram_id=telegram_id,
                created_at=datetime.now()
            )

    def get_session(self, session_id: int) -> Optional[Session]:
        """Получение сессии по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
            
            session = cursor.fetchone()
            if not session:
                return None
                
            return Session(
                id=session[0],
                date=datetime.fromisoformat(session[1]),
                time_start=datetime.strptime(session[2], '%H:%M').time(),
                time_end=datetime.strptime(session[3], '%H:%M').time(),
                max_players=session[4],
                message_id=session[5],
                chat_id=session[6]
            )

    def create_session(self, date: date, time_start: time,
                      time_end: time, max_players: int) -> Session:
        """Создание новой игровой сессии"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (date, time_start, time_end, max_players)
                VALUES (?, ?, ?, ?)
            ''', (date.isoformat(), time_start.strftime('%H:%M'), 
                 time_end.strftime('%H:%M'), max_players))
            
            return Session(
                id=cursor.lastrowid,
                date=date,
                time_start=time_start,
                time_end=time_end,
                max_players=max_players
            )

    def get_session_by_time(self, date: date, time_str: str) -> Optional[Session]:
        """Получение сессии по дате и времени начала"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sessions 
                WHERE date = ? AND time_start = ?
            ''', (date.isoformat(), time_str))
            
            session = cursor.fetchone()
            if not session:
                return None
                
            return Session(
                id=session[0],
                date=datetime.fromisoformat(session[1]),
                time_start=datetime.strptime(session[2], '%H:%M').time(),
                time_end=datetime.strptime(session[3], '%H:%M').time(),
                max_players=session[4],
                message_id=session[5],
                chat_id=session[6]
            )

    def update_session_message(self, session_id: int, message_id: int, 
                             chat_id: int) -> None:
        """Обновление ID сообщения для сессии"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sessions 
                SET message_id = ?, chat_id = ?
                WHERE id = ?
            ''', (message_id, chat_id, session_id))
            conn.commit()

    def register_player(self, session_id: int, player_id: int, 
                       status: PlayerStatus) -> Registration:
        """Регистрация игрока на сессию"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute('''
                INSERT INTO registrations 
                (session_id, player_id, status, registration_time)
                VALUES (?, ?, ?, ?)
            ''', (session_id, player_id, status.value, now.isoformat()))
            
            return Registration(
                id=cursor.lastrowid,
                session_id=session_id,
                player_id=player_id,
                status=status,
                registration_time=now
            )

    def get_session_players(self, session_id: int) -> List[Tuple[Player, Registration]]:
        """Получение списка игроков для сессии"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, r.* 
                FROM players p
                JOIN registrations r ON p.id = r.player_id
                WHERE r.session_id = ? AND r.status = ?
                ORDER BY r.registration_time
            ''', (session_id, PlayerStatus.MAIN.value))
            
            results = []
            for row in cursor.fetchall():
                player = Player(
                    id=row[0],
                    full_name=row[1],
                    telegram_id=row[2],
                    created_at=datetime.fromisoformat(row[3])
                )
                registration = Registration(
                    id=row[4],
                    session_id=row[5],
                    player_id=row[6],
                    status=PlayerStatus(row[7]),
                    registration_time=datetime.fromisoformat(row[8])
                )
                results.append((player, registration))
            
            return results
            def get_session_reserve(self, session_id: int) -> List[Tuple[Player, Registration]]:
        """Получение списка резерва для сессии"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, r.* 
                FROM players p
                JOIN registrations r ON p.id = r.player_id
                WHERE r.session_id = ? AND r.status = ?
                ORDER BY r.registration_time
            ''', (session_id, PlayerStatus.RESERVE.value))
            
            results = []
            for row in cursor.fetchall():
                player = Player(
                    id=row[0],
                    full_name=row[1],
                    telegram_id=row[2],
                    created_at=datetime.fromisoformat(row[3])
                )
                registration = Registration(
                    id=row[4],
                    session_id=row[5],
                    player_id=row[6],
                    status=PlayerStatus(row[7]),
                    registration_time=datetime.fromisoformat(row[8])
                )
                results.append((player, registration))
            
            return results

    def is_player_registered(self, session_id: int, telegram_id: int) -> bool:
        """Проверка, зарегистрирован ли игрок на сессию"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.id
                FROM registrations r
                JOIN players p ON r.player_id = p.id
                WHERE r.session_id = ? AND p.telegram_id = ?
            ''', (session_id, telegram_id))
            
            return cursor.fetchone() is not None

    def unregister_player(self, session_id: int, telegram_id: int) -> None:
        """Отмена регистрации игрока"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM registrations
                WHERE session_id = ? AND player_id IN (
                    SELECT id FROM players WHERE telegram_id = ?
                )
            ''', (session_id, telegram_id))
            conn.commit()

    def move_reserve_to_main(self, session_id: int) -> Optional[Player]:
        """Перемещение первого игрока из резерва в основной состав"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Получаем первого игрока из резерва
            cursor.execute('''
                SELECT p.*, r.id as reg_id
                FROM players p
                JOIN registrations r ON p.id = r.player_id
                WHERE r.session_id = ? AND r.status = ?
                ORDER BY r.registration_time
                LIMIT 1
            ''', (session_id, PlayerStatus.RESERVE.value))
            
            result = cursor.fetchone()
            if not result:
                return None
                
            player = Player(
                id=result[0],
                full_name=result[1],
                telegram_id=result[2],
                created_at=datetime.fromisoformat(result[3])
            )
            
            # Обновляем статус
            cursor.execute('''
                UPDATE registrations
                SET status = ?
                WHERE id = ?
            ''', (PlayerStatus.MAIN.value, result[4]))
            
            conn.commit()
            return player

    def remove_player_by_name(self, session_id: int, player_name: str) -> bool:
        """Удаление игрока по имени"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM registrations
                WHERE session_id = ? AND player_id IN (
                    SELECT id FROM players WHERE full_name = ?
                )
            ''', (session_id, player_name))
            
            return cursor.rowcount > 0

    def get_sessions_for_date(self, date: date) -> List[Session]:
        """Получение всех сессий на определенную дату"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sessions 
                WHERE date = ?
                ORDER BY time_start
            ''', (date.isoformat(),))
            
            sessions = []
            for row in cursor.fetchall():
                session = Session(
                    id=row[0],
                    date=datetime.fromisoformat(row[1]),
                    time_start=datetime.strptime(row[2], '%H:%M').time(),
                    time_end=datetime.strptime(row[3], '%H:%M').time(),
                    max_players=row[4],
                    message_id=row[5],
                    chat_id=row[6]
                )
                sessions.append(session)
            
            return sessions

    def set_bot_enabled(self, enabled: bool) -> None:
        """Включение/выключение бота"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', ('bot_enabled', str(enabled)))
            conn.commit()

    def is_bot_enabled(self) -> bool:
        """Проверка, включен ли бот"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT value FROM settings WHERE key = ?
            ''', ('bot_enabled',))
            
            result = cursor.fetchone()
            return result is None or result[0].lower() == 'true'

    def get_player_stats(self, player_name: str) -> Optional[dict]:
        """Получение статистики игрока"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_games,
                    MAX(s.date) as last_game
                FROM registrations r
                JOIN players p ON r.player_id = p.id
                JOIN sessions s ON r.session_id = s.id
                WHERE p.full_name = ?
            ''', (player_name,))
            
            result = cursor.fetchone()
            if not result:
                return None
                
            return {
                'total_games': result[0],
                'last_game': datetime.fromisoformat(result[1]).date() if result[1] else None
            }

    def get_general_stats(self) -> dict:
        """Получение общей статистики"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Общее количество сессий
            cursor.execute('SELECT COUNT(*) FROM sessions')
            total_sessions = cursor.fetchone()[0]
            
            # Общее количество игроков
            cursor.execute('SELECT COUNT(*) FROM players')
            total_players = cursor.fetchone()[0]
            
            # Активные игроки (играли в последний месяц)
            cursor.execute('''
                SELECT COUNT(DISTINCT p.id)
                FROM players p
                JOIN registrations r ON p.id = r.player_id
                JOIN sessions s ON r.session_id = s.id
                WHERE s.date >= date('now', '-1 month')
            ''')
            active_players = cursor.fetchone()[0]
            
            return {
                'total_sessions': total_sessions,
                'total_players': total_players,
                'active_players': active_players
            }
