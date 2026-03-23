import os
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from docx import Document
import fitz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Paleta Moderna ────────────────────────────────────────────────
SIDEBAR_BG      = "#1A1D23"
SIDEBAR_ACCENT  = "#2D3240"
SIDEBAR_LINE    = "#353B4A"
CARD_BG         = "#FFFFFF"
BG_MAIN         = "#F3F4F6"
BG_WHITE        = "#FFFFFF"
ACCENT          = "#C5461B"
ACCENT_HOVER    = "#AF3D16"
ACCENT_LIGHT    = "#FFF1EA"
TEXT_DARK       = "#111827"
TEXT_SECONDARY  = "#4B5563"
TEXT_MUTED      = "#6B7280"
TEXT_LIGHT      = "#9CA3AF"
BORDER_COLOR    = "#E5E7EB"
HEADER_BG       = "#FFFFFF"
ROW_HOVER       = "#F9FAFB"
ROW_ALT         = "#FCFCFD"
BTN_SECONDARY   = "#F3F4F6"
BTN_SEC_HOVER   = "#E5E7EB"
BTN_SEC_TEXT    = "#374151"
SUCCESS_BG      = "#ECFDF5"
SUCCESS_TEXT    = "#065F46"
INPUT_BG        = "#F9FAFB"
INPUT_BORDER    = "#D1D5DB"

BASE_PATH = r"C:\GencoServer"

PASTAS_DISPONIVEIS = [
    "Clients", "Cotação - CTC", "Genco Various", "Inspections - QC",
    "Invoices PO - GNC", "Quotation - QT", "Samples - SMP",
    "Shipments - GNC", "Suppliers",
]

EXTENSOES_MAP = {
    "Todos": "All",
    ".pdf": ".pdf",
    ".docx": ".docx",
    ".xlsx": ".xlsx",
    ".xls": ".xls",
    ".txt": ".txt",
    ".jpg": ".jpg",
    ".png": ".png",
}

EXTENSOES_UI = list(EXTENSOES_MAP.keys())

BADGE_MAP = {
    ".pdf":  ("PDF",  "#DC2626", "#FEF2F2"),
    ".docx": ("DOCX", "#2563EB", "#EFF6FF"),
    ".xlsx": ("XLSX", "#059669", "#ECFDF5"),
    ".xls":  ("XLS",  "#059669", "#ECFDF5"),
    ".txt":  ("TXT",  "#6B7280", "#F3F4F6"),
    ".jpg":  ("IMG",  "#7C3AED", "#F5F3FF"),
    ".png":  ("IMG",  "#7C3AED", "#F5F3FF"),
    "folder": ("PASTA", "#B45309", "#FEF3C7"),
}

FONT_FAMILY = "Segoe UI"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class GencoBuscaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Genco Busca")
        self.geometry("1360x860")
        self.minsize(1180, 720)
        self.configure(fg_color=BG_MAIN)
        self.protocol("WM_DELETE_WINDOW", self._fechar)

        self.spinner_frames = []
        self.spinner_gif = None
        self.spinner_running = False
        self.spinner_anim_id = None
        self.toast_id = None
        self.fechando = False

        self.pasta_var = ctk.StringVar(value="Todas as pastas")
        self.extensao_var = ctk.StringVar(value="Todos")
        self.buscar_conteudo_var = ctk.BooleanVar(value=False)

        self.progress_label = None
        self.entrada_busca = None
        self.label_qtd = None
        self.result_scroll = None
        self.result_rows = []

        self._centralizar(820, 520)
        self._carregar_spinner()
        self._mostrar_login()

    def _centralizar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _fechar(self):
        self.fechando = True
        self._parar_spinner()
        if self.toast_id:
            try:
                self.after_cancel(self.toast_id)
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass

    def _limpar_tela(self):
        for w in self.winfo_children():
            w.destroy()

    def _carregar_spinner(self):
        caminho = os.path.join(BASE_DIR, "spinner.gif")
        if not os.path.exists(caminho):
            return
        try:
            self.spinner_gif = Image.open(caminho)
            while True:
                frame = self.spinner_gif.copy().convert("RGBA").resize((16, 16), Image.Resampling.LANCZOS)
                self.spinner_frames.append(ImageTk.PhotoImage(frame))
                self.spinner_gif.seek(self.spinner_gif.tell() + 1)
        except EOFError:
            pass
        except Exception:
            self.spinner_frames = []

    def _animar_spinner(self, ind=0):
        if self.fechando:
            return

        lbl = self.progress_label

        if self.spinner_running and self.spinner_frames and lbl and lbl.winfo_exists():
            frame = self.spinner_frames[ind]
            lbl.configure(image=frame, text="  Buscando...", fg=ACCENT)
            lbl.image = frame
            self.spinner_anim_id = self.after(90, self._animar_spinner, (ind + 1) % len(self.spinner_frames))
        else:
            if lbl and lbl.winfo_exists():
                lbl.configure(image="", text="")
                lbl.image = None

    def _iniciar_spinner(self):
        if self.spinner_running:
            return
        self.spinner_running = True
        self._animar_spinner()

    def _parar_spinner(self):
        self.spinner_running = False
        if self.spinner_anim_id:
            try:
                self.after_cancel(self.spinner_anim_id)
            except Exception:
                pass
            self.spinner_anim_id = None

        lbl = self.progress_label
        if lbl and lbl.winfo_exists():
            try:
                lbl.configure(image="", text="")
                lbl.image = None
            except Exception:
                pass

    def _mostrar_login(self):
        self._limpar_tela()
        self._centralizar(820, 520)
        self.resizable(False, False)

        container = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        container.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(container, fg_color=SIDEBAR_BG, corner_radius=0, width=300)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        sb_body = ctk.CTkFrame(sidebar, fg_color="transparent")
        sb_body.pack(fill="both", expand=True, padx=36)

        icon_outer = ctk.CTkFrame(sb_body, fg_color=ACCENT, corner_radius=16, width=52, height=52)
        icon_outer.pack(pady=(80, 0))
        icon_outer.pack_propagate(False)

        ctk.CTkLabel(
            icon_outer,
            text="G",
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkFrame(sb_body, fg_color=SIDEBAR_LINE, height=1, width=200).pack(pady=(32, 24))

        ctk.CTkLabel(
            sb_body,
            text="GENCO BUSCA",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color="white",
        ).pack()

        ctk.CTkLabel(
            sb_body,
            text="Server File Finder",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#9CA3AF",
        ).pack(pady=(6, 0))

        ctk.CTkLabel(
            sb_body,
            text="Localize documentos, cotações\ne arquivos do servidor interno.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color="#6B7280",
            justify="center",
        ).pack(pady=(20, 0))

        ctk.CTkLabel(
            sidebar,
            text="© 2026 Genco Import & Export",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            text_color="#4B5563",
        ).pack(side="bottom", pady=20)

        right = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=0)
        right.pack(side="left", fill="both", expand=True)
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(right, fg_color="transparent")
        inner.grid(row=0, column=0)

        try:
            logo_img = Image.open(os.path.join(BASE_DIR, "logo_genco_login.png"))
            logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(248, 70))
            logo_label = ctk.CTkLabel(inner, image=logo_ctk, text="", fg_color="transparent")
            logo_label.pack(pady=(0, 32))
            logo_label.image = logo_ctk
        except Exception as e:
            print("Erro logo login:", e)

        ctk.CTkLabel(
            inner,
            text="Bem-vindo ao Genco Busca",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text="Ferramenta interna de busca de documentos",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED,
        ).pack(pady=(0, 40))

        ctk.CTkButton(
            inner,
            text="Acessar  →",
            command=self._mostrar_busca,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=10,
            width=300,
            height=48,
            cursor="hand2",
        ).pack()

        ctk.CTkLabel(
            inner,
            text="v2.0  •  Acesso interno",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            text_color=TEXT_LIGHT,
        ).pack(pady=(16, 0))

    def _mostrar_busca(self):
        self._limpar_tela()
        self.resizable(True, True)
        self._centralizar(1360, 860)
        self.minsize(1180, 720)

        search_frame = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        search_frame.pack(fill="both", expand=True)
        self._search_frame = search_frame

        header = ctk.CTkFrame(search_frame, fg_color=HEADER_BG, corner_radius=0, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=28)

        logo_area = ctk.CTkFrame(header_inner, fg_color="transparent")
        logo_area.pack(side="left", pady=14)

        try:
            logo_img = Image.open(os.path.join(BASE_DIR, "logo_genco_inicio.png"))
            logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(120, 32))
            logo_label = ctk.CTkLabel(logo_area, image=logo_ctk, text="")
            logo_label.pack(side="left")
            logo_label.image = logo_ctk
        except Exception as e:
            print("Erro logo busca:", e)

        ctk.CTkLabel(
            header_inner,
            text="Server File Finder v2.0",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color=TEXT_MUTED,
        ).pack(side="right", pady=18)

        ctk.CTkFrame(search_frame, fg_color=BORDER_COLOR, height=1, corner_radius=0).pack(fill="x")

        center = ctk.CTkFrame(search_frame, fg_color=BG_MAIN, corner_radius=0)
        center.pack(fill="both", expand=True, padx=36, pady=(26, 18))
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(4, weight=1)

        title_row = ctk.CTkFrame(center, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_row,
            text="Busca de Arquivos",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(side="left")

        ctk.CTkLabel(
            center,
            text="Pesquise arquivos e pastas no servidor da Genco",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(6, 20))

        search_card = ctk.CTkFrame(
            center,
            fg_color=BG_WHITE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        search_card.grid(row=2, column=0, sticky="ew", pady=(0, 18))

        card_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        card_inner.pack(fill="x", padx=22, pady=22)
        card_inner.grid_columnconfigure(0, weight=1)

        form_row = ctk.CTkFrame(card_inner, fg_color="transparent")
        form_row.pack(fill="x", pady=(0, 16))
        form_row.grid_columnconfigure(0, weight=1)

        col_s = ctk.CTkFrame(form_row, fg_color="transparent")
        col_s.grid(row=0, column=0, sticky="ew", padx=(0, 14))
        col_s.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            col_s,
            text="TERMO DE BUSCA",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=TEXT_LIGHT,
        ).pack(anchor="w", pady=(0, 8))

        entry_wrap = ctk.CTkFrame(
            col_s,
            fg_color=BG_WHITE,
            corner_radius=12,
            border_width=1,
            border_color=INPUT_BORDER,
        height=44
        )
        entry_wrap.pack(fill="x")
        entry_wrap.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            entry_wrap,
            text="⌕",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16),
            text_color=TEXT_MUTED,
            fg_color="transparent",
            width=26
        )
        icon_label.pack(side="left", padx=(12, 4))

        self.entrada_busca = ctk.CTkEntry(
            entry_wrap,
            height=42,
            corner_radius=12,
            border_width=0,
            fg_color=BG_WHITE,
            text_color=TEXT_DARK,
            placeholder_text="Nome do arquivo ou pasta...",
            placeholder_text_color=TEXT_LIGHT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        self.entrada_busca.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.entrada_busca.bind("<Return>", lambda e: self._iniciar_busca())
        self.entrada_busca.bind("<FocusIn>", lambda e: entry_wrap.configure(border_color=INPUT_BORDER))
        self.entrada_busca.bind("<FocusOut>", lambda e: entry_wrap.configure(border_color=INPUT_BORDER))

        col_f = ctk.CTkFrame(form_row, fg_color="transparent", width=200)
        col_f.grid(row=0, column=1, sticky="w", padx=(0, 14))
        col_f.grid_propagate(False)

        ctk.CTkLabel(
            col_f,
            text="PASTA",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=TEXT_LIGHT,
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkComboBox(
            col_f,
            values=["Todas as pastas"] + PASTAS_DISPONIVEIS,
            variable=self.pasta_var,
            width=200,
            height=42,
            corner_radius=12,
            border_width=1,
            border_color=INPUT_BORDER,
            fg_color=INPUT_BG,
            button_color=INPUT_BG,
            button_hover_color=BTN_SECONDARY,
            text_color=TEXT_DARK,
            dropdown_fg_color=BG_WHITE,
            dropdown_hover_color=ROW_HOVER,
            dropdown_text_color=TEXT_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        ).pack()

        col_e = ctk.CTkFrame(form_row, fg_color="transparent", width=150)
        col_e.grid(row=0, column=2, sticky="w", padx=(0, 16))
        col_e.grid_propagate(False)

        ctk.CTkLabel(
            col_e,
            text="TIPO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=TEXT_LIGHT,
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkComboBox(
            col_e,
            values=EXTENSOES_UI,
            variable=self.extensao_var,
            width=150,
            height=42,
            corner_radius=12,
            border_width=1,
            border_color=INPUT_BORDER,
            fg_color=INPUT_BG,
            button_color=INPUT_BG,
            button_hover_color=BTN_SECONDARY,
            text_color=TEXT_DARK,
            dropdown_fg_color=BG_WHITE,
            dropdown_hover_color=ROW_HOVER,
            dropdown_text_color=TEXT_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        ).pack()

        col_b = ctk.CTkFrame(form_row, fg_color="transparent")
        col_b.grid(row=0, column=3, sticky="se")

        ctk.CTkLabel(col_b, text="", height=1).pack(pady=(0, 8))

        btns = ctk.CTkFrame(col_b, fg_color="transparent")
        btns.pack()

        ctk.CTkButton(
            btns,
            text="✕  Limpar",
            command=self._limpar,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=BTN_SECONDARY,
            hover_color=BTN_SEC_HOVER,
            text_color=BTN_SEC_TEXT,
            corner_radius=12,
            width=106,
            height=40,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns,
            text="🔍  Buscar",
            command=self._iniciar_busca,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=12,
            width=120,
            height=40,
            cursor="hand2",
        ).pack(side="left")

        ctk.CTkCheckBox(
            card_inner,
            text="  Buscar dentro do conteúdo (.pdf e .docx)",
            variable=self.buscar_conteudo_var,
            text_color=TEXT_MUTED,
            border_color=INPUT_BORDER,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=6,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        ).pack(anchor="w")

        status_bar = ctk.CTkFrame(center, fg_color="transparent", height=24)
        status_bar.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        status_bar.grid_propagate(False)

        self.progress_label = tk.Label(
            status_bar,
            text="",
            bg=BG_MAIN,
            fg=ACCENT,
            font=(FONT_FAMILY, 10),
            anchor="w",
            compound="left"
        )
        self.progress_label.pack(side="left")

        result_card = ctk.CTkFrame(
            center,
            fg_color=BG_WHITE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        result_card.grid(row=4, column=0, sticky="nsew")

        result_header = ctk.CTkFrame(result_card, fg_color=BG_WHITE, corner_radius=0, height=52)
        result_header.pack(fill="x")
        result_header.pack_propagate(False)

        ctk.CTkLabel(
            result_header,
            text="Resultados",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(side="left", padx=20, pady=14)

        self.label_qtd = ctk.CTkLabel(
            result_header,
            text="",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=TEXT_DARK,
            fg_color="#F3F4F6",
            corner_radius=14,
            padx=14,
            pady=4,
        )
        self.label_qtd.pack(side="right", padx=18, pady=10)

        ctk.CTkFrame(result_card, fg_color=BORDER_COLOR, height=1, corner_radius=0).pack(fill="x")

        self.result_scroll = ctk.CTkScrollableFrame(
            result_card,
            fg_color=BG_WHITE,
            corner_radius=0,
            scrollbar_button_color="#D1D5DB",
            scrollbar_button_hover_color="#9CA3AF",
        )
        self.result_scroll.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(search_frame, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=(4, 10))

        ctk.CTkLabel(
            footer,
            text="Genco Import & Export  •  Server File Finder  •  v2.0",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=TEXT_LIGHT,
        ).pack()

    def _limpar_resultados(self):
        for w in self.result_scroll.winfo_children():
            w.destroy()
        self.result_rows = []

    def _adicionar_linha(self, caminho, idx):
        ext = os.path.splitext(caminho)[1].lower()
        is_folder = os.path.isdir(caminho)
        row_bg = BG_WHITE if idx % 2 == 0 else ROW_ALT

        row = ctk.CTkFrame(
            self.result_scroll,
            fg_color=row_bg,
            corner_radius=0,
            height=70
        )
        row.pack(fill="x")
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=8)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        if is_folder:
            badge_text, badge_color, badge_bg = BADGE_MAP["folder"]
            icon_box = ctk.CTkFrame(left, fg_color="#F3F4F6", corner_radius=12, width=40, height=40)
            icon_box.pack(side="left", padx=(0, 14))
            icon_box.pack_propagate(False)
            ctk.CTkLabel(
                icon_box,
                text="📂",
                font=ctk.CTkFont(size=18),
                text_color="#F59E0B"
            ).place(relx=0.5, rely=0.5, anchor="center")
        else:
            badge_text, badge_color, badge_bg = BADGE_MAP.get(ext, ("FILE", "#6B7280", "#F3F4F6"))
            icon_box = ctk.CTkFrame(left, fg_color="#F3F4F6", corner_radius=12, width=40, height=40)
            icon_box.pack(side="left", padx=(0, 14))
            icon_box.pack_propagate(False)

            icon_char = "📄"
            if ext in [".xlsx", ".xls"]:
                icon_char = "📊"
            elif ext == ".pdf":
                icon_char = "📄"

            ctk.CTkLabel(
                icon_box,
                text=icon_char,
                font=ctk.CTkFont(size=16),
            ).place(relx=0.5, rely=0.5, anchor="center")

        text_frame = ctk.CTkFrame(left, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)

        nome_arquivo = os.path.basename(caminho)
        dir_path = os.path.dirname(caminho)

        ctk.CTkLabel(
            text_frame,
            text=nome_arquivo,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_DARK,
            anchor="w",
        ).pack(anchor="w", pady=(2, 2))

        ctk.CTkLabel(
            text_frame,
            text=caminho,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        right = ctk.CTkFrame(inner, fg_color="transparent", width=100)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        ctk.CTkLabel(
            right,
            text=badge_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=badge_color,
            fg_color=badge_bg,
            corner_radius=14,
            width=56,
            height=26,
        ).pack(anchor="e", pady=10)

        divider = ctk.CTkFrame(self.result_scroll, fg_color=BORDER_COLOR, height=1, corner_radius=0)
        divider.pack(fill="x")

        for w in [row, inner, left, text_frame, icon_box, right]:
            w.bind("<Double-Button-1>", lambda e, c=caminho: self._abrir(c))
            w.bind("<Button-3>", lambda e, c=caminho: self._copiar(c))

        self.result_rows.append((row, divider))

    def _mostrar_resultados(self, resultados):
        self._limpar_resultados()
        self._parar_spinner()

        if not resultados:
            messagebox.showinfo("Aviso", "Nenhum arquivo encontrado.")
            self.label_qtd.configure(text="")
            return

        for idx, caminho in enumerate(resultados):
            self._adicionar_linha(caminho, idx)

        texto = f"{len(resultados)} arquivo(s) encontrado(s)"
        self.label_qtd.configure(text=texto)

    def _ler_docx(self, caminho):
        try:
            doc = Document(caminho)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return ""

    def _ler_pdf(self, caminho):
        try:
            with fitz.open(caminho) as doc:
                return "\n".join(page.get_text() for page in doc)
        except Exception:
            return ""

    def _buscar_em(self, diretorio_raiz, termo):
        buscar_conteudo = self.buscar_conteudo_var.get()
        extensao_ui = self.extensao_var.get()
        extensao_escolhida = EXTENSOES_MAP.get(extensao_ui, "All")

        exatos, relacionados = [], []
        extensoes_ok = [".pdf", ".docx", ".xlsx", ".xls", ".txt", ".jpg", ".png"]
        limite = 100

        if not os.path.exists(diretorio_raiz):
            return []

        for raiz, pastas, arquivos in os.walk(diretorio_raiz):
            try:
                for pasta in pastas:
                    nome = pasta.lower()
                    c = os.path.join(raiz, pasta)
                    if nome == termo:
                        exatos.append(c)
                    elif termo in nome:
                        relacionados.append(c)

                for arquivo in arquivos:
                    if len(exatos) + len(relacionados) >= limite:
                        break

                    nome_arq, ext = os.path.splitext(arquivo)
                    ext = ext.lower()

                    if ext not in extensoes_ok:
                        continue

                    if extensao_escolhida != "All" and ext != extensao_escolhida:
                        continue

                    c = os.path.join(raiz, arquivo)
                    tem_conteudo = False

                    if buscar_conteudo:
                        if ext == ".pdf":
                            tem_conteudo = termo in self._ler_pdf(c).lower()
                        elif ext == ".docx":
                            tem_conteudo = termo in self._ler_docx(c).lower()

                    if nome_arq.lower() == termo or tem_conteudo:
                        exatos.append(c)
                    elif termo in nome_arq.lower():
                        relacionados.append(c)
            except (PermissionError, Exception):
                pass

        return exatos + relacionados

    def _thread_pasta(self, termo, pasta):
        resultados = self._buscar_em(os.path.join(BASE_PATH, pasta), termo)
        self.after(0, lambda: self._mostrar_resultados(resultados))

    def _thread_todas(self, termo):
        resultados = []
        for p in PASTAS_DISPONIVEIS:
            resultados += self._buscar_em(os.path.join(BASE_PATH, p), termo)
        self.after(0, lambda: self._mostrar_resultados(resultados))

    def _iniciar_busca(self):
        termo = self.entrada_busca.get().strip().lower()
        if not termo:
            messagebox.showwarning("Atenção", "Digite o nome do arquivo ou pasta.")
            return

        pasta = self.pasta_var.get().strip()
        self._iniciar_spinner()

        if not pasta or pasta == "Todas as pastas":
            threading.Thread(target=self._thread_todas, args=(termo,), daemon=True).start()
        else:
            threading.Thread(target=self._thread_pasta, args=(termo, pasta), daemon=True).start()

    def _limpar(self):
        self._parar_spinner()
        self.entrada_busca.delete(0, "end")
        self.label_qtd.configure(text="")
        self.pasta_var.set("Todas as pastas")
        self.extensao_var.set("Todos")
        self.buscar_conteudo_var.set(False)
        self._limpar_resultados()

    def _abrir(self, caminho):
        try:
            os.startfile(caminho)
        except Exception:
            pass

    def _copiar(self, caminho):
        try:
            self.clipboard_clear()
            self.clipboard_append(caminho)

            aviso = ctk.CTkLabel(
                self._search_frame,
                text="  ✓  Caminho copiado  ",
                fg_color=SUCCESS_BG,
                text_color=SUCCESS_TEXT,
                corner_radius=10,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            )
            aviso.place(relx=1.0, rely=1.0, anchor="se", x=-24, y=-20)

            if self.toast_id:
                try:
                    self.after_cancel(self.toast_id)
                except Exception:
                    pass

            self.toast_id = self.after(1800, lambda: aviso.destroy() if aviso.winfo_exists() else None)
        except Exception:
            pass


if __name__ == "__main__":
    app = GencoBuscaApp()
    app.mainloop()