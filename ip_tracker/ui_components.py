# ip_tracker/ui_components.py
import customtkinter
import tkinter as tk
from .ip_extractor import IPExtractor # <-- IMPORTAÇÃO CORRIGIDA

class PasteEnabledInputDialog(customtkinter.CTkInputDialog):
    def __init__(self, *args, ip_extractor: IPExtractor, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip_extractor = ip_extractor

        # Focado apenas no Mac, como solicitado
        self.bind("<Command-v>", self._handle_paste_dialog)

    def _handle_paste_dialog(self, event=None):
        extracted_ip = None
        try:
            clipboard_text = self.clipboard_get()
            extracted_ip = self.ip_extractor.extract_from_text(clipboard_text)
            if extracted_ip:
                self._entry.delete(0, "end")
                self._entry.insert(0, extracted_ip)
                return
        except tk.TclError:
            pass # Sem texto, tentar imagem

        extracted_ip = self.ip_extractor.extract_from_image()
        if extracted_ip:
            self._entry.delete(0, "end")
            self._entry.insert(0, extracted_ip)