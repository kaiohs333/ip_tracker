# ip_tracker/database.py
import psycopg2
from psycopg2.extras import DictCursor # <-- IMPORTANTE
from .config import DB_SETTINGS

class DatabaseError(Exception):
    """Exceção customizada para erros de banco."""
    pass

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    try:
        # Usa DictCursor para que os resultados sejam como dicionários
        conn = psycopg2.connect(**DB_SETTINGS, cursor_factory=DictCursor)
        return conn
    except psycopg2.OperationalError as e:
        # Levanta um erro que a GUI pode capturar
        raise DatabaseError(f"Não foi possível conectar ao PostgreSQL: {e}") from e

def register_ip_in_db(ip_address, mobile_code, country, record_type) -> bool:
    """Insere ou ATUALIZA um registro de IP.
    Retorna True se bem-sucedido.
    """
    # Sua lógica de ON CONFLICT DO UPDATE é ótima!
    sql = """
        INSERT INTO registered_ips (ip_address, mobile_code, country, record_type)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ip_address) DO UPDATE SET
            mobile_code = EXCLUDED.mobile_code,
            country = EXCLUDED.country,
            record_type = EXCLUDED.record_type,
            registration_date = CURRENT_TIMESTAMP;
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (ip_address, mobile_code, country, record_type))
            conn.commit()
            return True
    except Exception as e:
        if conn: conn.rollback()
        # Levanta o erro para a camada de serviço tratar
        raise DatabaseError(f"Erro inesperado ao registrar/atualizar o IP: {e}") from e
    finally:
        if conn: conn.close()

def search_ip_in_db(ip_address) -> dict | None:
    """Busca por um IP e retorna seus dados (como um dict) ou None."""
    sql = "SELECT ip_address, mobile_code, country, registration_date, record_type FROM registered_ips WHERE ip_address = %s;"
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (ip_address,))
            result = cur.fetchone()
            return result # <-- Retorna a linha (que é um DictRow) ou None
    except Exception as e:
        # Levanta o erro para a camada de serviço tratar
        raise DatabaseError(f"Erro inesperado ao buscar o IP: {e}") from e
    finally:
        if conn: conn.close()