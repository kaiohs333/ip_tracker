# ip_tracker/ui_components.py
import customtkinter
import tkinter as tk
import threading # <-- Importado
from PIL import Image, ImageGrab # <-- Importado
from .ip_extractor import IPExtractor 

class PasteEnabledInputDialog(customtkinter.CTkInputDialog):
    def __init__(self, *args, ip_extractor: IPExtractor, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip_extractor = ip_extractor

        # Focado apenas no Mac
        self.bind("<Command-v>", self._handle_paste_dialog)

    def _handle_paste_dialog(self, event=None):
        """
        Lida com o 'colar' de forma segura para threads, espelhando a lógica da app_gui.
        Executa no *Thread Principal*.
        """
        
        # 1. Tenta colar TEXTO (rápido, sem thread)
        try:
            clipboard_text = self.clipboard_get()
            extracted_ip = self.ip_extractor.extract_from_text(clipboard_text)
            if extracted_ip:
                self._entry.delete(0, "end") # _entry é o campo de texto do diálogo
                self._entry.insert(0, extracted_ip)
                return
        except tk.TclError:
            pass # Não é texto, prossiga para tentar imagem.
        except Exception as e:
            print(f"Erro ao colar texto no diálogo: {e}")
            return

        # 2. Tenta pegar IMAGEM (ainda no Thread Principal)
        try:
            image = ImageGrab.grabclipboard()
            if not isinstance(image, Image.Image):
                # Não é texto e nem imagem. Fim.
                return
        except Exception as e:
            print(f"Erro no diálogo ao pegar imagem do clipboard: {e}")
            return

        # 3. TEMOS UMA IMAGEM. Inicie o thread de OCR.
        # Não precisamos desabilitar a UI, pois o diálogo já é modal (bloqueia)
        
        # Inicia o thread SOMENTE para a tarefa lenta (OCR)
        threading.Thread(target=self._run_dialog_ocr_task, args=(image,), daemon=True).start()

    def _run_dialog_ocr_task(self, image_object: Image.Image):
        """
        Executa a tarefa lenta de OCR no *Thread Secundário*.
        """
        extracted_ip = None
        try:
            # A única coisa no thread: processar a imagem (lento)
            extracted_ip = self.ip_extractor.extract_from_image(image_object)
        except Exception as e:
            print(f"Erro na thread de OCR do diálogo: {e}")
            # Não podemos mostrar um pop-up aqui facilmente, apenas logar
        
        # 4. A tarefa lenta acabou. Agende a atualização da UI no Thread Principal.
        def ui_update():
            # Verifica se o widget do diálogo ainda existe
            # (o usuário pode ter fechado)
            if self._entry.winfo_exists(): 
                self._entry.delete(0, "end")
                self._entry.insert(0, extracted_ip)
        
        if extracted_ip:
            # Usa self.after() para agendar a atualização na thread principal
            self.after(0, ui_update)