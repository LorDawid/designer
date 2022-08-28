from itertools import product
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pixel import Pixel
import pickle
import os

class NewProject(QWidget):
    PROJECTTYPES = {
        "Bransoletka": "bracelet"
    }

    def __init__(self, launcherWindow):
        super().__init__()
        self.resize(400, 300)
        self.show()
        self.loadStyleSheet("light")
        self.launcherWindow = launcherWindow

        self.setWindowIcon(QIcon("icons/designer.png"))
        self.setWindowTitle("Stworz nowy projekt")

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignTop)

        self.projectName = QLineEdit()
        self.projectName.setFixedHeight(40)

        self.fileLocationLayout = QHBoxLayout()
        self.fileLocationLayout.setSpacing(0)
        self.fileLocationInput = QLineEdit(objectName="chooseFileNewProjectEdit")
        self.fileLocationInput.setFixedHeight(40)
        self.fileLocationButton = QToolButton(text="...", clicked = self.chooseFileLocation, objectName="chooseFileNewProjectButton")
        self.fileLocationButton.setFixedSize(40, 40)
        self.fileLocationLayout.addWidget(self.fileLocationInput)
        self.fileLocationLayout.addWidget(self.fileLocationButton)

        self.sizeLayout = QHBoxLayout()
        self.xSize = QLineEdit()
        self.xSize.setFixedHeight(40)
        self.ySize = QLineEdit()
        self.ySize.setFixedHeight(40)
        self.sizeLayout.addWidget(self.xSize)
        self.sizeLayout.addWidget(QLabel(text="x"))
        self.sizeLayout.addWidget(self.ySize)

        self.projectType = QComboBox()
        self.projectType.addItems(["Bransoletka"])
        self.projectType.setFixedHeight(40)

        self.finalLayout = QHBoxLayout()
        self.saveButton = QToolButton(text="Zapisz i otworz", objectName="coloredButton", clicked=self.saveAndOpen)
        self.saveButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cancelButton = QToolButton(text="Anuluj", clicked=self.cancel)
        self.cancelButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.finalLayout.addWidget(self.cancelButton)
        self.finalLayout.addWidget(self.saveButton)

        self.mainLayout.addWidget(QLabel(text="Nazwa projektu", objectName="projectSettingsHints"))
        self.mainLayout.addWidget(self.projectName)
        self.mainLayout.addWidget(QLabel(text="Lokalizacja pliku", objectName="projectSettingsHints"))
        self.mainLayout.addLayout(self.fileLocationLayout)
        self.mainLayout.addWidget(QLabel(text="Rozmiar projektu", objectName="projectSettingsHints"))
        self.mainLayout.addLayout(self.sizeLayout)
        self.mainLayout.addWidget(QLabel(text="Typ projektu", objectName="projectSettingsHints"))
        self.mainLayout.addWidget(self.projectType)
        self.mainLayout.addLayout(self.finalLayout)

    def chooseFileLocation(self) -> None:
        safeProjectName = self.projectName.text()

        for illegalCharacter in ["#","%","&","{","}","\\","<",">","*","?","/"," ","$","!","'","\"",":","@","+","`","|","="]:
            safeProjectName = safeProjectName.replace(illegalCharacter,"_")

        fileName, _ = QFileDialog.getSaveFileName(self,"Wybierz lokalizacje zapisu pliku",safeProjectName,"Projekty (*.dpct)")
        self.fileLocationInput.setText(fileName)

    def cancel(self) -> None:
        self.close()

    def errorMessage(self, text: str, informativeText: str) -> None:
        message = QMessageBox()
        message.setIcon(QMessageBox.Critical)
        message.setText(text)
        message.setInformativeText(informativeText)
        message.setWindowTitle("Blad")
        message.exec_()

    def saveAndOpen(self) -> None:
        filePath = self.fileLocationInput.text()
        if not os.access(os.path.dirname(filePath), os.W_OK):
            self.errorMessage("Nie mozna zapisac pliku", "Sprawdz, czy lokalizacja pliku jest poprawna")
            return

        try:
            size = int(self.xSize.text()), int(self.ySize.text())
        except ValueError:
            self.errorMessage("Wybrany rozmiar nie jest liczbami", "Sprawdz, czy rozmiar zostal poprawnie wpisany")
            return

        contents = {pixel: Pixel(*pixel, (255,0,255)) for pixel in product(range(size[0]), range(size[1]))}

        toWrite = {
            "type": self.PROJECTTYPES[self.projectType.currentText()],
            "size": [self.xSize.text(), self.ySize.text()],
            "contents": contents
        }

        try:
            with open(filePath, "wb") as f:
                pickle.dump(toWrite, f)
        except Exception:
            self.errorMessage("Nie mozna zapisac pliku", "Nieznany problem, sprobuj ponownie")

        self.launcherWindow.openEditor(filePath)

    def loadStyleSheet(self, color: str) -> None:
        with open(f"{color}.qss", "r") as file:
            self.setStyleSheet(file.read())