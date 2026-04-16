import os
import sys
import json
import subprocess
import tempfile
import threading
import urllib.request
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from docx import Document
import fitz
import time
import logging
from datetime import datetime

# ── Compressor module ─────────────────────────────────────────────
from modules.compressor import (
    get_file_type, get_file_size_str, compress_image, compress_video,
    compress_batch, scan_folder,
    estimate_image_size, estimate_video_size, estimate_batch_size,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, QUALITY_PRESETS,
)
import windnd

# ── BASE_DIR: _MEIPASS quando empacotado (PyInstaller), raiz do projeto em dev
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    APP_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    APP_DIR = BASE_DIR

CONFIG_FILE = os.path.join(APP_DIR, "config", "config.json")
LOG_FILE = os.path.join(APP_DIR, "genco_search.log")

VERSION = "1.0.6"
GITHUB_REPO = "DanielGenco/BotDeBusca"

# ── Logging Setup ──────────────────────────────────────────────
def _setup_logging():
    """Configure logging profissional com arquivo e console"""
    try:
        log_format = '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logging.info("=" * 60)
        logging.info(f"Genco Search v{VERSION} iniciado")
        logging.info("=" * 60)
    except Exception as e:
        print(f"Erro ao configurar logging: {e}")

_setup_logging()

# ── Palette - Light Theme ──────────────────────────────────────
PALETTE_LIGHT = {
    "ACCENT":          "#7B2320",
    "ACCENT_HOVER":    "#601A18",
    "ACCENT_LIGHT":    "#FEF2F2",
    "ACCENT_MEDIUM":   "#F5C6C5",
    "BG_MAIN":         "#F0F2F5",
    "BG_WHITE":        "#FFFFFF",
    "CARD_BG":         "#FFFFFF",
    "TEXT_DARK":       "#111827",
    "TEXT_SECONDARY":  "#374151",
    "TEXT_MUTED":      "#6B7280",
    "TEXT_LIGHT":      "#9CA3AF",
    "BORDER_COLOR":    "#E5E7EB",
    "BORDER_LIGHT":    "#F3F4F6",
    "HEADER_BG":       "#FFFFFF",
    "ROW_HOVER":       "#FAFBFF",
    "ROW_ALT":         "#FCFCFD",
    "BTN_SECONDARY":   "#F3F4F6",
    "BTN_SEC_HOVER":   "#E5E7EB",
    "BTN_SEC_TEXT":    "#374151",
    "SUCCESS_BG":      "#ECFDF5",
    "SUCCESS_TEXT":    "#065F46",
    "INPUT_BG":        "#FFFFFF",
    "INPUT_BORDER":    "#D1D5DB",
    "INPUT_FOCUS":     "#7B2320",
    "COL_HEADER_BG":   "#F8F9FB",
    "SIDEBAR_BG":      "#7B2320",
    "SIDEBAR_LINE":    "#9B3330",
    "SHADOW_COLOR":    "#E2E4E9",
}

# ── Palette - Dark Theme ──────────────────────────────────────
PALETTE_DARK = {
    "ACCENT":          "#EF4444",
    "ACCENT_HOVER":    "#F87171",
    "ACCENT_LIGHT":    "#7F1D1D",
    "ACCENT_MEDIUM":   "#991B1B",
    "BG_MAIN":         "#0F172A",
    "BG_WHITE":        "#1E293B",
    "CARD_BG":         "#1E293B",
    "TEXT_DARK":       "#F1F5F9",
    "TEXT_SECONDARY":  "#CBD5E1",
    "TEXT_MUTED":      "#94A3B8",
    "TEXT_LIGHT":      "#64748B",
    "BORDER_COLOR":    "#334155",
    "BORDER_LIGHT":    "#475569",
    "HEADER_BG":       "#1E293B",
    "ROW_HOVER":       "#334155",
    "ROW_ALT":         "#1E293B",
    "BTN_SECONDARY":   "#334155",
    "BTN_SEC_HOVER":   "#475569",
    "BTN_SEC_TEXT":    "#E2E8F0",
    "SUCCESS_BG":      "#064E3B",
    "SUCCESS_TEXT":    "#86EFAC",
    "INPUT_BG":        "#0F172A",
    "INPUT_BORDER":    "#334155",
    "INPUT_FOCUS":     "#EF4444",
    "COL_HEADER_BG":   "#1E293B",
    "SIDEBAR_BG":      "#7B2320",
    "SIDEBAR_LINE":    "#9B3330",
    "SHADOW_COLOR":    "#0F172A",
}

# ── Default colors (ajustadas dinamicamente) ────────────────────
ACCENT          = "#7B2320"
ACCENT_HOVER    = "#601A18"
ACCENT_LIGHT    = "#FEF2F2"
ACCENT_MEDIUM   = "#F5C6C5"
BG_MAIN         = "#F0F2F5"
BG_WHITE        = "#FFFFFF"
CARD_BG         = "#FFFFFF"
TEXT_DARK       = "#111827"
TEXT_SECONDARY  = "#374151"
TEXT_MUTED      = "#6B7280"
TEXT_LIGHT      = "#9CA3AF"
BORDER_COLOR    = "#E5E7EB"
BORDER_LIGHT    = "#F3F4F6"
HEADER_BG       = "#FFFFFF"
ROW_HOVER       = "#FAFBFF"
ROW_ALT         = "#FCFCFD"
BTN_SECONDARY   = "#F3F4F6"
BTN_SEC_HOVER   = "#E5E7EB"
BTN_SEC_TEXT    = "#374151"
SUCCESS_BG      = "#ECFDF5"
SUCCESS_TEXT    = "#065F46"
INPUT_BG        = "#FFFFFF"
INPUT_BORDER    = "#D1D5DB"
INPUT_FOCUS     = "#7B2320"
COL_HEADER_BG   = "#F8F9FB"
SIDEBAR_BG      = "#7B2320"
SIDEBAR_LINE    = "#9B3330"
SHADOW_COLOR    = "#E2E4E9"

# ── Spacing System ─────────────────────────────────────────────
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_2XL = 32
SPACING_3XL = 48

CORNER_RADIUS_SM = 8
CORNER_RADIUS_MD = 10
CORNER_RADIUS_LG = 12
CORNER_RADIUS_XL = 16

BASE_PATHS = [
    r"C:\GencoServer", r"C:\Genco Server",
    r"D:\GencoServer", r"D:\Genco Server",
    r"Z:\GencoServer", r"Z:\Genco Server",
]

AVAILABLE_FOLDERS = [
    "After-Sales-Ticket - AST", "Audit", "Clients", "Cotação - CTC", "Finance Genco", "Genco IT", "Genco Various", "Inspections - QC",
    "Invoices PO - GNC", "Marketing", "Office BR", "Office CH", "Quotation - QT", "Samples - SMP",
    "Shipments - GNC", "Suppliers",
]

EXTENSIONS_MAP = {
    "All":    "All",
    ".pdf":   ".pdf",
    ".docx":  ".docx",
    ".xlsx":  ".xlsx",
    ".xls":   ".xls",
    ".txt":   ".txt",
    ".jpg":   ".jpg",
    ".png":   ".png",
}

EXTENSIONS_UI = list(EXTENSIONS_MAP.keys())

BADGE_MAP = {
    ".pdf":   ("PDF",    "#DC2626", "#FEF2F2"),
    ".docx":  ("DOCX",   "#2563EB", "#EFF6FF"),
    ".xlsx":  ("XLSX",   "#059669", "#ECFDF5"),
    ".xls":   ("XLS",    "#059669", "#ECFDF5"),
    ".txt":   ("TXT",    "#6B7280", "#F3F4F6"),
    ".jpg":   ("IMG",    "#7C3AED", "#F5F3FF"),
    ".png":   ("IMG",    "#7C3AED", "#F5F3FF"),
    "folder": ("FOLDER", "#B45309", "#FEF3C7"),
}

ICON_MAP = {
    ".pdf":   ("📕", "#FEF2F2", "#DC2626"),
    ".docx":  ("📄", "#EFF6FF", "#2563EB"),
    ".xlsx":  ("📊", "#ECFDF5", "#059669"),
    ".xls":   ("📊", "#ECFDF5", "#059669"),
    ".txt":   ("📝", "#F3F4F6", "#6B7280"),
    ".jpg":   ("🖼", "#F5F3FF", "#7C3AED"),
    ".png":   ("🖼", "#F5F3FF", "#7C3AED"),
    "folder": ("📁", "#FEF3C7", "#B45309"),
}

FONT_FAMILY = "Segoe UI"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class GencoSearchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        try:
            self.withdraw()
            self.title("Genco Search")
            self.minsize(1180, 720)
            self.protocol("WM_DELETE_WINDOW", self._close)
            
            # ── Theme system
            self.current_theme = "light"  # "light" ou "dark"
            self._load_config()
            self._apply_theme(self.current_theme)

            self.configure(fg_color=BG_MAIN)

            self.spinner_frames = []
            self.spinner_gif = None
            self.spinner_running = False
            self.spinner_anim_id = None
            self._spinner_frame = None
            self._spinner_label = None
            self.toast_id = None
            self.closing = False
            self._fade_anim_id = None
            self._theme_toggle = None

            self.folder_var = ctk.StringVar(value="All folders")
            self.extension_var = ctk.StringVar(value="All")
            self.search_content_var = ctk.BooleanVar(value=False)

            self.search_entry = None
            self.count_label = None
            self.count_number_label = None
            self.result_scroll = None
            self.result_rows = []
            self._search_frame = None
            self._empty_state_frame = None

            # Compressor state
            self._comp_file_path = None
            self._comp_file_type = None
            self._comp_batch_folder = None
            self._comp_batch_files = []
            self._comp_progress_bar = None
            self._comp_progress_label = None
            self._comp_result_frame = None
            self._comp_thread = None
            self._comp_cancel_event = None

            self._load_spinner()
            self._show_login()
            threading.Thread(target=self._check_for_updates, daemon=True).start()
            
            logging.info("Aplicação inicializada com sucesso")
        except Exception as e:
            logging.error(f"Erro ao inicializar aplicação: {e}", exc_info=True)
            self._show_error("Initialization Error", f"Failed to initialize application:\n{e}")
            self.destroy()

    # ── Configuration Management ───────────────────────────────

    def _load_config(self):
        """Carrega configurações do arquivo config.json"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_theme = config.get("theme", "light")
                    logging.info(f"Configurações carregadas: tema {self.current_theme}")
            else:
                self._save_config()
        except Exception as e:
            logging.warning(f"Erro ao carregar config: {e}, usando padrão")
            self.current_theme = "light"

    def _save_config(self):
        """Salva configurações no arquivo config.json"""
        try:
            # Cria a pasta config se não existir
            config_dir = os.path.dirname(CONFIG_FILE)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            config = {"theme": self.current_theme}
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logging.info(f"Configurações salvas: tema {self.current_theme}")
        except Exception as e:
            logging.error(f"Erro ao salvar config: {e}")

    def _apply_theme(self, theme_name):
        """Aplica tema (light/dark) atualizando variáveis globais"""
        global ACCENT, ACCENT_HOVER, ACCENT_LIGHT, ACCENT_MEDIUM, BG_MAIN, BG_WHITE
        global CARD_BG, TEXT_DARK, TEXT_SECONDARY, TEXT_MUTED, TEXT_LIGHT, BORDER_COLOR
        global BORDER_LIGHT, HEADER_BG, ROW_HOVER, ROW_ALT, BTN_SECONDARY, BTN_SEC_HOVER
        global BTN_SEC_TEXT, SUCCESS_BG, SUCCESS_TEXT, INPUT_BG, INPUT_BORDER, INPUT_FOCUS
        global COL_HEADER_BG, SIDEBAR_BG, SIDEBAR_LINE, SHADOW_COLOR
        
        try:
            palette = PALETTE_DARK if theme_name == "dark" else PALETTE_LIGHT
            
            ACCENT = palette["ACCENT"]
            ACCENT_HOVER = palette["ACCENT_HOVER"]
            ACCENT_LIGHT = palette["ACCENT_LIGHT"]
            ACCENT_MEDIUM = palette["ACCENT_MEDIUM"]
            BG_MAIN = palette["BG_MAIN"]
            BG_WHITE = palette["BG_WHITE"]
            CARD_BG = palette["CARD_BG"]
            TEXT_DARK = palette["TEXT_DARK"]
            TEXT_SECONDARY = palette["TEXT_SECONDARY"]
            TEXT_MUTED = palette["TEXT_MUTED"]
            TEXT_LIGHT = palette["TEXT_LIGHT"]
            BORDER_COLOR = palette["BORDER_COLOR"]
            BORDER_LIGHT = palette["BORDER_LIGHT"]
            HEADER_BG = palette["HEADER_BG"]
            ROW_HOVER = palette["ROW_HOVER"]
            ROW_ALT = palette["ROW_ALT"]
            BTN_SECONDARY = palette["BTN_SECONDARY"]
            BTN_SEC_HOVER = palette["BTN_SEC_HOVER"]
            BTN_SEC_TEXT = palette["BTN_SEC_TEXT"]
            SUCCESS_BG = palette["SUCCESS_BG"]
            SUCCESS_TEXT = palette["SUCCESS_TEXT"]
            INPUT_BG = palette["INPUT_BG"]
            INPUT_BORDER = palette["INPUT_BORDER"]
            INPUT_FOCUS = palette["INPUT_FOCUS"]
            COL_HEADER_BG = palette["COL_HEADER_BG"]
            SIDEBAR_BG = palette["SIDEBAR_BG"]
            SIDEBAR_LINE = palette["SIDEBAR_LINE"]
            SHADOW_COLOR = palette["SHADOW_COLOR"]
            
            self.current_theme = theme_name
            mode = "dark" if theme_name == "dark" else "light"
            ctk.set_appearance_mode(mode)
            logging.info(f"Tema '{theme_name}' aplicado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao aplicar tema: {e}", exc_info=True)

    def _toggle_theme(self):
        """Alterna entre light e dark mode"""
        try:
            new_theme = "dark" if self.current_theme == "light" else "light"
            self._apply_theme(new_theme)
            self._save_config()

            # Refaz a tela atual para atualizar cores
            if hasattr(self, '_comp_on_screen') and self._comp_on_screen:
                self._show_compressor()
            elif hasattr(self, '_search_frame') and self._search_frame:
                self._show_search()

            logging.info(f"Tema alterado para: {new_theme}")
        except Exception as e:
            logging.error(f"Erro ao alternar tema: {e}", exc_info=True)
            self._show_error("Theme Error", f"Failed to change theme:\n{e}")

    # ── Error Handling ─────────────────────────────────────────

    def _show_error(self, title, message):
        """Mostra erro em messagebox com log automático"""
        logging.error(f"{title}: {message}")
        try:
            messagebox.showerror(title, message)
        except Exception as e:
            logging.error(f"Erro ao exibir messagebox: {e}")

    def _show_warning(self, title, message):
        """Mostra aviso em messagebox com log automático"""
        logging.warning(f"{title}: {message}")
        try:
            messagebox.showwarning(title, message)
        except Exception as e:
            logging.error(f"Erro ao exibir messagebox: {e}")

    # ── Utilities ────────────────────────────────────────────────

    def _fade_in(self, widget, duration_ms=300, steps=20):
        """Fade-in animation for widgets"""
        if self.closing:
            return
                
        widget.configure(fg_color=BG_MAIN)
        widget.pack(fill="both", expand=True)
        self.update_idletasks()
        
        start_alpha = 0
        step_delay = max(10, duration_ms // steps)
        
        def animate(step=0):
            if self.closing or not widget.winfo_exists():
                return
            alpha = min(step / steps, 1.0)
            step += 1
            if step <= steps:
                self._fade_anim_id = self.after(step_delay, lambda: animate(step))

        animate()

    def _fade_out(self, widget, duration_ms=200, callback=None):
        """Fade-out animation for widgets (optional callback after completion)"""
        if self.closing:
            return
        
        step_delay = max(10, duration_ms // 15)
        
        def complete():
            try:
                if widget.winfo_exists():
                    widget.pack_forget()
            except Exception:
                pass
            if callback:
                callback()
        
        self.after(duration_ms, complete)

    def _center_window(self, w, h):
        self.geometry(f"{w}x{h}")
        self.update_idletasks()
        actual_w = self.winfo_width()
        actual_h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - actual_w) // 2)
        y = max(0, (sh - actual_h) // 2)
        self.geometry(f"+{x}+{y}")
        self.update_idletasks()
        self.deiconify()
        self.lift()

    def _close(self):
        self.closing = True
        self._stop_spinner()
        if self._fade_anim_id:
            try:
                self.after_cancel(self._fade_anim_id)
            except Exception:
                pass
            self._fade_anim_id = None
        if self.toast_id:
            try:
                self.after_cancel(self.toast_id)
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass

    def _clear_screen(self):
        for w in self.winfo_children():
            w.destroy()

    def _load_spinner(self):
        path = os.path.join(BASE_DIR, "assets", "lupapesquisa.gif")
        if not os.path.exists(path):
            logging.warning(f"Spinner GIF não encontrado: {path}")
            return
        try:
            self.spinner_gif = Image.open(path)
            while True:
                frame = self.spinner_gif.copy().convert("RGBA").resize((40, 40), Image.Resampling.LANCZOS)
                self.spinner_frames.append(ImageTk.PhotoImage(frame))
                self.spinner_gif.seek(self.spinner_gif.tell() + 1)
        except EOFError:
            logging.info("Spinner GIF carregado com sucesso")
        except Exception as e:
            logging.error(f"Erro ao carregar spinner: {e}", exc_info=True)
            self.spinner_frames = []

    def _animate_spinner(self, ind=0):
        if self.closing:
            return
        if self.spinner_running and self.spinner_frames and self._spinner_label and self._spinner_label.winfo_exists():
            frame = self.spinner_frames[ind]
            self._spinner_label.configure(image=frame)
            self._spinner_label.image = frame
            self.spinner_anim_id = self.after(90, self._animate_spinner, (ind + 1) % len(self.spinner_frames))

    def _start_spinner(self):
        if self.spinner_running:
            return
        self.spinner_running = True
        self._clear_results()
        self._spinner_frame = ctk.CTkFrame(self.result_scroll, fg_color="transparent")
        self._spinner_frame.pack(expand=True, pady=48)

        row = ctk.CTkFrame(self._spinner_frame, fg_color="transparent")
        row.pack()

        ctk.CTkLabel(
            row,
            text="Searching...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 8))

        self._spinner_label = tk.Label(row, bg=BG_WHITE, bd=0)
        self._spinner_label.pack(side="left")

        self._animate_spinner()

    def _stop_spinner(self):
        self.spinner_running = False
        if self.spinner_anim_id:
            try:
                self.after_cancel(self.spinner_anim_id)
            except Exception:
                pass
            self.spinner_anim_id = None
        if self._spinner_frame and self._spinner_frame.winfo_exists():
            self._spinner_frame.destroy()
        self._spinner_frame = None
        self._spinner_label = None

    # ── Login Screen ─────────────────────────────────────────────

    def _show_login(self):
        self._clear_screen()
        self.resizable(False, False)

        container = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        container.pack(fill="both", expand=True)

        # Left sidebar
        sidebar = ctk.CTkFrame(container, fg_color=SIDEBAR_BG, corner_radius=0, width=300)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        sb_body = ctk.CTkFrame(sidebar, fg_color="transparent")
        sb_body.pack(fill="both", expand=True, padx=SPACING_2XL)

        ctk.CTkFrame(sb_body, fg_color=SIDEBAR_LINE, height=1, width=220).pack(pady=(SPACING_2XL, SPACING_LG))

        title_block = ctk.CTkFrame(sb_body, fg_color="transparent")
        title_block.pack(pady=(0, 0))

        ctk.CTkLabel(
            title_block,
            text="GENCO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=40, weight="bold"),
            text_color="white",
        ).pack()

        busca_row = ctk.CTkFrame(title_block, fg_color="transparent")
        busca_row.pack()

        ctk.CTkLabel(
            busca_row,
            text="SEARCH",
            font=ctk.CTkFont(family=FONT_FAMILY, size=40, weight="bold"),
            text_color="white",
        ).pack(side="left")

        try:
            lupa_img = Image.open(os.path.join(BASE_DIR, "assets", "lupa_tela_inicial.png"))
            lupa_ctk = ctk.CTkImage(light_image=lupa_img, dark_image=lupa_img, size=(38, 38))
            lupa_label = ctk.CTkLabel(busca_row, image=lupa_ctk, text="", fg_color="transparent")
            lupa_label.pack(side="left", padx=(SPACING_MD, 0), pady=(SPACING_SM, 0))
            lupa_label.image = lupa_ctk
        except Exception as e:
            print("Erro ao carregar lupa:", e)

        ctk.CTkLabel(
            sb_body,
            text="Server File Finder",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16),
            text_color="#BABFCE",
        ).pack(pady=(120, 0))

        ctk.CTkLabel(
            sb_body,
            text="Find documents, quotations,\nand files from the internal server.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color="#BABFCE",
            justify="center",
        ).pack(pady=(SPACING_LG, 0))

        ctk.CTkLabel(
            sidebar,
            text="© 2026 Genco Import & Export",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#BABFCE",
        ).pack(side="bottom", pady=SPACING_LG)
            
        # Right area
        right = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=0)
        right.pack(side="left", fill="both", expand=True)
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(right, fg_color="transparent")
        inner.grid(row=0, column=0)

        try:
            logo_img = Image.open(os.path.join(BASE_DIR, "assets", "icon.png"))
            logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(290, 290))
            logo_label = ctk.CTkLabel(inner, image=logo_ctk, text="", fg_color="transparent")
            logo_label.pack(pady=(0, SPACING_2XL))
            logo_label.image = logo_ctk
        except Exception as e:
            print("Login logo error:", e)

        ctk.CTkLabel(
            inner,
            text="Welcome to Genco Search",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(pady=(0, SPACING_SM))

        ctk.CTkLabel(
            inner,
            text="Internal tools for the Genco team",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_MUTED,
        ).pack(pady=(0, SPACING_2XL))

        # Buttons row
        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(pady=(SPACING_LG, 0))

        ctk.CTkButton(
            btn_row,
            text="File and Folder Search",
            command=self._show_search,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=CORNER_RADIUS_LG,
            width=230,
            height=48,
            cursor="hand2",
        ).pack(side="left", padx=(0, SPACING_MD))

        ctk.CTkButton(
            btn_row,
            text="Compressor",
            command=self._show_compressor,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=CORNER_RADIUS_LG,
            width=230,
            height=48,
            cursor="hand2",
        ).pack(side="left")

        ctk.CTkLabel(
            inner,
            text=f"v{VERSION} •  Internal access",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_LIGHT,
        ).pack(pady=(SPACING_3XL, 0))

        self.after(100, lambda: self._center_window(820, 520))

    # ── Search Screen (Redesigned) ───────────────────────────────

    def _show_search(self):
        self._clear_screen()
        self._comp_on_screen = False
        self.resizable(True, True)
        self._center_window(1360, 860)
        self.minsize(1180, 720)
        self.state("zoomed")

        search_frame = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        search_frame.pack(fill="both", expand=True)
        self._search_frame = search_frame

        # ── Header ────────────────────────────────────────────────
        header_shadow = ctk.CTkFrame(search_frame, fg_color=SHADOW_COLOR, corner_radius=0, height=1)
        header = ctk.CTkFrame(search_frame, fg_color=HEADER_BG, corner_radius=0, height=66)
        header.pack(fill="x")
        header.pack_propagate(False)
        header_shadow.pack(fill="x")

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=SPACING_2XL)

        # Logo area
        logo_area = ctk.CTkFrame(header_inner, fg_color="transparent")
        logo_area.pack(side="left")

        try:
            logo_img = Image.open(os.path.join(BASE_DIR, "assets", "icon.png"))
            logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(50, 50))
            logo_label = ctk.CTkLabel(logo_area, image=logo_ctk, text="")
            logo_label.pack(side="left", pady=SPACING_LG)
            logo_label.image = logo_ctk
        except Exception:
            icon_box = ctk.CTkFrame(logo_area, fg_color=ACCENT, corner_radius=CORNER_RADIUS_MD, width=36, height=36)
            icon_box.pack(side="left", pady=SPACING_LG)
            icon_box.pack_propagate(False)
            ctk.CTkLabel(
                icon_box, text="G",
                font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
                text_color="white",
            ).place(relx=0.5, rely=0.5, anchor="center")

            txt_frame = ctk.CTkFrame(logo_area, fg_color="transparent")
            txt_frame.pack(side="left", padx=(SPACING_MD, 0), pady=SPACING_LG)
            ctk.CTkLabel(
                txt_frame, text="GENCO",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                text_color=TEXT_DARK,
            ).pack(anchor="w")
            ctk.CTkLabel(
                txt_frame, text="Import & Export",
                font=ctk.CTkFont(family=FONT_FAMILY, size=9),
                text_color=TEXT_MUTED,
            ).pack(anchor="w")

        # Vertical separator in the header
        ctk.CTkFrame(
            header_inner, fg_color=BORDER_COLOR,
            width=1, height=28,
        ).pack(side="left", padx=SPACING_LG, pady=SPACING_LG)

        # ── Navigation tabs ───────────────────────────────────────
        nav_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        nav_frame.pack(side="left", fill="y")

        # Active tab — Search
        ctk.CTkButton(
            nav_frame, text="Search",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=ACCENT_LIGHT,
            hover_color=ACCENT_LIGHT,
            text_color=ACCENT,
            corner_radius=CORNER_RADIUS_SM,
            width=80, height=32,
        ).pack(side="left", pady=SPACING_LG)

        ctk.CTkButton(
            nav_frame, text="Compressor",
            command=self._show_compressor,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color="transparent",
            hover_color=ACCENT_LIGHT,
            text_color=TEXT_MUTED,
            corner_radius=CORNER_RADIUS_SM,
            width=100, height=32, cursor="hand2",
        ).pack(side="left", padx=(SPACING_SM, 0), pady=SPACING_LG)

        # Theme toggle + Version pill on the right
        right_area = ctk.CTkFrame(header_inner, fg_color="transparent")
        right_area.pack(side="right", fill="y")

        # Theme toggle button
        theme_icon = "☀" if self.current_theme == "light" else "🌙"
        self._theme_toggle = ctk.CTkButton(
            right_area,
            text=theme_icon,
            command=self._toggle_theme,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            fg_color="transparent",
            hover_color=ACCENT_LIGHT,
            text_color=ACCENT,
            width=32,
            height=32,
            corner_radius=CORNER_RADIUS_MD,
            cursor="hand2",
        )
        self._theme_toggle.pack(side="right", padx=(SPACING_SM, SPACING_MD), pady=SPACING_LG)

        # Version pill on the right
        pill = ctk.CTkFrame(right_area, fg_color="#F0FDF4", corner_radius=20, border_width=1, border_color="#BBF7D0")
        pill.pack(side="right", pady=SPACING_LG, padx=(0, SPACING_SM))
        pill_inner = ctk.CTkFrame(pill, fg_color="transparent")
        pill_inner.pack(padx=SPACING_SM, pady=SPACING_XS)

        dot = ctk.CTkFrame(pill_inner, fg_color="#10B981", corner_radius=4, width=7, height=7)
        dot.pack(side="left", padx=(0, SPACING_SM))
        dot.pack_propagate(False)
        ctk.CTkLabel(
            pill_inner,
            text="Server File Finder  v1.0.6",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color="#065F46",
        ).pack(side="left")

        # ── Main area ─────────────────────────────────────────────
        main = ctk.CTkFrame(search_frame, fg_color="transparent", corner_radius=0)
        main.pack(fill="both", expand=True, padx=SPACING_2XL, pady=(SPACING_LG, SPACING_SM))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # ── Page title ────────────────────────────────────────────
        title_row = ctk.CTkFrame(main, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, SPACING_LG))

        accent_bar = ctk.CTkFrame(title_row, fg_color=ACCENT, width=4, height=36, corner_radius=2)
        accent_bar.pack(side="left", padx=(0, SPACING_MD))
        accent_bar.pack_propagate(False)

        title_text = ctk.CTkFrame(title_row, fg_color="transparent")
        title_text.pack(side="left")

        ctk.CTkLabel(
            title_text,
            text="File Search",
            font=ctk.CTkFont(family=FONT_FAMILY, size=21, weight="bold"),
            text_color=TEXT_DARK,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_text,
            text="Search files and folders on the Genco server",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(SPACING_XS, 0))

        # ── Search card ───────────────────────────────────────────
        search_card = ctk.CTkFrame(
            main,
            fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        search_card.grid(row=1, column=0, sticky="ew", pady=(0, SPACING_SM))

        card_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        card_inner.pack(fill="x", padx=SPACING_XL, pady=SPACING_LG)

        # ─ Main search bar (hero) ─
        search_hero = ctk.CTkFrame(
            card_inner,
            fg_color=INPUT_BG,
            corner_radius=CORNER_RADIUS_LG,
            border_width=2,
            border_color=INPUT_BORDER,
            height=52,
        )
        search_hero.pack(fill="x", pady=(0, SPACING_LG))
        search_hero.pack_propagate(False)

        # Frame interno para preservar a borda completa
        search_inner = ctk.CTkFrame(
            search_hero,
            fg_color="transparent",
            corner_radius=0,
        )
        search_inner.pack(fill="both", expand=True, padx=2, pady=2)

        # Magnifying glass icon
        search_icon_frame = ctk.CTkFrame(
            search_inner,
            fg_color=ACCENT_LIGHT,
            corner_radius=CORNER_RADIUS_SM,
            width=34,
            height=34,
        )
        search_icon_frame.pack(side="left", padx=(SPACING_SM, 0), pady=SPACING_SM)
        search_icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            search_icon_frame,
            text="⌕",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16),
            text_color=ACCENT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        self.search_entry = ctk.CTkEntry(
            search_inner,
            height=46,
            corner_radius=CORNER_RADIUS_MD,
            border_width=0,
            fg_color="transparent",
            text_color=TEXT_DARK,
            placeholder_text="Type the file or folder name",
            placeholder_text_color=TEXT_LIGHT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        self.search_entry.pack(side="left", fill="both", expand=True, padx=(SPACING_MD, SPACING_SM), pady=2)
        self.search_entry.bind("<Return>", lambda e: self._start_search())

        # Internal vertical divider
        ctk.CTkFrame(
            search_inner,
            fg_color=BORDER_COLOR,
            width=1,
            height=28,
        ).pack(side="left", pady=SPACING_LG)

        # Inline buttons in the search bar
        ctk.CTkButton(
            search_inner,
            text="Clear",
            command=self._clear,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color="transparent",
            hover_color=BTN_SEC_HOVER,
            text_color=TEXT_MUTED,
            corner_radius=CORNER_RADIUS_SM,
            width=72,
            height=34,
            cursor="hand2",
        ).pack(side="left", padx=(SPACING_SM, SPACING_XS), pady=SPACING_SM)

        ctk.CTkButton(
            search_inner,
            text="Search",
            command=self._start_search,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=CORNER_RADIUS_MD,
            width=120,
            height=36,
            cursor="hand2",
        ).pack(side="left", padx=(SPACING_XS, SPACING_SM), pady=SPACING_SM)

        # ─ Filter row ─
        filters_row = ctk.CTkFrame(card_inner, fg_color="transparent")
        filters_row.pack(fill="x")

        # Label "Filters:"
        ctk.CTkLabel(
            filters_row,
            text="Filters:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color="#000000",
        ).pack(side="left", padx=(SPACING_XS, SPACING_MD))

        # Folder
        folder_wrap = ctk.CTkFrame(filters_row, fg_color="transparent")
        folder_wrap.pack(side="left", padx=(0, SPACING_MD))

        ctk.CTkLabel(
            folder_wrap,
            text="Folder",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="#000000",
        ).pack(anchor="w", pady=(0, SPACING_XS))

        ctk.CTkComboBox(
            folder_wrap,
            values=["All folders"] + AVAILABLE_FOLDERS,
            variable=self.folder_var,
            width=200,
            height=36,
            corner_radius=CORNER_RADIUS_SM,
            border_width=1,
            border_color=INPUT_BORDER,
            fg_color=INPUT_BG,
            button_color="#E5E7EB",
            button_hover_color=BTN_SECONDARY,
            text_color=TEXT_SECONDARY,
            dropdown_fg_color=BG_WHITE,
            dropdown_hover_color=ACCENT_LIGHT,
            dropdown_text_color=TEXT_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        ).pack()

        # Type
        type_wrap = ctk.CTkFrame(filters_row, fg_color="transparent")
        type_wrap.pack(side="left", padx=(0, SPACING_LG))

        ctk.CTkLabel(
            type_wrap,
            text="Type",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="#000000",
        ).pack(anchor="w", pady=(0, SPACING_XS))

        ctk.CTkComboBox(
            type_wrap,
            values=EXTENSIONS_UI,
            variable=self.extension_var,
            width=140,
            height=36,
            corner_radius=CORNER_RADIUS_SM,
            border_width=1,
            border_color=INPUT_BORDER,
            fg_color=INPUT_BG,
            button_color="#E5E7EB",
            button_hover_color=BTN_SECONDARY,
            text_color=TEXT_SECONDARY,
            dropdown_fg_color=BG_WHITE,
            dropdown_hover_color=ACCENT_LIGHT,
            dropdown_text_color=TEXT_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        ).pack()

        # Vertical separator
        ctk.CTkFrame(filters_row, fg_color=BORDER_COLOR, width=1, height=36).pack(side="left", padx=SPACING_LG)

        # Checkbox
        ctk.CTkCheckBox(
            filters_row,
            text="Search inside content (TEMPORALY DISABLED)",
            variable=self.search_content_var,
            text_color=TEXT_MUTED,
            border_color=INPUT_BORDER,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            checkbox_width=17,
            checkbox_height=17,
            corner_radius=5,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            state="disabled",
        ).pack(side="left")

        # ── Results card ──────────────────────────────────────────
        result_card = ctk.CTkFrame(
            main,
            fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        result_card.grid(row=2, column=0, sticky="nsew")

        # Results header
        result_header = ctk.CTkFrame(result_card, fg_color=BG_WHITE, corner_radius=0, height=52)
        result_header.pack(fill="x")
        result_header.pack_propagate(False)

        rh_left = ctk.CTkFrame(result_header, fg_color="transparent")
        rh_left.pack(side="left", padx=SPACING_XL, pady=SPACING_LG, fill="y")

        ctk.CTkLabel(
            rh_left,
            text="Results",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(side="left")

        # Divider
        ctk.CTkFrame(result_card, fg_color=BORDER_COLOR, height=1, corner_radius=0).pack(fill="x")

        # Column header
        col_header = ctk.CTkFrame(result_card, fg_color=COL_HEADER_BG, corner_radius=0, height=32)
        col_header.pack(fill="x")
        col_header.pack_propagate(False)

        col_h_inner = ctk.CTkFrame(col_header, fg_color="transparent")
        col_h_inner.pack(fill="both", expand=True, padx=SPACING_XL)

        ctk.CTkLabel(
            col_h_inner,
            text="NAME / PATH",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(side="left", pady=SPACING_SM)

        ctk.CTkLabel(
            col_h_inner,
            text="TYPE",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="e",
            width=60,
        ).pack(side="right", pady=SPACING_SM)

        # Thin divider
        ctk.CTkFrame(result_card, fg_color=BORDER_LIGHT, height=1, corner_radius=0).pack(fill="x")

        # Results scroll
        scroll_container = ctk.CTkFrame(result_card, fg_color=BG_WHITE, corner_radius=0)
        scroll_container.pack(fill="both", expand=True)

        self.result_scroll = ctk.CTkScrollableFrame(
            scroll_container,
            fg_color=BG_WHITE,
            corner_radius=0,
            scrollbar_button_color="#D1D5DB",
            scrollbar_button_hover_color=ACCENT,
        )
        self.result_scroll.pack(fill="both", expand=True)

        # Initial empty state
        self._show_empty_state()

        # Footer
        footer = ctk.CTkFrame(search_frame, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=(SPACING_XS, SPACING_MD))

        ctk.CTkLabel(
            footer,
            text="Genco Import & Export  •  Server File Finder  •  v1.0.6",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            text_color=TEXT_LIGHT,
        ).pack()

    # ── Empty state ──────────────────────────────────────────────

    def _show_empty_state(self):
        self._empty_state_frame = ctk.CTkFrame(self.result_scroll, fg_color="transparent")
        self._empty_state_frame.pack(expand=True, pady=SPACING_3XL)

        ctk.CTkLabel(
            self._empty_state_frame,
            text="🔍",
            font=ctk.CTkFont(size=36),
        ).pack()

        ctk.CTkLabel(
            self._empty_state_frame,
            text="No search performed",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=TEXT_SECONDARY,
        ).pack(pady=(SPACING_MD, SPACING_XS))

        ctk.CTkLabel(
            self._empty_state_frame,
            text="Enter a term above and click Search to find files.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_LIGHT,
        ).pack()

    def _remove_empty_state(self):
        if self._empty_state_frame and self._empty_state_frame.winfo_exists():
            self._empty_state_frame.destroy()
            self._empty_state_frame = None

    # ── Result rows ──────────────────────────────────────────────

    def _clear_results(self):
        for w in self.result_scroll.winfo_children():
            w.destroy()
        self.result_rows = []
        self._empty_state_frame = None

    def _add_row(self, path, idx):
        ext = os.path.splitext(path)[1].lower()
        is_folder = os.path.isdir(path)

        if is_folder:
            badge_text, badge_color, badge_bg = BADGE_MAP["folder"]
            icon_char, icon_bg, icon_fg = ICON_MAP["folder"]
        else:
            badge_text, badge_color, badge_bg = BADGE_MAP.get(ext, ("FILE", "#6B7280", "#F3F4F6"))
            icon_char, icon_bg, icon_fg = ICON_MAP.get(ext, ("📄", "#F3F4F6", "#6B7280"))

        row_bg = BG_WHITE

        row = ctk.CTkFrame(
            self.result_scroll,
            fg_color=row_bg,
            corner_radius=0,
            height=66,
        )
        row.pack(fill="x")
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING_XL, pady=SPACING_MD)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        # Colored icon by type
        icon_box = ctk.CTkFrame(left, fg_color=icon_bg, corner_radius=CORNER_RADIUS_MD, width=40, height=40)
        icon_box.pack(side="left", padx=(0, SPACING_LG))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(
            icon_box,
            text=icon_char,
            font=ctk.CTkFont(size=16),
        ).place(relx=0.5, rely=0.5, anchor="center")

        text_frame = ctk.CTkFrame(left, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)

        file_name = os.path.basename(path)

        ctk.CTkLabel(
            text_frame,
            text=file_name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_DARK,
            anchor="w",
        ).pack(anchor="w", pady=(SPACING_XS, SPACING_XS))

        ctk.CTkLabel(
            text_frame,
            text=path,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(anchor="w")

        # Type badge
        right_col = ctk.CTkFrame(inner, fg_color="transparent", width=72)
        right_col.pack(side="right", fill="y")
        right_col.pack_propagate(False)

        ctk.CTkLabel(
            right_col,
            text=badge_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=badge_color,
            fg_color=badge_bg,
            corner_radius=CORNER_RADIUS_SM,
            width=54,
            height=26,
        ).pack(anchor="e", pady=SPACING_SM)

        # Hover effect
        def on_enter(e, r=row, ri=inner, l=left, tf=text_frame, ib=icon_box, rc=right_col):
            for w in [r, ri, l, tf, ib, rc]:
                try:
                    w.configure(fg_color=ACCENT_LIGHT)
                except Exception:
                    pass

        def on_leave(e, r=row, ri=inner, l=left, tf=text_frame, rc=right_col):
            for w in [r, ri, l, tf, rc]:
                try:
                    w.configure(fg_color=BG_WHITE if w != rc else "transparent")
                except Exception:
                    pass

        for w in [row, inner, left, text_frame, icon_box, right_col]:
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", lambda e, p=path: self._open(p))
            w.bind("<Button-3>", lambda e, p=path: self._copy(p))

        # Ultra-thin divider between rows
        divider = ctk.CTkFrame(self.result_scroll, fg_color=BORDER_LIGHT, height=1, corner_radius=0)
        divider.pack(fill="x")

        self.result_rows.append((row, divider))

    def _show_results(self, results):
        self._clear_results()
        self._stop_spinner()

        if not results:
            # Empty state "no results"
            empty = ctk.CTkFrame(self.result_scroll, fg_color="transparent")
            empty.pack(expand=True, pady=SPACING_3XL)
            self._empty_state_frame = empty

            ctk.CTkLabel(
                empty,
                text="😕",
                font=ctk.CTkFont(size=36),
            ).pack()

            ctk.CTkLabel(
                empty,
                text="No files found",
                font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                text_color=TEXT_SECONDARY,
            ).pack(pady=(SPACING_MD, SPACING_XS))

            ctk.CTkLabel(
                empty,
                text="Try other terms or check the applied filters.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=TEXT_LIGHT,
            ).pack()

            if self.count_number_label:
                self.count_number_label.configure(text="0")
            if self.count_label:
                self.count_label.configure(text=" file(s) found")
            return

        for idx, path in enumerate(results):
            self._add_row(path, idx)

        n = len(results)
        if self.count_number_label:
            self.count_number_label.configure(text=str(n))
        if self.count_label:
            self.count_label.configure(text=" file(s) found")

    # ── Search ───────────────────────────────────────────────────

    def _read_docx(self, path):
        """Lê conteúdo de arquivo DOCX com tratamento de erro"""
        try:
            doc = Document(path)
            content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            logging.debug(f"DOCX lido com sucesso: {path}")
            return content
        except PermissionError:
            logging.warning(f"Permissão negada ao ler DOCX: {path}")
            return ""
        except Exception as e:
            logging.warning(f"Erro ao ler DOCX {path}: {type(e).__name__}: {e}")
            return ""

    def _read_pdf(self, path):
        """Lê conteúdo de arquivo PDF com tratamento de erro"""
        try:
            with fitz.open(path) as doc:
                content = "\n".join(page.get_text() for page in doc)
            logging.debug(f"PDF lido com sucesso: {path}")
            return content
        except PermissionError:
            logging.warning(f"Permissão negada ao ler PDF: {path}")
            return ""
        except Exception as e:
            logging.warning(f"Erro ao ler PDF {path}: {type(e).__name__}: {e}")
            return ""

    @staticmethod
    def _normalize(text):
        """Normaliza texto removendo espaços"""
        return text.replace(" ", "")

    def _search_in(self, root_directory, term):
        """Realiza busca com tratamento robusto de erros"""
        try:
            search_content = self.search_content_var.get()
            extension_ui = self.extension_var.get()
            selected_extension = EXTENSIONS_MAP.get(extension_ui, "All")

            exact_matches, related_matches = [], []
            valid_extensions = [".pdf", ".docx", ".xlsx", ".xls", ".txt", ".jpg", ".png"]
            limit = 100

            if not os.path.exists(root_directory):
                logging.debug(f"Diretório não encontrado: {root_directory}")
                return []

            norm_term = self._normalize(term)

            for root, folders, files in os.walk(root_directory):
                try:
                    for folder in folders:
                        name = folder.lower()
                        norm_name = self._normalize(name)
                        path = os.path.join(root, folder)
                        if name == term or norm_name == norm_term:
                            exact_matches.append(path)
                        elif term in name or norm_term in norm_name:
                            related_matches.append(path)

                    for file in files:
                        if len(exact_matches) + len(related_matches) >= limit:
                            break

                        file_name, ext = os.path.splitext(file)
                        ext = ext.lower()

                        if ext not in valid_extensions:
                            continue

                        if selected_extension != "All" and ext != selected_extension:
                            continue

                        path = os.path.join(root, file)
                        has_content = False

                        if search_content:
                            try:
                                if ext == ".pdf":
                                    has_content = norm_term in self._normalize(self._read_pdf(path).lower())
                                elif ext == ".docx":
                                    has_content = norm_term in self._normalize(self._read_docx(path).lower())
                            except Exception as e:
                                logging.debug(f"Erro ao buscar conteúdo em {path}: {e}")

                        norm_file = self._normalize(file_name.lower())
                        if file_name.lower() == term or norm_file == norm_term or has_content:
                            exact_matches.append(path)
                        elif term in file_name.lower() or norm_term in norm_file:
                            related_matches.append(path)
                except (PermissionError, OSError) as e:
                    logging.debug(f"Erro ao acessar {root}: {type(e).__name__}")
                    continue
                except Exception as e:
                    logging.error(f"Erro inesperado em _search_in: {e}", exc_info=True)
                    continue

            logging.info(f"Busca concluída: {len(exact_matches)} exatos, {len(related_matches)} relacionados")
            return exact_matches + related_matches
        except Exception as e:
            logging.error(f"Erro crítico em _search_in: {e}", exc_info=True)
            return []

    def _folder_thread(self, term, folder):
        """Thread para busca em pasta específica"""
        try:
            results = []
            for bp in BASE_PATHS:
                results += self._search_in(os.path.join(bp, folder), term)
            self.after(0, lambda: self._show_results(results))
            logging.info(f"Busca em pasta '{folder}' concluída com {len(results)} resultados")
        except Exception as e:
            logging.error(f"Erro na thread de busca: {e}", exc_info=True)
            self.after(0, lambda: self._show_error("Search Error", f"Failed to search:\n{e}"))

    def _all_folders_thread(self, term):
        """Thread para busca em todas as pastas"""
        try:
            results = []
            for bp in BASE_PATHS:
                for f in AVAILABLE_FOLDERS:
                    results += self._search_in(os.path.join(bp, f), term)
            self.after(0, lambda: self._show_results(results))
            logging.info(f"Busca em todas as pastas concluída com {len(results)} resultados")
        except Exception as e:
            logging.error(f"Erro na thread de busca: {e}", exc_info=True)
            self.after(0, lambda: self._show_error("Search Error", f"Failed to search:\n{e}"))

    def _start_search(self):
        """Inicia busca com validação e tratamento de erros"""
        try:
            term = self.search_entry.get().strip().lower()
            if not term:
                self._show_warning("Input Required", "Please enter a file or folder name.")
                logging.warning("Tentativa de busca com termo vazio")
                return

            folder = self.folder_var.get().strip()
            self._remove_empty_state()
            self._clear_results()
            self._start_spinner()

            logging.info(f"Iniciando busca: termo='{term}', pasta='{folder}'")
            
            if not folder or folder == "All folders":
                threading.Thread(target=self._all_folders_thread, args=(term,), daemon=True).start()
            else:
                threading.Thread(target=self._folder_thread, args=(term, folder), daemon=True).start()
        except Exception as e:
            logging.error(f"Erro ao iniciar busca: {e}", exc_info=True)
            self._show_error("Search Error", f"Failed to start search:\n{e}")
            self._stop_spinner()

    def _clear(self):
        """Limpa busca e contexto com tratamento de erro"""
        try:
            self._stop_spinner()
            if self.search_entry:
                self.search_entry.delete(0, "end")
            if self.count_number_label:
                self.count_number_label.configure(text="")
            if self.count_label:
                self.count_label.configure(text="")
            self.folder_var.set("All folders")
            self.extension_var.set("All")
            self.search_content_var.set(False)
            self._clear_results()
            self._show_empty_state()
            logging.info("Busca limpa e contexto resetado")
        except Exception as e:
            logging.error(f"Erro ao limpar: {e}", exc_info=True)

    def _open(self, path):
        """Abre arquivo/pasta com tratamento robusto"""
        try:
            if not os.path.exists(path):
                self._show_error("File Not Found", f"The file or folder could not be found:\n{path}")
                logging.warning(f"Tentativa de abrir caminho inexistente: {path}")
                return
                
            os.startfile(path)
            logging.info(f"Arquivo/pasta aberto: {path}")
        except PermissionError:
            self._show_error("Permission Denied", f"You don't have permission to open:\n{path}")
            logging.warning(f"Permissão negada: {path}")
        except Exception as e:
            self._show_error("Cannot Open", f"Failed to open file:\n{type(e).__name__}: {e}")
            logging.error(f"Erro ao abrir arquivo {path}: {e}", exc_info=True)

    def _copy(self, path):
        """Copia caminho para área de transferência com feedback"""
        try:
            if not os.path.exists(path):
                self._show_warning("File Not Found", f"Cannot copy path - file not found:\n{path}")
                logging.warning(f"Tentativa de copiar caminho inexistente: {path}")
                return
                
            self.clipboard_clear()
            self.clipboard_append(path)

            notice = ctk.CTkLabel(
                self._search_frame,
                text="  ✓  Path copied  ",
                fg_color=SUCCESS_BG,
                text_color=SUCCESS_TEXT,
                corner_radius=CORNER_RADIUS_MD,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            )
            notice.place(relx=1.0, rely=1.0, anchor="se", x=-SPACING_XL, y=-SPACING_LG)

            if self.toast_id:
                try:
                    self.after_cancel(self.toast_id)
                except Exception:
                    pass

            self.toast_id = self.after(1800, lambda: notice.destroy() if notice.winfo_exists() else None)
            logging.info(f"Caminho copiado: {path}")
        except Exception as e:
            logging.error(f"Erro ao copiar caminho: {e}", exc_info=True)
            self._show_error("Copy Error", f"Failed to copy path:\n{e}")

    # ── Auto-update ──────────────────────────────────────────────

    def _check_for_updates(self):
        """Verifica atualizações no GitHub com tratamento de erro"""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "GencoBusca-Updater"})
            
            try:
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
            except urllib.error.URLError as e:
                logging.info(f"Não foi possível verificar atualizações (sem internet): {e}")
                return
            except json.JSONDecodeError as e:
                logging.warning(f"Resposta JSON inválida de GitHub: {e}")
                return

            latest_tag = data.get("tag_name", "").lstrip("v")
            if not latest_tag:
                logging.info("Tag de versão não encontrada no GitHub")
                return

            try:
                current = tuple(int(x) for x in VERSION.split("."))
                latest  = tuple(int(x) for x in latest_tag.split("."))
            except ValueError as e:
                logging.warning(f"Erro ao comparar versões: {e}")
                return

            if latest <= current:
                logging.info(f"Versão atual ({VERSION}) é a mais recente")
                return

            download_url = None
            for asset in data.get("assets", []):
                if asset["name"].lower().endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break

            if download_url:
                release_notes = data.get("body", "").strip()
                logging.info(f"Nova versão encontrada: {latest_tag}")
                self.after(0, lambda: self._show_update_dialog(latest_tag, download_url, release_notes))
        except Exception as e:
            logging.debug(f"Erro ao verificar updates: {type(e).__name__}: {e}")

    def _show_update_dialog(self, new_version, download_url, release_notes=""):
        """Mostra diálogo de atualização disponível"""
        try:
            dialog_height = 330 if release_notes else 230
            dialog = ctk.CTkToplevel(self)
            dialog.title("Update Available")
            dialog.geometry(f"440x{dialog_height}")
            dialog.resizable(False, False)
            dialog.configure(fg_color=BG_WHITE)
            dialog.grab_set()
            dialog.lift()
            dialog.focus_force()

            self.update_idletasks()
            x = self.winfo_x() + (self.winfo_width()  // 2) - 220
            y = self.winfo_y() + (self.winfo_height() // 2) - (dialog_height // 2)
            dialog.geometry(f"+{x}+{y}")

            ctk.CTkLabel(
                dialog,
                text="New update available!",
                font=ctk.CTkFont(family=FONT_FAMILY, size=17, weight="bold"),
                text_color=TEXT_DARK,
            ).pack(pady=(SPACING_2XL, SPACING_SM))

            ctk.CTkLabel(
                dialog,
                text=f"Version {new_version} is ready to download.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                text_color=TEXT_MUTED,
                justify="center",
            ).pack(pady=(0, SPACING_SM))

            if release_notes:
                notes_frame = ctk.CTkFrame(dialog, fg_color="#F3F4F6", corner_radius=CORNER_RADIUS_MD)
                notes_frame.pack(padx=SPACING_2XL, pady=(0, SPACING_LG), fill="x")

                ctk.CTkLabel(
                    notes_frame,
                    text="What's new:",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                    text_color=TEXT_DARK,
                    anchor="w",
                ).pack(padx=SPACING_MD, pady=(SPACING_SM, 0), anchor="w")

                ctk.CTkLabel(
                    notes_frame,
                    text=release_notes,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                    text_color=TEXT_MUTED,
                    anchor="w",
                    justify="left",
                    wraplength=380,
                ).pack(padx=SPACING_MD, pady=(2, SPACING_SM), anchor="w")

            btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_row.pack()

            ctk.CTkButton(
                btn_row,
                text="Update Now",
                command=lambda: self._download_and_install(download_url, dialog),
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                fg_color=ACCENT,
                hover_color=ACCENT_HOVER,
                text_color="white",
                corner_radius=CORNER_RADIUS_MD,
                width=160,
                height=40,
                cursor="hand2",
            ).pack(side="left", padx=(0, SPACING_MD))

            ctk.CTkButton(
                btn_row,
                text="Later",
                command=dialog.destroy,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                fg_color=BTN_SECONDARY,
                hover_color=BTN_SEC_HOVER,
                text_color=BTN_SEC_TEXT,
                corner_radius=CORNER_RADIUS_MD,
                width=100,
                height=40,
                cursor="hand2",
            ).pack(side="left")
            
            logging.info("Diálogo de atualização exibido")
        except Exception as e:
            logging.error(f"Erro ao exibir diálogo de atualização: {e}", exc_info=True)

    def _download_and_install(self, url, dialog):
        """Baixa e instala atualização com progresso"""
        dialog.destroy()

        try:
            prog = ctk.CTkToplevel(self)
            prog.title("Downloading update...")
            prog.geometry("400x150")
            prog.resizable(False, False)
            prog.configure(fg_color=BG_WHITE)
            prog.grab_set()
            prog.lift()

            self.update_idletasks()
            x = self.winfo_x() + (self.winfo_width()  // 2) - 200
            y = self.winfo_y() + (self.winfo_height() // 2) - 75
            prog.geometry(f"+{x}+{y}")

            ctk.CTkLabel(
                prog,
                text="Downloading update...",
                font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                text_color=TEXT_DARK,
            ).pack(pady=(SPACING_LG, SPACING_MD))

            bar = ctk.CTkProgressBar(prog, width=340, progress_color=ACCENT)
            bar.pack()
            bar.set(0)

            pct_label = ctk.CTkLabel(
                prog,
                text="0%",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=TEXT_MUTED,
            )
            pct_label.pack(pady=(SPACING_SM, 0))

            def do_download():
                try:
                    fd, tmp = tempfile.mkstemp(suffix=".exe")
                    os.close(fd)
                    
                    logging.info(f"Iniciando download: {url}")

                    def reporthook(block_num, block_size, total_size):
                        if total_size > 0 and not self.closing:
                            pct = min(block_num * block_size / total_size, 1.0)
                            self.after(0, lambda p=pct: bar.set(p))
                            self.after(0, lambda p=pct: pct_label.configure(text=f"{int(p * 100)}%"))

                    urllib.request.urlretrieve(url, tmp, reporthook)
                    logging.info(f"Download concluído: {tmp}")

                    if not self.closing:
                        self.after(0, lambda: self._launch_installer(tmp, prog))
                except urllib.error.URLError as e:
                    logging.error(f"Erro de conexão ao baixar: {e}")
                    if not self.closing:
                        self.after(0, prog.destroy)
                        self.after(0, lambda: self._show_error(
                            "Download Error", f"Failed to download update:\nConnection error: {e}"
                        ))
                except OSError as e:
                    logging.error(f"Erro de sistema ao baixar/salvar: {e}")
                    if not self.closing:
                        self.after(0, prog.destroy)
                        self.after(0, lambda: self._show_error(
                            "Download Error", f"Failed to download update:\nDisk or permission error: {e}"
                        ))
                except Exception as e:
                    logging.error(f"Erro inesperado no download: {e}", exc_info=True)
                    if not self.closing:
                        self.after(0, prog.destroy)
                        self.after(0, lambda: self._show_error(
                            "Download Error", f"Failed to download update:\n{type(e).__name__}: {e}"
                        ))

            threading.Thread(target=do_download, daemon=True).start()
        except Exception as e:
            logging.error(f"Erro ao criar dialog de download: {e}", exc_info=True)
            self._show_error("Update Error", f"Failed to start download:\n{e}")

    def _launch_installer(self, installer_path, prog_dialog):
        """Lança instalador com tratamento de erro"""
        try:
            prog_dialog.destroy()
            logging.info(f"Lançando instalador: {installer_path}")
            subprocess.Popen([installer_path], shell=True)
            self._close()
        except FileNotFoundError:
            logging.error(f"Arquivo instalador não encontrado: {installer_path}")
            self._show_error("Installation Error", f"Installer file not found.")
        except PermissionError:
            logging.error(f"Permissão negada para executar instalador: {installer_path}")
            self._show_error("Installation Error", "Permission denied to execute installer.")
        except Exception as e:
            logging.error(f"Erro ao lançar instalador: {e}", exc_info=True)
            self._show_error("Installation Error", f"Failed to launch installer:\n{e}")


    # ══════════════════════════════════════════════════════════════
    # ══  COMPRESSOR SCREEN  ═══════════════════════════════════════
    # ══════════════════════════════════════════════════════════════

    def _show_compressor(self):
        self._clear_screen()
        self._search_frame = None
        self._comp_on_screen = True
        self.resizable(True, True)
        self._center_window(1360, 860)
        self.minsize(1180, 720)
        self.state("zoomed")

        # Reset state
        self._comp_file_path = None
        self._comp_file_type = None

        comp_frame = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        comp_frame.pack(fill="both", expand=True)

        # ── Header (same pattern as search) ───────────────────────
        header_shadow = ctk.CTkFrame(comp_frame, fg_color=SHADOW_COLOR, corner_radius=0, height=1)
        header = ctk.CTkFrame(comp_frame, fg_color=HEADER_BG, corner_radius=0, height=66)
        header.pack(fill="x")
        header.pack_propagate(False)
        header_shadow.pack(fill="x")

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=SPACING_2XL)

        # Logo area
        logo_area = ctk.CTkFrame(header_inner, fg_color="transparent")
        logo_area.pack(side="left")

        try:
            logo_img = Image.open(os.path.join(BASE_DIR, "assets", "icon.png"))
            logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(50, 50))
            logo_label = ctk.CTkLabel(logo_area, image=logo_ctk, text="")
            logo_label.pack(side="left", pady=SPACING_LG)
            logo_label.image = logo_ctk
        except Exception:
            icon_box = ctk.CTkFrame(logo_area, fg_color=ACCENT, corner_radius=CORNER_RADIUS_MD, width=36, height=36)
            icon_box.pack(side="left", pady=SPACING_LG)
            icon_box.pack_propagate(False)
            ctk.CTkLabel(
                icon_box, text="G",
                font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
                text_color="white",
            ).place(relx=0.5, rely=0.5, anchor="center")

        # Separator
        ctk.CTkFrame(
            header_inner, fg_color=BORDER_COLOR,
            width=1, height=28,
        ).pack(side="left", padx=SPACING_LG, pady=SPACING_LG)

        # ── Navigation tabs ───────────────────────────────────────
        nav_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        nav_frame.pack(side="left", fill="y")

        ctk.CTkButton(
            nav_frame, text="Search",
            command=self._show_search,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color="transparent",
            hover_color=ACCENT_LIGHT,
            text_color=TEXT_MUTED,
            corner_radius=CORNER_RADIUS_SM,
            width=80, height=32, cursor="hand2",
        ).pack(side="left", pady=SPACING_LG)

        # Active tab
        comp_tab = ctk.CTkButton(
            nav_frame, text="Compressor",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=ACCENT_LIGHT,
            hover_color=ACCENT_LIGHT,
            text_color=ACCENT,
            corner_radius=CORNER_RADIUS_SM,
            width=100, height=32,
        )
        comp_tab.pack(side="left", padx=(SPACING_SM, 0), pady=SPACING_LG)

        # Right area — theme toggle
        right_area = ctk.CTkFrame(header_inner, fg_color="transparent")
        right_area.pack(side="right", fill="y")

        theme_icon = "☀" if self.current_theme == "light" else "🌙"
        self._theme_toggle = ctk.CTkButton(
            right_area, text=theme_icon,
            command=self._toggle_theme,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            fg_color="transparent",
            hover_color=ACCENT_LIGHT,
            text_color=ACCENT,
            width=32, height=32,
            corner_radius=CORNER_RADIUS_MD, cursor="hand2",
        )
        self._theme_toggle.pack(side="right", padx=(SPACING_SM, SPACING_MD), pady=SPACING_LG)

        # Version pill
        pill = ctk.CTkFrame(right_area, fg_color="#F0FDF4", corner_radius=20, border_width=1, border_color="#BBF7D0")
        pill.pack(side="right", pady=SPACING_LG, padx=(0, SPACING_SM))
        pill_inner = ctk.CTkFrame(pill, fg_color="transparent")
        pill_inner.pack(padx=SPACING_SM, pady=SPACING_XS)
        dot = ctk.CTkFrame(pill_inner, fg_color="#10B981", corner_radius=4, width=7, height=7)
        dot.pack(side="left", padx=(0, SPACING_SM))
        dot.pack_propagate(False)
        ctk.CTkLabel(
            pill_inner, text=f"Compressor  v{VERSION}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color="#065F46",
        ).pack(side="left")

        # ── Main area ─────────────────────────────────────────────
        main = ctk.CTkFrame(comp_frame, fg_color="transparent", corner_radius=0)
        main.pack(fill="both", expand=True, padx=SPACING_2XL, pady=(SPACING_LG, SPACING_SM))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # ── Page title ────────────────────────────────────────────
        title_row = ctk.CTkFrame(main, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, SPACING_LG))

        accent_bar = ctk.CTkFrame(title_row, fg_color=ACCENT, width=4, height=36, corner_radius=2)
        accent_bar.pack(side="left", padx=(0, SPACING_MD))
        accent_bar.pack_propagate(False)

        title_text = ctk.CTkFrame(title_row, fg_color="transparent")
        title_text.pack(side="left")

        ctk.CTkLabel(
            title_text, text="File Compressor",
            font=ctk.CTkFont(family=FONT_FAMILY, size=21, weight="bold"),
            text_color=TEXT_DARK, anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_text, text="Compress images and videos to reduce file size",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15),
            text_color=TEXT_MUTED, anchor="w",
        ).pack(anchor="w", pady=(SPACING_XS, 0))

        # ── Upload card ───────────────────────────────────────────
        upload_card = ctk.CTkFrame(
            main, fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1, border_color=BORDER_COLOR,
        )
        upload_card.grid(row=1, column=0, sticky="ew", pady=(0, SPACING_SM))

        card_inner = ctk.CTkFrame(upload_card, fg_color="transparent")
        card_inner.pack(fill="x", padx=SPACING_XL, pady=SPACING_LG)

        # ── Drop zone ─────────────────────────────────────────────
        self._comp_drop_zone = ctk.CTkFrame(
            card_inner, fg_color=ACCENT_LIGHT,
            corner_radius=CORNER_RADIUS_LG,
            border_width=2, border_color=ACCENT_MEDIUM,
            height=140,
        )
        self._comp_drop_zone.pack(fill="x", pady=(0, SPACING_LG))
        self._comp_drop_zone.pack_propagate(False)

        drop_inner = ctk.CTkFrame(self._comp_drop_zone, fg_color="transparent")
        drop_inner.place(relx=0.5, rely=0.5, anchor="center")

        self._comp_drop_icon = ctk.CTkLabel(
            drop_inner, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=32),
            text_color=ACCENT,
        )
        self._comp_drop_icon.pack()

        self._comp_drop_text = ctk.CTkLabel(
            drop_inner, text="Click or drag a file or folder here",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color=TEXT_SECONDARY,
        )
        self._comp_drop_text.pack(pady=(SPACING_XS, 0))

        self._comp_drop_sub = ctk.CTkLabel(
            drop_inner, text="JPG, PNG, WebP, MP4, MOV, AVI, MKV",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED,
        )
        self._comp_drop_sub.pack()

        # Make the whole zone clickable
        for widget in [self._comp_drop_zone, drop_inner, self._comp_drop_icon,
                       self._comp_drop_text, self._comp_drop_sub]:
            widget.bind("<Button-1>", lambda e: self._comp_select_file())
            widget.configure(cursor="hand2")

        # Enable drag and drop on the entire window
        windnd.hook_dropfiles(self, func=self._comp_on_drop)

        # ── Options row ───────────────────────────────────────────
        self._comp_options_frame = ctk.CTkFrame(card_inner, fg_color="transparent")
        # Hidden until file is selected

        # ── Progress area ─────────────────────────────────────────
        self._comp_progress_frame = ctk.CTkFrame(card_inner, fg_color="transparent")
        # Hidden until compression starts

        # ── Results area ──────────────────────────────────────────
        result_area = ctk.CTkFrame(main, fg_color="transparent")
        result_area.grid(row=2, column=0, sticky="nsew")
        self._comp_result_frame = result_area

        # ── How it works (initial state) ──────────────────────────
        self._comp_show_how_it_works()

    # ── Compressor: How it Works ─────────────────────────────────

    def _comp_show_how_it_works(self):
        """Mostra os 3 passos ilustrativos na área de resultado."""
        for w in self._comp_result_frame.winfo_children():
            w.destroy()

        how_card = ctk.CTkFrame(
            self._comp_result_frame, fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1, border_color=BORDER_COLOR,
        )
        how_card.pack(fill="x", pady=(0, SPACING_SM))

        inner = ctk.CTkFrame(how_card, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING_XL, pady=SPACING_LG)

        # Title
        ctk.CTkLabel(
            inner, text="How it works",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(anchor="w", pady=(0, SPACING_LG))

        # Three steps in a row
        steps_row = ctk.CTkFrame(inner, fg_color="transparent")
        steps_row.pack(fill="x")
        steps_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        steps = [
            ("1", "Select a file", "Click the area above or drag\nan image or video file"),
            ("2", "Adjust settings", "Choose compression level,\nquality and output format"),
            ("3", "Download result", "Get your compressed file\nwith reduced size"),
        ]

        for i, (number, title, desc) in enumerate(steps):
            col = i * 2  # 0, 2, 4

            step_frame = ctk.CTkFrame(steps_row, fg_color="transparent")
            step_frame.grid(row=0, column=col, sticky="nsew", padx=SPACING_SM)

            # Number circle
            circle = ctk.CTkFrame(
                step_frame, fg_color=ACCENT, corner_radius=20,
                width=40, height=40,
            )
            circle.pack(pady=(0, SPACING_MD))
            circle.pack_propagate(False)

            ctk.CTkLabel(
                circle, text=number,
                font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
                text_color="white",
            ).place(relx=0.5, rely=0.5, anchor="center")

            # Step title
            ctk.CTkLabel(
                step_frame, text=title,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                text_color=TEXT_DARK,
            ).pack(pady=(0, SPACING_XS))

            # Step description
            ctk.CTkLabel(
                step_frame, text=desc,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=TEXT_MUTED, justify="center",
            ).pack()

            # Arrow between steps (not after the last one)
            if i < 2:
                arrow_label = ctk.CTkLabel(
                    steps_row, text="->",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=20),
                    text_color=TEXT_LIGHT,
                )
                arrow_label.grid(row=0, column=col + 1, padx=SPACING_XS)

    # ── Compressor: File Selection ────────────────────────────────

    def _comp_select_file(self):
        filetypes = [
            ("Images & Videos", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif *.mp4 *.mov *.avi *.mkv *.webm *.wmv *.flv"),
            ("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif"),
            ("Videos", "*.mp4 *.mov *.avi *.mkv *.webm *.wmv *.flv"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(
            title="Select file to compress",
            filetypes=filetypes,
        )
        if not path:
            return
        self._comp_load_path(path)

    def _comp_select_folder(self):
        path = filedialog.askdirectory(title="Select folder to compress")
        if not path:
            return
        self._comp_load_path(path)

    def _comp_on_drop(self, files):
        """Callback do windnd quando arquivos/pastas são arrastados para a janela."""
        if not files:
            return
        path = files[0].decode("utf-8") if isinstance(files[0], bytes) else files[0]
        self._comp_load_path(path)

    def _comp_load_path(self, path):
        """Carrega um arquivo ou pasta no compressor."""
        if os.path.isdir(path):
            self._comp_load_folder(path)
        else:
            self._comp_load_file(path)

    def _comp_load_file(self, path):
        """Carrega um arquivo selecionado ou arrastado no compressor."""
        file_type = get_file_type(path)
        if not file_type:
            self._show_warning("Unsupported File", "Please select an image or video file.")
            return

        self._comp_file_path = path
        self._comp_file_type = file_type
        self._comp_batch_folder = None
        file_size = os.path.getsize(path)
        file_name = os.path.basename(path)

        # Update drop zone to show selected file
        if file_type == "image":
            self._comp_drop_icon.configure(text="")
        else:
            self._comp_drop_icon.configure(text="")

        self._comp_drop_text.configure(
            text=file_name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        )
        self._comp_drop_sub.configure(
            text=f"{file_type.upper()}  •  {get_file_size_str(file_size)}  •  Click or drag to change",
        )

        # Show options
        self._comp_show_options(file_type)

    def _comp_load_folder(self, folder_path):
        """Carrega uma pasta para compressão em lote."""
        files = scan_folder(folder_path)
        if not files:
            self._show_warning("No Files Found", "No supported images or videos found in this folder.")
            return

        self._comp_file_path = None
        self._comp_file_type = None
        self._comp_batch_folder = folder_path
        self._comp_batch_files = files

        images = [f for f in files if f["type"] == "image"]
        videos = [f for f in files if f["type"] == "video"]
        total_size = sum(f["size"] for f in files)
        folder_name = os.path.basename(folder_path)

        self._comp_drop_icon.configure(text="")
        self._comp_drop_text.configure(
            text=folder_name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        )

        parts = []
        if images:
            parts.append(f"{len(images)} images")
        if videos:
            parts.append(f"{len(videos)} videos")
        summary = ", ".join(parts)

        self._comp_drop_sub.configure(
            text=f"FOLDER  •  {summary}  •  {get_file_size_str(total_size)}  •  Click or drag to change",
        )

        # Show options
        self._comp_show_options("folder")

    # ── Compressor: Options Panel ─────────────────────────────────

    def _comp_show_options(self, file_type):
        # Clear previous options
        for w in self._comp_options_frame.winfo_children():
            w.destroy()
        for w in self._comp_result_frame.winfo_children():
            w.destroy()

        self._comp_options_frame.pack(fill="x", pady=(0, SPACING_LG))

        if file_type == "folder":
            self._comp_show_batch_options()
        elif file_type == "image":
            self._comp_show_image_options()
        else:
            self._comp_show_video_options()

    def _comp_show_image_options(self):
        frame = self._comp_options_frame

        # Row: quality + format + compress button
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")

        # Quality slider
        qual_frame = ctk.CTkFrame(row, fg_color="transparent")
        qual_frame.pack(side="left", fill="x", expand=True)

        qual_label = ctk.CTkLabel(
            qual_frame, text="Quality: 75%",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_DARK,
        )
        qual_label.pack(anchor="w")

        ctk.CTkLabel(
            qual_frame, text="Lower = smaller file, less quality",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        self._comp_img_quality = ctk.IntVar(value=75)

        def on_quality_change(val):
            self._comp_img_quality.set(int(val))
            qual_label.configure(text=f"Quality: {int(val)}%")
            self._comp_update_preview()

        slider = ctk.CTkSlider(
            qual_frame, from_=10, to=100,
            variable=self._comp_img_quality,
            command=on_quality_change,
            fg_color=BORDER_COLOR,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            width=300, height=16,
        )
        slider.pack(anchor="w", pady=(SPACING_SM, 0))

        # Format dropdown
        fmt_frame = ctk.CTkFrame(row, fg_color="transparent")
        fmt_frame.pack(side="left", padx=(SPACING_2XL, SPACING_2XL))

        ctk.CTkLabel(
            fmt_frame, text="Output Format",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(anchor="w")

        self._comp_img_format = ctk.StringVar(value="Same as original")

        ctk.CTkOptionMenu(
            fmt_frame,
            variable=self._comp_img_format,
            values=["Same as original", "JPEG", "PNG", "WEBP"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=INPUT_BG,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            text_color=TEXT_DARK,
            dropdown_fg_color=BG_WHITE,
            dropdown_text_color=TEXT_DARK,
            dropdown_hover_color=ACCENT_LIGHT,
            corner_radius=CORNER_RADIUS_SM,
            width=160,
            command=lambda _: self._comp_update_preview(),
        ).pack(anchor="w", pady=(SPACING_SM, 0))

        # Compress button
        ctk.CTkButton(
            row, text="Compress Image",
            command=self._comp_start_image,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=CORNER_RADIUS_LG,
            width=180, height=44, cursor="hand2",
        ).pack(side="right", pady=(SPACING_SM, 0))

        # Preview
        self._comp_create_preview(frame)
        self._comp_update_preview()

    def _comp_show_video_options(self):
        frame = self._comp_options_frame

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")

        # Quality preset
        preset_frame = ctk.CTkFrame(row, fg_color="transparent")
        preset_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            preset_frame, text="Compression Level",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(anchor="w")

        ctk.CTkLabel(
            preset_frame, text="Higher compression = smaller file, less quality",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        self._comp_vid_preset = ctk.StringVar(value="medium")

        presets_row = ctk.CTkFrame(preset_frame, fg_color="transparent")
        presets_row.pack(anchor="w", pady=(SPACING_SM, 0))

        for key, config in QUALITY_PRESETS.items():
            is_selected = key == "medium"
            btn = ctk.CTkButton(
                presets_row, text=config["label"],
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                fg_color=ACCENT if is_selected else BTN_SECONDARY,
                hover_color=ACCENT_HOVER if is_selected else BTN_SEC_HOVER,
                text_color="white" if is_selected else BTN_SEC_TEXT,
                corner_radius=CORNER_RADIUS_SM,
                height=32, cursor="hand2",
            )
            btn.pack(side="left", padx=(0, SPACING_SM))
            btn.configure(command=lambda k=key, b=btn, r=presets_row: self._comp_select_preset(k, b, r))

        # Resolution dropdown
        res_frame = ctk.CTkFrame(row, fg_color="transparent")
        res_frame.pack(side="left", padx=(SPACING_2XL, SPACING_2XL))

        ctk.CTkLabel(
            res_frame, text="Max Resolution",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(anchor="w")

        self._comp_vid_resolution = ctk.StringVar(value="Original")

        ctk.CTkOptionMenu(
            res_frame,
            variable=self._comp_vid_resolution,
            values=["Original", "1080p", "720p", "480p"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=INPUT_BG,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            text_color=TEXT_DARK,
            dropdown_fg_color=BG_WHITE,
            dropdown_text_color=TEXT_DARK,
            dropdown_hover_color=ACCENT_LIGHT,
            corner_radius=CORNER_RADIUS_SM,
            width=140,
            command=lambda _: self._comp_update_preview(),
        ).pack(anchor="w", pady=(SPACING_SM, 0))

        # Compress button
        ctk.CTkButton(
            row, text="Compress Video",
            command=self._comp_start_video,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=CORNER_RADIUS_LG,
            width=180, height=44, cursor="hand2",
        ).pack(side="right", pady=(SPACING_SM, 0))

        # Preview
        self._comp_create_preview(frame)
        self._comp_update_preview()

    def _comp_show_batch_options(self):
        frame = self._comp_options_frame

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")

        # Image quality slider
        qual_frame = ctk.CTkFrame(row, fg_color="transparent")
        qual_frame.pack(side="left", fill="x", expand=True)

        qual_label = ctk.CTkLabel(
            qual_frame, text="Image Quality: 75%",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_DARK,
        )
        qual_label.pack(anchor="w")

        self._comp_img_quality = ctk.IntVar(value=75)

        self._comp_batch_debounce_id = None

        def on_quality_change(val):
            self._comp_img_quality.set(int(val))
            qual_label.configure(text=f"Image Quality: {int(val)}%")
            # Debounce: só atualiza a prévia 300ms após parar de mexer
            if self._comp_batch_debounce_id:
                self.after_cancel(self._comp_batch_debounce_id)
            self._comp_batch_debounce_id = self.after(300, self._comp_update_preview)

        ctk.CTkSlider(
            qual_frame, from_=10, to=100,
            variable=self._comp_img_quality,
            command=on_quality_change,
            fg_color=BORDER_COLOR,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            width=250, height=16,
        ).pack(anchor="w", pady=(SPACING_SM, 0))

        # Video preset
        preset_frame = ctk.CTkFrame(row, fg_color="transparent")
        preset_frame.pack(side="left", padx=(SPACING_2XL, SPACING_2XL))

        ctk.CTkLabel(
            preset_frame, text="Compression",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(anchor="w")

        self._comp_vid_preset = ctk.StringVar(value="medium")

        ctk.CTkOptionMenu(
            preset_frame,
            variable=self._comp_vid_preset,
            values=["low", "medium", "high"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=INPUT_BG,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            text_color=TEXT_DARK,
            dropdown_fg_color=BG_WHITE,
            dropdown_text_color=TEXT_DARK,
            dropdown_hover_color=ACCENT_LIGHT,
            corner_radius=CORNER_RADIUS_SM,
            width=140,
            command=lambda _: self._comp_update_preview(),
        ).pack(anchor="w", pady=(SPACING_SM, 0))

        # Compress button
        ctk.CTkButton(
            row, text="Compress All",
            command=self._comp_start_batch,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=CORNER_RADIUS_LG,
            width=180, height=44, cursor="hand2",
        ).pack(side="right", pady=(SPACING_SM, 0))

        # Preview
        self._comp_create_preview(frame)
        self._comp_update_preview()

    def _comp_select_preset(self, key, btn, parent):
        self._comp_vid_preset.set(key)
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkButton):
                child.configure(
                    fg_color=BTN_SECONDARY,
                    hover_color=BTN_SEC_HOVER,
                    text_color=BTN_SEC_TEXT,
                )
        btn.configure(
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
        )
        self._comp_update_preview()

    # ── Compressor: Preview UI ────────────────────────────────────

    def _comp_create_preview(self, parent):
        """Cria o frame de prévia de tamanhos."""
        preview = ctk.CTkFrame(parent, fg_color=ACCENT_LIGHT, corner_radius=CORNER_RADIUS_MD)
        preview.pack(fill="x", pady=(SPACING_LG, 0))

        inner = ctk.CTkFrame(preview, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING_LG, pady=SPACING_MD)
        inner.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Original size
        orig_f = ctk.CTkFrame(inner, fg_color="transparent")
        orig_f.grid(row=0, column=0)
        ctk.CTkLabel(orig_f, text="Original",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=TEXT_MUTED).pack()
        self._comp_preview_original = ctk.CTkLabel(
            orig_f, text="--",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"), text_color=TEXT_DARK)
        self._comp_preview_original.pack()

        # Arrow
        ctk.CTkLabel(inner, text="->",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=16), text_color=TEXT_MUTED
                     ).grid(row=0, column=1)

        # Estimated size
        est_f = ctk.CTkFrame(inner, fg_color="transparent")
        est_f.grid(row=0, column=2)
        ctk.CTkLabel(est_f, text="Estimated",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=TEXT_MUTED).pack()
        self._comp_preview_estimated = ctk.CTkLabel(
            est_f, text="--",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"), text_color=ACCENT)
        self._comp_preview_estimated.pack()

        # Separator
        ctk.CTkLabel(inner, text="|",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=16), text_color=BORDER_COLOR
                     ).grid(row=0, column=3)

        # Reduction
        red_f = ctk.CTkFrame(inner, fg_color="transparent")
        red_f.grid(row=0, column=4)
        ctk.CTkLabel(red_f, text="Reduction",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=10), text_color=TEXT_MUTED).pack()
        self._comp_preview_reduction = ctk.CTkLabel(
            red_f, text="--",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"), text_color=SUCCESS_TEXT)
        self._comp_preview_reduction.pack()

    def _comp_update_preview(self):
        """Recalcula e atualiza a prévia de tamanhos."""
        def _do_estimate():
            if self._comp_batch_folder and self._comp_batch_files:
                quality = self._comp_img_quality.get() if hasattr(self, '_comp_img_quality') else 75
                preset = self._comp_vid_preset.get() if hasattr(self, '_comp_vid_preset') else "medium"
                est = estimate_batch_size(self._comp_batch_files,
                                          image_quality=quality, video_preset=preset)
            elif self._comp_file_path and self._comp_file_type == "image":
                quality = self._comp_img_quality.get() if hasattr(self, '_comp_img_quality') else 75
                fmt = self._comp_img_format.get() if hasattr(self, '_comp_img_format') else "Same as original"
                out_fmt = None if fmt == "Same as original" else fmt
                est = estimate_image_size(self._comp_file_path, quality=quality, output_format=out_fmt)
            elif self._comp_file_path and self._comp_file_type == "video":
                preset = self._comp_vid_preset.get() if hasattr(self, '_comp_vid_preset') else "medium"
                res_choice = self._comp_vid_resolution.get() if hasattr(self, '_comp_vid_resolution') else "Original"
                max_res = {"1080p": 1080, "720p": 720, "480p": 480}.get(res_choice)
                est = estimate_video_size(self._comp_file_path, quality_preset=preset, max_resolution=max_res)
            else:
                return

            original = est["original_size"]
            estimated = est["estimated_size"]
            reduction = ((original - estimated) / original * 100) if original > 0 else 0

            self.after(0, lambda: self._comp_set_preview_values(original, estimated, reduction))

        threading.Thread(target=_do_estimate, daemon=True).start()

    def _comp_set_preview_values(self, original, estimated, reduction):
        """Atualiza os labels da prévia na thread principal."""
        if hasattr(self, '_comp_preview_original') and self._comp_preview_original.winfo_exists():
            self._comp_preview_original.configure(text=get_file_size_str(original))
        if hasattr(self, '_comp_preview_estimated') and self._comp_preview_estimated.winfo_exists():
            self._comp_preview_estimated.configure(text=f"~{get_file_size_str(estimated)}")
        if hasattr(self, '_comp_preview_reduction') and self._comp_preview_reduction.winfo_exists():
            self._comp_preview_reduction.configure(text=f"~{reduction:.0f}%")

    # ── Compressor: Start Compression ─────────────────────────────

    def _comp_start_image(self):
        if not self._comp_file_path:
            return

        quality = self._comp_img_quality.get()
        fmt_choice = self._comp_img_format.get()
        output_format = None if fmt_choice == "Same as original" else fmt_choice

        # Determine output extension
        if output_format:
            ext_map = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
            out_ext = ext_map.get(output_format, ".jpg")
        else:
            out_ext = os.path.splitext(self._comp_file_path)[1]

        # Ask where to save
        base_name = os.path.splitext(os.path.basename(self._comp_file_path))[0]
        output_path = filedialog.asksaveasfilename(
            title="Save compressed image as",
            initialfile=f"{base_name}_compressed{out_ext}",
            defaultextension=out_ext,
            filetypes=[("Image files", f"*{out_ext}"), ("All files", "*.*")],
        )
        if not output_path:
            return

        self._comp_show_progress("Compressing image...")

        # Image compression is fast — run directly but use after() to update UI
        def do_compress():
            result = compress_image(
                self._comp_file_path, output_path,
                quality=quality, output_format=output_format,
            )
            self.after(0, lambda: self._comp_show_result(result, output_path))

        threading.Thread(target=do_compress, daemon=True).start()

    def _comp_start_video(self):
        if not self._comp_file_path:
            return

        preset = self._comp_vid_preset.get()
        res_choice = self._comp_vid_resolution.get()
        max_res = None
        if res_choice == "1080p":
            max_res = 1080
        elif res_choice == "720p":
            max_res = 720
        elif res_choice == "480p":
            max_res = 480

        # Ask where to save
        base_name = os.path.splitext(os.path.basename(self._comp_file_path))[0]
        out_ext = os.path.splitext(self._comp_file_path)[1]
        output_path = filedialog.asksaveasfilename(
            title="Save compressed video as",
            initialfile=f"{base_name}_compressed{out_ext}",
            defaultextension=out_ext,
            filetypes=[("Video files", f"*{out_ext}"), ("MP4 files", "*.mp4"), ("All files", "*.*")],
        )
        if not output_path:
            return

        self._comp_cancel_event = threading.Event()
        self._comp_show_progress("Compressing video... This may take a while.")

        def on_progress(percent):
            self.after(0, lambda p=percent: self._comp_update_progress(p))

        def on_complete(result):
            self.after(0, lambda: self._comp_show_result(result, output_path))

        self._comp_thread = compress_video(
            self._comp_file_path, output_path,
            quality_preset=preset, max_resolution=max_res,
            on_progress=on_progress, on_complete=on_complete,
            cancel_event=self._comp_cancel_event,
        )

    def _comp_start_batch(self):
        if not self._comp_batch_folder:
            return

        image_quality = self._comp_img_quality.get()
        video_preset = self._comp_vid_preset.get()

        # Ask where to save
        folder_name = os.path.basename(self._comp_batch_folder)
        output_folder = filedialog.askdirectory(
            title=f"Select destination folder for compressed files",
        )
        if not output_folder:
            return

        self._comp_cancel_event = threading.Event()
        total = len(self._comp_batch_files)
        self._comp_show_batch_progress(0, total, "Starting...")

        def on_file_start(index, total, filename, filetype):
            self.after(0, lambda: self._comp_show_batch_progress(
                index, total, f"Compressing {filename}  ({filetype})"
            ))

        def on_file_progress(percent):
            self.after(0, lambda p=percent: self._comp_update_progress(p))

        def on_file_complete(index, total, result):
            self.after(0, lambda: self._comp_update_batch_file_count(index + 1, total))

        def on_batch_complete(summary):
            self.after(0, lambda: self._comp_show_batch_result(summary, output_folder))

        self._comp_thread = compress_batch(
            self._comp_batch_folder, output_folder,
            image_quality=image_quality,
            video_preset=video_preset,
            on_file_start=on_file_start,
            on_file_progress=on_file_progress,
            on_file_complete=on_file_complete,
            on_batch_complete=on_batch_complete,
            cancel_event=self._comp_cancel_event,
        )

    # ── Compressor: Batch Progress UI ─────────────────────────────

    def _comp_show_batch_progress(self, current, total, message):
        for w in self._comp_result_frame.winfo_children():
            w.destroy()

        progress_card = ctk.CTkFrame(
            self._comp_result_frame, fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1, border_color=BORDER_COLOR,
        )
        progress_card.pack(fill="x", pady=(0, SPACING_SM))

        inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING_XL, pady=SPACING_LG)

        # Header row: file count + cancel
        header_row = ctk.CTkFrame(inner, fg_color="transparent")
        header_row.pack(fill="x")

        self._comp_batch_count_label = ctk.CTkLabel(
            header_row, text=f"File {current} of {total}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=TEXT_DARK,
        )
        self._comp_batch_count_label.pack(side="left")

        self._comp_cancel_btn = ctk.CTkButton(
            header_row, text="Cancel",
            command=self._comp_cancel,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="white",
            corner_radius=CORNER_RADIUS_SM,
            width=80, height=30, cursor="hand2",
        )
        self._comp_cancel_btn.pack(side="right")

        # Current file label
        self._comp_progress_label = ctk.CTkLabel(
            inner, text=message,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY,
        )
        self._comp_progress_label.pack(anchor="w", pady=(SPACING_SM, 0))

        # Overall progress bar (files)
        overall_frame = ctk.CTkFrame(inner, fg_color="transparent")
        overall_frame.pack(fill="x", pady=(SPACING_SM, 0))

        ctk.CTkLabel(
            overall_frame, text="Overall",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        self._comp_batch_progress_bar = ctk.CTkProgressBar(
            overall_frame, fg_color=BORDER_COLOR,
            progress_color=ACCENT,
            corner_radius=CORNER_RADIUS_SM,
            height=10,
        )
        self._comp_batch_progress_bar.pack(fill="x", pady=(SPACING_XS, 0))
        self._comp_batch_progress_bar.set(current / total if total > 0 else 0)

        # Per-file progress bar (for videos)
        file_frame = ctk.CTkFrame(inner, fg_color="transparent")
        file_frame.pack(fill="x", pady=(SPACING_SM, 0))

        ctk.CTkLabel(
            file_frame, text="Current file",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        self._comp_progress_bar = ctk.CTkProgressBar(
            file_frame, fg_color=BORDER_COLOR,
            progress_color=ACCENT,
            corner_radius=CORNER_RADIUS_SM,
            height=8,
        )
        self._comp_progress_bar.pack(fill="x", pady=(SPACING_XS, 0))
        self._comp_progress_bar.set(0)

        self._comp_percent_label = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=TEXT_MUTED,
        )
        self._comp_percent_label.pack(anchor="e")

    def _comp_update_batch_file_count(self, current, total):
        if hasattr(self, '_comp_batch_count_label') and self._comp_batch_count_label.winfo_exists():
            self._comp_batch_count_label.configure(text=f"File {current} of {total}")
        if hasattr(self, '_comp_batch_progress_bar') and self._comp_batch_progress_bar.winfo_exists():
            self._comp_batch_progress_bar.set(current / total if total > 0 else 0)
        # Reset per-file progress for the next file
        if self._comp_progress_bar and self._comp_progress_bar.winfo_exists():
            self._comp_progress_bar.set(0)

    # ── Compressor: Batch Result UI ───────────────────────────────

    def _comp_show_batch_result(self, summary, output_folder):
        if summary.get("error") == "cancelled":
            self._comp_cancel()
            return

        for w in self._comp_result_frame.winfo_children():
            w.destroy()

        result_card = ctk.CTkFrame(
            self._comp_result_frame, fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1, border_color=BORDER_COLOR,
        )
        result_card.pack(fill="x", pady=(0, SPACING_SM))

        inner = ctk.CTkFrame(result_card, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING_XL, pady=SPACING_LG)

        total_files = summary.get("total_files", 0)

        if total_files == 0:
            ctk.CTkLabel(
                inner, text="No supported files found",
                font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
                text_color=TEXT_MUTED,
            ).pack(anchor="w")
            return

        # Success header
        success_header = ctk.CTkFrame(inner, fg_color="transparent")
        success_header.pack(fill="x")

        completed = summary.get("completed", 0)
        failed = summary.get("failed", 0)

        ctk.CTkLabel(
            success_header, text=f"Batch compression complete!",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=SUCCESS_TEXT,
        ).pack(side="left")

        ctk.CTkButton(
            success_header, text="Open folder",
            command=lambda: self._comp_open_folder(os.path.join(output_folder, ".")),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BTN_SECONDARY,
            hover_color=BTN_SEC_HOVER,
            text_color=BTN_SEC_TEXT,
            corner_radius=CORNER_RADIUS_SM,
            width=100, height=30, cursor="hand2",
        ).pack(side="right")

        # File count summary
        count_text = f"{completed} files compressed"
        if failed > 0:
            count_text += f"  •  {failed} failed"

        ctk.CTkLabel(
            inner, text=count_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(SPACING_XS, 0))

        # Size stats
        total_original = summary.get("total_original", 0)
        total_compressed = summary.get("total_compressed", 0)
        reduction = summary.get("reduction_percent", 0)

        stats_frame = ctk.CTkFrame(inner, fg_color=ACCENT_LIGHT, corner_radius=CORNER_RADIUS_MD)
        stats_frame.pack(fill="x", pady=(SPACING_LG, 0))

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=SPACING_LG, pady=SPACING_LG)
        stats_inner.grid_columnconfigure((0, 1, 2), weight=1)

        # Original
        orig_f = ctk.CTkFrame(stats_inner, fg_color="transparent")
        orig_f.grid(row=0, column=0)
        ctk.CTkLabel(orig_f, text="Total Original",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=TEXT_MUTED).pack()
        ctk.CTkLabel(orig_f, text=get_file_size_str(total_original),
                     font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"), text_color=TEXT_DARK).pack()

        # Arrow
        ctk.CTkLabel(stats_inner, text="->",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=18), text_color=TEXT_MUTED
                     ).grid(row=0, column=1)

        # Compressed
        comp_f = ctk.CTkFrame(stats_inner, fg_color="transparent")
        comp_f.grid(row=0, column=2)
        ctk.CTkLabel(comp_f, text="Total Compressed",
                     font=ctk.CTkFont(family=FONT_FAMILY, size=11), text_color=TEXT_MUTED).pack()
        ctk.CTkLabel(comp_f, text=get_file_size_str(total_compressed),
                     font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"), text_color=ACCENT).pack()

        # Reduction badge
        saved = total_original - total_compressed
        badge_frame = ctk.CTkFrame(inner, fg_color=SUCCESS_BG, corner_radius=CORNER_RADIUS_MD)
        badge_frame.pack(fill="x", pady=(SPACING_SM, 0))

        ctk.CTkLabel(
            badge_frame,
            text=f"Reduced by {reduction:.1f}%  •  Saved {get_file_size_str(saved)}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=SUCCESS_TEXT,
        ).pack(padx=SPACING_LG, pady=SPACING_MD)

    def _comp_cancel(self):
        """Cancela a compressão em andamento."""
        if self._comp_cancel_event:
            self._comp_cancel_event.set()
        # Limpar UI de progresso
        for w in self._comp_result_frame.winfo_children():
            w.destroy()

        # Mostrar mensagem de cancelamento
        cancel_card = ctk.CTkFrame(
            self._comp_result_frame, fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1, border_color=BORDER_COLOR,
        )
        cancel_card.pack(fill="x", pady=(0, SPACING_SM))

        inner = ctk.CTkFrame(cancel_card, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING_XL, pady=SPACING_LG)

        ctk.CTkLabel(
            inner, text="Compression cancelled",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner, text="You can select a new file or adjust settings and try again.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_LIGHT,
        ).pack(anchor="w", pady=(SPACING_XS, 0))

    # ── Compressor: Progress UI ───────────────────────────────────

    def _comp_show_progress(self, message):
        # Clear results
        for w in self._comp_result_frame.winfo_children():
            w.destroy()

        progress_card = ctk.CTkFrame(
            self._comp_result_frame, fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1, border_color=BORDER_COLOR,
        )
        progress_card.pack(fill="x", pady=(0, SPACING_SM))

        inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING_XL, pady=SPACING_LG)

        # Header row: message + cancel button
        header_row = ctk.CTkFrame(inner, fg_color="transparent")
        header_row.pack(fill="x")

        self._comp_progress_label = ctk.CTkLabel(
            header_row, text=message,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_SECONDARY,
        )
        self._comp_progress_label.pack(side="left")

        self._comp_cancel_btn = ctk.CTkButton(
            header_row, text="Cancel",
            command=self._comp_cancel,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="white",
            corner_radius=CORNER_RADIUS_SM,
            width=80, height=30, cursor="hand2",
        )
        self._comp_cancel_btn.pack(side="right")

        self._comp_progress_bar = ctk.CTkProgressBar(
            inner, fg_color=BORDER_COLOR,
            progress_color=ACCENT,
            corner_radius=CORNER_RADIUS_SM,
            height=12, width=400,
        )
        self._comp_progress_bar.pack(fill="x", pady=(SPACING_SM, 0))
        self._comp_progress_bar.set(0)

        self._comp_percent_label = ctk.CTkLabel(
            inner, text="0%",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED,
        )
        self._comp_percent_label.pack(anchor="e", pady=(SPACING_XS, 0))

    def _comp_update_progress(self, percent):
        if self._comp_progress_bar and self._comp_progress_bar.winfo_exists():
            self._comp_progress_bar.set(percent / 100.0)
        if hasattr(self, '_comp_percent_label') and self._comp_percent_label.winfo_exists():
            self._comp_percent_label.configure(text=f"{percent:.0f}%")

    # ── Compressor: Results UI ────────────────────────────────────

    def _comp_show_result(self, result, output_path):
        # Ignorar se foi cancelado (UI já mostra mensagem de cancelamento)
        if result.get("error") == "cancelled":
            return

        for w in self._comp_result_frame.winfo_children():
            w.destroy()

        result_card = ctk.CTkFrame(
            self._comp_result_frame, fg_color=BG_WHITE,
            corner_radius=CORNER_RADIUS_XL,
            border_width=1, border_color=BORDER_COLOR,
        )
        result_card.pack(fill="x", pady=(0, SPACING_SM))

        inner = ctk.CTkFrame(result_card, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING_XL, pady=SPACING_LG)

        if not result.get("success"):
            # Error state
            ctk.CTkLabel(
                inner, text="Compression failed",
                font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
                text_color="#DC2626",
            ).pack(anchor="w")

            ctk.CTkLabel(
                inner, text=result.get("error", "Unknown error"),
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=TEXT_MUTED,
            ).pack(anchor="w", pady=(SPACING_SM, 0))
            return

        # Success state
        success_header = ctk.CTkFrame(inner, fg_color="transparent")
        success_header.pack(fill="x")

        ctk.CTkLabel(
            success_header, text="Compression complete!",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=SUCCESS_TEXT,
        ).pack(side="left")

        # Open folder button
        ctk.CTkButton(
            success_header, text="Open folder",
            command=lambda: self._comp_open_folder(output_path),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BTN_SECONDARY,
            hover_color=BTN_SEC_HOVER,
            text_color=BTN_SEC_TEXT,
            corner_radius=CORNER_RADIUS_SM,
            width=100, height=30, cursor="hand2",
        ).pack(side="right")

        # Stats
        stats_frame = ctk.CTkFrame(inner, fg_color=ACCENT_LIGHT, corner_radius=CORNER_RADIUS_MD)
        stats_frame.pack(fill="x", pady=(SPACING_LG, 0))

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=SPACING_LG, pady=SPACING_LG)

        original_size = result["original_size"]
        compressed_size = result["compressed_size"]
        reduction = result["reduction_percent"]

        # Three columns: Original | Compressed | Reduction
        stats_inner.grid_columnconfigure((0, 1, 2), weight=1)

        # Original
        orig_frame = ctk.CTkFrame(stats_inner, fg_color="transparent")
        orig_frame.grid(row=0, column=0)
        ctk.CTkLabel(
            orig_frame, text="Original",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED,
        ).pack()
        ctk.CTkLabel(
            orig_frame, text=get_file_size_str(original_size),
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=TEXT_DARK,
        ).pack()

        # Arrow
        ctk.CTkLabel(
            stats_inner, text="->",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18),
            text_color=TEXT_MUTED,
        ).grid(row=0, column=1, padx=SPACING_SM)

        # Compressed
        comp_frame = ctk.CTkFrame(stats_inner, fg_color="transparent")
        comp_frame.grid(row=0, column=1)

        # Reduction badge
        reduce_frame = ctk.CTkFrame(stats_inner, fg_color="transparent")
        reduce_frame.grid(row=0, column=2)
        ctk.CTkLabel(
            reduce_frame, text="Compressed",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED,
        ).pack()
        ctk.CTkLabel(
            reduce_frame, text=get_file_size_str(compressed_size),
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=ACCENT,
        ).pack()

        # Reduction percentage — big badge
        badge_frame = ctk.CTkFrame(inner, fg_color=SUCCESS_BG, corner_radius=CORNER_RADIUS_MD)
        badge_frame.pack(fill="x", pady=(SPACING_SM, 0))

        ctk.CTkLabel(
            badge_frame,
            text=f"Reduced by {reduction:.1f}%  •  Saved {get_file_size_str(original_size - compressed_size)}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=SUCCESS_TEXT,
        ).pack(padx=SPACING_LG, pady=SPACING_MD)

    def _comp_open_folder(self, filepath):
        try:
            folder = os.path.dirname(filepath)
            os.startfile(folder)
        except Exception as e:
            logging.error(f"Erro ao abrir pasta: {e}")


if __name__ == "__main__":
    app = GencoSearchApp()
    app.mainloop()