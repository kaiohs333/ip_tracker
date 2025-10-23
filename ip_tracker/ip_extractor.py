# ip_tracker/ip_extractor.py
import re
import pytesseract
from PIL import ImageGrab, Image
from tkinter import messagebox

# --- Funções Base de Extração ---

def find_ip_in_text(text: str) -> str | None:
    """Procura por um endereço IP em uma string de texto."""
    if not text:
        return None
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, text)
    if found_ips:
        return found_ips[0] # Retorna o primeiro IP encontrado
    return None

def extract_ip_from_clipboard_image() -> str | None:
    """Extrai um endereço IP de uma imagem na área de transferência usando OCR."""
    try:
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            text = pytesseract.image_to_string(image, lang='eng')
            return find_ip_in_text(text)
    except Exception as e:
        # A GUI não deve travar se o OCR falhar, apenas registre
        print(f"Erro ao extrair IP da imagem do clipboard via OCR: {e}")
    return None

# --- Classe 'Wrapper' ---

class IPExtractor:
    """Abstrai a extração de IPs de texto ou imagem."""
    def extract_from_text(self, text: str) -> str | None:
        return find_ip_in_text(text)

    def extract_from_image(self) -> str | None:
        return extract_ip_from_clipboard_image()