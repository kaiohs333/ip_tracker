# ip_tracker/app_gui.py
import customtkinter
import tkinter as tk
from tkinter import messagebox
import threading

# --- IMPORTAÇÕES ATUALIZADAS ---
from .ip_service import IPService
from .ip_extractor import IPExtractor
from .database import DatabaseError

# A GUI não precisa saber sobre os componentes internos,
# ela apenas chama os métodos de serviço.
# ---------------------------------

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue") # Corrigido de 'set_color_theme' para 'set_default_color_theme'

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Registrador de IP")
        self.geometry("400x250")

        # Injeta as dependências na inicialização
        self.ip_service = IPService(IPExtractor())

        self._create_widgets()
        self._bind_events()

    def _create_widgets(self):
        frame = customtkinter.CTkFrame(self)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        frame.grid_columnconfigure((0, 1, 2), weight=1)

        # IP Entry
        customtkinter.CTkLabel(frame, text="Endereço IP:").grid(row=0, column=0, sticky="w", pady=10, padx=10)
        self.ip_entry = customtkinter.CTkEntry(frame, width=220)
        self.ip_entry.grid(row=0, column=1, columnspan=2, pady=10, padx=10, sticky="ew")

        # Mobile Code
        customtkinter.CTkLabel(frame, text="Código Mobile:").grid(row=1, column=0, sticky="w", pady=10, padx=10)
        self.mobile_code_entry = customtkinter.CTkEntry(frame, width=220)
        self.mobile_code_entry.grid(row=1, column=1, columnspan=2, pady=10, padx=10, sticky="ew")

        # Type
        customtkinter.CTkLabel(frame, text="Tipo:").grid(row=2, column=0, sticky="w", pady=10, padx=10)
        self.record_type_seg = customtkinter.CTkSegmentedButton(frame, values=["Publicação", "Revisão"])
        self.record_type_seg.set("Publicação")
        self.record_type_seg.grid(row=2, column=1, columnspan=2, pady=10, padx=10, sticky="ew")

        # Buttons
        self.register_button = customtkinter.CTkButton(frame, text="Registrar IP", command=self._on_register_clicked)
        self.register_button.grid(row=3, column=1, sticky="ew", pady=20, padx=5)

        self.search_button = customtkinter.CTkButton(frame, text="Consultar IP", command=self._on_search_clicked)
        self.search_button.grid(row=3, column=2, sticky="ew", pady=20, padx=5)

    def _bind_events(self):
        # Bind apenas para Mac, como solicitado
        self.bind("<Command-v>", self._handle_paste)

    def _handle_paste(self, event=None):
        """Lida com o 'colar' em uma thread separada para não travar a UI."""
        self._set_ui_state(False) # Desativa a UI

        def paste_task():
            try:
                extracted_ip = self.ip_service.process_paste_event(
                    clipboard_get_func=self.clipboard_get,
                    # Usa 'self.after' para garantir que o messagebox rode na thread principal
                    show_info_func=lambda title, msg: self.after(0, lambda: messagebox.showinfo(title, msg))
                )
                if extracted_ip:
                    self._update_ip_entry(extracted_ip)
            except Exception as e:
                print(f"Erro inesperado no paste_task: {e}")
            finally:
                self._set_ui_state(True) # Reativa a UI
        
        threading.Thread(target=paste_task, daemon=True).start()

    def _update_ip_entry(self, ip: str):
        """Atualiza o campo de IP na thread principal."""
        def update():
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, ip)
        self.after(0, update)

    def _set_ui_state(self, enabled: bool):
        """Ativa ou desativa os widgets da UI na thread principal."""
        state = "normal" if enabled else "disabled"
        def set_state():
            self.register_button.configure(state=state)
            self.search_button.configure(state=state)
            self.ip_entry.configure(state=state)
            self.mobile_code_entry.configure(state=state)
            self.record_type_seg.configure(state=state)
        self.after(0, set_state)

    def _on_register_clicked(self):
        """Inicia o fluxo de registro em uma thread separada."""
        ip = self.ip_entry.get().strip()
        mobile_code = self.mobile_code_entry.get().strip()
        record_type = self.record_type_seg.get()

        self._set_ui_state(False)

        def register_task():
            try:
                self.ip_service.handle_register_flow(
                    ip=ip,
                    mobile_code=mobile_code,
                    record_type=record_type,
                    show_warning_func=lambda title, msg: self.after(0, lambda: messagebox.showwarning(title, msg)),
                    ask_yes_no_func=messagebox.askyesno, # askyesno é thread-safe
                    show_info_func=lambda title, msg: self.after(0, lambda: messagebox.showinfo(title, msg)),
                    show_error_func=lambda title, msg: self.after(0, lambda: messagebox.showerror(title, msg))
                )
            except DatabaseError as e:
                # Captura erros de conexão que podem ter ocorrido
                self.after(0, lambda: messagebox.showerror("Erro de Banco", str(e)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro Inesperado", str(e)))
            finally:
                self._set_ui_state(True)

        threading.Thread(target=register_task, daemon=True).start()

    def _on_search_clicked(self):
        """Inicia o fluxo de busca em uma thread separada."""
        self._set_ui_state(False)

        def search_task():
            try:
                self.ip_service.handle_search_flow(
                    show_info_func=lambda title, msg: self.after(0, lambda: messagebox.showinfo(title, msg)),
                    show_error_func=lambda title, msg: self.after(0, lambda: messagebox.showerror(title, msg))
                )
            except DatabaseError as e:
                self.after(0, lambda: messagebox.showerror("Erro de Banco", str(e)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro Inesperado", str(e)))
            finally:
                self._set_ui_state(True)

        threading.Thread(target=search_task, daemon=True).start()