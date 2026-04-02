import os
import sys
import json
import subprocess
import tempfile
import threading
import urllib.request
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from docx import Document
import fitz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VERSION = "1.0.2"
GITHUB_REPO = "DanielGenco/BotDeBusca"

# ── Palette ───────────────────────────────────────────────────────
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

BASE_PATH = r"C:\GencoServer"

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
    ".pdf":   ("📄", "#FEF2F2", "#DC2626"),
    ".docx":  ("📝", "#EFF6FF", "#2563EB"),
    ".xlsx":  ("📊", "#ECFDF5", "#059669"),
    ".xls":   ("📊", "#ECFDF5", "#059669"),
    ".txt":   ("📃", "#F3F4F6", "#6B7280"),
    ".jpg":   ("🖼", "#F5F3FF", "#7C3AED"),
    ".png":   ("🖼", "#F5F3FF", "#7C3AED"),
    "folder": ("📂", "#FEF3C7", "#B45309"),
}

FONT_FAMILY = "Segoe UI"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class GencoSearchApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Genco Busca")
        self.geometry("1360x860")
        self.minsize(1180, 720)
        self.configure(fg_color=BG_MAIN)
        self.protocol("WM_DELETE_WINDOW", self._close)

        self.spinner_frames = []
        self.spinner_gif = None
        self.spinner_running = False
        self.spinner_anim_id = None
        self.toast_id = None
        self.closing = False

        self.folder_var = ctk.StringVar(value="All folders")
        self.extension_var = ctk.StringVar(value="All")
        self.search_content_var = ctk.BooleanVar(value=False)

        self.progress_label = None
        self.search_entry = None
        self.count_label = None
        self.count_number_label = None
        self.result_scroll = None
        self.result_rows = []
        self._search_frame = None
        self._empty_state_frame = None

        self._center_window(820, 520)
        self._load_spinner()
        self._show_login()
        threading.Thread(target=self._check_for_updates, daemon=True).start()

    # ── Utilities ────────────────────────────────────────────────

    def _center_window(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _close(self):
        self.closing = True
        self._stop_spinner()
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
        path = os.path.join(BASE_DIR, "spinner.gif")
        if not os.path.exists(path):
            return
        try:
            self.spinner_gif = Image.open(path)
            while True:
                frame = self.spinner_gif.copy().convert("RGBA").resize((14, 14), Image.Resampling.LANCZOS)
                self.spinner_frames.append(ImageTk.PhotoImage(frame))
                self.spinner_gif.seek(self.spinner_gif.tell() + 1)
        except EOFError:
            pass
        except Exception:
            self.spinner_frames = []

    def _animate_spinner(self, ind=0):
        if self.closing:
            return
        lbl = self.progress_label
        if self.spinner_running and self.spinner_frames and lbl and lbl.winfo_exists():
            frame = self.spinner_frames[ind]
            lbl.configure(image=frame, text="  Searching...", fg=ACCENT)
            lbl.image = frame
            self.spinner_anim_id = self.after(90, self._animate_spinner, (ind + 1) % len(self.spinner_frames))
        else:
            if lbl and lbl.winfo_exists():
                lbl.configure(image="", text="")
                lbl.image = None

    def _start_spinner(self):
        if self.spinner_running:
            return
        self.spinner_running = True
        self._animate_spinner()

    def _stop_spinner(self):
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

    # ── Login Screen ─────────────────────────────────────────────

    def _show_login(self):
        self._clear_screen()
        self._center_window(820, 520)
        self.resizable(False, False)

        container = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        container.pack(fill="both", expand=True)

        # Left sidebar
        sidebar = ctk.CTkFrame(container, fg_color=SIDEBAR_BG, corner_radius=0, width=300)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        sb_body = ctk.CTkFrame(sidebar, fg_color="transparent")
        sb_body.pack(fill="both", expand=True, padx=36)

        ctk.CTkFrame(sb_body, fg_color=SIDEBAR_LINE, height=1, width=220).pack(pady=(28, 22))

        title_block = ctk.CTkFrame(sb_body, fg_color="transparent")
        title_block.pack(pady=(0, 0))

        ctk.CTkLabel(
            title_block,
            text="GENCO",
            font=ctk.CTkFont(family=FONT_FAMILY, size=50, weight="bold"),
            text_color="white",
        ).pack()

        busca_row = ctk.CTkFrame(title_block, fg_color="transparent")
        busca_row.pack()

        ctk.CTkLabel(
            busca_row,
            text="BUSCA",
            font=ctk.CTkFont(family=FONT_FAMILY, size=50, weight="bold"),
            text_color="white",
        ).pack(side="left")

        try:
            lupa_img = Image.open(os.path.join(BASE_DIR, "lupa_tela_inicial.png"))
            lupa_ctk = ctk.CTkImage(light_image=lupa_img, dark_image=lupa_img, size=(38, 38))
            lupa_label = ctk.CTkLabel(busca_row, image=lupa_ctk, text="", fg_color="transparent")
            lupa_label.pack(side="left", padx=(10, 0), pady=(8, 0))
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
        ).pack(pady=(20, 0))

        ctk.CTkLabel(
            sidebar,
            text="© 2026 Genco Import & Export",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#BABFCE",
        ).pack(side="bottom", pady=20)
            
        # Right area
        right = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=0)
        right.pack(side="left", fill="both", expand=True)
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(right, fg_color="transparent")
        inner.grid(row=0, column=0)

        try:
            logo_img = Image.open(os.path.join(BASE_DIR, "icon.png"))
            logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(290, 290))
            logo_label = ctk.CTkLabel(inner, image=logo_ctk, text="", fg_color="transparent")
            logo_label.pack(pady=(0, 32))
            logo_label.image = logo_ctk
        except Exception as e:
            print("Login logo error:", e)

        ctk.CTkLabel(
            inner,
            text="Welcome to Genco Busca",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text="Internal document search tool",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_MUTED,
        ).pack(pady=(0, 40))

        ctk.CTkButton(
            inner,
            text="Access →",
            command=self._show_search,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=10,
            width=300,
            height=48,
            cursor="hand2",
        ).pack(pady=(25, 0))

        ctk.CTkLabel(
            inner,
            text=f"v{VERSION} •  Internal access",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_LIGHT,
        ).pack(pady=(60, 0))

    # ── Search Screen (Redesigned) ───────────────────────────────

    def _show_search(self):
        self._clear_screen()
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
        header_inner.pack(fill="both", expand=True, padx=32)

        # Logo area
        logo_area = ctk.CTkFrame(header_inner, fg_color="transparent")
        logo_area.pack(side="left")

        try:
            logo_img = Image.open(os.path.join(BASE_DIR, "icon.png"))
            logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(50, 50))
            logo_label = ctk.CTkLabel(logo_area, image=logo_ctk, text="")
            logo_label.pack(side="left", pady=16)
            logo_label.image = logo_ctk
        except Exception:
            icon_box = ctk.CTkFrame(logo_area, fg_color=ACCENT, corner_radius=10, width=36, height=36)
            icon_box.pack(side="left", pady=15)
            icon_box.pack_propagate(False)
            ctk.CTkLabel(
                icon_box, text="G",
                font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
                text_color="white",
            ).place(relx=0.5, rely=0.5, anchor="center")

            txt_frame = ctk.CTkFrame(logo_area, fg_color="transparent")
            txt_frame.pack(side="left", padx=(10, 0), pady=15)
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
        ).pack(side="left", padx=20, pady=19)

        ctk.CTkLabel(
            header_inner,
            text="Genco Busca",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_MUTED,
        ).pack(side="left")

        # Version pill on the right
        pill = ctk.CTkFrame(header_inner, fg_color="#F0FDF4", corner_radius=20, border_width=1, border_color="#BBF7D0")
        pill.pack(side="right", pady=22)
        pill_inner = ctk.CTkFrame(pill, fg_color="transparent")
        pill_inner.pack(padx=12, pady=5)

        dot = ctk.CTkFrame(pill_inner, fg_color="#10B981", corner_radius=4, width=7, height=7)
        dot.pack(side="left", padx=(0, 7))
        dot.pack_propagate(False)
        ctk.CTkLabel(
            pill_inner,
            text="Server File Finder  v1.0.1",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color="#065F46",
        ).pack(side="left")

        # ── Main area ─────────────────────────────────────────────
        main = ctk.CTkFrame(search_frame, fg_color="transparent", corner_radius=0)
        main.pack(fill="both", expand=True, padx=36, pady=(28, 16))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)

        # ── Page title ────────────────────────────────────────────
        title_row = ctk.CTkFrame(main, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        accent_bar = ctk.CTkFrame(title_row, fg_color=ACCENT, width=4, height=36, corner_radius=2)
        accent_bar.pack(side="left", padx=(0, 14))
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
        ).pack(anchor="w", pady=(2, 0))

        # ── Search card ───────────────────────────────────────────
        search_card = ctk.CTkFrame(
            main,
            fg_color=BG_WHITE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        search_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        card_inner = ctk.CTkFrame(search_card, fg_color="transparent")
        card_inner.pack(fill="x", padx=24, pady=22)

        # ─ Main search bar (hero) ─
        search_hero = ctk.CTkFrame(
            card_inner,
            fg_color=INPUT_BG,
            corner_radius=12,
            border_width=2,
            border_color=INPUT_BORDER,
            height=52,
        )
        search_hero.pack(fill="x", pady=(0, 16))
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
            corner_radius=8,
            width=34,
            height=34,
        )
        search_icon_frame.pack(side="left", padx=(7, 0), pady=7)
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
            corner_radius=10,
            border_width=0,
            fg_color="transparent",
            text_color=TEXT_DARK,
            placeholder_text="Type the file or folder name",
            placeholder_text_color=TEXT_LIGHT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        self.search_entry.pack(side="left", fill="both", expand=True, padx=(10, 6), pady=2)
        self.search_entry.bind("<Return>", lambda e: self._start_search())

        # Internal vertical divider
        ctk.CTkFrame(
            search_inner,
            fg_color=BORDER_COLOR,
            width=1,
            height=28,
        ).pack(side="left", pady=11)

        # Inline buttons in the search bar
        ctk.CTkButton(
            search_inner,
            text="Clear",
            command=self._clear,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color="transparent",
            hover_color=BTN_SEC_HOVER,
            text_color=TEXT_MUTED,
            corner_radius=8,
            width=72,
            height=34,
            cursor="hand2",
        ).pack(side="left", padx=(6, 4), pady=7)

        ctk.CTkButton(
            search_inner,
            text="Search",
            command=self._start_search,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            corner_radius=10,
            width=120,
            height=36,
            cursor="hand2",
        ).pack(side="left", padx=(2, 7), pady=6)

        # ─ Filter row ─
        filters_row = ctk.CTkFrame(card_inner, fg_color="transparent")
        filters_row.pack(fill="x")

        # Label "Filters:"
        ctk.CTkLabel(
            filters_row,
            text="Filters:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color="#000000",
        ).pack(side="left", padx=(2, 14))

        # Folder
        folder_wrap = ctk.CTkFrame(filters_row, fg_color="transparent")
        folder_wrap.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            folder_wrap,
            text="Folder",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="#000000",
        ).pack(anchor="w", pady=(0, 3))

        ctk.CTkComboBox(
            folder_wrap,
            values=["All folders"] + AVAILABLE_FOLDERS,
            variable=self.folder_var,
            width=200,
            height=36,
            corner_radius=9,
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
        type_wrap.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            type_wrap,
            text="Type",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="#000000",
        ).pack(anchor="w", pady=(0, 3))

        ctk.CTkComboBox(
            type_wrap,
            values=EXTENSIONS_UI,
            variable=self.extension_var,
            width=140,
            height=36,
            corner_radius=9,
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
        ctk.CTkFrame(filters_row, fg_color=BORDER_COLOR, width=1, height=36).pack(side="left", padx=14)

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

        # ── Status/spinner bar ────────────────────────────────────
        status_bar = ctk.CTkFrame(main, fg_color="transparent", height=20)
        status_bar.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        status_bar.grid_propagate(False)

        self.progress_label = tk.Label(
            status_bar,
            text="",
            bg=BG_MAIN,
            fg=ACCENT,
            font=(FONT_FAMILY, 10),
            anchor="w",
            compound="left",
        )
        self.progress_label.pack(side="left", padx=2)

        # ── Results card ──────────────────────────────────────────
        result_card = ctk.CTkFrame(
            main,
            fg_color=BG_WHITE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        result_card.grid(row=3, column=0, sticky="nsew")

        # Results header
        result_header = ctk.CTkFrame(result_card, fg_color=BG_WHITE, corner_radius=0, height=52)
        result_header.pack(fill="x")
        result_header.pack_propagate(False)

        rh_left = ctk.CTkFrame(result_header, fg_color="transparent")
        rh_left.pack(side="left", padx=22, pady=14, fill="y")

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
        col_h_inner.pack(fill="both", expand=True, padx=22)

        ctk.CTkLabel(
            col_h_inner,
            text="NAME / PATH",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(side="left", pady=8)

        ctk.CTkLabel(
            col_h_inner,
            text="TYPE",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="e",
            width=60,
        ).pack(side="right", pady=8)

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
        footer.pack(fill="x", side="bottom", pady=(2, 10))

        ctk.CTkLabel(
            footer,
            text="Genco Import & Export  •  Server File Finder  •  v1.0.1",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            text_color=TEXT_LIGHT,
        ).pack()

    # ── Empty state ──────────────────────────────────────────────

    def _show_empty_state(self):
        self._empty_state_frame = ctk.CTkFrame(self.result_scroll, fg_color="transparent")
        self._empty_state_frame.pack(expand=True, pady=48)

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
        ).pack(pady=(12, 4))

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
        inner.pack(fill="both", expand=True, padx=22, pady=11)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        # Colored icon by type
        icon_box = ctk.CTkFrame(left, fg_color=icon_bg, corner_radius=11, width=40, height=40)
        icon_box.pack(side="left", padx=(0, 16))
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
        ).pack(anchor="w", pady=(2, 1))

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
            corner_radius=7,
            width=54,
            height=26,
        ).pack(anchor="e", pady=7)

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
            empty.pack(expand=True, pady=48)
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
            ).pack(pady=(12, 4))

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
        try:
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return ""

    def _read_pdf(self, path):
        try:
            with fitz.open(path) as doc:
                return "\n".join(page.get_text() for page in doc)
        except Exception:
            return ""

    def _search_in(self, root_directory, term):
        search_content = self.search_content_var.get()
        extension_ui = self.extension_var.get()
        selected_extension = EXTENSIONS_MAP.get(extension_ui, "All")

        exact_matches, related_matches = [], []
        valid_extensions = [".pdf", ".docx", ".xlsx", ".xls", ".txt", ".jpg", ".png"]
        limit = 100

        if not os.path.exists(root_directory):
            return []

        for root, folders, files in os.walk(root_directory):
            try:
                for folder in folders:
                    name = folder.lower()
                    path = os.path.join(root, folder)
                    if name == term:
                        exact_matches.append(path)
                    elif term in name:
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
                        if ext == ".pdf":
                            has_content = term in self._read_pdf(path).lower()
                        elif ext == ".docx":
                            has_content = term in self._read_docx(path).lower()

                    if file_name.lower() == term or has_content:
                        exact_matches.append(path)
                    elif term in file_name.lower():
                        related_matches.append(path)
            except (PermissionError, Exception):
                pass

        return exact_matches + related_matches

    def _folder_thread(self, term, folder):
        results = self._search_in(os.path.join(BASE_PATH, folder), term)
        self.after(0, lambda: self._show_results(results))

    def _all_folders_thread(self, term):
        results = []
        for f in AVAILABLE_FOLDERS:
            results += self._search_in(os.path.join(BASE_PATH, f), term)
        self.after(0, lambda: self._show_results(results))

    def _start_search(self):
        term = self.search_entry.get().strip().lower()
        if not term:
            messagebox.showwarning("Warning", "Enter the file or folder name.")
            return

        folder = self.folder_var.get().strip()
        self._remove_empty_state()
        self._clear_results()
        self._start_spinner()

        if not folder or folder == "All folders":
            threading.Thread(target=self._all_folders_thread, args=(term,), daemon=True).start()
        else:
            threading.Thread(target=self._folder_thread, args=(term, folder), daemon=True).start()

    def _clear(self):
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

    def _open(self, path):
        try:
            os.startfile(path)
        except Exception:
            pass

    def _copy(self, path):
        try:
            self.clipboard_clear()
            self.clipboard_append(path)

            notice = ctk.CTkLabel(
                self._search_frame,
                text="  ✓  Path copied  ",
                fg_color=SUCCESS_BG,
                text_color=SUCCESS_TEXT,
                corner_radius=10,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            )
            notice.place(relx=1.0, rely=1.0, anchor="se", x=-24, y=-20)

            if self.toast_id:
                try:
                    self.after_cancel(self.toast_id)
                except Exception:
                    pass

            self.toast_id = self.after(1800, lambda: notice.destroy() if notice.winfo_exists() else None)
        except Exception:
            pass

    # ── Auto-update ──────────────────────────────────────────────

    def _check_for_updates(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "GencoBusca-Updater"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode())

            latest_tag = data.get("tag_name", "").lstrip("v")
            if not latest_tag:
                return

            current = tuple(int(x) for x in VERSION.split("."))
            latest  = tuple(int(x) for x in latest_tag.split("."))
            if latest <= current:
                return

            download_url = None
            for asset in data.get("assets", []):
                if asset["name"].lower().endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break

            if download_url:
                self.after(0, lambda: self._show_update_dialog(latest_tag, download_url))
        except Exception:
            pass  # sem internet ou repositório privado — ignora silenciosamente

    def _show_update_dialog(self, new_version, download_url):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Update Available")
        dialog.geometry("440x230")
        dialog.resizable(False, False)
        dialog.configure(fg_color=BG_WHITE)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  // 2) - 220
        y = self.winfo_y() + (self.winfo_height() // 2) - 115
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text="New update available!",
            font=ctk.CTkFont(family=FONT_FAMILY, size=17, weight="bold"),
            text_color=TEXT_DARK,
        ).pack(pady=(32, 6))

        ctk.CTkLabel(
            dialog,
            text=f"Version {new_version} is ready to download.\nDo you want to install it now?",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_MUTED,
            justify="center",
        ).pack(pady=(0, 28))

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
            corner_radius=8,
            width=160,
            height=40,
            cursor="hand2",
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="Later",
            command=dialog.destroy,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=BTN_SECONDARY,
            hover_color=BTN_SEC_HOVER,
            text_color=BTN_SEC_TEXT,
            corner_radius=8,
            width=100,
            height=40,
            cursor="hand2",
        ).pack(side="left")

    def _download_and_install(self, url, dialog):
        dialog.destroy()

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
        ).pack(pady=(28, 10))

        bar = ctk.CTkProgressBar(prog, width=340, progress_color=ACCENT)
        bar.pack()
        bar.set(0)

        pct_label = ctk.CTkLabel(
            prog,
            text="0%",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED,
        )
        pct_label.pack(pady=(6, 0))

        def do_download():
            try:
                fd, tmp = tempfile.mkstemp(suffix=".exe")
                os.close(fd)

                def reporthook(block_num, block_size, total_size):
                    if total_size > 0 and not self.closing:
                        pct = min(block_num * block_size / total_size, 1.0)
                        self.after(0, lambda p=pct: bar.set(p))
                        self.after(0, lambda p=pct: pct_label.configure(text=f"{int(p * 100)}%"))

                urllib.request.urlretrieve(url, tmp, reporthook)

                if not self.closing:
                    self.after(0, lambda: self._launch_installer(tmp, prog))
            except Exception as e:
                if not self.closing:
                    self.after(0, prog.destroy)
                    self.after(0, lambda: messagebox.showerror(
                        "Update Error", f"Failed to download update:\n{e}"
                    ))

        threading.Thread(target=do_download, daemon=True).start()

    def _launch_installer(self, installer_path, prog_dialog):
        prog_dialog.destroy()
        subprocess.Popen([installer_path], shell=True)
        self._close()


if __name__ == "__main__":
    app = GencoSearchApp()
    app.mainloop()