# This Python 3 Code Editor was written as a tool to Write Small Python 3 Software.
# This Program was meant to be open source.
# Author: Mike Cintron W3XPT
# Software Version 2.1

import html
import os
import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QHBoxLayout, QWidget,
    QFileDialog, QMessageBox, QToolBar, QDockWidget, QTextEdit, QStatusBar,
    QDialog, QLabel, QLineEdit, QPushButton, QCheckBox,
)
from PyQt6.QtGui import (
    QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QAction, QIcon, QPainter,
    QTextFormat, QTextDocument, QKeySequence,
)
from PyQt6.QtCore import Qt, QProcess, QRegularExpression, QRect, QSize, QSettings

RECENT_FILES_MAX = 10
INDENT_SIZE = 4
SETTINGS_ORG = "W3XPT"
SETTINGS_APP = "PythonCodeEditor"

# --- Dark Theme Stylesheet ---
DARK_STYLESHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #f0f0f0;
        border: none;
    }
    QMainWindow, QMenuBar, QToolBar {
        background-color: #3c3c3c;
    }
    QPlainTextEdit, QTextEdit {
        background-color: #2b2b2b;
        color: #f0f0f0;
        border: 1px solid #3c3c3c;
        font-family: Consolas, "JetBrains Mono", "Courier New", monospace;
    }
    QMenuBar::item {
        background-color: #3c3c3c;
        color: #f0f0f0;
    }
    QMenuBar::item:selected, QMenu::item:selected {
        background-color: #555555;
    }
    QMenu {
        background-color: #3c3c3c;
        border: 1px solid #555555;
    }
    QStatusBar {
        background-color: #3c3c3c;
    }
    QDockWidget > QWidget {
        background-color: #2b2b2b;
    }
    QDockWidget::title {
        background-color: #3c3c3c;
        text-align: left;
        padding-left: 5px;
    }
    QPushButton {
        background-color: #555555;
        border: 1px solid #3c3c3c;
        padding: 5px;
        border-radius: 2px;
    }
    QPushButton:hover {
        background-color: #6a6a6a;
    }
    QPushButton:pressed {
        background-color: #4a4a4a;
    }
    QLineEdit {
        background-color: #2b2b2b;
        color: #f0f0f0;
        border: 1px solid #555555;
        padding: 4px;
    }
    QCheckBox {
        spacing: 6px;
    }
    QMessageBox {
        background-color: #2b2b2b;
    }
    QMessageBox QLabel {
        color: #f0f0f0;
    }
"""


class FindReplaceDialog(QDialog):
    """Non-modal find and replace dialog."""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("Find and Replace")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.returnPressed.connect(self.find_next)
        find_row.addWidget(self.find_input)
        layout.addLayout(find_row)

        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        self.replace_input.returnPressed.connect(self.replace_one)
        replace_row.addWidget(self.replace_input)
        layout.addLayout(replace_row)

        self.case_sensitive = QCheckBox("Match case")
        layout.addWidget(self.case_sensitive)

        button_row = QHBoxLayout()
        find_prev_btn = QPushButton("Find Previous")
        find_prev_btn.clicked.connect(self.find_previous)
        find_next_btn = QPushButton("Find Next")
        find_next_btn.clicked.connect(self.find_next)
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self.replace_one)
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self.replace_all)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        button_row.addWidget(find_prev_btn)
        button_row.addWidget(find_next_btn)
        button_row.addWidget(replace_btn)
        button_row.addWidget(replace_all_btn)
        button_row.addStretch()
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)

    def _find_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def find_next(self):
        text = self.find_input.text()
        if not text:
            return
        found = self.editor.document().find(text, self.editor.textCursor(), self._find_flags())
        if found.isNull():
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            found = self.editor.document().find(text, cursor, self._find_flags())
        if not found.isNull():
            self.editor.setTextCursor(found)

    def find_previous(self):
        text = self.find_input.text()
        if not text:
            return
        flags = self._find_flags() | QTextDocument.FindFlag.FindBackward
        found = self.editor.document().find(text, self.editor.textCursor(), flags)
        if found.isNull():
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.editor.setTextCursor(cursor)
            found = self.editor.document().find(text, cursor, flags)
        if not found.isNull():
            self.editor.setTextCursor(found)

    def replace_one(self):
        text = self.find_input.text()
        if not text:
            return
        cursor = self.editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText().replace("\u2029", "\n") == text:
            cursor.insertText(self.replace_input.text())
        self.find_next()

    def replace_all(self):
        text = self.find_input.text()
        if not text:
            return
        replace_text = self.replace_input.text()
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)
        count = 0
        while True:
            found = self.editor.document().find(text, self.editor.textCursor(), self._find_flags())
            if found.isNull():
                break
            found.insertText(replace_text)
            self.editor.setTextCursor(found)
            count += 1
        cursor.endEditBlock()
        self.parent().status_bar.showMessage(f"Replaced {count} occurrence(s).", 3000)


class LineNumberArea(QWidget):
    """A widget that displays line numbers for a CodeEditor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    """Custom editor with line numbers, current-line highlight, and Python indent."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        space = 10 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor("#3a3d42")
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#313335"))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(
                    0, int(top), self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number,
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self._indent_selection()
            return
        if event.key() == Qt.Key.Key_Backtab:
            self._dedent_selection()
            return
        super().keyPressEvent(event)

    def _selected_block_range(self):
        cursor = self.textCursor()
        start = min(cursor.anchor(), cursor.position())
        end = max(cursor.anchor(), cursor.position())
        temp = self.textCursor()
        temp.setPosition(start)
        start_block = temp.blockNumber()
        temp.setPosition(end)
        end_block = temp.blockNumber()
        if end > start and temp.positionInBlock() == 0 and end_block > start_block:
            end_block -= 1
        return start_block, end_block

    def _indent_selection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.insertText(" " * INDENT_SIZE)
            return

        start_block, end_block = self._selected_block_range()
        cursor.beginEditBlock()
        for block_num in range(end_block, start_block - 1, -1):
            block = self.document().findBlockByNumber(block_num)
            block_cursor = self.textCursor()
            block_cursor.setPosition(block.position())
            block_cursor.insertText(" " * INDENT_SIZE)
        cursor.endEditBlock()

    def _dedent_selection(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            block = cursor.block()
            text = block.text()
            remove = 0
            for ch in text[:INDENT_SIZE]:
                if ch == " ":
                    remove += 1
                else:
                    break
            if remove:
                block_cursor = self.textCursor()
                block_cursor.setPosition(block.position())
                block_cursor.movePosition(
                    block_cursor.MoveOperation.Right,
                    block_cursor.MoveMode.KeepAnchor,
                    remove,
                )
                block_cursor.removeSelectedText()
            return

        start_block, end_block = self._selected_block_range()
        cursor.beginEditBlock()
        for block_num in range(start_block, end_block + 1):
            block = self.document().findBlockByNumber(block_num)
            text = block.text()
            remove = 0
            for ch in text[:INDENT_SIZE]:
                if ch == " ":
                    remove += 1
                else:
                    break
            if remove:
                block_cursor = self.textCursor()
                block_cursor.setPosition(block.position())
                block_cursor.movePosition(
                    block_cursor.MoveOperation.Right,
                    block_cursor.MoveMode.KeepAnchor,
                    remove,
                )
                block_cursor.removeSelectedText()
        cursor.endEditBlock()


class PythonCodeEditor(QMainWindow):
    """Main window for the Python Code Editor application."""

    def __init__(self):
        super().__init__()
        self.current_file_path = None
        self.process = QProcess(self)
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.find_replace_dialog = None
        self._manual_stop = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Python Code Editor")
        self.setGeometry(100, 100, 1000, 700)

        font = QFont("Consolas", 11)
        if not QFont("Consolas").exactMatch():
            font = QFont("Courier New", 11)

        self.editor = CodeEditor()
        self.editor.setFont(font)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.highlighter = PythonSyntaxHighlighter(self.editor.document())
        self.setCentralWidget(self.editor)

        self.create_output_dock()
        self.create_actions()
        self.create_menus()
        self.create_toolbar()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.line_col_label = QLabel("Ln 1, Col 1")
        self.status_bar.addPermanentWidget(self.line_col_label)
        self.status_bar.showMessage("Ready")

        self.editor.textChanged.connect(self.document_was_modified)
        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.handle_process_error)

        self.restore_session()

    def create_output_dock(self):
        self.output_dock = QDockWidget("Output", self)
        self.output_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setFont(QFont("Consolas", 10))
        self.output_dock.setWidget(self.output_text_edit)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)

    def create_actions(self):
        self.new_action = QAction(QIcon.fromTheme("document-new"), "&New", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_file)

        self.open_action = QAction(QIcon.fromTheme("document-open"), "&Open...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_file)

        self.save_action = QAction(QIcon.fromTheme("document-save"), "&Save", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_file)

        self.save_as_action = QAction(QIcon.fromTheme("document-save-as"), "Save &As...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self.save_file_as)

        self.exit_action = QAction(QIcon.fromTheme("application-exit"), "E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        self.undo_action = QAction(QIcon.fromTheme("edit-undo"), "&Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.editor.undo)

        self.redo_action = QAction(QIcon.fromTheme("edit-redo"), "&Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.editor.redo)

        self.cut_action = QAction(QIcon.fromTheme("edit-cut"), "Cu&t", self)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.cut_action.triggered.connect(self.editor.cut)

        self.copy_action = QAction(QIcon.fromTheme("edit-copy"), "&Copy", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.editor.copy)

        self.paste_action = QAction(QIcon.fromTheme("edit-paste"), "&Paste", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.editor.paste)

        self.find_action = QAction(QIcon.fromTheme("edit-find"), "Find && Replace...", self)
        self.find_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_action.triggered.connect(self.show_find_replace)

        self.run_action = QAction(QIcon.fromTheme("system-run"), "&Run", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self.run_code)

        self.stop_action = QAction(QIcon.fromTheme("process-stop"), "&Stop", self)
        self.stop_action.setShortcut("Shift+F5")
        self.stop_action.triggered.connect(self.stop_code)
        self.stop_action.setEnabled(False)

        self.increase_font_action = QAction(QIcon.fromTheme("zoom-in"), "Increase Font", self)
        self.increase_font_action.setShortcut("Ctrl++")
        self.increase_font_action.triggered.connect(self.increase_font_size)

        self.decrease_font_action = QAction(QIcon.fromTheme("zoom-out"), "Decrease Font", self)
        self.decrease_font_action.setShortcut("Ctrl+-")
        self.decrease_font_action.triggered.connect(self.decrease_font_size)

        self.guide_action = QAction(QIcon.fromTheme("help-contents"), "User's Guide", self)
        self.guide_action.setShortcut("F1")
        self.guide_action.triggered.connect(self.show_user_guide)

        self.install_action = QAction(QIcon.fromTheme("help-faq"), "Installation Guide", self)
        self.install_action.triggered.connect(self.show_installation_guide)

        self.about_action = QAction(QIcon.fromTheme("help-about"), "About", self)
        self.about_action.triggered.connect(self.show_about_dialog)

    def create_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        self.recent_menu = file_menu.addMenu("Recent Files")
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.find_action)

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.increase_font_action)
        view_menu.addAction(self.decrease_font_action)

        run_menu = self.menuBar().addMenu("&Run")
        run_menu.addAction(self.run_action)
        run_menu.addAction(self.stop_action)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.guide_action)
        help_menu.addAction(self.install_action)
        help_menu.addSeparator()
        help_menu.addAction(self.about_action)

        self.update_recent_files_menu()

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(self.find_action)
        toolbar.addSeparator()
        toolbar.addAction(self.increase_font_action)
        toolbar.addAction(self.decrease_font_action)
        toolbar.addSeparator()
        toolbar.addAction(self.run_action)
        toolbar.addAction(self.stop_action)

    def closeEvent(self, event):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)
        if self.current_file_path:
            self.settings.setValue("lastFile", self.current_file_path)
        else:
            self.settings.remove("lastFile")
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    def document_was_modified(self):
        self.setWindowModified(True)

    def update_cursor_position(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.line_col_label.setText(f"Ln {line}, Col {col}")

    def set_current_file(self, file_path):
        self.current_file_path = file_path
        self.editor.document().setModified(False)
        self.setWindowModified(False)

        shown_name = file_path if file_path else "Untitled.py"
        self.setWindowTitle(f"{shown_name}[*] - Python Code Editor")
        self.status_bar.showMessage(f"File: {shown_name}")
        self.update_cursor_position()

    def show_find_replace(self):
        if self.find_replace_dialog is None:
            self.find_replace_dialog = FindReplaceDialog(self.editor, self)
        selected = self.editor.textCursor().selectedText().replace("\u2029", "\n")
        if selected and "\n" not in selected:
            self.find_replace_dialog.find_input.setText(selected)
        self.find_replace_dialog.show()
        self.find_replace_dialog.raise_()
        self.find_replace_dialog.activateWindow()
        self.find_replace_dialog.find_input.setFocus()

    def _recent_files_list(self):
        recent = self.settings.value("recentFiles", [])
        if isinstance(recent, str):
            return [recent] if recent else []
        return list(recent)

    def add_recent_file(self, file_path):
        path = os.path.abspath(file_path)
        recent = self._recent_files_list()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.settings.setValue("recentFiles", recent[:RECENT_FILES_MAX])
        self.update_recent_files_menu()

    def remove_recent_file(self, file_path):
        path = os.path.abspath(file_path)
        recent = [p for p in self._recent_files_list() if p != path]
        self.settings.setValue("recentFiles", recent)
        self.update_recent_files_menu()

    def clear_recent_files(self):
        self.settings.setValue("recentFiles", [])
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        self.recent_menu.clear()
        recent = self._recent_files_list()
        if not recent:
            empty = QAction("(No recent files)", self)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)
            return
        for path in recent:
            action = QAction(path, self)
            action.triggered.connect(lambda _checked, p=path: self.open_recent_file(p))
            self.recent_menu.addAction(action)
        self.recent_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self.clear_recent_files)
        self.recent_menu.addAction(clear_action)

    def open_recent_file(self, file_path):
        if not self.maybe_save():
            return
        if os.path.isfile(file_path):
            self.load_file(file_path)
        else:
            QMessageBox.warning(self, "Recent File", f"File not found:\n{file_path}")
            self.remove_recent_file(file_path)

    def restore_session(self):
        last_file = self.settings.value("lastFile", "")
        if last_file and os.path.isfile(last_file):
            self.load_file(last_file, add_to_recent=False)
        else:
            self.new_file()

    def increase_font_size(self):
        font = self.editor.font()
        if font.pointSize() < 72:
            font.setPointSize(font.pointSize() + 2)
            self.editor.setFont(font)
            output_font = self.output_text_edit.font()
            output_font.setPointSize(output_font.pointSize() + 2)
            self.output_text_edit.setFont(output_font)

    def decrease_font_size(self):
        font = self.editor.font()
        if font.pointSize() > 6:
            font.setPointSize(font.pointSize() - 2)
            self.editor.setFont(font)
            output_font = self.output_text_edit.font()
            output_font.setPointSize(output_font.pointSize() - 2)
            self.output_text_edit.setFont(output_font)

    def show_about_dialog(self):
        QMessageBox.about(
            self, "About Python Code Editor",
            "<h2>W3XPT's Python Code Editor v2.1</h2>"
            "<p>A simple yet powerful code editor for Python 3, built with PyQt6.</p>"
            "<p>Features include syntax highlighting, find/replace, line numbers, "
            "recent files, session restore, and direct code execution.</p>",
        )

    def show_user_guide(self):
        guide_text = """
        <h2>Python Code Editor - User's Guide</h2>

        <h3>File Operations</h3>
        <ul>
            <li><b>New (Ctrl+N):</b> Creates a new, blank file.</li>
            <li><b>Open (Ctrl+O):</b> Opens an existing Python file.</li>
            <li><b>Save (Ctrl+S):</b> Saves the current file.</li>
            <li><b>Save As (Ctrl+Shift+S):</b> Saves under a new name.</li>
            <li><b>Recent Files:</b> Reopen recently edited files from the File menu.</li>
        </ul>

        <h3>Editing</h3>
        <ul>
            <li><b>Undo / Redo (Ctrl+Z / Ctrl+Y):</b> Step through edit history.</li>
            <li><b>Find &amp; Replace (Ctrl+F):</b> Search and replace text.</li>
            <li><b>Indent / Dedent (Tab / Shift+Tab):</b> Indent selected lines or insert spaces.</li>
            <li><b>Syntax Highlighting:</b> Python code is highlighted automatically.</li>
        </ul>

        <h3>Running Code</h3>
        <ul>
            <li><b>Run (F5):</b> Saves and executes the script in its own directory.</li>
            <li><b>Stop (Shift+F5):</b> Terminates a running script.</li>
            <li><b>Output:</b> stdout and stderr appear in the Output panel.</li>
        </ul>
        """
        QMessageBox.information(self, "User's Guide", guide_text)

    def show_installation_guide(self):
        install_text = """
        <h2>Python Code Editor - Installation Guide</h2>

        <h3>Prerequisites</h3>
        <p>Python 3.8 or newer.</p>

        <h3>Installation</h3>
        <p>Install dependencies from the project folder:</p>
        <pre style="background-color: #3c3c3c; padding: 5px; border-radius: 3px;">pip install -r requirements.txt</pre>

        <h3>Running the Editor</h3>
        <pre style="background-color: #3c3c3c; padding: 5px; border-radius: 3px;">python editor.py</pre>
        """
        QMessageBox.information(self, "Installation Guide", install_text)

    def new_file(self):
        if self.maybe_save():
            self.editor.clear()
            self.set_current_file(None)
            self.editor.document().setModified(False)
            self.setWindowModified(False)

    def _default_open_dir(self):
        if self.current_file_path:
            return os.path.dirname(self.current_file_path)
        last_file = self.settings.value("lastFile", "")
        if last_file and os.path.isfile(last_file):
            return os.path.dirname(last_file)
        return ""

    def load_file(self, file_path, add_to_recent=True):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            self.set_current_file(file_path)
            self.settings.setValue("lastFile", file_path)
            if add_to_recent:
                self.add_recent_file(file_path)
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def open_file(self):
        if self.maybe_save():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open File", self._default_open_dir(),
                "Python Files (*.py);;All Files (*)",
            )
            if file_path:
                self.load_file(file_path)

    def save_file(self):
        if self.current_file_path is None:
            return self.save_file_as()
        return self._write_to_file(self.current_file_path)

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", self.current_file_path or "Untitled.py",
            "Python Files (*.py);;All Files (*)",
        )
        if file_path:
            return self._write_to_file(file_path)
        return False

    def _write_to_file(self, file_path):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self.set_current_file(file_path)
            self.settings.setValue("lastFile", file_path)
            self.add_recent_file(file_path)
            self.status_bar.showMessage(f"Saved to {file_path}", 2000)
            return True
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")
            return False

    def maybe_save(self):
        if not self.editor.document().isModified():
            return True

        ret = QMessageBox.warning(
            self, "Python Code Editor",
            "The document has been modified.\nDo you want to save your changes?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )

        if ret == QMessageBox.StandardButton.Save:
            return self.save_file()
        if ret == QMessageBox.StandardButton.Cancel:
            return False
        return True

    def run_code(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.status_bar.showMessage("A script is already running.", 3000)
            return

        if not self.save_file():
            self.status_bar.showMessage("Save cancelled. Run aborted.", 3000)
            return

        if not self.current_file_path:
            QMessageBox.warning(self, "Cannot Run", "Please save the file before running.")
            return

        self.output_text_edit.clear()
        safe_path = html.escape(self.current_file_path)
        self.output_text_edit.append(
            f"<font color='#888888'>--- Running {safe_path} ---</font><br>"
        )

        work_dir = os.path.dirname(os.path.abspath(self.current_file_path))
        if work_dir:
            self.process.setWorkingDirectory(work_dir)

        self.run_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.process.start(sys.executable, [self.current_file_path])

    def stop_code(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self._manual_stop = True
            self.process.kill()
            self.status_bar.showMessage("Execution stopped.", 3000)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.output_text_edit.insertPlainText(data)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        escaped = html.escape(data).replace("\n", "<br>")
        self.output_text_edit.insertHtml(f"<font color='#DA4453'>{escaped}</font>")

    def handle_process_error(self, error):
        messages = {
            QProcess.ProcessError.FailedToStart: "Failed to start Python.",
            QProcess.ProcessError.Crashed: "The process crashed.",
            QProcess.ProcessError.Timedout: "The process timed out.",
            QProcess.ProcessError.WriteError: "Could not write to the process.",
            QProcess.ProcessError.ReadError: "Could not read from the process.",
            QProcess.ProcessError.UnknownError: "An unknown process error occurred.",
        }
        QMessageBox.critical(self, "Run Error", messages.get(error, "Process error."))

    def process_finished(self, _exit_code=None, _exit_status=None):
        if self._manual_stop:
            footer = "--- Execution Stopped ---"
            self._manual_stop = False
        else:
            footer = "--- Execution Finished ---"
        self.output_text_edit.append(f"<br><font color='#888888'>{footer}</font>")
        self.run_action.setEnabled(True)
        self.stop_action.setEnabled(False)


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python, optimized for a dark theme."""

    @staticmethod
    def _regex(pattern):
        """Return a valid QRegularExpression, or None if the pattern is invalid."""
        expr = QRegularExpression(pattern)
        return expr if expr.isValid() else None

    def _add_rule(self, pattern, fmt):
        expr = self._regex(pattern)
        if expr is not None:
            self.highlighting_rules.append((expr, fmt))

    def _add_capture_rule(self, pattern, fmt, group=1):
        expr = self._regex(pattern)
        if expr is not None:
            self.capture_group_rules.append((expr, fmt, group))

    def __init__(self, parent):
        super().__init__(parent)
        self.highlighting_rules = []
        self.capture_group_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "and", "as", "assert", "async", "await", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for", "from", "global",
            "if", "import", "in", "is", "lambda", "None", "nonlocal", "not", "or", "pass",
            "raise", "return", "True", "try", "while", "with", "yield",
        ]
        self.highlighting_rules.extend(
            [(QRegularExpression(rf"\b{w}\b"), keyword_format) for w in keywords]
        )

        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#4EC9B0"))
        builtins = [
            "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes", "callable",
            "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod",
            "enumerate", "eval", "exec", "filter", "float", "format", "frozenset", "getattr",
            "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
            "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min",
            "next", "object", "oct", "open", "ord", "pow", "print", "property", "range",
            "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod",
            "str", "sum", "super", "tuple", "type", "vars", "zip",
        ]
        self.highlighting_rules.extend(
            [(QRegularExpression(rf"\b{b}\b"), builtin_format) for b in builtins]
        )

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#C586C0"))
        self.highlighting_rules.append(
            (QRegularExpression(r"@\w+(?:\.\w+)*"), decorator_format)
        )

        self_format = QTextCharFormat()
        self_format.setForeground(QColor("#9CDCFE"))
        self_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"\bself\b"), self_format))

        cls_format = QTextCharFormat()
        cls_format.setForeground(QColor("#9CDCFE"))
        self.highlighting_rules.append(
            (QRegularExpression(r"\bcls\b"), cls_format)
        )

        type_format = QTextCharFormat()
        type_format.setForeground(QColor("#4EC9B0"))
        type_names = [
            "int", "str", "float", "bool", "bytes", "list", "dict", "tuple", "set",
            "Any", "Optional", "Union", "Callable", "Iterable", "Iterator", "Type",
        ]
        # Qt does not support variable-length lookbehind (e.g. (?<=:\s*)).
        for name in type_names:
            self._add_capture_rule(rf"(?::\s*|\->\s*)({name})\b", type_format)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        prefixed_string_format = QTextCharFormat()
        prefixed_string_format.setForeground(QColor("#CE9178"))
        string_prefix = r"(?:[rRuUbBfF]{1,2})"
        self.highlighting_rules.append(
            (QRegularExpression(rf'{string_prefix}""".*?"""'), prefixed_string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(rf"{string_prefix}'''.*?'''"), prefixed_string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(rf'{string_prefix}"(?:\\.|[^"\\])*"'), prefixed_string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(rf"{string_prefix}'(?:\\.|[^'\\])*'"), prefixed_string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r'"(?:\\.|[^"\\])*"'), self.string_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"'(?:\\.|[^'\\])*'"), self.string_format)
        )

        fexpr_format = QTextCharFormat()
        fexpr_format.setForeground(QColor("#9CDCFE"))
        self.highlighting_rules.append(
            (QRegularExpression(r"\{[^{}]*\}"), fexpr_format)
        )

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), comment_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append(
            (QRegularExpression(r"\b0[xX][0-9a-fA-F]+\b"), number_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"\b\d+\.\d+([eE][+-]?\d+)?\b"), number_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression(r"\b\d+\b"), number_format)
        )

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))
        self._add_rule(r"\b[A-Za-z_]\w*(?=\()", function_format)
        self._add_capture_rule(r"\bclass\s+(\w+)", function_format)
        self._add_capture_rule(r"\bdef\s+(\w+)", function_format)

    def highlightBlock(self, text):
        for pattern, format_rule in self.highlighting_rules:
            match = pattern.globalMatch(text)
            while match.hasNext():
                hit = match.next()
                self.setFormat(hit.capturedStart(), hit.capturedLength(), format_rule)

        for pattern, format_rule, group in self.capture_group_rules:
            match = pattern.globalMatch(text)
            while match.hasNext():
                hit = match.next()
                self.setFormat(
                    hit.capturedStart(group), hit.capturedLength(group), format_rule
                )

        self.setCurrentBlockState(0)
        in_multiline_state = self.previousBlockState()

        delimiter = ""
        if in_multiline_state == 1:
            delimiter = "'''"
        elif in_multiline_state == 2:
            delimiter = '"""'

        if in_multiline_state > 0:
            end_index = text.find(delimiter)
            if end_index == -1:
                self.setCurrentBlockState(in_multiline_state)
                self.setFormat(0, len(text), self.string_format)
                return
            length = end_index + len(delimiter)
            self.setFormat(0, length, self.string_format)
            start_index = length
        else:
            start_index = 0

        while start_index < len(text):
            start_s = text.find("'''", start_index)
            start_d = text.find('"""', start_index)

            if start_s == -1 and start_d == -1:
                break

            if start_d == -1 or (start_s != -1 and start_s < start_d):
                new_start_index = start_s
                delimiter = "'''"
                state = 1
            else:
                new_start_index = start_d
                delimiter = '"""'
                state = 2

            prefix_start = new_start_index
            while prefix_start > 0 and text[prefix_start - 1] in "rRuUbBfF":
                prefix_start -= 1

            end_index = text.find(delimiter, new_start_index + len(delimiter))
            if end_index == -1:
                self.setCurrentBlockState(state)
                length = len(text) - prefix_start
                self.setFormat(prefix_start, length, self.string_format)
                break
            length = end_index - prefix_start + len(delimiter)
            self.setFormat(prefix_start, length, self.string_format)
            start_index = new_start_index + length


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOrganizationName(SETTINGS_ORG)
    app.setApplicationName(SETTINGS_APP)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)

    editor_window = PythonCodeEditor()
    editor_window.show()
    sys.exit(app.exec())

