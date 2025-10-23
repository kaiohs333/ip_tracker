# --- IMPORTS ---
import tkinter as tk
from tkinter import messagebox, simpledialog
import re
import requests
import psycopg2
from PIL import ImageGrab, Image
import pytesseract
import customtkinter # Importe o customtkinter
import platform # Para checar o SO

# --- CONFIGURAÇÕES ---
# Configurações de conexão com o PostgreSQL
DB_SETTINGS = {
    "dbname": "ip_tracker",
    "user": "postgres",
    "password": "sua_senha_aqui",
   "host": "localhost",
    "port": "5432"
}

# --- LÓGICA DE BACKEND (IDÊNTICA) ---

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        return conn
    except psycopg2.OperationalError as e:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao PostgreSQL: {e}")
        return None

def get_ip_info(ip_address):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'success':
            return {"country": data.get('country', 'Não encontrado')}
        else:
            return {"country": "País não encontrado"}
    except requests.RequestException as e:
        print(f"Erro ao buscar informações do IP: {e}")
        return {"country": "Erro na busca"}

def find_ip_in_text(text):
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, text)
    if found_ips:
        return found_ips[0]
    return None

def extract_ip_from_clipboard_image():
    try:
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            text = pytesseract.image_to_string(image, lang='eng')
            print(f"Texto extraído do OCR: {text}")
            ip = find_ip_in_text(text)
            return ip
        else:
            return None # Não é um erro, só não é uma imagem
    except Exception as e:
        # Só mostre o erro se não for um 'tk.TclError' (que significa clipboard vazio ou com texto)
        if 'no image data' not in str(e) and 'clipboard_get' not in str(e):
             messagebox.showerror("Erro de OCR", f"Não foi possível processar a imagem: {e}")
        return None

def register_ip_in_db(ip_address, mobile_code, country):
    sql = """
        INSERT INTO registered_ips (ip_address, mobile_code, country)
        VALUES (%s, %s, %s)
        ON CONFLICT (ip_address) DO NOTHING;
    """
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (ip_address, mobile_code, country))
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
    sql = "SELECT ip_address, mobile_code, country, registration_date FROM registered_ips WHERE ip_address = %s;"
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (ip_address,))
            result = cur.fetchone()
            if result:
                info = f"IP: {result[0]}\nCódigo Mobile: {result[1]}\nPaís: {result[2]}\nData de Registro: {result[3].strftime('%d/%m/%Y %H:%M:%S')}"
                messagebox.showinfo("Resultado da Busca", info)
            else:
                messagebox.showinfo("Resultado da Busca", f"O IP {ip_address} não foi encontrado.")
    except Exception as e:
        messagebox.showerror("Erro de DB", f"Falha ao buscar o IP: {e}")
    finally:
        if conn: conn.close()

# --- INTERFACE GRÁFICA (GUI) COM CUSTOMTKINTER ---

# Configurações de aparência
customtkinter.set_appearance_mode("dark")  # "dark", "light", ou "system"
customtkinter.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class App(customtkinter.CTk): # Herda de CTk em vez de tk.Tk
    def __init__(self):
        super().__init__()

        self.title("Registrador de IP")
        self.geometry("400x200") # Define um tamanho inicial

        # Frame principal
        frame = customtkinter.CTkFrame(self)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Campo de IP
        customtkinter.CTkLabel(frame, text="Endereço IP:").grid(row=0, column=0, sticky="w", pady=10, padx=10)
        self.ip_entry = customtkinter.CTkEntry(frame, width=220)
        self.ip_entry.grid(row=0, column=1, columnspan=2, pady=10, padx=10)
        
        # O bind para o paste (Windows/Linux)
        self.ip_entry.bind("<Control-v>", self.handle_paste)
        
        # Bind para o paste (macOS)
        if platform.system() == "Darwin": # Darwin é o nome do kernel do macOS
            self.bind("<Command-v>", self.handle_paste) # Pega o Cmd+V na janela inteira
        else:
            self.bind("<Control-v>", self.handle_paste) # Pega o Ctrl+V na janela inteira

        # Campo de Código Mobile
        customtkinter.CTkLabel(frame, text="Código Mobile:").grid(row=1, column=0, sticky="w", pady=10, padx=10)
        self.mobile_code_entry = customtkinter.CTkEntry(frame, width=220)
        self.mobile_code_entry.grid(row=1, column=1, columnspan=2, pady=10, padx=10)

        # Botões
        self.register_button = customtkinter.CTkButton(frame, text="Registrar IP", command=self.register)
        self.register_button.grid(row=2, column=1, sticky="ew", pady=20, padx=5)

        self.search_button = customtkinter.CTkButton(frame, text="Consultar IP", command=self.search)
        self.search_button.grid(row=2, column=2, sticky="ew", pady=20, padx=5)

    def handle_paste(self, event=None):
        # 1. Tenta colar texto
        try:
            clipboard_text = self.clipboard_get()
            if find_ip_in_text(clipboard_text):
                 self.ip_entry.delete(0, "end")
                 self.ip_entry.insert(0, clipboard_text)
                 return
        except tk.TclError:
            pass # Se não for texto, continua para imagem

        # 2. Tenta extrair da imagem
        extracted_ip = extract_ip_from_clipboard_image()
        if extracted_ip:
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, extracted_ip)
            messagebox.showinfo("Sucesso OCR", f"IP {extracted_ip} extraído da imagem!")
        else:
            # Não mostra aviso se for só um paste de texto normal sem IP
            pass

    def register(self):
        ip = self.ip_entry.get().strip()
        mobile_code = self.mobile_code_entry.get().strip()
        if not ip:
            messagebox.showwarning("Campo Vazio", "O campo de IP é obrigatório.")
            return

        info = get_ip_info(ip)
        country = info.get("country", "Desconhecido")
        
        confirm = messagebox.askyesno("Confirmar Registro", f"Registrar o IP {ip} para o país '{country}'?")
        if confirm:
            register_ip_in_db(ip, mobile_code, country)

    def search(self):
        # O simpledialog do tkinter ainda funciona, mas o do CTk é mais bonito
        dialog = customtkinter.CTkInputDialog(text="Digite o endereço IP para buscar:", title="Consultar IP")
        ip = dialog.get_input()
        
        if ip:
            search_ip_in_db(ip.strip())

if __name__ == "__main__":
    app = App() # Cria a instância do app
    app.mainloop() # Inicia o loop