import re
import requests
import pytesseract
from PIL import ImageGrab, Image
from tkinter import messagebox

def get_ip_info(ip_address):
    """Busca informações de geolocalização de um IP."""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'success':
            return {"country": data.get('country')}
        else:
            return {"country": None}
    except requests.RequestException as e:
        print(f"Erro ao buscar informações do IP: {e}")
        return {"country": None}

def find_ip_in_text(text):
    """Encontra o primeiro endereço IPv4 válido em uma string de texto."""
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, text)
    if found_ips:
        return found_ips[0]
    return None

def extract_ip_from_clipboard_image():
    """Pega uma imagem do clipboard, extrai texto via OCR e procura por um IP."""
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