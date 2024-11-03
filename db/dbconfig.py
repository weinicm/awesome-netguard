import os

class DBConfig:
    def __init__(self):
        self.DB_HOST = os.getenv("DATABASE_HOST", "localhost")
        self.DB_PORT = os.getenv("DATABASE_PORT", "5432")
        self.DB_NAME = os.getenv("POSTGRES_DB", "netguard")
        self.DB_USER = os.getenv("POSTGRES_USER")
        self.DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        self.DB_POOL_MIN_SIZE = 15
        self.DB_POOL_MAX_SIZE = 30
        

db_config = DBConfig()