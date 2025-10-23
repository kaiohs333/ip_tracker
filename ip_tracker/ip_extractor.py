# ip_tracker/ip_extractor.py
import re
import pytesseract
from PIL import Image

# --- Funções Base de Extração ---

def find_ip_in_text(text: str) -> str | None:
    """Procura por um endereço IP em uma string de texto."""
    if not text:
        return None
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, text)
    if found_ips:
        return found_ips[0]
    return None

def ocr_image_to_ip(image: Image.Image) -> str | None:
    """Executa OCR em um objeto de imagem e procura por um IP."""
    try:
        text = pytesseract.image_to_string(image, lang='eng')
        print(f"Texto extraído do OCR: {text}")
        return find_ip_in_text(text)
    except Exception as e:
        print(f"Erro durante o OCR: {e}")
        # Propaga o erro para a thread principal tratar
        raise e 

# --- Classe 'Wrapper' ---

class IPExtractor:
    """Abstrai a extração de IPs de texto ou imagem."""
    
    def extract_from_text(self, text: str) -> str | None:
        """Extrai IP de uma string de texto."""
        return find_ip_in_text(text)

    def extract_from_image(self, image: Image.Image) -> str | None:
        """Extrai IP de um objeto de Imagem (PIL)."""
        # Agora este método espera um objeto de imagem
        return ocr_image_to_ip(image)