from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from editor import *
import json
import sys
import os

from newproject import NewProject

class Launcher(QWidget):
    PROJECTTYPES = {
        "bracelet": "Bransoletka"
    }

    def __init__(self) -> None:
        super().__init__()
        self.resize(800, 600)
        self.setWindowIcon(QIcon("icons/designer.png"))
        self.setWindowTitle("Projektant")

        self.loadStyleSheet("light")

        self.titleLayout = QVBoxLayout(self)
        self.titleLayout.setAlignment(Qt.AlignTop)

        self.title = QLabel(text="Projektant", objectName="projectManagerTitle")

        self.mainLayout = QHBoxLayout()

        self.options = QVBoxLayout()
        self.options.setAlignment(Qt.AlignTop)

        self.newProjectButton = QToolButton(objectName="projectManagerButton")
        self.newProjectButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.newProjectButton.setIcon(QIcon("icons/dark/plus.png"))
        self.newProjectButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newProjectButton.setText("  Stworz nowy projekt")
        self.newProjectButton.clicked.connect(self.newProject)

        self.openProjectButton = QToolButton(objectName="projectManagerButton")
        self.openProjectButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.openProjectButton.setIcon(QIcon("icons/dark/document.png"))
        self.openProjectButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.openProjectButton.setText("  Otworz istniejacy projekt")
        self.openProjectButton.clicked.connect(self.openProject)

        self.optionsTitle = QLabel(text="Rozpocznij", objectName="recentsTitle")

        self.options.addWidget(self.optionsTitle)
        self.options.addWidget(self.newProjectButton)
        self.options.addWidget(self.openProjectButton)

        self.recentsLayout = QVBoxLayout()
        self.recentsLayout.setAlignment(Qt.AlignTop)
        self.recentsTitle = QLabel(text="Ostatnie projekty", objectName="recentsTitle")
        self.recentsLayout.addWidget(self.recentsTitle)
        self.loadRecentProjects()

        self.mainLayout.addLayout(self.options)
        div = QLabel(objectName="divider")
        div.setFixedWidth(2)
        self.mainLayout.addWidget(div)
        self.mainLayout.addLayout(self.recentsLayout)
        self.mainLayout.setStretch(0, 3)
        self.mainLayout.setStretch(1, 1)
        self.mainLayout.setStretch(2, 4)

        self.titleLayout.addWidget(self.title)
        self.titleLayout.addLayout(self.mainLayout)
        self.titleLayout.setStretch(1, 1)

    def loadStyleSheet(self, color: str) -> None:
        with open(f"{color}.qss", "r") as file:
            self.setStyleSheet(file.read())

    def loadRecentProjects(self) -> None:
        with open("recentProjects.json") as file:
            recents = json.loads(file.read())

        self.recents = []
        for file in recents:
            text = file["name"] + "\n" + self.PROJECTTYPES[file["type"]]
            button = QToolButton(text=text,objectName="projectButton")
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            button.clicked.connect(partial(self.openEditor, projectLocation=file["location"]))
            self.recents.append(file)
            self.recentsLayout.addWidget(button)

    def openProject(self) -> None:
        fileLocation, _ = QFileDialog.getOpenFileName(self,"Otworz projekt", "","Projekty (*.dpct)")
        self.openEditor(fileLocation)

    def newProject(self) -> None:
        self.newProjectWindow = NewProject(self)

    def errorMessage(self, text: str, informativeText: str) -> None:
        message = QMessageBox()
        message.setIcon(QMessageBox.Critical)
        message.setText(text)
        message.setInformativeText(informativeText)
        message.setWindowTitle("Blad")
        message.exec_()

    def openEditor(self, projectLocation: str) -> None:
        if not os.path.exists(projectLocation): 
            self.errorMessage("Nie mozna otworzyc pliku", "Sprawdz czy adres pliku jest poprawny")
            return
        self.hide()
        self.editor = Editor(projectLocation)

if __name__ == "__main__":
    if os.name == "nt":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("did.designer.1.0")

    app = QApplication(sys.argv)
    appWindow = Launcher()
    appWindow.show()
    app.exec_()
    sys.exit()