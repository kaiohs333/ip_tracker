import tkinter as tk
from tkinter import messagebox, simpledialog
import re
import requests
import psycopg2
from PIL import ImageGrab, Image
import pytesseract

# --- CONFIGURAÇÕES ---

# Configure o caminho para o executável do Tesseract se não estiver no PATH do sistema
# Exemplo Windows: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configurações de conexão com o PostgreSQL
DB_SETTINGS = {
    "dbname": "ip_tracker",
    "user": "postgres", # Seu usuário
    "password": "", # Sua senha
    "host": "localhost",
    "port": "5432"
}

# --- LÓGICA DE BACKEND ---

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        return conn
    except psycopg2.OperationalError as e:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao PostgreSQL: {e}")
        return None

def get_ip_info(ip_address):
    """Busca informações de geolocalização de um IP usando uma API pública."""
    try:
        # Usando a API ip-api.com que é simples e não requer chave para uso básico
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        response.raise_for_status()  # Lança um erro para respostas ruins (4xx ou 5xx)
        data = response.json()
        if data['status'] == 'success':
            return {"country": data.get('country', 'Não encontrado')}
        else:
            return {"country": "País não encontrado"}
    except requests.RequestException as e:
        print(f"Erro ao buscar informações do IP: {e}")
        return {"country": "Erro na busca"}

def find_ip_in_text(text):
    """Encontra o primeiro endereço IPv4 válido em uma string de texto."""
    # Regex para encontrar endereços IPv4
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, text)
    if found_ips:
        return found_ips[0] # Retorna o primeiro IP encontrado
    return None

def extract_ip_from_clipboard_image():
    """Pega uma imagem do clipboard, extrai texto via OCR e procura por um IP."""
    try:
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            # Converte a imagem para um formato que o Tesseract entende melhor
            text = pytesseract.image_to_string(image, lang='eng')
            print(f"Texto extraído do OCR: {text}") # Para depuração
            ip = find_ip_in_text(text)
            return ip
        else:
            messagebox.showinfo("Clipboard", "Nenhuma imagem encontrada no clipboard.")
            return None
    except Exception as e:
        messagebox.showerror("Erro de OCR", f"Não foi possível processar a imagem: {e}")
        return None

def register_ip_in_db(ip_address, mobile_code, country):
    """Insere um novo registro de IP no banco de dados."""
    sql = """
        INSERT INTO registered_ips (ip_address, mobile_code, country)
        VALUES (%s, %s, %s)
        ON CONFLICT (ip_address) DO NOTHING;
    """
    conn = get_db_connection()
    if not conn:
        return
    
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
        if conn:
            conn.close()
            
def search_ip_in_db(ip_address):
    """Busca por um IP no banco de dados e mostra suas informações."""
    sql = "SELECT ip_address, mobile_code, country, registration_date FROM registered_ips WHERE ip_address = %s;"
    conn = get_db_connection()
    if not conn:
        return
        
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
        if conn:
            conn.close()

# --- INTERFACE GRÁFICA (GUI) ---

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Registrador de IP")

        # Frame principal
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(padx=10, pady=10)

        # Campo de IP
        tk.Label(frame, text="Endereço IP:").grid(row=0, column=0, sticky="w", pady=2)
        self.ip_entry = tk.Entry(frame, width=40)
        self.ip_entry.grid(row=0, column=1, columnspan=2, pady=2)
        self.ip_entry.bind("<Command-v>", self.handle_paste) # Associa Ctrl+V à função

        # Campo de Código Mobile
        tk.Label(frame, text="Código Mobile:").grid(row=1, column=0, sticky="w", pady=2)
        self.mobile_code_entry = tk.Entry(frame, width=40)
        self.mobile_code_entry.grid(row=1, column=1, columnspan=2, pady=2)

        # Botões
        self.register_button = tk.Button(frame, text="Registrar IP", command=self.register)
        self.register_button.grid(row=2, column=1, sticky="ew", pady=10)

        self.search_button = tk.Button(frame, text="Consultar IP", command=self.search)
        self.search_button.grid(row=2, column=2, sticky="ew", pady=10, padx=5)
        
        # Label de instrução
        tk.Label(frame, text="Pressione Ctrl+V no campo de IP para colar de um print screen.", font=("Arial", 8)).grid(row=3, column=0, columnspan=3, pady=5)

    def handle_paste(self, event=None):
        """Função especial para o evento de colar (Ctrl+V)."""
        # Primeiro, tenta colar texto normal
        try:
            clipboard_text = self.root.clipboard_get()
            # Se o texto colado parece um IP, apenas use-o
            if find_ip_in_text(clipboard_text):
                 self.ip_entry.delete(0, tk.END)
                 self.ip_entry.insert(0, clipboard_text)
                 return # Termina aqui se colou texto
        except tk.TclError:
            # Se não for texto, deve ser uma imagem
            pass

        # Se não for texto, tenta extrair da imagem
        extracted_ip = extract_ip_from_clipboard_image()
        if extracted_ip:
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, extracted_ip)
            messagebox.showinfo("Sucesso OCR", f"IP {extracted_ip} extraído da imagem!")
    
    def register(self):
        ip = self.ip_entry.get().strip()
        mobile_code = self.mobile_code_entry.get().strip()

        if not ip:
            messagebox.showwarning("Campo Vazio", "O campo de IP é obrigatório.")
            return

        # Busca o país do IP
        info = get_ip_info(ip)
        country = info.get("country", "Desconhecido")
        
        # Pede confirmação ao usuário
        confirm = messagebox.askyesno("Confirmar Registro", f"Registrar o IP {ip} para o país '{country}'?")
        if confirm:
            register_ip_in_db(ip, mobile_code, country)

    def search(self):
        ip = simpledialog.askstring("Consultar IP", "Digite o endereço IP para buscar:", parent=self.root)
        if ip:
            search_ip_in_db(ip.strip())

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()