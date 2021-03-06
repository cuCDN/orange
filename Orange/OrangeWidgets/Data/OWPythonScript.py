import sys
import os
import code
import keyword
import itertools
import unicodedata

from PyQt4.QtGui import (
    QSyntaxHighlighter, QPlainTextEdit, QTextCharFormat, QTextCursor,
    QTextDocument, QPlainTextDocumentLayout, QBrush, QFont, QColor, QPalette,
    QStyledItemDelegate, QStyleOptionViewItemV4, QLineEdit, QListView,
    QSizePolicy, QAction, QMenu, QKeySequence, QSplitter, QToolButton,
    QItemSelectionModel, QFileDialog
)

from PyQt4.QtCore import Qt, QRegExp, QByteArray
from PyQt4.QtCore import SIGNAL

from OWWidget import *

from OWItemModels import PyListModel, ModelActionsWidget

import OWGUI
import Orange

NAME = "Python Script"
DESCRIPTION = "Executes a Python script."
LONG_DESCRIPTION = ""
ICON = "icons/PythonScript.svg"
PRIORITY = 3150

INPUTS = [("in_data", Orange.data.Table, "setExampleTable", Default),
          ("in_distance", Orange.misc.SymMatrix, "setDistanceMatrix", Default),
          ("in_learner", Orange.core.Learner, "setLearner", Default),
          ("in_classifier", Orange.core.Classifier, "setClassifier", Default),
          ("in_object", object, "setObject")]

OUTPUTS = [("out_data", Orange.data.Table, ),
           ("out_distance", Orange.misc.SymMatrix, ),
           ("out_learner", Orange.core.Learner, ),
           ("out_classifier", Orange.core.Classifier, Dynamic),
           ("out_object", object, Dynamic)]


def text_format(foreground=Qt.black, weight=QFont.Normal):
    fmt = QTextCharFormat()
    fmt.setForeground(QBrush(foreground))
    fmt.setFontWeight(weight)
    return fmt


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):

        self.keywordFormat = text_format(Qt.blue, QFont.Bold)
        self.stringFormat = text_format(Qt.darkGreen)
        self.defFormat = text_format(Qt.black, QFont.Bold)
        self.commentFormat = text_format(Qt.lightGray)
        self.decoratorFormat = text_format(Qt.darkGray)

        self.keywords = list(keyword.kwlist)

        self.rules = [(QRegExp(r"\b%s\b" % kwd), self.keywordFormat)
                      for kwd in self.keywords] + \
                     [(QRegExp(r"\bdef\s+([A-Za-z_]+[A-Za-z0-9_]+)\s*\("),
                       self.defFormat),
                      (QRegExp(r"\bclass\s+([A-Za-z_]+[A-Za-z0-9_]+)\s*\("),
                       self.defFormat),
                      (QRegExp(r"'.*'"), self.stringFormat),
                      (QRegExp(r'".*"'), self.stringFormat),
                      (QRegExp(r"#.*"), self.commentFormat),
                      (QRegExp(r"@[A-Za-z_]+[A-Za-z0-9_]+"),
                       self.decoratorFormat)]

        self.multilineStart = QRegExp(r"(''')|" + r'(""")')
        self.multilineEnd = QRegExp(r"(''')|" + r'(""")')

        QSyntaxHighlighter.__init__(self, parent)

    def highlightBlock(self, text):
        for pattern, format in self.rules:
            exp = QRegExp(pattern)
            index = exp.indexIn(text)
            while index >= 0:
                length = exp.matchedLength()
                if exp.numCaptures() > 0:
                    self.setFormat(exp.pos(1), len(str(exp.cap(1))), format)
                else:
                    self.setFormat(exp.pos(0), len(str(exp.cap(0))), format)
                index = exp.indexIn(text, index + length)

        # Multi line strings
        start = self.multilineStart
        end = self.multilineEnd

        self.setCurrentBlockState(0)
        startIndex, skip = 0, 0
        if self.previousBlockState() != 1:
            startIndex, skip = start.indexIn(text), 3
        while startIndex >= 0:
            endIndex = end.indexIn(text, startIndex + skip)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLen = len(text) - startIndex
            else:
                commentLen = endIndex - startIndex + 3
            self.setFormat(startIndex, commentLen, self.stringFormat)
            startIndex, skip = (start.indexIn(text,
                                              startIndex + commentLen + 3),
                                3)


class PythonScriptEditor(QPlainTextEdit):
    INDENT = 4

    def lastLine(self):
        text = str(self.toPlainText())
        pos = self.textCursor().position()
        index = text.rfind("\n", 0, pos)
        text = text[index: pos].lstrip("\n")
        return text

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            text = self.lastLine()
            indent = len(text) - len(text.lstrip())
            if text.strip() == "pass" or text.strip().startswith("return "):
                indent = max(0, indent - self.INDENT)
            elif text.strip().endswith(":"):
                indent += self.INDENT
            QPlainTextEdit.keyPressEvent(self, event)
            self.insertPlainText(" " * indent)
        elif event.key() == Qt.Key_Tab:
            self.insertPlainText(" " * self.INDENT)
        elif event.key() == Qt.Key_Backspace:
            text = self.lastLine()
            if text and not text.strip():
                cursor = self.textCursor()
                for i in range(min(self.INDENT, len(text))):
                    cursor.deletePreviousChar()
            else:
                QPlainTextEdit.keyPressEvent(self, event)

        else:
            QPlainTextEdit.keyPressEvent(self, event)


class PythonConsole(QPlainTextEdit, code.InteractiveConsole):
    def __init__(self, locals=None, parent=None):
        QPlainTextEdit.__init__(self, parent)
        code.InteractiveConsole.__init__(self, locals)
        self.history, self.historyInd = [""], 0
        self.loop = self.interact()
        self.loop.next()

    def setLocals(self, locals):
        self.locals = locals

    def interact(self, banner=None):
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "
        cprt = ('Type "help", "copyright", "credits" or "license" '
                'for more information.')
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        else:
            self.write("%s\n" % str(banner))
        more = 0
        while 1:
            try:
                if more:
                    prompt = sys.ps2
                else:
                    prompt = sys.ps1
                self.new_prompt(prompt)
                yield
                try:
                    line = self.raw_input(prompt)
                except EOFError:
                    self.write("\n")
                    break
                else:
                    more = self.push(line)
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0

    def raw_input(self, prompt):
        input = str(self.document().lastBlock().previous().text())
        return input[len(prompt):]

    def new_prompt(self, prompt):
        self.write(prompt)
        self.newPromptPos = self.textCursor().position()

    def write(self, data):
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.insertText(data)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def push(self, line):
        if self.history[0] != line:
            self.history.insert(0, line)
        self.historyInd = 0

        saved = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = self, self
            return code.InteractiveConsole.push(self, line)
        finally:
            sys.stdout, sys.stderr = saved

    def setLine(self, line):
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.End)
        cursor.setPosition(self.newPromptPos, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(line)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.write("\n")
            self.loop.next()
        elif event.key() == Qt.Key_Up:
            self.historyUp()
        elif event.key() == Qt.Key_Down:
            self.historyDown()
        elif event.key() == Qt.Key_Tab:
            self.complete()
        elif event.key() in [Qt.Key_Left, Qt.Key_Backspace]:
            if self.textCursor().position() > self.newPromptPos:
                QPlainTextEdit.keyPressEvent(self, event)
        else:
            QPlainTextEdit.keyPressEvent(self, event)

    def historyUp(self):
        self.setLine(self.history[self.historyInd])
        self.historyInd = min(self.historyInd + 1, len(self.history) - 1)

    def historyDown(self):
        self.setLine(self.history[self.historyInd])
        self.historyInd = max(self.historyInd - 1, 0)

    def complete(self):
        pass

    def _moveCursorToInputLine(self):
        """
        Move the cursor to the input line if not already there. If the cursor
        if already in the input line (at position greater or equal to
        `newPromptPos`) it is left unchanged, otherwise it is moved at the
        end.

        """
        cursor = self.textCursor()
        pos = cursor.position()
        if pos < self.newPromptPos:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)

    def pasteCode(self, source):
        """
        Paste source code into the console.
        """
        self._moveCursorToInputLine()

        for line in interleave(source.splitlines(), itertools.repeat("\n")):
            if line != "\n":
                self.insertPlainText(line)
            else:
                self.write("\n")
                self.loop.next()

    def insertFromMimeData(self, source):
        """
        Reimplemented from QPlainTextEdit.insertFromMimeData.
        """
        if source.hasText():
            self.pasteCode(unicode(source.text()))
            return


def interleave(seq1, seq2):
    """
    Interleave elements of `seq2` between consecutive elements of `seq1`.

        >>> list(interleave([1, 3, 5], [2, 4]))
        [1, 2, 3, 4, 5]

    """
    iterator1, iterator2 = iter(seq1), iter(seq2)
    leading = next(iterator1)
    for element in iterator1:
        yield leading
        yield next(iterator2)
        leading = element

    yield leading


class Script(object):
    Modified = 1
    MissingFromFilesystem = 2

    def __init__(self, name, script, flags=0, sourceFileName=None):
        self.name = name
        self.script = script
        self.flags = flags
        self.sourceFileName = sourceFileName


class ScriptItemDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def displayText(self, variant, locale):
        script = variant.toPyObject()
        if script.flags & Script.Modified:
            return QString("*" + script.name)
        else:
            return QString(script.name)

    def paint(self, painter, option, index):
        script = index.data(Qt.DisplayRole).toPyObject()

        if script.flags & Script.Modified:
            option = QStyleOptionViewItemV4(option)
            option.palette.setColor(QPalette.Text, QColor(Qt.red))
            option.palette.setColor(QPalette.Highlight, QColor(Qt.darkRed))
        QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        return QLineEdit(parent)

    def setEditorData(self, editor, index):
        script = index.data(Qt.DisplayRole).toPyObject()
        editor.setText(script.name)

    def setModelData(self, editor, model, index):
        model[index.row()].name = str(editor.text())


def select_row(view, row):
    """
    Select a `row` in an item view
    """
    selmodel = view.selectionModel()
    selmodel.select(view.model().index(row, 0),
                    QItemSelectionModel.ClearAndSelect)


class OWPythonScript(OWWidget):

    settingsList = ["libraryListSource", "currentScriptIndex",
                    "splitterState", "auto_execute"]

    def __init__(self, parent=None, signalManager=None):
        OWWidget.__init__(self, parent, signalManager, 'Python Script')

        self.inputs = [("in_data", Orange.data.Table, self.setExampleTable,
                        Default),
                       ("in_distance", Orange.misc.SymMatrix,
                        self.setDistanceMatrix, Default),
                       ("in_learner", Orange.core.Learner, self.setLearner,
                        Default),
                       ("in_classifier", Orange.core.Classifier,
                        self.setClassifier, Default),
                       ("in_object", object, self.setObject)]

        self.outputs = [("out_data", Orange.data.Table),
                        ("out_distance", Orange.misc.SymMatrix),
                        ("out_learner", Orange.core.Learner),
                        ("out_classifier", Orange.core.Classifier, Dynamic),
                        ("out_object", object, Dynamic)]

        self.in_data = None
        self.in_distance = None
        self.in_learner = None
        self.in_classifier = None
        self.in_object = None
        self.auto_execute = False

        self.libraryListSource = [Script("Hello world",
                                         "print 'Hello world'\n")]
        self.currentScriptIndex = 0
        self.splitterState = None
        self.loadSettings()

        for s in self.libraryListSource:
            s.flags = 0

        self._cachedDocuments = {}

        self.infoBox = OWGUI.widgetBox(self.controlArea, 'Info')
        OWGUI.label(
            self.infoBox, self,
            "<p>Execute python script.</p><p>Input variables:<ul><li> " +
            "<li>".join(t[0] for t in self.inputs) +
            "</ul></p><p>Output variables:<ul><li>" +
            "<li>".join(t[0] for t in self.outputs) +
            "</ul></p>"
        )

        self.libraryList = PyListModel(
           [], self,
           flags=Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        )

        self.libraryList.wrap(self.libraryListSource)

        self.controlBox = OWGUI.widgetBox(self.controlArea, 'Library')
        self.controlBox.layout().setSpacing(1)

        self.libraryView = QListView(
            editTriggers=QListView.DoubleClicked |
                         QListView.EditKeyPressed,
            sizePolicy=QSizePolicy(QSizePolicy.Ignored,
                                   QSizePolicy.Preferred)
        )
        self.libraryView.setItemDelegate(ScriptItemDelegate(self))
        self.libraryView.setModel(self.libraryList)

        self.libraryView.selectionModel().selectionChanged.connect(
            self.onSelectedScriptChanged
        )
        self.controlBox.layout().addWidget(self.libraryView)

        w = ModelActionsWidget()

        self.addNewScriptAction = action = QAction("+", self)
        action.setToolTip("Add a new script to the library")
        action.triggered.connect(self.onAddScript)
        w.addAction(action)

        action = QAction(unicodedata.lookup("MINUS SIGN"), self)
        action.setToolTip("Remove script from library")
        action.triggered.connect(self.onRemoveScript)
        w.addAction(action)

        action = QAction("Update", self)
        action.setToolTip("Save changes in the editor to library")
        action.setShortcut(QKeySequence(QKeySequence.Save))
        action.triggered.connect(self.commitChangesToLibrary)
        w.addAction(action)

        action = QAction("More", self, toolTip="More actions")

        new_from_file = QAction("Import a script from a file", self)
        save_to_file = QAction("Save selected script to a file", self)
        save_to_file.setShortcut(QKeySequence(QKeySequence.SaveAs))

        new_from_file.triggered.connect(self.onAddScriptFromFile)
        save_to_file.triggered.connect(self.saveScript)

        menu = QMenu(w)
        menu.addAction(new_from_file)
        menu.addAction(save_to_file)
        action.setMenu(menu)
        button = w.addAction(action)
        button.setPopupMode(QToolButton.InstantPopup)

        w.layout().setSpacing(1)

        self.controlBox.layout().addWidget(w)

        self.runBox = OWGUI.widgetBox(self.controlArea, 'Run')
        OWGUI.button(self.runBox, self, "Execute", callback=self.execute)
        OWGUI.checkBox(self.runBox, self, "auto_execute", "Auto execute",
                       tooltip=("Run the script automatically whenever "
                                "the inputs to the widget change."))

        self.splitter = QSplitter(Qt.Vertical, self.mainArea)
        self.mainArea.layout().addWidget(self.splitter)

        self.defaultFont = defaultFont = \
            "Monaco" if sys.platform == "darwin" else "Courier"

        self.textBox = OWGUI.widgetBox(self, 'Python script')
        self.splitter.addWidget(self.textBox)
        self.text = PythonScriptEditor(self)
        self.textBox.layout().addWidget(self.text)

        self.textBox.setAlignment(Qt.AlignVCenter)
        self.text.setTabStopWidth(4)

        self.text.modificationChanged[bool].connect(self.onModificationChanged)

        self.consoleBox = OWGUI.widgetBox(self, 'Console')
        self.splitter.addWidget(self.consoleBox)
        self.console = PythonConsole(self.__dict__, self)
        self.consoleBox.layout().addWidget(self.console)
        self.console.document().setDefaultFont(QFont(defaultFont))
        self.consoleBox.setAlignment(Qt.AlignBottom)
        self.console.setTabStopWidth(4)

        select_row(self.libraryView, self.currentScriptIndex)

        self.splitter.setSizes([2, 1])
        if self.splitterState is not None:
            self.splitter.restoreState(QByteArray(self.splitterState))

        self.splitter.splitterMoved[int, int].connect(self.onSpliterMoved)
        self.controlArea.layout().addStretch(1)
        self.resize(800, 600)

    def setExampleTable(self, et):
        self.in_data = et

    def setDistanceMatrix(self, dm):
        self.in_distance = dm

    def setLearner(self, learner):
        self.in_learner = learner

    def setClassifier(self, classifier):
        self.in_classifier = classifier

    def setObject(self, obj):
        self.in_object = obj

    def handleNewSignals(self):
        if self.auto_execute:
            self.execute()

    def selectedScriptIndex(self):
        rows = self.libraryView.selectionModel().selectedRows()
        if rows:
            return  [i.row() for i in rows][0]
        else:
            return None

    def setSelectedScript(self, index):
        select_row(self.libraryView, index)

    def onAddScript(self, *args):
        self.libraryList.append(Script("New script", "", 0))
        self.setSelectedScript(len(self.libraryList) - 1)

    def onAddScriptFromFile(self, *args):
        filename = QFileDialog.getOpenFileName(
            self, 'Open Python Script',
            os.path.expanduser("~/"),
            'Python files (*.py)\nAll files(*.*)'
        )

        filename = unicode(filename)
        if filename:
            name = os.path.basename(filename)
            self.libraryList.append(Script(name, open(filename, "rb").read(),
                                           0, filename))
            self.setSelectedScript(len(self.libraryList) - 1)

    def onRemoveScript(self, *args):
        index = self.selectedScriptIndex()
        if index is not None:
            del self.libraryList[index]
            select_row(self.libraryView, max(index - 1, 0))

    def onSelectedScriptChanged(self, selected, deselected):
        index = [i.row() for i in selected.indexes()]
        if index:
            current = index[0]
            self.text.setDocument(self.documentForScript(current))
            self.currentScriptIndex = current

    def documentForScript(self, script=0):
        if type(script) != Script:
            script = self.libraryList[script]

        if script not in self._cachedDocuments:
            doc = QTextDocument(self)
            doc.setDocumentLayout(QPlainTextDocumentLayout(doc))
            doc.setPlainText(script.script)
            doc.setDefaultFont(QFont(self.defaultFont))
            doc.highlighter = PythonSyntaxHighlighter(doc)
            doc.modificationChanged[bool].connect(self.onModificationChanged)
            doc.setModified(False)
            self._cachedDocuments[script] = doc
        return self._cachedDocuments[script]

    def commitChangesToLibrary(self, *args):
        index = self.selectedScriptIndex()
        if index is not None:
            self.libraryList[index].script = unicode(self.text.toPlainText())
            self.text.document().setModified(False)
            self.libraryList.emitDataChanged(index)

    def onModificationChanged(self, modified):
        index = self.selectedScriptIndex()
        if index is not None:
            self.libraryList[index].flags = Script.Modified if modified else 0
            self.libraryList.emitDataChanged(index)

    def onSpliterMoved(self, pos, ind):
        self.splitterState = str(self.splitter.saveState())

    def saveScript(self):
        index = self.selectedScriptIndex()
        filename = os.path.expanduser("~/")
        if index is not None:
            script = self.libraryList[index]
            filename = script.sourceFileName or filename

        filename = QFileDialog.getSaveFileName(
            self, 'Save Python Script',
            filename,
            'Python files (*.py)\nAll files(*.*)'
        )

        self.codeFile = unicode(filename)

        if self.codeFile:
            fn = ""
            head, tail = os.path.splitext(self.codeFile)
            if not tail:
                fn = head + ".py"
            else:
                fn = self.codeFile

            f = open(fn, 'w')
            f.write(self.text.toPlainText())
            f.close()

    def execute(self):
        self._script = str(self.text.toPlainText())
        self.console.write("\nRunning script:\n")
        self.console.push("exec(_script)")
        self.console.new_prompt(sys.ps1)
        for out in self.outputs:
            signal = out[0]
            self.send(signal, getattr(self, signal, None))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ow = OWPythonScript()
    ow.show()
    app.exec_()
    ow.saveSettings()
