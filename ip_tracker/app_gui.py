import customtkinter
import tkinter as tk
from tkinter import messagebox
from ip_tracker.ui_components import PasteEnabledInputDialog
from ip_tracker.database import register_ip_in_db, search_ip_in_db
from ip_tracker.utils import get_ip_info, find_ip_in_text, extract_ip_from_clipboard_image

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Registrador de IP")
        self.geometry("400x250") 

        frame = customtkinter.CTkFrame(self)
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Campo de IP (row 0)
        customtkinter.CTkLabel(frame, text="Endereço IP:").grid(row=0, column=0, sticky="w", pady=10, padx=10)
        self.ip_entry = customtkinter.CTkEntry(frame, width=220)
        self.ip_entry.grid(row=0, column=1, columnspan=2, pady=10, padx=10, sticky="ew")
        
        # Associa o Cmd+V à janela inteira.
        self.bind("<Command-v>", self.handle_paste)

        # Campo de Código Mobile (row 1)
        customtkinter.CTkLabel(frame, text="Código Mobile:").grid(row=1, column=0, sticky="w", pady=10, padx=10)
        self.mobile_code_entry = customtkinter.CTkEntry(frame, width=220)
        self.mobile_code_entry.grid(row=1, column=1, columnspan=2, pady=10, padx=10, sticky="ew")

        # Tipo (row 2)
        customtkinter.CTkLabel(frame, text="Tipo:").grid(row=2, column=0, sticky="w", pady=10, padx=10)
        self.record_type_seg = customtkinter.CTkSegmentedButton(frame, values=["Publicação", "Revisão"])
        self.record_type_seg.set("Publicação")
        self.record_type_seg.grid(row=2, column=1, columnspan=2, pady=10, padx=10, sticky="ew")

        # Botões (row 3)
        self.register_button = customtkinter.CTkButton(frame, text="Registrar IP", command=self.register)
        self.register_button.grid(row=3, column=1, sticky="ew", pady=20, padx=5)

        self.search_button = customtkinter.CTkButton(frame, text="Consultar IP", command=self.search)
        self.search_button.grid(row=3, column=2, sticky="ew", pady=20, padx=5)

    def handle_paste(self, event=None):
        try:
            clipboard_text = self.clipboard_get()
            if find_ip_in_text(clipboard_text):
                 self.ip_entry.delete(0, "end")
                 self.ip_entry.insert(0, clipboard_text)
                 return
        except tk.TclError:
            pass

        extracted_ip = extract_ip_from_clipboard_image()
        if extracted_ip:
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, extracted_ip)
            messagebox.showinfo("Sucesso OCR", f"IP {extracted_ip} extraído da imagem!")
        else:
            pass

    def register(self):
        ip = self.ip_entry.get().strip()
        mobile_code = self.mobile_code_entry.get().strip()
        record_type = self.record_type_seg.get() 
        
        if not ip:
            messagebox.showwarning("Campo Vazio", "O campo de IP é obrigatório.")
            return

        info = get_ip_info(ip)
        country = info.get("country")

        if not country:
            dialog = PasteEnabledInputDialog(
                text="Não foi possível encontrar o país automaticamente.\nPor favor, digite o país:",
                title="País Não Encontrado"
            )
            country_input = dialog.get_input()
            
            if country_input:
                country = country_input
            else:
                messagebox.showwarning("Cancelado", "Registro cancelado. O país é necessário.")
                return

        confirm = messagebox.askyesno(
            "Confirmar Registro", 
            f"Registrar o IP {ip} para o país '{country}' como uma '{record_type}'?"
        )
        
        if confirm:
            register_ip_in_db(ip, mobile_code, country, record_type)

    def search(self):
        dialog = PasteEnabledInputDialog(
            text="Digite o endereço IP para buscar:", 
            title="Consultar IP"
        )
        ip = dialog.get_input()
        
        if ip:
            search_ip_in_db(ip.strip())