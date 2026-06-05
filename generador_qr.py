"""
Generador de QR para videos
============================
Requisitos:
    pip install qrcode[pil] pillow

Cómo correr:
    python generador_qr.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import qrcode
from PIL import Image, ImageTk
import io
import os
import re
from datetime import datetime


# ─── Colores del tema ──────────────────────────────────────────────────────────
BG          = "#1e1e20"
SURFACE     = "#2a2a2e"
SURFACE2    = "#313136"
BORDER      = "#3a3a40"
TEXT        = "#f0efea"
TEXT_MUTED  = "#9c9b96"
ACCENT      = "#4f8ef7"
ACCENT_DARK = "#3a72d4"
SUCCESS     = "#5ab870"
BTN_BG      = "#313136"
BTN_HOVER   = "#3d3d44"


# ─── Plataformas ───────────────────────────────────────────────────────────────
PLATFORMS = {
    "YouTube":    {"placeholder": "https://www.youtube.com/watch?v=...",        "color": "#c0392b"},
    "Streamable": {"placeholder": "https://streamable.com/...",                 "color": "#1a73e8"},
    "Vimeo":      {"placeholder": "https://vimeo.com/...",                      "color": "#1ab7ea"},
    "TikTok":     {"placeholder": "https://www.tiktok.com/@usuario/video/...",  "color": "#010101"},
    "Otro enlace":{"placeholder": "https://...",                                "color": "#555555"},
}

EC_LEVELS = {
    "L – Mínimo (7%)":  qrcode.constants.ERROR_CORRECT_L,
    "M – Medio (15%)":  qrcode.constants.ERROR_CORRECT_M,
    "Q – Alto (25%)":   qrcode.constants.ERROR_CORRECT_Q,
    "H – Máximo (30%)": qrcode.constants.ERROR_CORRECT_H,
}


# ─── App principal ─────────────────────────────────────────────────────────────
class QRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generador de QR")
        self.resizable(True, True)
        self.configure(bg=BG)
        self.minsize(700, 560)

        # Estado
        self.current_platform = tk.StringVar(value="YouTube")
        self.qr_fg   = "#000000"
        self.qr_bg   = "#ffffff"
        self.qr_image: Image.Image | None = None
        self.history  = []  # list of dicts

        self._build_styles()
        self._build_ui()
        self.update_placeholder()

    # ── Estilos ttk ────────────────────────────────────────────────────────────
    def _build_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure(".",            background=BG,      foreground=TEXT,  font=("Helvetica", 11))
        s.configure("TFrame",       background=BG)
        s.configure("Card.TFrame",  background=SURFACE, relief="flat")
        s.configure("TLabel",       background=BG,      foreground=TEXT,  font=("Helvetica", 11))
        s.configure("Muted.TLabel", background=SURFACE, foreground=TEXT_MUTED, font=("Helvetica", 9))
        s.configure("Title.TLabel", background=BG,      foreground=TEXT,  font=("Helvetica", 20, "bold"))
        s.configure("Sub.TLabel",   background=BG,      foreground=TEXT_MUTED, font=("Helvetica", 10))
        s.configure("SectionLabel.TLabel", background=SURFACE, foreground=TEXT_MUTED,
                    font=("Helvetica", 9, "bold"))

        s.configure("TCombobox", fieldbackground=SURFACE2, background=SURFACE2,
                    foreground=TEXT, selectforeground=TEXT, selectbackground=SURFACE2,
                    arrowcolor=TEXT_MUTED, borderwidth=0)
        s.map("TCombobox", fieldbackground=[("readonly", SURFACE2)])

        s.configure("Accent.TButton", background=ACCENT,  foreground="white",
                    font=("Helvetica", 12, "bold"), borderwidth=0, relief="flat", padding=(0, 10))
        s.map("Accent.TButton",
              background=[("active", ACCENT_DARK), ("pressed", ACCENT_DARK)])

        s.configure("Secondary.TButton", background=BTN_BG, foreground=TEXT,
                    font=("Helvetica", 10), borderwidth=0, relief="flat", padding=(0, 8))
        s.map("Secondary.TButton",
              background=[("active", BTN_HOVER), ("pressed", BTN_HOVER)])

        s.configure("Plat.TButton", background=SURFACE2, foreground=TEXT_MUTED,
                    font=("Helvetica", 10), borderwidth=1, relief="solid", padding=(0, 8))
        s.map("Plat.TButton",
              background=[("active", SURFACE), ("selected", SURFACE)],
              foreground=[("active", TEXT)])

        s.configure("Horizontal.TScale", background=SURFACE, troughcolor=SURFACE2,
                    sliderrelief="flat", sliderlength=18)

        s.configure("Hist.TFrame", background=SURFACE2, relief="flat")

    # ── Layout principal ────────────────────────────────────────────────────────
    def _build_ui(self):
        # Columnas: formulario | preview
        self.columnconfigure(0, weight=3, minsize=380)
        self.columnconfigure(1, weight=2, minsize=260)
        self.rowconfigure(0, weight=1)

        self._build_left()
        self._build_right()

    # ── Panel izquierdo ─────────────────────────────────────────────────────────
    def _build_left(self):
        left = ttk.Frame(self, padding=(24, 24, 12, 24))
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)

        # Título
        ttk.Label(left, text="Generador de QR", style="Title.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(left, text="Para videos en YouTube, Streamable, Vimeo y más",
                  style="Sub.TLabel", background=BG).grid(row=1, column=0, sticky="w", pady=(2, 16))

        # Card formulario
        card = ttk.Frame(left, style="Card.TFrame", padding=(20, 18))
        card.grid(row=2, column=0, sticky="ew")
        card.columnconfigure(0, weight=1)

        row = 0

        # Plataforma
        ttk.Label(card, text="PLATAFORMA", style="SectionLabel.TLabel").grid(
            row=row, column=0, sticky="w", pady=(0, 6)); row += 1

        plat_frame = ttk.Frame(card, style="Card.TFrame")
        plat_frame.grid(row=row, column=0, sticky="ew", pady=(0, 16)); row += 1
        plat_frame.columnconfigure(tuple(range(len(PLATFORMS))), weight=1)

        self.plat_buttons = {}
        for i, name in enumerate(PLATFORMS):
            btn = tk.Button(
                plat_frame, text=name,
                bg=SURFACE2, fg=TEXT_MUTED, relief="flat",
                font=("Helvetica", 9, "bold"), cursor="hand2",
                activebackground=SURFACE, activeforeground=TEXT,
                bd=1, highlightthickness=1, highlightbackground=BORDER,
                padx=4, pady=6,
                command=lambda n=name: self.select_platform(n)
            )
            btn.grid(row=0, column=i, sticky="ew", padx=2)
            self.plat_buttons[name] = btn
        self.select_platform("YouTube", init=True)

        # URL
        ttk.Label(card, text="URL DEL VIDEO", style="SectionLabel.TLabel").grid(
            row=row, column=0, sticky="w", pady=(0, 6)); row += 1

        self.url_var = tk.StringVar()
        url_entry = tk.Entry(card, textvariable=self.url_var,
                             bg=SURFACE2, fg=TEXT, insertbackground=TEXT,
                             relief="flat", font=("Helvetica", 11),
                             highlightthickness=1, highlightbackground=BORDER,
                             highlightcolor=ACCENT)
        url_entry.grid(row=row, column=0, sticky="ew", ipady=8, pady=(0, 14)); row += 1
        url_entry.bind("<Return>", lambda e: self.generate())

        # Título
        ttk.Label(card, text="TÍTULO / DESCRIPCIÓN (OPCIONAL)", style="SectionLabel.TLabel").grid(
            row=row, column=0, sticky="w", pady=(0, 6)); row += 1

        self.title_var = tk.StringVar()
        title_entry = tk.Entry(card, textvariable=self.title_var,
                               bg=SURFACE2, fg=TEXT, insertbackground=TEXT,
                               relief="flat", font=("Helvetica", 11),
                               highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=ACCENT)
        title_entry.grid(row=row, column=0, sticky="ew", ipady=8, pady=(0, 14)); row += 1

        # Separador
        sep = ttk.Separator(card, orient="horizontal")
        sep.grid(row=row, column=0, sticky="ew", pady=(0, 14)); row += 1

        # Opciones avanzadas (toggle)
        self.adv_open = False
        self.adv_btn = tk.Button(card, text="▸  Opciones avanzadas",
                                 bg=SURFACE, fg=TEXT_MUTED, relief="flat",
                                 font=("Helvetica", 9, "bold"), cursor="hand2",
                                 activebackground=SURFACE, activeforeground=TEXT,
                                 anchor="w", command=self.toggle_advanced)
        self.adv_btn.grid(row=row, column=0, sticky="ew", pady=(0, 4)); row += 1

        self.adv_frame = ttk.Frame(card, style="Card.TFrame")
        self.adv_row_index = row; row += 1  # reservar espacio

        # Botón generar
        gen_btn = ttk.Button(card, text="  Generar código QR",
                             style="Accent.TButton", command=self.generate)
        gen_btn.grid(row=row, column=0, sticky="ew", pady=(10, 0)); row += 1

        # Historial
        ttk.Label(left, text="HISTORIAL DE SESIÓN", style="Sub.TLabel",
                  background=BG, foreground=TEXT_MUTED,
                  font=("Helvetica", 9, "bold")).grid(
            row=3, column=0, sticky="w", pady=(20, 6))

        hist_outer = tk.Frame(left, bg=BG)
        hist_outer.grid(row=4, column=0, sticky="ew")
        hist_outer.columnconfigure(0, weight=1)

        self.hist_canvas = tk.Canvas(hist_outer, bg=BG, bd=0,
                                     highlightthickness=0, height=160)
        sb = ttk.Scrollbar(hist_outer, orient="vertical",
                           command=self.hist_canvas.yview)
        self.hist_canvas.configure(yscrollcommand=sb.set)
        self.hist_canvas.grid(row=0, column=0, sticky="ew")
        sb.grid(row=0, column=1, sticky="ns")

        self.hist_inner = tk.Frame(self.hist_canvas, bg=BG)
        self.hist_win   = self.hist_canvas.create_window(
            (0, 0), window=self.hist_inner, anchor="nw")
        self.hist_inner.bind("<Configure>", self._on_hist_configure)
        self.hist_canvas.bind("<Configure>",
            lambda e: self.hist_canvas.itemconfig(self.hist_win, width=e.width))

        self._build_advanced(card)

    def _on_hist_configure(self, e):
        self.hist_canvas.configure(scrollregion=self.hist_canvas.bbox("all"))

    # ── Opciones avanzadas ──────────────────────────────────────────────────────
    def _build_advanced(self, card):
        f = self.adv_frame
        f.columnconfigure((0, 1), weight=1)

        # Colores
        ttk.Label(f, text="COLOR QR", style="SectionLabel.TLabel").grid(
            row=0, column=0, sticky="w", pady=(8, 4))
        ttk.Label(f, text="FONDO", style="SectionLabel.TLabel").grid(
            row=0, column=1, sticky="w", pady=(8, 4))

        self.fg_preview = tk.Button(
            f, bg=self.qr_fg, relief="flat", width=4, height=1, cursor="hand2",
            command=lambda: self.pick_color("fg"))
        self.fg_preview.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 12))

        self.bg_preview = tk.Button(
            f, bg=self.qr_bg, relief="flat", width=4, height=1, cursor="hand2",
            command=lambda: self.pick_color("bg"))
        self.bg_preview.grid(row=1, column=1, sticky="w", pady=(0, 12))

        # Tamaño
        self.size_var = tk.IntVar(value=300)
        ttk.Label(f, text="TAMAÑO (px)", style="SectionLabel.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        size_row = ttk.Frame(f, style="Card.TFrame")
        size_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        size_row.columnconfigure(0, weight=1)

        scale = ttk.Scale(size_row, from_=128, to=512, variable=self.size_var,
                          orient="horizontal", command=lambda v: self._update_size_label())
        scale.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.size_label = ttk.Label(size_row, text="300 px",
                                    style="SectionLabel.TLabel", width=6)
        self.size_label.grid(row=0, column=1)

        # Corrección de errores
        ttk.Label(f, text="CORRECCIÓN DE ERRORES", style="SectionLabel.TLabel").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.ec_var = tk.StringVar(value="M – Medio (15%)")
        ec_combo = ttk.Combobox(f, textvariable=self.ec_var,
                                values=list(EC_LEVELS.keys()),
                                state="readonly", font=("Helvetica", 10))
        ec_combo.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    def _update_size_label(self):
        v = int(self.size_var.get())
        # snap to multiples of 32
        snapped = round(v / 32) * 32
        self.size_label.config(text=f"{snapped} px")

    def toggle_advanced(self):
        if self.adv_open:
            self.adv_frame.grid_forget()
            self.adv_btn.config(text="▸  Opciones avanzadas")
        else:
            self.adv_frame.grid(row=self.adv_row_index, column=0, sticky="ew")
            self.adv_btn.config(text="▾  Opciones avanzadas")
        self.adv_open = not self.adv_open

    # ── Panel derecho (preview) ─────────────────────────────────────────────────
    def _build_right(self):
        right = ttk.Frame(self, padding=(12, 24, 24, 24))
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        ttk.Label(right, text="VISTA PREVIA", style="Sub.TLabel",
                  background=BG, foreground=TEXT_MUTED,
                  font=("Helvetica", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Marco del QR
        self.preview_frame = tk.Frame(right, bg=SURFACE, bd=0,
                                      highlightthickness=1,
                                      highlightbackground=BORDER)
        self.preview_frame.grid(row=1, column=0, sticky="nsew")
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)

        self.qr_label = tk.Label(self.preview_frame, bg=SURFACE,
                                 text="El QR aparecerá\naquí",
                                 fg=TEXT_MUTED, font=("Helvetica", 11))
        self.qr_label.grid(row=0, column=0, padx=20, pady=40)

        # Botones de descarga
        btn_frame = ttk.Frame(right)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        btn_frame.columnconfigure((0, 1, 2), weight=1)

        for col, (label, cmd) in enumerate([
            ("💾  PNG",  self.save_png),
            ("📄  SVG",  self.save_svg),
            ("📋  Copiar URL", self.copy_url),
        ]):
            b = ttk.Button(btn_frame, text=label,
                           style="Secondary.TButton", command=cmd)
            b.grid(row=0, column=col, sticky="ew", padx=2)

    # ── Lógica ─────────────────────────────────────────────────────────────────
    def select_platform(self, name, init=False):
        self.current_platform.set(name)
        for n, btn in self.plat_buttons.items():
            if n == name:
                btn.config(bg=ACCENT, fg="white",
                           highlightbackground=ACCENT)
            else:
                btn.config(bg=SURFACE2, fg=TEXT_MUTED,
                           highlightbackground=BORDER)
        if not init:
            self.update_placeholder()

    def update_placeholder(self):
        plat = self.current_platform.get()
        ph   = PLATFORMS[plat]["placeholder"]
        # Limpiar URL y mostrar placeholder visual
        self.url_var.set("")
        # Tkinter no tiene placeholder nativo; se puede simular pero es simple omitirlo

    def generate(self):
        url   = self.url_var.get().strip()
        title = self.title_var.get().strip()

        if not url:
            messagebox.showwarning("URL requerida", "Ingresa la URL del video antes de generar.")
            return

        size = max(128, min(512, round(int(self.size_var.get()) / 32) * 32))
        ec   = EC_LEVELS[self.ec_var.get()]

        qr = qrcode.QRCode(
            version=None,
            error_correction=ec,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color=self.qr_fg, back_color=self.qr_bg)
        img = img.resize((size, size), Image.NEAREST)
        self.qr_image = img

        # Mostrar en preview (ajustar a 240x240 max para la UI)
        display_size = min(240, size)
        preview_img  = img.resize((display_size, display_size), Image.NEAREST)
        tk_img = ImageTk.PhotoImage(preview_img)
        self.qr_label.config(image=tk_img, text="", bg="white",
                             padx=0, pady=0)
        self.qr_label.image = tk_img  # evitar GC

        self._add_history(url, title or url)

    def pick_color(self, which):
        current = self.qr_fg if which == "fg" else self.qr_bg
        result  = colorchooser.askcolor(color=current, title="Elegir color")
        if result and result[1]:
            hex_color = result[1]
            if which == "fg":
                self.qr_fg = hex_color
                self.fg_preview.config(bg=hex_color)
            else:
                self.qr_bg = hex_color
                self.bg_preview.config(bg=hex_color)

    def save_png(self):
        if self.qr_image is None:
            messagebox.showinfo("Sin QR", "Genera un QR primero.")
            return
        slug = self._slugify(self.title_var.get() or "qr")
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Todos", "*.*")],
            initialfile=slug + ".png",
            title="Guardar como PNG"
        )
        if path:
            self.qr_image.save(path, "PNG")
            messagebox.showinfo("Guardado", f"PNG guardado en:\n{path}")

    def save_svg(self):
        if self.qr_image is None:
            messagebox.showinfo("Sin QR", "Genera un QR primero.")
            return

        # Generar SVG vectorial (no pixel-based) con qrcode
        url = self.url_var.get().strip()
        ec  = EC_LEVELS[self.ec_var.get()]

        import qrcode.image.svg as qr_svg
        import io as _io

        factory = qr_svg.SvgFillImage
        qr = qrcode.make(url, image_factory=factory, error_correction=ec)

        slug = self._slugify(self.title_var.get() or "qr")
        path = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG", "*.svg"), ("Todos", "*.*")],
            initialfile=slug + ".svg",
            title="Guardar como SVG"
        )
        if path:
            qr.save(path)
            messagebox.showinfo("Guardado", f"SVG guardado en:\n{path}")

    def copy_url(self):
        url = self.url_var.get().strip()
        if not url:
            return
        self.clipboard_clear()
        self.clipboard_append(url)
        messagebox.showinfo("Copiado", "URL copiada al portapapeles.")

    def _add_history(self, url, label):
        now = datetime.now().strftime("%H:%M")
        plat = self.current_platform.get()
        color = PLATFORMS[plat]["color"]
        entry = {"url": url, "label": label, "time": now, "color": color, "plat": plat}
        self.history.insert(0, entry)
        if len(self.history) > 15:
            self.history.pop()
        self._render_history()

    def _render_history(self):
        for w in self.hist_inner.winfo_children():
            w.destroy()
        self.hist_inner.columnconfigure(0, weight=1)

        for i, h in enumerate(self.history):
            row_frame = tk.Frame(self.hist_inner, bg=SURFACE2, cursor="hand2")
            row_frame.grid(row=i, column=0, sticky="ew", pady=2)
            row_frame.columnconfigure(1, weight=1)

            dot = tk.Frame(row_frame, bg=h["color"], width=8, height=8)
            dot.grid(row=0, column=0, padx=(8, 6), pady=8)
            dot.grid_propagate(False)

            lbl_text = h["label"][:55] + "…" if len(h["label"]) > 55 else h["label"]
            lbl = tk.Label(row_frame, text=lbl_text, bg=SURFACE2, fg=TEXT_MUTED,
                           font=("Helvetica", 9), anchor="w")
            lbl.grid(row=0, column=1, sticky="ew")

            time_lbl = tk.Label(row_frame, text=h["time"], bg=SURFACE2,
                                fg=TEXT_MUTED, font=("Helvetica", 9, "bold"))
            time_lbl.grid(row=0, column=2, padx=8)

            # Click para recargar
            for widget in (row_frame, dot, lbl, time_lbl):
                widget.bind("<Button-1>", lambda e, idx=i: self._load_history(idx))

        self.hist_inner.update_idletasks()
        self.hist_canvas.configure(scrollregion=self.hist_canvas.bbox("all"))

    def _load_history(self, idx):
        h = self.history[idx]
        self.url_var.set(h["url"])
        self.title_var.set(h["label"] if h["label"] != h["url"] else "")
        self.select_platform(h["plat"])
        self.generate()

    @staticmethod
    def _slugify(s):
        s = s.lower().strip()
        for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")]:
            s = s.replace(a, b)
        s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
        return s or "qr"


# ─── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QRApp()
    app.mainloop()
