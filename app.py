"""
app.py - Advanced Modern Desktop UI Dashboard
Features: Left Sidebar Navigation, KPI Metric Cards, Dynamic Frame Switching,
Dark-Slate Styling, Custom Styled Data Tables, and Dual Matplotlib Visualizations.
"""

import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import backend

# Global Appearance Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Theme Color Palette (Modern Slate & Neon Accents)
COLOR_BG_MAIN = "#0F172A"       # Deep Slate Background
COLOR_BG_SIDEBAR = "#0B0F19"    # Darker Sidebar
COLOR_CARD_BG = "#1E293B"       # Card Container Background
COLOR_ACCENT = "#6366F1"        # Primary Indigo Accent
COLOR_ACCENT_HOVER = "#4F46E5"  # Hover Indigo
COLOR_TEXT_MUTED = "#94A3B8"    # Secondary Text
COLOR_SUCCESS = "#10B981"       # Emerald Green
COLOR_WARNING = "#F59E0B"       # Amber Warning
COLOR_DANGER = "#EF4444"        # Coral Red


class ModernOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FileOrganizer Pro — Modern Storage Dashboard")
        self.geometry("1280x780")
        self.minsize(1050, 650)
        self.configure(fg_color=COLOR_BG_MAIN)

        # State Variables
        self.inventory: list[dict] = []
        self.duplicates: dict[str, list[str]] = {}
        self.scanned_directory: str = ""

        # Layout Setup
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_area()
        self.setup_navigation_frames()

        # Show default view
        self.show_frame("analytics")

    # ---------------- UI Setup ----------------
    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=COLOR_BG_SIDEBAR, corner_radius=0, width=240)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(6, weight=1)

        # App Brand Header
        lbl_brand = ctk.CTkLabel(
            sidebar, 
            text="⚡ FileOrganizer", 
            font=("Inter", 20, "bold"),
            text_color="#F8FAFC"
        )
        lbl_brand.grid(row=0, column=0, padx=20, pady=(25, 5), sticky="w")

        lbl_sub = ctk.CTkLabel(
            sidebar, 
            text="EF101 System Engine", 
            font=("Inter", 11),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_sub.grid(row=1, column=0, padx=20, pady=(0, 25), sticky="w")

        # Navigation Buttons
        self.nav_btns = {}
        nav_items = [
            ("analytics", "📊 Analytics Dashboard"),
            ("inventory", "📂 File Explorer"),
            ("duplicates", "🔍 Duplicate Audit"),
            ("organize", "🗂️ Batch Organizer")
        ]

        for idx, (key, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                font=("Inter", 13, "bold"),
                fg_color="transparent",
                text_color="#94A3B8",
                hover_color=COLOR_CARD_BG,
                anchor="w",
                height=42,
                corner_radius=8,
                command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=idx, column=0, padx=12, pady=4, sticky="ew")
            self.nav_btns[key] = btn

        # Footer Info
        lbl_ver = ctk.CTkLabel(sidebar, text="v2.0 Modern Build", font=("Inter", 10), text_color="gray50")
        lbl_ver.grid(row=7, column=0, padx=20, pady=15, sticky="s")

    def setup_main_area(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Top Control & Scan Header Bar
        header_card = ctk.CTkFrame(self.main_container, fg_color=COLOR_CARD_BG, corner_radius=12)
        header_card.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        btn_scan = ctk.CTkButton(
            header_card,
            text="Select Directory & Scan",
            font=("Inter", 13, "bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            height=38,
            corner_radius=8,
            command=self.execute_scan
        )
        btn_scan.pack(side="left", padx=15, pady=12)

        self.lbl_active_dir = ctk.CTkLabel(
            header_card,
            text="No directory loaded",
            font=("Inter", 12),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_active_dir.pack(side="left", padx=10)

        self.btn_export_top = ctk.CTkButton(
            header_card,
            text="Export CSV",
            font=("Inter", 12, "bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=38,
            corner_radius=8,
            state="disabled",
            command=self.export_csv
        )
        self.btn_export_top.pack(side="right", padx=15, pady=12)

    def setup_navigation_frames(self):
        self.frames = {}

        # 1. Analytics Frame
        frame_analytics = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["analytics"] = frame_analytics

        # KPI Metrics Cards Grid
        metrics_grid = ctk.CTkFrame(frame_analytics, fg_color="transparent")
        metrics_grid.pack(fill="x", pady=(0, 15))
        metrics_grid.columnconfigure((0, 1, 2), weight=1, uniform="equal")

        self.card_files = self.create_kpi_card(metrics_grid, "Total Files", "0", "#3B82F6", 0)
        self.card_size = self.create_kpi_card(metrics_grid, "Total Storage", "0 MB", "#10B981", 1)
        self.card_dups = self.create_kpi_card(metrics_grid, "Duplicates Found", "0", "#F59E0B", 2)

        self.chart_area = ctk.CTkFrame(frame_analytics, fg_color=COLOR_CARD_BG, corner_radius=12)
        self.chart_area.pack(fill="both", expand=True)

        # 2. Inventory Frame
        frame_inventory = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["inventory"] = frame_inventory

        search_bar = ctk.CTkFrame(frame_inventory, fg_color=COLOR_CARD_BG, corner_radius=10)
        search_bar.pack(fill="x", pady=(0, 12))

        self.search_entry = ctk.CTkEntry(
            search_bar,
            placeholder_text="🔍 Search files by name, category, or extension...",
            font=("Inter", 13),
            fg_color="transparent",
            border_width=0,
            height=40
        )
        self.search_entry.pack(fill="x", padx=10)
        self.search_entry.bind("<KeyRelease>", self.filter_table)

        # Treeview Custom Style
        table_container = ctk.CTkFrame(frame_inventory, fg_color=COLOR_CARD_BG, corner_radius=12)
        table_container.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#1E293B", foreground="#F8FAFC", fieldbackground="#1E293B", rowheight=32, borderwidth=0)
        style.configure("Treeview.Heading", background="#0F172A", foreground="#6366F1", font=("Inter", 10, "bold"), relief="flat")
        style.map("Treeview", background=[('selected', '#4338CA')])

        cols = ("name", "category", "size_mb", "extension", "path")
        self.table = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse")
        
        self.table.heading("name", text="File Name")
        self.table.heading("category", text="Category")
        self.table.heading("size_mb", text="Size (MB)")
        self.table.heading("extension", text="Extension")
        self.table.heading("path", text="Full Path")

        self.table.column("name", width=220)
        self.table.column("category", width=110)
        self.table.column("size_mb", width=90, anchor="e")
        self.table.column("extension", width=90, anchor="center")
        self.table.column("path", width=450)

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.table.yview)
        self.table.configure(yscroll=scrollbar.set)
        
        self.table.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        self.table.bind("<Double-1>", self.on_double_click)

        # 3. Duplicates Frame
        frame_duplicates = ctk.CTkFrame(self.main_container, fg_color=COLOR_CARD_BG, corner_radius=12)
        self.frames["duplicates"] = frame_duplicates

        self.txt_dups = ctk.CTkTextbox(
            frame_duplicates, 
            font=("Consolas", 12), 
            fg_color="transparent", 
            text_color="#E2E8F0"
        )
        self.txt_dups.pack(fill="both", expand=True, padx=15, pady=15)

        # 4. Batch Organizer Frame
        frame_organize = ctk.CTkFrame(self.main_container, fg_color=COLOR_CARD_BG, corner_radius=12)
        self.frames["organize"] = frame_organize

        org_card = ctk.CTkFrame(frame_organize, fg_color="transparent")
        org_card.pack(fill="both", expand=True, padx=25, pady=25)

        lbl_org_title = ctk.CTkLabel(org_card, text="Automated Category Structuring", font=("Inter", 18, "bold"))
        lbl_org_title.pack(anchor="w", pady=(0, 5))

        lbl_org_desc = ctk.CTkLabel(
            org_card, 
            text="Safely copy sorted files into structured category folders (Images, Documents, Audio, etc.).", 
            text_color=COLOR_TEXT_MUTED,
            font=("Inter", 12)
        )
        lbl_org_desc.pack(anchor="w", pady=(0, 20))

        self.btn_run_org = ctk.CTkButton(
            org_card,
            text="Choose Target Directory & Execute Copy",
            font=("Inter", 13, "bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            height=42,
            corner_radius=8,
            state="disabled",
            command=self.execute_organize
        )
        self.btn_run_org.pack(anchor="w", pady=(0, 15))

        self.txt_org_log = ctk.CTkTextbox(org_card, font=("Consolas", 11), fg_color="#0F172A", text_color="#10B981")
        self.txt_org_log.pack(fill="both", expand=True)

    def create_kpi_card(self, parent, title, initial_val, accent_color, col_idx):
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=12)
        card.grid(row=0, column=col_idx, padx=6 if col_idx == 1 else 0, sticky="ew")

        border_strip = ctk.CTkFrame(card, fg_color=accent_color, height=4, corner_radius=0)
        border_strip.pack(fill="x", side="top")

        lbl_t = ctk.CTkLabel(card, text=title, font=("Inter", 11, "bold"), text_color=COLOR_TEXT_MUTED)
        lbl_t.pack(anchor="w", padx=15, pady=(12, 2))

        lbl_val = ctk.CTkLabel(card, text=initial_val, font=("Inter", 22, "bold"), text_color="#F8FAFC")
        lbl_val.pack(anchor="w", padx=15, pady=(0, 12))

        return lbl_val

    def show_frame(self, frame_key):
        for key, btn in self.nav_btns.items():
            if key == frame_key:
                btn.configure(fg_color=COLOR_CARD_BG, text_color="#F8FAFC")
            else:
                btn.configure(fg_color="transparent", text_color="#94A3B8")

        for f in self.frames.values():
            f.grid_forget()

        self.frames[frame_key].grid(row=1, column=0, sticky="nsew")

    # ---------------- Application Controller Logic ----------------
    def execute_scan(self):
        target_dir = filedialog.askdirectory()
        if not target_dir:
            return

        self.scanned_directory = target_dir
        self.lbl_active_dir.configure(text=f"Active: {target_dir}", text_color=COLOR_SUCCESS)
        self.update()

        # Execute Engine
        self.inventory = backend.scan_directory(target_dir)
        self.duplicates = backend.find_duplicates(self.inventory)

        self.btn_export_top.configure(state="normal")
        self.btn_run_org.configure(state="normal")

        # Update Views
        self.update_metrics()
        self.render_charts()
        self.populate_table(self.inventory)
        self.render_duplicates()

    def update_metrics(self):
        total_count = len(self.inventory)
        total_size_mb = sum(i['size_mb'] for i in self.inventory)
        dup_groups = len(self.duplicates)

        self.card_files.configure(text=f"{total_count:,}")
        if total_size_mb > 1024:
            self.card_size.configure(text=f"{round(total_size_mb / 1024, 2)} GB")
        else:
            self.card_size.configure(text=f"{round(total_size_mb, 2)} MB")

        self.card_dups.configure(text=f"{dup_groups} Groups")

    def render_charts(self):
        for widget in self.chart_area.winfo_children():
            widget.destroy()

        if not self.inventory:
            return

        cat_counts = {}
        for item in self.inventory:
            c = item['category']
            cat_counts[c] = cat_counts.get(c, 0) + 1

        # Matplotlib Dark Theme Figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.8), facecolor='#1E293B')
        
        # Donut Chart
        colors = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#64748B']
        ax1.set_facecolor('#1E293B')
        ax1.pie(
            list(cat_counts.values()), 
            labels=list(cat_counts.keys()), 
            autopct='%1.1f%%', 
            colors=colors[:len(cat_counts)],
            textprops=dict(color="#F8FAFC", fontsize=9),
            wedgeprops=dict(width=0.4, edgecolor='#1E293B')
        )
        ax1.set_title("File Category Ratio", color="#F8FAFC", fontsize=11, fontweight="bold")

        # Horizontal Bar Chart
        ax2.set_facecolor('#1E293B')
        ax2.barh(list(cat_counts.keys()), list(cat_counts.values()), color='#6366F1', height=0.5)
        ax2.tick_params(colors='#94A3B8', labelsize=8)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color('#334155')
        ax2.spines['bottom'].set_color('#334155')
        ax2.set_title("Volume by Category", color="#F8FAFC", fontsize=11, fontweight="bold")

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def populate_table(self, data_list):
        for row in self.table.get_children():
            self.table.delete(row)

        for item in data_list:
            self.table.insert("", "end", values=(
                item['name'], item['category'], item['size_mb'], item['extension'], item['path']
            ))

    def filter_table(self, event):
        query = self.search_entry.get().lower()
        filtered = [
            i for i in self.inventory 
            if query in i['name'].lower() or query in i['category'].lower() or query in i['extension'].lower()
        ]
        self.populate_table(filtered)

    def on_double_click(self, event):
        selected = self.table.selection()
        if not selected:
            return

        item_vals = self.table.item(selected[0], "values")
        file_path, category = item_vals[4], item_vals[1]

        if category == "Images":
            meta = backend.extract_image_metadata(file_path)
            messagebox.showinfo("Image Inspector", f"File: {item_vals[0]}\nResolution: {meta['dimensions']}\nFormat: {meta['format']}")
        else:
            messagebox.showinfo("File Inspector", f"File: {item_vals[0]}\nSize: {item_vals[2]} MB\nPath: {file_path}")

    def render_duplicates(self):
        self.txt_dups.delete("1.0", "end")
        if not self.duplicates:
            self.txt_dups.insert("1.0", "No exact duplicate content detected using SHA-256 analysis.")
            return

        out = "=== CRYPTOGRAPHIC SHA-256 DUPLICATE GROUPS ===\n\n"
        for idx, (f_hash, paths) in enumerate(self.duplicates.items(), start=1):
            out += f"Group {idx} [Hash: {f_hash[:16]}...]:\n"
            for p in paths:
                out += f"  └── {p}\n"
            out += "\n"
        self.txt_dups.insert("1.0", out)

    def export_csv(self):
        target = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
        if target and backend.export_inventory_csv(self.inventory, target):
            messagebox.showinfo("Export Successful", f"Inventory saved to:\n{target}")

    def execute_organize(self):
        dest = filedialog.askdirectory(title="Select Destination Directory")
        if not dest:
            return

        logs = backend.organize_files_safely(self.inventory, dest, mode='copy')
        self.txt_org_log.delete("1.0", "end")
        self.txt_org_log.insert("1.0", "\n".join(logs))
        messagebox.showinfo("Operation Complete", f"Files copied successfully to:\n{dest}")


if __name__ == "__main__":
    app = ModernOrganizerApp()
    app.mainloop()