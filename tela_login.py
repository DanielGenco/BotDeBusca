import os
import customtkinter as ctk
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SIDEBAR_BG   = "#7B2320"
CARD_BG      = "#FFFFFF"
TEXT_DARK    = "#1A1A2E"
TEXT_MUTED   = "#8A9BAE"
ACCENT       = "#7B2320"
BTN_HOVER    = "#9E3330"
SIDEBAR_LINE = "#A04040"

ctk.set_appearance_mode("light")


def mostrar_login():
    return_val = [None]
    fechando = [False]

    win = ctk.CTk()
    win.title("Genco Busca")
    win.geometry("780x490")
    win.resizable(False, False)

    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - 390
    y = (win.winfo_screenheight() // 2) - 245
    win.geometry(f"780x490+{x}+{y}")

    def fechar_login(resultado=None):
        if fechando[0]:
            return

        fechando[0] = True
        return_val[0] = resultado

        try:
            win.withdraw()
        except:
            pass

        try:
            win.quit()
        except:
            pass

        try:
            win.after(50, lambda: destruir_janela())
        except:
            destruir_janela()

    def destruir_janela():
        try:
            if win.winfo_exists():
                win.destroy()
        except:
            pass

    win.grid_columnconfigure(0, weight=0)
    win.grid_columnconfigure(1, weight=1)
    win.grid_rowconfigure(0, weight=1)

    sidebar = ctk.CTkFrame(win, fg_color=SIDEBAR_BG, corner_radius=0, width=270)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)
    sidebar.grid_rowconfigure(0, weight=1)
    sidebar.grid_rowconfigure(1, weight=0)
    sidebar.grid_columnconfigure(0, weight=1)

    sb_body = ctk.CTkFrame(sidebar, fg_color="transparent")
    sb_body.grid(row=0, column=0, padx=32, sticky="ew")

    icon_outer = ctk.CTkFrame(sb_body, fg_color="#A04040", corner_radius=28, width=56, height=56)
    icon_outer.pack(pady=(72, 0))
    icon_outer.pack_propagate(False)

    ctk.CTkLabel(
        icon_outer,
        text="🔍",
        font=ctk.CTkFont(size=24),
        fg_color="transparent",
        text_color="white"
    ).place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkFrame(sb_body, fg_color=SIDEBAR_LINE, height=1, width=180).pack(pady=(28, 22))

    ctk.CTkLabel(
        sb_body,
        text="Server File Finder",
        font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
        text_color="white",
        fg_color="transparent"
    ).pack()

    ctk.CTkLabel(
        sb_body,
        text="Internal document search tool",
        font=ctk.CTkFont(family="Segoe UI", size=9),
        text_color="#C89090",
        fg_color="transparent",
        justify="center"
    ).pack(pady=(7, 0))

    ctk.CTkLabel(
        sidebar,
        text="© 2026 Genco I&E",
        font=ctk.CTkFont(family="Segoe UI", size=8),
        text_color="#B07070",
        fg_color="transparent"
    ).grid(row=1, column=0, pady=18)

    card = ctk.CTkFrame(win, fg_color=CARD_BG, corner_radius=0)
    card.grid(row=0, column=1, sticky="nsew")
    card.grid_rowconfigure(0, weight=1)
    card.grid_columnconfigure(0, weight=1)

    inner = ctk.CTkFrame(card, fg_color="transparent")
    inner.grid(row=0, column=0)

    try:
        logo_img = Image.open(os.path.join(BASE_DIR, "logo_genco_login.png"))
        logo_ctk = ctk.CTkImage(light_image=logo_img, size=(248, 70))
        ctk.CTkLabel(
            inner,
            image=logo_ctk,
            text="",
            fg_color="transparent"
        ).pack(pady=(0, 28))
    except Exception as e:
        print("Erro ao carregar logo:", e)

    ctk.CTkLabel(
        inner,
        text="Welcome to Genco Busca",
        font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        text_color=TEXT_DARK,
        fg_color="transparent"
    ).pack(pady=(0, 8))

    ctk.CTkLabel(
        inner,
        text="Internal document search tool for Genco's server",
        font=ctk.CTkFont(family="Segoe UI", size=10),
        text_color=TEXT_MUTED,
        fg_color="transparent"
    ).pack(pady=(0, 36))

    def acessar():
        fechar_login(True)

    ctk.CTkButton(
        inner,
        text="Access",
        command=acessar,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        fg_color=ACCENT,
        hover_color=BTN_HOVER,
        text_color="white",
        corner_radius=8,
        width=290,
        height=46,
        cursor="hand2"
    ).pack()

    win.protocol("WM_DELETE_WINDOW", lambda: fechar_login(None))
    win.mainloop()

    try:
        destruir_janela()
    except:
        pass

    return return_val[0]


if __name__ == "__main__":
    mostrar_login()