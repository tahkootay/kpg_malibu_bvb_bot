def __init__(self, db_path: str):
    """
    Инициализация соединения с базой данных
    
    Args:
        db_path: путь к файлу базы данных
    """
    # Создаём директорию для БД, если её нет
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    self.db_path = db_path
    self.logger = logging.getLogger('kpg_malibu_bvb')
    self.create_tables()