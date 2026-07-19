
import os

# Centralized Theme Configuration for Attar AIS
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME_FILE = os.path.join(BASE_DIR, "last_theme.txt")

def get_saved_theme():
    try:
        if os.path.exists(THEME_FILE):
            with open(THEME_FILE, "r") as f:
                theme = f.read().strip()
                if theme in ["dark", "light"]:
                    return theme
    except Exception as e:
        print(f"Theme read error: {e}")
    return 'dark'

def save_theme(theme):
    with open(THEME_FILE, "w") as f:
        f.write(theme)
    refresh_theme()

DARK_COLORS = {
    "bg":            "#0F172A",
    "bg_card":       "#1E293B",
    "bg_mid":        "#334155",
    "sidebar":       "#020617",
    "sidebar_mid":   "#0F172A",
    "sidebar_active":"#065F46",
    "sidebar_text":  "#FFFFFF",
    "accent":        "#10B981",
    "accent2":       "#34D399",
    "accent_light":  "#064E3B",
    "green":         "#10B981",
    "green_light":   "#064E3B",
    "red":           "#EF4444",
    "red_light":     "#7F1D1D",
    "yellow":        "#F59E0B",
    "yellow_light":  "#78350F",
    "blue":          "#3B82F6",
    "blue_light":    "#1E3A8A",
    "text_main":     "#F8FAFC",
    "text_sub":      "#CBD5E1",
    "text_dim":      "#94A3B8",
    "border":        "#334155",
    "separator":     "#1E293B",
}

LIGHT_COLORS = {
    "bg":            "#F1F5F9",
    "bg_card":       "#FFFFFF",
    "bg_mid":        "#E2E8F0",
    "sidebar":       "#0F172A",
    "sidebar_mid":   "#1E293B",
    "sidebar_active":"#065F46",
    "sidebar_text":  "#FFFFFF",
    "accent":        "#059669",
    "accent2":       "#34D399",
    "accent_light":  "#D1FAE5",
    "green":         "#059669",
    "green_light":   "#ECFDF5",
    "red":           "#DC2626",
    "red_light":     "#FEF2F2",
    "yellow":        "#D97706",
    "yellow_light":  "#FFFBEB",
    "blue":          "#2563EB",
    "blue_light":    "#EFF6FF",
    "text_main":     "#0F172A",
    "text_sub":      "#334155",
    "text_dim":      "#64748B",
    "border":        "#CBD5E1",
    "separator":     "#E2E8F0",
}

COLORS = {}
GLOBAL_STYLE = ""

def get_current_theme():
    return get_saved_theme()

def refresh_theme():
    global GLOBAL_STYLE
    theme = get_current_theme()
    new_colors = DARK_COLORS if theme == 'dark' else LIGHT_COLORS
    COLORS.clear()
    COLORS.update(new_colors)
    GLOBAL_STYLE = _generate_style()

def _generate_style():
    theme = get_saved_theme()
    alt_bg = COLORS['bg'] if theme == 'dark' else '#F8FAFC'
    
    return f"""
QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text_main']};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}}
QScrollArea, QScrollArea QWidget {{ background: transparent; border: none; }}

/* Table Spacing & Smoothness - Cleaned Up Vertical Headers */
QTableWidget {{
    background-color: {COLORS['bg_card']};
    alternate-background-color: {alt_bg};
    gridline-color: transparent;
    border: 1.5px solid {COLORS['border']};
    border-radius: 12px;
    outline: 0;
}}
QTableWidget::item {{
    padding: 10px;
    border: none;
}}
QHeaderView::section {{
    background-color: {COLORS['bg_mid']};
    color: {COLORS['text_dim']};
    padding: 10px;
    border: none;
    font-weight: 900;
    text-transform: uppercase;
    font-size: 11px;
}}
/* Hide the weird pill-shaped vertical headers globally */
QHeaderView::vertical {{
    background: transparent;
    width: 0px;
}}
QHeaderView::section:vertical {{
    background: transparent;
    border: none;
    color: transparent;
    width: 0px;
}}

/* Input Spacing */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_main']};
    border: 1.5px solid {COLORS['border']};
    border-radius: 10px;
    padding: 10px 15px;
}}
QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{ 
    border: 1.5px solid {COLORS['accent']}; 
    background-color: {COLORS['sidebar_mid'] if theme == 'dark' else '#F8FAFC'};
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_main']};
    border: 1.5px solid {COLORS['border']};
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 800;
}}
QPushButton:hover {{ 
    background-color: {COLORS['bg_mid']}; 
    border: 1.5px solid {COLORS['accent']};
}}
"""

def get_button_style(color_key='accent', font_size=13, padding="10px 20px"):
    return f"""
        QPushButton {{
            background-color: {COLORS[color_key]};
            color: white;
            border: none;
            border-radius: 8px;
            padding: {padding};
            font-weight: 800;
            font-size: {font_size}px;
        }}
        QPushButton:hover {{
            background-color: {COLORS[color_key + '_light'] if color_key + '_light' in COLORS else COLORS[color_key]};
            margin-top: -1px;
        }}
        QPushButton:pressed {{
            margin-top: 1px;
        }}
    """

def get_action_button_style(color_key='accent'):
    return get_button_style(color_key, font_size=11, padding="4px 10px")

# Initial Load
refresh_theme()

def apply_theme(widget_or_app):
    widget_or_app.setStyleSheet(GLOBAL_STYLE)
