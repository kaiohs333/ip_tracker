import pytesseract
from PIL import ImageGrab, Image
import re
import platform

# (Conteúdo do seu test_ocr.py)
print(f"Rodando no sistema: {platform.system()}")

def find_ip_in_text(text):
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, text)
    if found_ips:
        return found_ips[0] 
    return None

def test_clipboard_ocr():
    print("Tentando ler imagem do clipboard...")
    try:
        image = ImageGrab.grabclipboard()
        if image is None:
            print("ERRO: Nenhuma imagem encontrada no clipboard.")
            return

        if isinstance(image, Image.Image):
            print("Sucesso! Imagem encontrada no clipboard.")
            text = pytesseract.image_to_string(image, lang='eng')
            print("--- TEXTO EXTRAÍDO DO OCR ---")
            print(text)
            print("------------------------------")

            if not text.strip():
                print("AVISO: O OCR não conseguiu extrair nenhum texto da imagem.")
                return

            ip = find_ip_in_text(text)
            if ip:
                print(f"Sucesso! IP encontrado: {ip}")
            else:
                print("ERRO: Texto foi extraído, mas nenhum padrão de IP foi encontrado nele.")
        else:
            print(f"AVISO: O clipboard não contém uma imagem (tipo: {type(image)}).")
    except Exception as e:
        print(f"\n--- ERRO FATAL DURANTE O TESTE ---")
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_clipboard_ocr()