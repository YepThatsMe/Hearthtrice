from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QToolButton, QComboBox, QFrame, QShortcut
)
from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from PyQt5.QtGui import QFont, QTextCharFormat, QKeySequence, QWheelEvent


FONT_SIZES = (10, 13, 16)


class InfoBaseWidget(QWidget):
    save_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.edit_btn = QPushButton("Редактировать", self)
        self.edit_btn.setMinimumWidth(220)
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        self.save_btn = QPushButton("Сохранить", self)
        self.save_btn.setMinimumWidth(100)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.hide()
        self.cancel_btn = QPushButton("Отменить", self)
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.hide()
        self.toolbar = QWidget(self)
        tb_layout = QHBoxLayout(self.toolbar)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        self.bold_btn = QToolButton(self)
        self.bold_btn.setText("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setToolTip("Жирный")
        self.bold_btn.clicked.connect(lambda: self._apply_char_format("bold"))
        self.italic_btn = QToolButton(self)
        self.italic_btn.setText("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setToolTip("Курсив")
        self.italic_btn.clicked.connect(lambda: self._apply_char_format("italic"))
        self.underline_btn = QToolButton(self)
        self.underline_btn.setText("U")
        self.underline_btn.setCheckable(True)
        self.underline_btn.setToolTip("Подчеркнутый")
        self.underline_btn.clicked.connect(lambda: self._apply_char_format("underline"))
        self.style_combo = QComboBox(self)
        self.style_combo.addItems(["Параграф", "Заголовок 1", "Заголовок 2"])
        self.style_combo.currentIndexChanged.connect(self._apply_block_style)
        self.toolbar.hide()
        tb_layout.addWidget(self.bold_btn)
        tb_layout.addWidget(self.italic_btn)
        tb_layout.addWidget(self.underline_btn)
        tb_layout.addWidget(self.style_combo)
        tb_layout.addStretch()
        self.center_btns = QWidget(self)
        center_layout = QHBoxLayout(self.center_btns)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addStretch(2)
        center_layout.addWidget(self.edit_btn)
        center_layout.addWidget(self.save_btn)
        center_layout.addWidget(self.cancel_btn)
        center_layout.addStretch(1)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.toolbar)
        btn_row.addStretch()
        btn_row.addWidget(self.center_btns)
        btn_row.addStretch()
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setAcceptRichText(True)
        self._apply_read_only_style()
        layout = QVBoxLayout(self)
        layout.addLayout(btn_row)
        layout.addWidget(self.text_edit)
        self.text_edit.cursorPositionChanged.connect(self._update_format_buttons)
        self._shortcut_b = QShortcut(QKeySequence("Ctrl+B"), self)
        self._shortcut_b.setContext(Qt.WidgetWithChildrenShortcut)
        self._shortcut_b.activated.connect(lambda: self._apply_char_format("bold"))
        self._shortcut_i = QShortcut(QKeySequence("Ctrl+I"), self)
        self._shortcut_i.setContext(Qt.WidgetWithChildrenShortcut)
        self._shortcut_i.activated.connect(lambda: self._apply_char_format("italic"))
        self._shortcut_u = QShortcut(QKeySequence("Ctrl+U"), self)
        self._shortcut_u.setContext(Qt.WidgetWithChildrenShortcut)
        self._shortcut_u.activated.connect(lambda: self._apply_char_format("underline"))
        self.text_edit.viewport().installEventFilter(self)

    def _apply_read_only_style(self):
        self.text_edit.setStyleSheet("QTextEdit { background: transparent; border: none; }")
        self.text_edit.setFrameShape(QFrame.NoFrame)
        self.text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.text_edit.setCursor(Qt.ArrowCursor)

    def _apply_editor_style(self):
        self.text_edit.setStyleSheet("")
        self.text_edit.setFrameShape(QFrame.StyledPanel)
        self.text_edit.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_edit.unsetCursor()

    def _block_style_index_from_format(self, cur: QTextCharFormat) -> int:
        size = cur.fontPointSize()
        if size <= 0:
            size = 10
        if size >= 15:
            return 1
        if size >= 12:
            return 2
        return 0

    def _update_format_buttons(self):
        if self.text_edit.isReadOnly():
            return
        cur = self.text_edit.currentCharFormat()
        self.bold_btn.blockSignals(True)
        self.italic_btn.blockSignals(True)
        self.underline_btn.blockSignals(True)
        self.style_combo.blockSignals(True)
        self.bold_btn.setChecked(cur.fontWeight() == QFont.Bold)
        self.italic_btn.setChecked(cur.fontItalic())
        self.underline_btn.setChecked(cur.fontUnderline())
        self.style_combo.setCurrentIndex(self._block_style_index_from_format(cur))
        self.bold_btn.blockSignals(False)
        self.italic_btn.blockSignals(False)
        self.underline_btn.blockSignals(False)
        self.style_combo.blockSignals(False)

    def _apply_char_format(self, fmt: str):
        cur = self.text_edit.currentCharFormat()
        cf = QTextCharFormat()
        if fmt == "bold":
            cf.setFontWeight(QFont.Normal if cur.fontWeight() == QFont.Bold else QFont.Bold)
        elif fmt == "italic":
            cf.setFontItalic(not cur.fontItalic())
        elif fmt == "underline":
            cf.setFontUnderline(not cur.fontUnderline())
        self.text_edit.mergeCurrentCharFormat(cf)
        self._update_format_buttons()

    def _apply_block_style(self, index: int):
        cursor = self.text_edit.textCursor()
        cf = QTextCharFormat()
        if index == 0:
            cf.setFontPointSize(10)
        elif index == 1:
            cf.setFontPointSize(16)
        elif index == 2:
            cf.setFontPointSize(13)
        cursor.movePosition(cursor.StartOfBlock)
        cursor.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
        cursor.mergeCharFormat(cf)
        self._update_format_buttons()

    def set_content(self, html: str):
        self.text_edit.blockSignals(True)
        if html.strip().startswith("<"):
            self.text_edit.setHtml(html)
        else:
            self.text_edit.setPlainText(html)
        self.text_edit.setReadOnly(True)
        self._apply_read_only_style()
        self.edit_btn.show()
        self.toolbar.hide()
        self.save_btn.hide()
        self.cancel_btn.hide()
        try:
            self.edit_btn.clicked.disconnect()
        except TypeError:
            pass
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        self.text_edit.blockSignals(False)

    def ensure_read_only(self):
        if not self.text_edit.isReadOnly():
            self._set_read_only()

    def _set_read_only(self):
        self.text_edit.setReadOnly(True)
        self._apply_read_only_style()
        self.edit_btn.show()
        self.toolbar.hide()
        self.save_btn.hide()
        self.cancel_btn.hide()
        try:
            self.edit_btn.clicked.disconnect()
        except TypeError:
            pass
        self.edit_btn.clicked.connect(self._on_edit_clicked)

    def _on_edit_clicked(self):
        self._content_backup = self.text_edit.toHtml()
        self.text_edit.setReadOnly(False)
        self._apply_editor_style()
        self.edit_btn.hide()
        self.toolbar.show()
        self.save_btn.show()
        self.cancel_btn.show()
        self._update_format_buttons()
        self.style_combo.blockSignals(True)
        self.style_combo.setCurrentIndex(0)
        self.style_combo.blockSignals(False)

    def _on_save_clicked(self):
        self.save_requested.emit(self.text_edit.toHtml())
        self._set_read_only()

    def _on_cancel_clicked(self):
        self.text_edit.blockSignals(True)
        self.text_edit.setHtml(getattr(self, "_content_backup", ""))
        self.text_edit.blockSignals(False)
        self._set_read_only()

    def eventFilter(self, obj, event):
        if obj is self.text_edit.viewport() and event.type() == QEvent.Wheel and isinstance(event, QWheelEvent):
            if event.modifiers() == Qt.ControlModifier and not self.text_edit.isReadOnly():
                delta = event.angleDelta().y()
                if delta != 0:
                    cur = self.text_edit.currentCharFormat()
                    size = cur.fontPointSize()
                    if size <= 0:
                        size = 10
                    idx = min(range(len(FONT_SIZES)), key=lambda i: abs(FONT_SIZES[i] - size))
                    if delta > 0:
                        idx = min(idx + 1, len(FONT_SIZES) - 1)
                    else:
                        idx = max(idx - 1, 0)
                    size = FONT_SIZES[idx]
                    cf = QTextCharFormat()
                    cf.setFontPointSize(size)
                    self.text_edit.mergeCurrentCharFormat(cf)
                    self._update_format_buttons()
                return True
        return super().eventFilter(obj, event)
