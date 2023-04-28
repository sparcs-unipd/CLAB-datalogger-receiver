"""
Module to configure the colors of the application.

Mainly contains the colors for the plots, but could be extended \
    in the future.

Author:
    Marco Perin

"""

from PySide6.QtGui import QPen, QBrush

from pyqtgraph import mkPen, mkBrush

GRAPHS_COLORS: list[str] = [
    '#0072BD',
    '#D95319',
    '#EDB120',
    '#7E2F8E',
    '#77AC30',
    '#4DBEEE',
    '#A2142F',
]

BACKGROUND_COLOR: str = '#22222255'

GRAPHS_WIDTH: int = 2


def get_graphs_pens() -> list[QPen]:
    return [mkPen(color=color, width=GRAPHS_WIDTH) for color in GRAPHS_COLORS]


def get_background_brush() -> QBrush:
    return mkBrush(BACKGROUND_COLOR)
