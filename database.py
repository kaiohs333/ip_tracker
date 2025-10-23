import psycopg2
from tkinter import messagebox
from config import DB_SETTINGS # Importa nossa configuração segura

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        return conn
    except psycopg2.OperationalError as e:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao PostgreSQL: {e}")
        return None

def register_ip_in_db(ip_address, mobile_code, country, record_type):
    """Insere um novo registro de IP no banco de dados."""
    sql = """
        INSERT INTO registered_ips (ip_address, mobile_code, country, record_type)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ip_address) DO NOTHING;
    """
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (ip_address, mobile_code, country, record_type))
            conn.commit()
            if cur.rowcount > 0:
                messagebox.showinfo("Sucesso", f"IP {ip_address} registrado com sucesso!")
            else:
                messagebox.showwarning("Aviso", f"O IP {ip_address} já existe no banco de dados.")
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Erro de DB", f"Falha ao registrar o IP: {e}")
    finally:
        if conn: conn.close()

def search_ip_in_db(ip_address):
    """Busca por um IP no banco de dados e mostra suas informações."""
    sql = "SELECT ip_address, mobile_code, country, registration_date, record_type FROM registered_ips WHERE ip_address = %s;"
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (ip_address,))
            result = cur.fetchone()
            if result:
                info = (
                    f"IP: {result[0]}\n"
                    f"Código Mobile: {result[1]}\n"
                    f"País: {result[2]}\n"
                    f"Tipo: {result[4]}\n"
                    f"Data de Registro: {result[3].strftime('%d/%m/%Y %H:%M:%S')}"
                )
                messagebox.showinfo("Resultado da Busca", info)
            else:
                messagebox.showinfo("Resultado da Busca", f"O IP {ip_address} não foi encontrado.")
    except Exception as e:
        messagebox.showerror("Erro de DB", f"Falha ao buscar o IP: {e}")
    finally:
        if conn: conn.close()