# This Python 3 Code Editor was written as a tool to Write Small Python 3 Software.
# This Program was meant to be open source.
# Author: Mike Cintron W3XPT
# Software Version 2.0

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox, QToolBar, QDockWidget, QTextEdit, QStatusBar
)
from PyQt6.QtGui import (
    QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QAction, QIcon, QPainter, QTextFormat
)
from PyQt6.QtCore import Qt, QProcess, QRegularExpression, QRect, QSize

# --- Dark Theme Stylesheet ---
# A professional dark theme stylesheet for a consistent look and feel.
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
        font-family: Courier, monospace;
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
    QMessageBox {
        background-color: #2b2b2b;
    }
    QMessageBox QLabel {
        color: #f0f0f0;
    }
"""

# --- Code Editor with Line Numbers ---
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
    """
    A custom QPlainTextEdit that includes a line number area and current line highlighting.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)

        # Connect signals for updating line numbers and highlighting
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        """Calculates the width required for the line number area."""
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        # Calculate space needed for digits plus a little padding
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        """Sets the margin of the editor to make space for the line numbers."""
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        """Updates the line number area when the editor is scrolled."""
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        """Handles the resize event to adjust the line number area's geometry."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        """Highlights the line where the cursor is currently located."""
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            # Use a subtle color for the highlight that fits the dark theme
            lineColor = QColor("#3a3d42")
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        """Paints the line numbers in the line number area."""
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#313335"))  # Background color for the line number area

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Iterate over all visible blocks and draw their line numbers
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor("#858585")) # Color for the line numbers
                painter.drawText(0, int(top), self.lineNumberArea.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1


# --- Main Application Window ---
class PythonCodeEditor(QMainWindow):
    """
    The main window for the Python Code Editor application.
    It orchestrates the editor, menus, toolbars, and code execution.
    """
    def __init__(self):
        super().__init__()
        self.current_file_path = None
        self.process = QProcess(self)
        self.init_ui()

    def init_ui(self):
        """Initializes the user interface."""
        self.setWindowTitle("Python Code Editor")
        self.setGeometry(100, 100, 1000, 700)

        # Set a professional font
        font = QFont("Courier", 11)
        
        # Main editor widget is now the custom CodeEditor
        self.editor = CodeEditor()
        self.editor.setFont(font)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Apply syntax highlighting
        self.highlighter = PythonSyntaxHighlighter(self.editor.document())

        # The central widget is just the editor itself
        self.setCentralWidget(self.editor)
        
        # Create output dock
        self.create_output_dock()

        # Create actions, menus, and toolbar
        self.create_actions()
        self.create_menus()
        self.create_toolbar()
        
        # Create Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Connect signals
        self.editor.textChanged.connect(self.document_was_modified)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        self.new_file()


    def create_output_dock(self):
        """Creates the dockable widget for code output."""
        self.output_dock = QDockWidget("Output", self)
        self.output_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setFont(QFont("Courier", 10))
        self.output_dock.setWidget(self.output_text_edit)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)


    def create_actions(self):
        """Creates QAction objects for menu items and toolbar buttons."""
        # File actions
        self.new_action = QAction(QIcon.fromTheme("document-new"), "&New", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self.new_file)

        self.open_action = QAction(QIcon.fromTheme("document-open"), "&Open...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)

        self.save_action = QAction(QIcon.fromTheme("document-save"), "&Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_file)

        self.save_as_action = QAction(QIcon.fromTheme("document-save-as"), "Save &As...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.triggered.connect(self.save_file_as)

        self.exit_action = QAction(QIcon.fromTheme("application-exit"), "E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        # Edit actions
        self.cut_action = QAction(QIcon.fromTheme("edit-cut"), "Cu&t", self)
        self.cut_action.setShortcut("Ctrl+X")
        self.cut_action.triggered.connect(self.editor.cut)
        
        self.copy_action = QAction(QIcon.fromTheme("edit-copy"), "&Copy", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.triggered.connect(self.editor.copy)
        
        self.paste_action = QAction(QIcon.fromTheme("edit-paste"), "&Paste", self)
        self.paste_action.setShortcut("Ctrl+V")
        self.paste_action.triggered.connect(self.editor.paste)

        # Run action
        self.run_action = QAction(QIcon.fromTheme("system-run"), "&Run", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self.run_code)

        # View actions for font size
        self.increase_font_action = QAction(QIcon.fromTheme("zoom-in"), "Increase Font", self)
        self.increase_font_action.setShortcut("Ctrl++")
        self.increase_font_action.triggered.connect(self.increase_font_size)

        self.decrease_font_action = QAction(QIcon.fromTheme("zoom-out"), "Decrease Font", self)
        self.decrease_font_action.setShortcut("Ctrl+-")
        self.decrease_font_action.triggered.connect(self.decrease_font_size)
        
        # Help actions
        self.guide_action = QAction(QIcon.fromTheme("help-contents"), "User's Guide", self)
        self.guide_action.setShortcut("F1")
        self.guide_action.triggered.connect(self.show_user_guide)

        self.install_action = QAction(QIcon.fromTheme("help-faq"), "Installation Guide", self)
        self.install_action.triggered.connect(self.show_installation_guide)
        
        self.about_action = QAction(QIcon.fromTheme("help-about"), "About", self)
        self.about_action.triggered.connect(self.show_about_dialog)


    def create_menus(self):
        """Creates the main menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)

        # View menu
        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.increase_font_action)
        view_menu.addAction(self.decrease_font_action)

        # Run menu
        run_menu = self.menuBar().addMenu("&Run")
        run_menu.addAction(self.run_action)

        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.guide_action)
        help_menu.addAction(self.install_action)
        help_menu.addSeparator()
        help_menu.addAction(self.about_action)

    def create_toolbar(self):
        """Creates the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.increase_font_action)
        toolbar.addAction(self.decrease_font_action)
        toolbar.addSeparator()
        toolbar.addAction(self.run_action)

    def closeEvent(self, event):
        """Handles the window close event."""
        if self.maybe_save():
            event.accept()
        else:
            event.ignore()

    def document_was_modified(self):
        """Marks the document as modified."""
        self.setWindowModified(True)

    def set_current_file(self, file_path):
        """Sets the current file path and updates the window title."""
        self.current_file_path = file_path
        self.editor.document().setModified(False)
        self.setWindowModified(False)
        
        if file_path:
            shown_name = file_path
        else:
            shown_name = "Untitled.py"
        
        self.setWindowTitle(f"{shown_name}[*] - Python Code Editor")
        self.status_bar.showMessage(f"File: {shown_name}")

    def increase_font_size(self):
        """Increases the font size of the editor and output."""
        font = self.editor.font()
        current_size = font.pointSize()
        if current_size < 72:
            font.setPointSize(current_size + 2)
            self.editor.setFont(font)
            # Also update output font size for consistency
            output_font = self.output_text_edit.font()
            output_font.setPointSize(output_font.pointSize() + 2)
            self.output_text_edit.setFont(output_font)


    def decrease_font_size(self):
        """Decreases the font size of the editor and output."""
        font = self.editor.font()
        current_size = font.pointSize()
        if current_size > 6:
            font.setPointSize(current_size - 2)
            self.editor.setFont(font)
            # Also update output font size for consistency
            output_font = self.output_text_edit.font()
            output_font.setPointSize(output_font.pointSize() - 2)
            self.output_text_edit.setFont(output_font)

    # --- Help Dialogs ---
    def show_about_dialog(self):
        """Displays the 'About' dialog box."""
        QMessageBox.about(self, "About Python Code Editor",
                          "<h2>W3XPT's Python Code Editor v2.0</h2>"
                          "<p>A simple yet powerful code editor for Python 3, "
                          "built with PyQt6.</p>"
                          "<p>This editor provides syntax highlighting, "
                          "line numbering, and direct code execution.</p>")

    def show_user_guide(self):
        """Displays a message box with the user guide."""
        guide_text = """
        <h2>Python Code Editor - User's Guide</h2>
        <p>This guide explains how to use the features of this code editor.</p>
        
        <h3>File Operations</h3>
        <ul>
            <li><b>New (Ctrl+N):</b> Creates a new, blank file.</li>
            <li><b>Open (Ctrl+O):</b> Opens an existing Python file (.py).</li>
            <li><b>Save (Ctrl+S):</b> Saves the current file. If it's a new file, it will ask for a file name.</li>
            <li><b>Save As (Ctrl+Shift+S):</b> Saves the current file under a new name.</li>
        </ul>

        <h3>Editing</h3>
        <ul>
            <li><b>Standard Controls:</b> Use standard Cut (Ctrl+X), Copy (Ctrl+C), and Paste (Ctrl+V) commands.</li>
            <li><b>Syntax Highlighting:</b> Python code is automatically highlighted to improve readability.</li>
            <li><b>Line Numbers:</b> Line numbers are displayed on the left for easy navigation.</li>
            <li><b>Current Line Highlight:</b> The line your cursor is on is highlighted.</li>
        </ul>

        <h3>View</h3>
        <ul>
            <li><b>Increase Font (Ctrl++):</b> Makes the text in the editor and output panel larger.</li>
            <li><b>Decrease Font (Ctrl+-):</b> Makes the text in the editor and output panel smaller.</li>
        </ul>

        <h3>Running Code</h3>
        <ul>
            <li><b>Run (F5):</b> Executes the Python code in the editor.</li>
            <li><b>Important:</b> You must save the file before it can be run. If the file is not saved, you will be prompted to save it first.</li>
            <li><b>Output:</b> The output of your script, including any errors, will be displayed in the "Output" panel at the bottom.</li>
        </ul>
        """
        QMessageBox.information(self, "User's Guide", guide_text)

    def show_installation_guide(self):
        """Displays a message box with the installation guide."""
        install_text = """
        <h2>Python Code Editor - Installation Guide</h2>
        <p>Follow these steps to set up and run the editor.</p>

        <h3>Prerequisites</h3>
        <p><b>1. Python 3:</b> You must have Python 3 installed on your system. You can download it from python.org.</p>

        <h3>Installation</h3>
        <p><b>2. Install PyQt6:</b> This application requires the PyQt6 library. Open your terminal or command prompt and run the following command:</p>
        <pre style="background-color: #3c3c3c; padding: 5px; border-radius: 3px;">pip install PyQt6</pre>

        <h3>Running the Editor</h3>
        <p><b>3. Save the Code:</b> Save the editor's source code as a Python file (e.g., <b>editor.py</b>).</p>
        <p><b>4. Execute from Terminal:</b> Navigate to the directory where you saved the file and run it using Python:</p>
        <pre style="background-color: #3c3c3c; padding: 5px; border-radius: 3px;">python editor.py</pre>
        <p>This will launch the application window.</p>
        """
        QMessageBox.information(self, "Installation Guide", install_text)

    # --- File Operations ---
    def new_file(self):
        """Creates a new, empty file."""
        if self.maybe_save():
            self.editor.clear()
            self.set_current_file(None)
            self.editor.document().setModified(False) # Ensure new file isn't marked as modified
            self.setWindowModified(False)

    def open_file(self):
        """Opens a file from the disk."""
        if self.maybe_save():
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Python Files (*.py);;All Files (*)")
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.editor.setPlainText(content)
                        self.set_current_file(file_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def save_file(self):
        """Saves the current file."""
        if self.current_file_path is None:
            return self.save_file_as()
        else:
            return self._write_to_file(self.current_file_path)
            
    def save_file_as(self):
        """Saves the current file under a new name."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", self.current_file_path or "Untitled.py", "Python Files (*.py);;All Files (*)")
        if file_path:
            return self._write_to_file(file_path)
        return False
        
    def _write_to_file(self, file_path):
        """Helper function to write content to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.set_current_file(file_path)
            self.status_bar.showMessage(f"Saved to {file_path}", 2000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")
            return False

    def maybe_save(self):
        """Prompts the user to save if the document has been modified."""
        if not self.editor.document().isModified():
            return True
        
        ret = QMessageBox.warning(self, "Python Code Editor",
                                  "The document has been modified.\n"
                                  "Do you want to save your changes?",
                                  QMessageBox.StandardButton.Save |
                                  QMessageBox.StandardButton.Discard |
                                  QMessageBox.StandardButton.Cancel)
        
        if ret == QMessageBox.StandardButton.Save:
            return self.save_file()
        elif ret == QMessageBox.StandardButton.Cancel:
            return False
        return True

    # --- Code Execution ---
    def run_code(self):
        """Runs the Python code in the editor."""
        if not self.save_file():
            # If save fails or is cancelled, don't run
            self.status_bar.showMessage("Save cancelled. Run aborted.", 3000)
            return

        if self.current_file_path:
            self.output_text_edit.clear()
            self.output_text_edit.append(f"<font color='#888888'>--- Running {self.current_file_path} ---</font><br>")
            
            # Find python executable
            python_executable = sys.executable

            self.run_action.setEnabled(False)
            self.process.start(python_executable, [self.current_file_path])
        else:
            QMessageBox.warning(self, "Cannot Run", "Please save the file before running.")

    def handle_stdout(self):
        """Handles standard output from the running process."""
        data = self.process.readAllStandardOutput().data().decode('utf-8')
        self.output_text_edit.insertPlainText(data)

    def handle_stderr(self):
        """Handles standard error from the running process."""
        data = self.process.readAllStandardError().data().decode('utf-8')
        # Display errors in a distinct color (e.g., red)
        self.output_text_edit.insertHtml(f"<font color='#DA4453'>{data.replace('\n', '<br>')}</font>")


    def process_finished(self):
        """Called when the external process finishes."""
        self.output_text_edit.append("<br><font color='#888888'>--- Execution Finished ---</font>")
        self.run_action.setEnabled(True)


# --- Syntax Highlighting ---
class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """
    A syntax highlighter for Python code, optimized for a dark theme.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.highlighting_rules = []

        # Keyword format (blue)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda",
            "None", "nonlocal", "not", "or", "pass", "raise", "return",
            "True", "try", "while", "with", "yield"
        ]
        # Use QRegularExpression for robust word boundary matching
        self.highlighting_rules.extend([(QRegularExpression(f"\\b{w}\\b"), keyword_format) for w in keywords])
        
        # Built-in functions format (teal)
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#4EC9B0"))
        builtins = [
            "abs", "all", "any", "ascii", "bin", "bool", "bytearray", 
            "bytes", "callable", "chr", "classmethod", "compile", "complex",
            "delattr", "dict", "dir", "divmod", "enumerate", "eval", "exec",
            "filter", "float", "format", "frozenset", "getattr", "globals",
            "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance",
            "issubclass", "iter", "len", "list", "locals", "map", "max",
            "memoryview", "min", "next", "object", "oct", "open", "ord", "pow",
            "print", "property", "range", "repr", "reversed", "round", "set",
            "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super",
            "tuple", "type", "vars", "zip"
        ]
        self.highlighting_rules.extend([(QRegularExpression(f"\\b{b}\\b"), builtin_format) for b in builtins])

        # 'self' format (light blue)
        self_format = QTextCharFormat()
        self_format.setForeground(QColor("#9CDCFE"))
        self_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression("\\bself\\b"), self_format))

        # String format (orange) - using non-greedy match
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))
        self.highlighting_rules.append((QRegularExpression("\".*?\""), self.string_format))
        self.highlighting_rules.append((QRegularExpression("'.*?'"), self.string_format))
        
        # Comment format (green)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression("#[^\n]*"), comment_format))

        # Number format (light green)
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append((QRegularExpression("\\b[0-9]+\\.?[0-9]*\\b"), number_format))

        # Function/Class name format (yellow)
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))
        # Match names followed by (
        self.highlighting_rules.append((QRegularExpression("\\b[A-Za-z0-9_]+(?=\\()"), function_format))
        # Match names after 'class'
        self.highlighting_rules.append((QRegularExpression("(?<=class\\s)[A-Za-z0-9_]+"), function_format))
        # Match names after 'def'
        self.highlighting_rules.append((QRegularExpression("(?<=def\\s)[A-Za-z0-9_]+"), function_format))

    def highlightBlock(self, text):
        """
        Applies syntax highlighting to the given block of text. This corrected version
        properly handles multiline strings that span across multiple blocks.
        """
        # Apply all single-line rules first
        for pattern, format_rule in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format_rule)
        
        # --- Handle multiline strings ---
        self.setCurrentBlockState(0)
        
        in_multiline_state = self.previousBlockState()
        
        delimiter = ""
        if in_multiline_state == 1:
            delimiter = "'''"
        elif in_multiline_state == 2:
            delimiter = '"""'
            
        # If we are continuing a multiline string from a previous block
        if in_multiline_state > 0:
            end_index = text.find(delimiter)
            if end_index == -1: # String does not end in this block
                self.setCurrentBlockState(in_multiline_state)
                self.setFormat(0, len(text), self.string_format)
                return
            else: # String ends in this block
                length = end_index + len(delimiter)
                self.setFormat(0, length, self.string_format)
                start_index = length
        else:
            start_index = 0
            
        # Look for new multiline strings in the rest of the block
        while start_index < len(text):
            start_s = text.find("'''", start_index)
            start_d = text.find('"""', start_index)

            if start_s == -1 and start_d == -1:
                break # No more multiline strings found
                
            # Determine which delimiter appears first
            if start_d == -1 or (start_s != -1 and start_s < start_d):
                new_start_index = start_s
                delimiter = "'''"
                state = 1
            else:
                new_start_index = start_d
                delimiter = '"""'
                state = 2

            # Find the end of this newly started string
            end_index = text.find(delimiter, new_start_index + len(delimiter))
            
            if end_index == -1: # Unclosed string
                self.setCurrentBlockState(state)
                length = len(text) - new_start_index
                self.setFormat(new_start_index, length, self.string_format)
                break # This block is done
            else: # Closed string
                length = end_index - new_start_index + len(delimiter)
                self.setFormat(new_start_index, length, self.string_format)
                start_index = new_start_index + length


# --- Main execution block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Use Fusion style for a consistent, modern look across platforms
    app.setStyle("Fusion") 
    
    # Apply the dark stylesheet to the entire application
    app.setStyleSheet(DARK_STYLESHEET)

    editor_window = PythonCodeEditor()
    editor_window.show()
    sys.exit(app.exec())
