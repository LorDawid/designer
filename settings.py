# pyright: reportGeneralTypeIssues=false, reportWildcardImportFromLibrary=false
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json
import sys
import os

from customWidgets import *

class SettingWidget(QHBoxLayout):
    def __init__(self, parent, text: str, clickableWidget: QWidget, widgetWidth: int = None) -> None:
        super().__init__()
        self.label = QLabel(text=text)
        self.label.setFixedHeight(40)
        self.addWidget(self.label)
        self.widgetWidth = widgetWidth

        if clickableWidget is not None:
            self.setClickableWidget(clickableWidget)

        parent.addLayout(self)

    def setClickableWidget(self, widget: QWidget) -> None:
        isWidget = isinstance(widget, QWidget)
        self.clickableWidget = widget

        if isWidget:
            if self.widgetWidth is not None: widget.setMaximumWidth(self.widgetWidth)
            widget.setFixedHeight(40)
            self.addWidget(widget)
        else:        self.addLayout(self.clickableWidget)

class Settings(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(400, 600)
        self.setWindowIcon(QIcon("icons/designer.png"))
        self.setWindowTitle("Projektant | Ustawienia")

        self.settingsLayout = QVBoxLayout(self)
        parent = self.settingsLayout

        #!----------------------------------
        self.settingsLayout.addWidget(CenteredLabel(text="Ustawienia", objectName="projectManagerTitle"))
        self.settingsLayout.addWidget(Divider(True))
        #?-
        self.theme = SettingWidget(parent, text="Motyw", clickableWidget=QComboBox(), widgetWidth=100)
        self.theme.clickableWidget.addItems(self.getThemes())
        self.clipboardSize = SettingWidget(parent, text="Pojemnosc schowka", clickableWidget=QSpinBox(), widgetWidth=100)
        self.autosaveTime = SettingWidget(parent, text="Czestotliwosc autozapisu (s)", clickableWidget=QSpinBox(), widgetWidth=100)
        self.settingsLayout.addWidget(Divider(True))

        #?-
        self.settingsLayout.addWidget(CenteredLabel(text="Siatka"))
        self.gridEnabled = SettingWidget(parent, text="Wlaczona", clickableWidget=QCheckBox(layoutDirection=Qt.RightToLeft), widgetWidth=100)
        self.gridColor = SettingWidget(parent, text="Kolor", clickableWidget=ColorChangeWidget())
        self.gridVisibility = SettingWidget(parent, text="Widocznosc (od ilu %)", clickableWidget=QSpinBox(), widgetWidth=100)
        self.gridVisibility.clickableWidget.setRange(20, 6400)
        self.gridVisibility.clickableWidget.setSingleStep(100)
        self.settingsLayout.addWidget(Divider(True))
        #?-
        self.settingsLayout.addWidget(CenteredLabel(text="Tworzenie projektow"))
        self.defaultColor = SettingWidget(parent, text="Domyslny kolor", clickableWidget=ColorChangeWidget())
        self.defaultLocation = SettingWidget(parent, text="Domyslna lokalizacja", clickableWidget=QLineEdit(), widgetWidth=100)
        self.settingsLayout.addWidget(Divider(True))
        #!----------------------------------

        self.optionLayout = QHBoxLayout()
        close = QToolButton(text="Zamknij", clicked=self.close)
        close.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        save = QToolButton(text="Zapisz", clicked=self.saveSettings, objectName="coloredButton")
        save.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.optionLayout.addWidget(close)
        self.optionLayout.addWidget(save)
        self.settingsLayout.addLayout(self.optionLayout)

        self.refreshSettings()

    def loadStyleSheet(self, color: str) -> None:
        with open(f"styles/{color}.qss", "r") as file:
            self.setStyleSheet(file.read())

    def errorMessage(self, text: str, informativeText: str) -> None:
        """Displays and error message in another window

        Args:
            text (str): Upper text on the window
            informativeText (str): Lower text on the window
        """
        message = QMessageBox(icon=QMessageBox.Critical, text=text, informativeText=informativeText)
        message.setWindowTitle("Blad")
        message.exec_()

    def refreshSettings(self) -> None:
        with open("settings.json", "r") as file:
            settings = json.loads(file.read())

        self.loadStyleSheet(settings["theme"])
        self.theme.clickableWidget.setCurrentIndex(self.theme.clickableWidget.findText(settings["theme"]))
        self.clipboardSize.clickableWidget.setValue(settings["clipboardSize"])
        self.autosaveTime.clickableWidget.setValue(settings["autosaveTime"]//1000)
        self.gridEnabled.clickableWidget.setChecked(settings["gridEnabled"])
        self.gridColor.clickableWidget.setColor(settings["gridColor"])
        self.gridVisibility.clickableWidget.setValue(settings["gridVisibility"])
        self.defaultColor.clickableWidget.setColor(settings["defaultColor"])
        self.defaultLocation.clickableWidget.setText(settings["defaultSaveLocation"])

    def getThemes(self) -> list:
        files = []
        try:
            path = os.path.join(os.getcwd(), "styles")
            files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
            for file in files:
                if file.split(".")[1] != "qss": files.remove(file)

            files = [f.split(".")[0] for f in files]
        except Exception:
            print("couldnt get themes")
        return files

    def saveSettings(self) -> None:
        try:
            filePath = self.defaultLocation.clickableWidget.text()
            if not os.access(os.path.dirname(filePath), os.W_OK):
                self.errorMessage("Nie mozna zapisac ustawien", "Domyslna lokalizacja pliku jest niepoprawna")
                return

            settings = {
                "theme": self.theme.clickableWidget.currentText(),
                "gridEnabled": self.gridEnabled.clickableWidget.isChecked(),
                "gridColor": self.gridColor.clickableWidget.color,
                "gridVisibility": int(self.gridVisibility.clickableWidget.text()),
                "defaultColor": self.defaultColor.clickableWidget.color,
                "defaultSaveLocation": filePath,
                "autosaveTime": int(self.autosaveTime.clickableWidget.text())*1000,
                "clipboardSize" : int(self.clipboardSize.clickableWidget.text())
            }

            with open("settings.json", "w") as file:
                file.write(json.dumps(settings))

            python = sys.executable
            os.execl(python, python, *sys.argv)

        except Exception:
            self.errorMessage("Nie mozna zapisac ustawien", "Sprawdz, czy wszystko zostalo poprawnie wypelnione")

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.refreshSettings()