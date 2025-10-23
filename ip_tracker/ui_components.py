import customtkinter
import tkinter as tk
from ip_tracker.utils import find_ip_in_text, extract_ip_from_clipboard_image

class PasteEnabledInputDialog(customtkinter.CTkInputDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bind("<Command-v>", self._handle_paste_dialog)

    def _handle_paste_dialog(self, event=None):
        try:
            clipboard_text = self.clipboard_get()
            if find_ip_in_text(clipboard_text):
                 self._entry.delete(0, "end")
                 self._entry.insert(0, clipboard_text)
                 return
        except tk.TclError:
            pass 

        extracted_ip = extract_ip_from_clipboard_image()
        if extracted_ip:
            self._entry.delete(0, "end")
            self._entry.insert(0, extracted_ip)
        else:
            pass