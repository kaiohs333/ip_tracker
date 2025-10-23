# --- IMPORTS ---
import tkinter as tk
from tkinter import messagebox, simpledialog
import re
import requests
import psycopg2
from PIL import ImageGrab, Image
import pytesseract
import customtkinter 
import platform # Para checar o SO

# --- CONFIGURAÇÕES ---
# Configurações de conexão com o PostgreSQL
DB_SETTINGS = {
    "dbname": "ip_tracker",
    "user": "postgres",
    "password": "your_password", # Atualizar senha
    "host": "localhost",
    "port": "5432"
}

# --- LÓGICA DE BACKEND ---

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
            # Retorna o país, que pode ser None se a API não souber
            return {"country": data.get('country')}
        else:
            return {"country": None}
    except requests.RequestException as e:
        print(f"Erro ao buscar informações do IP: {e}")
        return {"country": None} # Retorna None em caso de erro

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
            return None
    except Exception as e:
        if 'no image data' not in str(e) and 'clipboard_get' not in str(e):
             messagebox.showerror("Erro de OCR", f"Não foi possível processar a imagem: {e}")
        return None

# --- MUDANÇA AQUI ---
# A função agora aceita 'record_type'
def register_ip_in_db(ip_address, mobile_code, country, record_type):
    sql = """
        INSERT INTO registered_ips (ip_address, mobile_code, country, record_type)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ip_address) DO NOTHING;
    """
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            # Adicionado 'record_type' na execução
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

# --- MUDANÇA AQUI ---
# Busca o 'record_type' e o exibe
def search_ip_in_db(ip_address):
    # Adicionado 'record_type' no SELECT
    sql = "SELECT ip_address, mobile_code, country, registration_date, record_type FROM registered_ips WHERE ip_address = %s;"
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (ip_address,))
            result = cur.fetchone()
            if result:
                # Adicionado 'Tipo' (result[4]) na mensagem de exibição
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

# --- INTERFACE GRÁFICA (GUI) COM CUSTOMTKINTER ---

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Registrador de IP")
        # Aumentamos a altura da janela para o novo campo
        self.geometry("400x250") 

        frame = customtkinter.CTkFrame(self)
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        frame.grid_columnconfigure((0, 1, 2), weight=1) # Permite que os botões se expandam

        # Campo de IP (row 0)
        customtkinter.CTkLabel(frame, text="Endereço IP:").grid(row=0, column=0, sticky="w", pady=10, padx=10)
        self.ip_entry = customtkinter.CTkEntry(frame, width=220)
        self.ip_entry.grid(row=0, column=1, columnspan=2, pady=10, padx=10, sticky="ew")
        
        self.ip_entry.bind("<Control-v>", self.handle_paste)
        if platform.system() == "Darwin":
            self.bind("<Command-v>", self.handle_paste)
        else:
            self.bind("<Control-v>", self.handle_paste)

        # Campo de Código Mobile (row 1)
        customtkinter.CTkLabel(frame, text="Código Mobile:").grid(row=1, column=0, sticky="w", pady=10, padx=10)
        self.mobile_code_entry = customtkinter.CTkEntry(frame, width=220)
        self.mobile_code_entry.grid(row=1, column=1, columnspan=2, pady=10, padx=10, sticky="ew")

        # --- NOVO CAMPO AQUI (row 2) ---
        customtkinter.CTkLabel(frame, text="Tipo:").grid(row=2, column=0, sticky="w", pady=10, padx=10)
        # Usando SegmentedButton para ser mais claro que um Switch
        self.record_type_seg = customtkinter.CTkSegmentedButton(frame, values=["Publicação", "Revisão"])
        self.record_type_seg.set("Publicação") # Define "Publicação" como padrão
        self.record_type_seg.grid(row=2, column=1, columnspan=2, pady=10, padx=10, sticky="ew")

        # Botões (movidos para row 3)
        self.register_button = customtkinter.CTkButton(frame, text="Registrar IP", command=self.register)
        self.register_button.grid(row=3, column=1, sticky="ew", pady=20, padx=5)

        self.search_button = customtkinter.CTkButton(frame, text="Consultar IP", command=self.search)
        self.search_button.grid(row=3, column=2, sticky="ew", pady=20, padx=5)

    def handle_paste(self, event=None):
        try:
            clipboard_text = self.clipboard_get()
            if find_ip_in_text(clipboard_text):
                 self.ip_entry.delete(0, "end")
                 self.ip_entry.insert(0, clipboard_text)
                 return
        except tk.TclError:
            pass

        extracted_ip = extract_ip_from_clipboard_image()
        if extracted_ip:
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, extracted_ip)
            messagebox.showinfo("Sucesso OCR", f"IP {extracted_ip} extraído da imagem!")
        else:
            pass

    # --- MUDANÇA AQUI ---
    # Lógica de registro atualizada
    def register(self):
        ip = self.ip_entry.get().strip()
        mobile_code = self.mobile_code_entry.get().strip()
        # Pega o valor do botão segmentado
        record_type = self.record_type_seg.get() 
        
        if not ip:
            messagebox.showwarning("Campo Vazio", "O campo de IP é obrigatório.")
            return

        info = get_ip_info(ip)
        country = info.get("country") # Pega o país (pode ser None)

        # --- NOVA LÓGICA AQUI ---
        # Se o país não foi encontrado (é None ou vazio)
        if not country:
            dialog = customtkinter.CTkInputDialog(
                text="Não foi possível encontrar o país automaticamente.\nPor favor, digite o país:",
                title="País Não Encontrado"
            )
            country_input = dialog.get_input()
            
            if country_input: # Se o usuário digitou algo
                country = country_input
            else: # Se o usuário cancelou ou deixou em branco
                messagebox.showwarning("Cancelado", "Registro cancelado. O país é necessário.")
                return # Para a execução

        # Pergunta de confirmação atualizada
        confirm = messagebox.askyesno(
            "Confirmar Registro", 
            f"Registrar o IP {ip} para o país '{country}' como uma '{record_type}'?"
        )
        
        if confirm:
            # Envia o 'record_type' para a função do banco
            register_ip_in_db(ip, mobile_code, country, record_type)

    def search(self):
        dialog = customtkinter.CTkInputDialog(text="Digite o endereço IP para buscar:", title="Consultar IP")
        ip = dialog.get_input()
        
        if ip:
            search_ip_in_db(ip.strip())

if __name__ == "__main__":
    app = App()
    app.mainloop()