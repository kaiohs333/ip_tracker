import pytesseract
from PIL import ImageGrab, Image
import re
import platform

print(f"Rodando no sistema: {platform.system()}")

# Função para encontrar IP (a mesma do app.py)
def find_ip_in_text(text):
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    found_ips = re.findall(ip_pattern, text)
    if found_ips:
        return found_ips[0] # Retorna o primeiro IP encontrado
    return None

def test_clipboard_ocr():
    print("Tentando ler imagem do clipboard...")
    try:
        image = ImageGrab.grabclipboard()

        if image is None:
            print("ERRO: Nenhuma imagem encontrada no clipboard.")
            print("Por favor, tire um print screen (Cmd+Ctrl+Shift+4) e tente de novo.")
            return

        if isinstance(image, Image.Image):
            print("Sucesso! Imagem encontrada no clipboard.")

            # Extrai o texto da imagem
            text = pytesseract.image_to_string(image, lang='eng')

            print("--- TEXTO EXTRAÍDO DO OCR ---")
            print(text)
            print("------------------------------")

            if not text.strip():
                print("AVISO: O OCR não conseguiu extrair nenhum texto da imagem.")
                return

            # Procura pelo IP no texto extraído
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
        print("Isso geralmente acontece se o Tesseract não está instalado ou no PATH.")
        print("Verifique o Diagnóstico Passo 1.")

# --- Executa o teste ---
if __name__ == "__main__":
    test_clipboard_ocr()