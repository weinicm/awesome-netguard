import asyncpg
import logging
from db.dbconfig import DBConfig

class DBManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config = DBConfig()
            self.pool = None
            self.initialized = True

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                database=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD
            )
            logging.info("Database connection pool created successfully.")
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            logging.info("Database connection pool closed.")

    async def fetch(self, query, *args):
        if self.pool is None:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                logging.debug(f"Executing query: {query} with args: {args}")
                return await connection.fetch(query, *args)
            except Exception as e:
                logging.error(f"Error executing fetch: {e}")
                logging.error(f"Query: {query}")
                logging.error(f"Args: {args}")
                raise


    async def fetchrow(self, query, *args):
        if self.pool is None:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                return await connection.fetchrow(query, *args)
            except Exception as e:
                logging.error(f"Error executing fetchrow: {e}")
                raise

    async def execute(self, query, *args, fetch=False):
        if self.pool is None:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                if fetch:
                    # 使用 fetch 来获取返回的结果
                    return await connection.fetch(query, *args)
                else:
                    # 执行查询但不获取结果
                    await connection.execute(query, *args)
            except Exception as e:
                logging.error(f"Error executing query: {e}")
                raise

    async def execute_many(self, query, args_list):
        if self.pool is None:
            await self.connect()
        async with self.pool.acquire() as connection:
            try:
                return await connection.executemany(query, args_list)
            except Exception as e:
                logging.error(f"Error executing many: {e}")
                raise

# 示例用法
async def main():
    db_manager = DBManager()
    await db_manager.connect()
    
 ### --------------------------------------------------有空的时候,改成下面的异步单例-------------------------------------------------   
    
# import asyncpg
# import logging
# from db.dbconfig import DBConfig

# logger = logging.getLogger(__name__)

# class DBManager:
#     _instance = None

#     @classmethod
#     async def get_instance(cls) -> 'DBManager':
#         if cls._instance is None:
#             cls._instance = DBManager()
#             await cls._instance.connect()
#         return cls._instance

#     def __init__(self):
#         self.config = DBConfig()
#         self.pool = None

#     async def connect(self):
#         try:
#             self.pool = await asyncpg.create_pool(
#                 host=self.config.DB_HOST,
#                 port=self.config.DB_PORT,
#                 database=self.config.DB_NAME,
#                 user=self.config.DB_USER,
#                 password=self.config.DB_PASSWORD
#             )
#             logger.info("Database connection pool created successfully.")
#         except Exception as e:
#             logger.error(f"Error connecting to database: {e}")
#             raise

#     async def close(self):
#         """Close the database connection pool."""
#         if self.pool:
#             await self.pool.close()
#             logger.info("Database connection pool closed.")

#     async def fetch(self, query, *args):
#         if self.pool is None:
#             await self.connect()
#         async with self.pool.acquire() as connection:
#             try:
#                 logger.debug(f"Executing query: {query} with args: {args}")
#                 return await connection.fetch(query, *args)
#             except Exception as e:
#                 logger.error(f"Error executing fetch: {e}")
#                 logger.error(f"Query: {query}")
#                 logger.error(f"Args: {args}")
#                 raise

#     async def fetchrow(self, query, *args):
#         if self.pool is None:
#             await self.connect()
#         async with self.pool.acquire() as connection:
#             try:
#                 return await connection.fetchrow(query, *args)
#             except Exception as e:
#                 logger.error(f"Error executing fetchrow: {e}")
#                 raise

#     async def execute(self, query, *args, fetch=False):
#         if self.pool is None:
#             await self.connect()
#         async with self.pool.acquire() as connection:
#             try:
#                 if fetch:
#                     # 使用 fetch 来获取返回的结果
#                     return await connection.fetch(query, *args)
#                 else:
#                     # 执行查询但不获取结果
#                     await connection.execute(query, *args)
#             except Exception as e:
#                 logger.error(f"Error executing query: {e}")
#                 raise

#     async def execute_many(self, query, args_list):
#         if self.pool is None:
#             await self.connect()
#         async with self.pool.acquire() as connection:
#             try:
#                 return await connection.executemany(query, args_list)
#             except Exception as e:
#                 logger.error(f"Error executing many: {e}")
#                 raise

# # 示例用法
# async def main():
#     db_manager = await DBManager.get_instance()
#     # 进行数据库操作
#     result = await db_manager.fetch("SELECT * FROM some_table")
#     print(result)