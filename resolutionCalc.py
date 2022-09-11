from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import sys
import os

from settings import SettingWidget

class Calculator(QWidget):
    def __init__(self, newProjectWindow):
        super().__init__()
        self.resize(400, 100)
        self.refreshSettings()
        self.loadStyleSheet(self.settings["theme"])
        self.setWindowTitle("Projektant | Obliczanie rozdzielczosci")
        self.mainLayout = QVBoxLayout(self)
        self.newProjectWindow = newProjectWindow

        validator = QIntValidator()
        validator.setRange(0, 100)

        self.length = SettingWidget(self.mainLayout, "Dlugosc (cm)", QLineEdit(text="0"), 100)
        self.length.clickableWidget.setValidator(validator)
        self.cwidth = SettingWidget(self.mainLayout, "Szerokosc koralika (0.1mm)", QLineEdit(text="0"), 100)
        self.cwidth.clickableWidget.setValidator(validator)

        buttonLayout = QHBoxLayout()

        self.cancel = QToolButton(text="Anuluj", clicked=self.close)
        self.cancel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttonLayout.addWidget(self.cancel)

        self.apply = QToolButton(text="Zastosuj", objectName="coloredButton", clicked=self.calculate)
        self.apply.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttonLayout.addWidget(self.apply)
        self.mainLayout.addLayout(buttonLayout)

    def errorMessage(self, text: str, informativeText: str) -> None:
        message = QMessageBox()
        message.setIcon(QMessageBox.Critical)
        message.setText(text)
        message.setInformativeText(informativeText)
        message.setWindowTitle("Blad")
        message.exec_()

    def loadStyleSheet(self, color: str) -> None:
        with open(f"styles/{color}.qss", "r") as file:
            self.setStyleSheet(file.read())

    def refreshSettings(self) -> None:
        with open("settings.json", "r") as file:
            self.settings = json.loads(file.read())

    def calculate(self) -> None:
        try:
            length = int(self.length.clickableWidget.text())
            cwidth = int(self.cwidth.clickableWidget.text())
        except ValueError:
            self.errorMessage("Nie mozna obliczyc rozmiaru", "Sprawdz czy dane sa odpowiednio wprowadzone")
            return

        try:
            px = round((length*10)/(cwidth/10))
        except ZeroDivisionError:
            self.errorMessage("Nie mozna obliczyc rozmiaru", "Sprawdz czy dane sa odpowiednio wprowadzone")
            return

        self.newProjectWindow.xSize.setText(str(px))
        self.close()