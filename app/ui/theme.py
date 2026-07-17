"""Centralized visual themes and application stylesheet helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtGui import QColor

from app.ui.board.models import BoardTheme, CoordinateStyle


class ThemeName(Enum):
    """Built-in Mainline theme identifiers."""

    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class AppTheme:
    """Complete UI theme definition for app chrome and chessboard."""

    name: ThemeName
    background: str
    surface: str
    surface_alt: str
    elevated: str
    text: str
    muted_text: str
    border: str
    border_soft: str
    accent: str
    accent_hover: str
    accent_soft: str
    button: str
    button_hover: str
    button_pressed: str
    selection: str
    board: BoardTheme = field(default_factory=BoardTheme)


LIGHT_THEME = AppTheme(
    name=ThemeName.LIGHT,
    background="#F3F5F1",
    surface="#FFFFFF",
    surface_alt="#F8FAF6",
    elevated="#FFFFFF",
    text="#202622",
    muted_text="#69756D",
    border="#DCE3DA",
    border_soft="#E9EEE6",
    accent="#4F7BFF",
    accent_hover="#3F6DF2",
    accent_soft="#E9EEFF",
    button="#F8FAF7",
    button_hover="#EEF3EC",
    button_pressed="#E4EBE2",
    selection="#DCE7FF",
    board=BoardTheme(
        light_square=QColor("#EEE7D2"),
        dark_square=QColor("#7A9460"),
        border=QColor("#D8DED2"),
        border_background=QColor("#FFFFFF"),
        outer_margin_ratio=0.01,
        corner_radius_ratio=0.018,
        selected_color=QColor(255, 222, 93, 115),
        destination_color=QColor(35, 70, 38, 105),
        hover_color=QColor(255, 255, 255, 58),
        last_move_color=QColor(255, 235, 117, 88),
        coordinate_style=CoordinateStyle(
            light_square_text=QColor("#66745C"),
            dark_square_text=QColor("#E3EBCF"),
            opacity=0.62,
            edge_inset_ratio=0.09,
        ),
    ),
)

DARK_THEME = AppTheme(
    name=ThemeName.DARK,
    background="#1F2327",
    surface="#282D32",
    surface_alt="#23282D",
    elevated="#30363C",
    text="#ECEFF1",
    muted_text="#A8B1B8",
    border="#3C444B",
    border_soft="#333A40",
    accent="#8DA2FF",
    accent_hover="#A0B1FF",
    accent_soft="#303955",
    button="#30363C",
    button_hover="#394148",
    button_pressed="#252B30",
    selection="#344568",
    board=BoardTheme(
        light_square=QColor("#B9C0A4"),
        dark_square=QColor("#5E7354"),
        border=QColor("#3A4248"),
        border_background=QColor("#2A3035"),
        outer_margin_ratio=0.01,
        corner_radius_ratio=0.018,
        selected_color=QColor(255, 214, 89, 112),
        destination_color=QColor(18, 33, 23, 125),
        hover_color=QColor(255, 255, 255, 42),
        last_move_color=QColor(255, 226, 102, 76),
        coordinate_style=CoordinateStyle(
            light_square_text=QColor("#586250"),
            dark_square_text=QColor("#D8DEC9"),
            opacity=0.58,
            edge_inset_ratio=0.09,
        ),
    ),
)

THEMES = {ThemeName.LIGHT: LIGHT_THEME, ThemeName.DARK: DARK_THEME}


def stylesheet(theme: AppTheme) -> str:
    """Return a cohesive Qt stylesheet for Mainline widgets."""
    return f"""
    QMainWindow, #main_screen_stack, #home_screen, #workspace_screen, #drill_screen {{
        background: {theme.background};
        color: {theme.text};
        font-family: "Segoe UI", "Inter", "Arial";
        font-size: 13px;
    }}
    QMenuBar, QMenu, QStatusBar, QToolBar {{
        background: {theme.surface};
        color: {theme.text};
        border: 0;
    }}
    QMenuBar::item:selected, QMenu::item:selected {{ background: {theme.accent_soft}; border-radius: 6px; }}
    #home_title {{ font-size: 42px; font-weight: 750; color: {theme.text}; }}
    #home_subtitle, #muted_text {{ color: {theme.muted_text}; font-size: 14px; }}
    #section_heading, #screen_heading {{ color: {theme.text}; font-size: 20px; font-weight: 650; }}
    #panel_heading {{ color: {theme.text}; font-size: 13px; font-weight: 650; letter-spacing: 0.3px; }}
    #home_card, #board_region, #drill_board_shell, #move_tree_panel, #placeholder_panel {{
        background: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: 14px;
    }}
    QSplitter::handle {{ background: {theme.border_soft}; border-radius: 2px; margin: 4px; }}
    QPushButton, QToolButton {{
        background: {theme.button}; color: {theme.text}; border: 1px solid {theme.border};
        border-radius: 9px; padding: 7px 12px; font-weight: 600;
    }}
    QPushButton:hover, QToolButton:hover {{ background: {theme.button_hover}; border-color: {theme.accent}; }}
    QPushButton:pressed, QToolButton:pressed, QToolButton:checked {{ background: {theme.button_pressed}; }}
    QPushButton:disabled {{ color: {theme.muted_text}; background: {theme.surface_alt}; }}
    QLineEdit {{ background: {theme.surface_alt}; color: {theme.text}; border: 1px solid {theme.border}; border-radius: 9px; padding: 8px 10px; selection-background-color: {theme.selection}; }}
    QListWidget, QTreeWidget {{ background: {theme.surface_alt}; color: {theme.text}; border: 1px solid {theme.border_soft}; border-radius: 10px; padding: 5px; outline: 0; alternate-background-color: {theme.elevated}; }}
    QListWidget::item, QTreeWidget::item {{ border-radius: 7px; padding: 5px 7px; min-height: 24px; }}
    QListWidget::item:hover, QTreeWidget::item:hover {{ background: {theme.button_hover}; }}
    QListWidget::item:selected, QTreeWidget::item:selected {{ background: {theme.selection}; color: {theme.text}; }}
    QCheckBox {{ color: {theme.muted_text}; spacing: 8px; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 5px; border: 1px solid {theme.border}; background: {theme.surface_alt}; }}
    QCheckBox::indicator:checked {{ background: {theme.accent}; border-color: {theme.accent}; }}
    """
