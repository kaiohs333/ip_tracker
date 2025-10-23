# ip_tracker/ip_service.py
import tkinter as tk
from .database import register_ip_in_db, search_ip_in_db, DatabaseError
from .utils import get_ip_info
from .ip_extractor import IPExtractor

# --- Constantes de Mensagens (movidas para cá) ---
IP_FIELD_REQUIRED_MSG = "O campo de IP é obrigatório."
COUNTRY_NOT_FOUND_MSG = "Não foi possível encontrar o país automaticamente.\nPor favor, digite o país:"
COUNTRY_REQUIRED_CANCEL_MSG = "Registro cancelado. O país é necessário."
REGISTER_CONFIRM_TITLE = "Confirmar Registro"
REGISTER_CONFIRM_MSG = "Registrar o IP {ip} para o país \'{country}\' como uma \'{record_type}\'?"
SEARCH_IP_PROMPT = "Digite o endereço IP para buscar:"
OCR_SUCCESS_TITLE = "Sucesso OCR"
OCR_SUCCESS_MSG = "IP {ip} extraído da imagem!"

class IPService:
    """Encapsula a lógica de negócios para registro e busca de IPs."""

    def __init__(self, extractor: IPExtractor):
        self.extractor = extractor

    def get_ip_details(self, ip: str) -> dict:
        """Busca detalhes do IP na API externa."""
        return get_ip_info(ip)

    def register_ip(self, ip: str, mobile_code: str, country: str, record_type: str) -> bool:
        """Tenta registrar um IP no banco. Retorna True/False."""
        try:
            success = register_ip_in_db(ip, mobile_code, country, record_type)
            return success
        except DatabaseError as e:
            print(f"Erro ao registrar IP no serviço: {e}")
            return False

    def search_ip(self, ip: str) -> dict | None:
        """Tenta buscar um IP no banco. Retorna um dict ou None."""
        try:
            result = search_ip_in_db(ip)
            return result
        except DatabaseError as e:
            print(f"Erro ao buscar IP no serviço: {e}")
            return None

    def process_paste_event(self, clipboard_get_func, show_info_func) -> str | None:
        """Processa um evento de 'colar', checando texto e depois imagem."""
        extracted_ip = None
        try:
            clipboard_text = clipboard_get_func()
            extracted_ip = self.extractor.extract_from_text(clipboard_text)
            if extracted_ip:
                return extracted_ip
        except tk.TclError:
            pass # Sem texto no clipboard, tentar imagem

        extracted_ip = self.extractor.extract_from_image()
        if extracted_ip:
            show_info_func(OCR_SUCCESS_TITLE, OCR_SUCCESS_MSG.format(ip=extracted_ip))
            return extracted_ip
        return None

    def handle_register_flow(self, ip: str, mobile_code: str, record_type: str, show_warning_func, ask_yes_no_func, show_info_func, show_error_func):
        """Orquestra o fluxo completo de registro."""
        from .ui_components import PasteEnabledInputDialog # Import local para evitar ciclo

        if not ip:
            show_warning_func("Campo Vazio", IP_FIELD_REQUIRED_MSG)
            return

        country = None
        try:
            info = self.get_ip_details(ip)
            country = info.get("country") # Retorna None se 'country' não existir
        except Exception as e:
            show_error_func("Erro de Rede", f"Falha ao obter informações do IP: {e}")
            return

        if not country:
            dialog = PasteEnabledInputDialog(
                text=COUNTRY_NOT_FOUND_MSG,
                title="País Não Encontrado",
                ip_extractor=self.extractor
            )
            country_input = dialog.get_input()

            if country_input:
                country = country_input
            else:
                show_warning_func("Cancelado", COUNTRY_REQUIRED_CANCEL_MSG)
                return

        confirm = ask_yes_no_func(
            REGISTER_CONFIRM_TITLE,
            REGISTER_CONFIRM_MSG.format(ip=ip, country=country, record_type=record_type)
        )

        if confirm:
            if self.register_ip(ip, mobile_code, country, record_type):
                show_info_func("Sucesso", "IP registrado/atualizado com sucesso!")
            else:
                # O erro já foi logado pelo 'register_ip'
                show_error_func("Erro de Registro", "Falha ao registrar o IP. Verifique os logs.")
        else:
            show_info_func("Cancelado", "Registro de IP cancelado.")

    def handle_search_flow(self, show_info_func, show_error_func) -> dict | None:
        """Orquestra o fluxo completo de busca."""
        from .ui_components import PasteEnabledInputDialog # Import local para evitar ciclo

        dialog = PasteEnabledInputDialog(
            text=SEARCH_IP_PROMPT,
            title="Consultar IP",
            ip_extractor=self.extractor
        )
        ip_to_search = dialog.get_input()

        if ip_to_search:
            ip_to_search = ip_to_search.strip()
            result = self.search_ip(ip_to_search)
            
            if result:
                # --- ERRO CORRIGIDO AQUI ---
                # Removidas as barras \ desnecessárias de dentro das chaves {}
                # e \n usado em vez de \\n.
                info = (
                    f"IP: {result['ip_address']}\n"
                    f"Código Mobile: {result['mobile_code']}\n"
                    f"País: {result['country']}\n"
                    f"Tipo: {result['record_type']}\n"
                    f"Data de Registro: {result['registration_date'].strftime('%d/%m/%Y %H:%M:%S')}"
                )
                show_info_func("Resultado da Busca", info)
                return result
            else:
                show_info_func("Resultado da Busca", f"O IP {ip_to_search} não foi encontrado.")
                return None
        else:
            show_info_func("Cancelado", "Busca de IP cancelada.")
            return None