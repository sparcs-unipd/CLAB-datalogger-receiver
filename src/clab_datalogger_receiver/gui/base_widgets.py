from typing import Callable, Type

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget


class BoxButtonsWidget(QWidget):
    """Wrapper to instantiate a series of buttons in a QBoxLayout widget."""

    def __init__(
        self,
        names: list[str],
        fcns: list[Callable],
        layout_type: Type[QVBoxLayout | QHBoxLayout] = QHBoxLayout,
    ) -> None:
        """Init the widget generating buttons accordingly to the names \
              and functions list passed."""

        super().__init__()

        assert len(names) == len(fcns)

        layout = layout_type()
        # layout = QHBoxLayout()

        for name, func in zip(names, fcns):
            btn = QPushButton(name)
            btn.clicked.connect(func)
            layout.addWidget(btn)

        self.setLayout(layout)
