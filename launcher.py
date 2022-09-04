from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from editor import *
import json
import sys
import os

from newproject import NewProject
from settings import Settings

class Launcher(QWidget):
    PROJECTTYPES = {
        "bracelet": "Bransoletka"
    }

    def __init__(self) -> None:
        super().__init__()
        self.resize(800, 600)
        self.setWindowIcon(QIcon("icons/designer.png"))
        self.setWindowTitle("Projektant")

        self.settingsWindow = Settings()

        self.refreshSettings()
        self.loadStyleSheet(self.settings['theme'])

        self.titleLayout = QVBoxLayout(self)
        self.titleLayout.setAlignment(Qt.AlignTop)

        self.title = QLabel(text="Projektant", objectName="projectManagerTitle")

        self.mainLayout = QHBoxLayout()

        self.options = QVBoxLayout()
        self.options.setAlignment(Qt.AlignTop)

        self.newProjectButton = QToolButton(objectName="projectManagerButton")
        self.newProjectButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.newProjectButton.setIcon(QIcon(f"icons/{self.settings['theme']}/plus.png"))
        self.newProjectButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newProjectButton.setText("  Stworz nowy projekt")
        self.newProjectButton.clicked.connect(self.newProject)

        self.openProjectButton = QToolButton(objectName="projectManagerButton")
        self.openProjectButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.openProjectButton.setIcon(QIcon(f"icons/{self.settings['theme']}/document.png"))
        self.openProjectButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.openProjectButton.setText("  Otworz istniejacy projekt")
        self.openProjectButton.clicked.connect(self.openProject)

        self.settingsButton = QToolButton(objectName="projectManagerButton")
        self.settingsButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.settingsButton.setIcon(QIcon(f"icons/{self.settings['theme']}/settings.png"))
        self.settingsButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.settingsButton.setText("  Ustawienia")
        self.settingsButton.clicked.connect(self.openProject)

        self.options.addWidget(QLabel(text="Rozpocznij", objectName="recentsTitle"))
        self.options.addWidget(self.newProjectButton)
        self.options.addWidget(self.openProjectButton)
        self.options.addWidget(self.settingsButton)

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
        with open(f"styles/{color}.qss", "r") as file:
            self.setStyleSheet(file.read())

    def loadRecentProjects(self) -> None:
        with open("recentProjects.json") as file:
            recents = json.loads(file.read())

        self.recents = []
        for location, file in recents.items():
            if not (os.path.exists(location) and os.path.isfile(location)): location = "Plik zostal usuniety lub przeniesiony"
            layout = QHBoxLayout()
            layout.setSpacing(0)

            button = QToolButton(text=">",objectName="projectButton")
            button.setMaximumWidth(50)
            button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            button.clicked.connect(partial(self.openEditor, projectLocation=location))

            location = (location[:40] + '...') if len(location) > 40 else location
            file["name"] = (file["name"][:35] + '...') if len(file["name"]) > 35 else file["name"]
            text = f"""
            {file['name']}<br>
            <font size=5px>{self.PROJECTTYPES[file['type']]}</font>
            <font color='lightgray' size=5px>{location}</font>"""

            label = QLabel(text=text, objectName="projectLabel")
            label.setTextFormat(Qt.RichText)
            layout.addWidget(label)
            layout.addWidget(button)
            self.recentsLayout.addLayout(layout)
            self.recents.append(file)

    def refreshSettings(self) -> None:
        with open("settings.json", "r") as file:
            self.settings = json.loads(file.read())

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

    if len(sys.argv) == 2 and os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1]):
        appWindow = Editor(sys.argv[1])
    else:
        appWindow = Launcher()

    appWindow.show()
    app.exec_()
    sys.exit()