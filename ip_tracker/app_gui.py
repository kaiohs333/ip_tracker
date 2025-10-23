# ip_tracker/app_gui.py
import customtkinter
import tkinter as tk
from tkinter import messagebox
import threading
from PIL import Image, ImageGrab # Importar ImageGrab aqui

# Importações de serviço e extrator
from .ip_service import IPService
from .ip_extractor import IPExtractor
from .database import DatabaseError

# Constantes de UI (movidas do serviço, já que a UI é quem as usa)
OCR_SUCCESS_TITLE = "Sucesso OCR"
OCR_SUCCESS_MSG = "IP {ip} extraído da imagem!"

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Registrador de IP")
        self.geometry("400x250")

        self.ip_service = IPService(IPExtractor())

        self._create_widgets()
        self._bind_events()

    def _create_widgets(self):
        # (Seu código _create_widgets... está perfeito, sem alterações)
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
        # Bind apenas para Mac
        self.bind("<Command-v>", self._handle_paste)

    # --- LÓGICA DE PASTE CORRIGIDA ---

    def _handle_paste(self, event=None):
        """
        Lida com o 'colar' de forma segura para threads.
        Executa no *Thread Principal*.
        """
        
        # 1. Tenta colar TEXTO (rápido, sem thread)
        try:
            clipboard_text = self.clipboard_get()
            extracted_ip = self.ip_service.extractor.extract_from_text(clipboard_text)
            if extracted_ip:
                self._update_ip_entry(extracted_ip) # Colou texto, fim.
                return
        except tk.TclError:
            # Não é texto, normal. Prossiga para tentar imagem.
            pass
        except Exception as e:
            print(f"Erro ao colar texto: {e}")
            return

        # 2. Tenta pegar IMAGEM (ainda no Thread Principal)
        try:
            image = ImageGrab.grabclipboard()
            if not isinstance(image, Image.Image):
                # Não é texto e nem imagem. Fim.
                return
        except Exception as e:
            print(f"Erro ao pegar imagem do clipboard: {e}")
            messagebox.showerror("Erro de Clipboard", f"Não foi possível ler a imagem do clipboard: {e}")
            return

        # 3. TEMOS UMA IMAGEM. Agora, desabilite a UI e inicie o thread de OCR.
        self._set_ui_state(False)
        
        # Inicia o thread SOMENTE para a tarefa lenta (OCR)
        # Passa o objeto 'image' para o thread.
        threading.Thread(target=self._run_ocr_task, args=(image,), daemon=True).start()

    def _run_ocr_task(self, image_object: Image.Image):
        """
        Executa a tarefa lenta de OCR no *Thread Secundário*.
        """
        extracted_ip = None
        try:
            # A única coisa no thread: processar a imagem (lento)
            extracted_ip = self.ip_service.extractor.extract_from_image(image_object)
        except Exception as e:
            print(f"Erro na thread de OCR: {e}")
            self.after(0, lambda: messagebox.showerror("Erro de OCR", f"Falha ao processar a imagem: {e}"))

        # 4. A tarefa lenta acabou. Agende as atualizações da UI no Thread Principal.
        def ui_updates():
            # 4a. REABILITA A UI (PRIMEIRO!)
            self._set_ui_state(True)
            
            # 4b. MOSTRA O POP-UP E COLA O IP (DEPOIS!)
            if extracted_ip:
                messagebox.showinfo(OCR_SUCCESS_TITLE, OCR_SUCCESS_MSG.format(ip=extracted_ip))
                self._update_ip_entry(extracted_ip)
            else:
                messagebox.showwarning("Falha no OCR", "Não foi possível encontrar um IP na imagem.")
        
        self.after(0, ui_updates)

    # --- FIM DA LÓGICA DE PASTE ---

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

    # --- Funções de Registro e Busca (Seu código, está ótimo) ---

    def _on_register_clicked(self):
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
                    ask_yes_no_func=messagebox.askyesno,
                    show_info_func=lambda title, msg: self.after(0, lambda: messagebox.showinfo(title, msg)),
                    show_error_func=lambda title, msg: self.after(0, lambda: messagebox.showerror(title, msg))
                )
            except DatabaseError as e:
                self.after(0, lambda: messagebox.showerror("Erro de Banco", str(e)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro Inesperado", str(e)))
            finally:
                self._set_ui_state(True)

        threading.Thread(target=register_task, daemon=True).start()

    def _on_search_clicked(self):
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