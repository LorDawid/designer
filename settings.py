from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json

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

        self.scrollableArea = QScrollArea(self, objectName="noBorder")
        self.scrollableArea.setWidgetResizable(True)
        self.settingsLayout = QVBoxLayout()
        self.settingsWidget = QWidget(objectName="noBorder")
        self.settingsWidget.setLayout(self.settingsLayout)
        self.scrollableArea.setWidget(self.settingsWidget)
        self.scrollableArea.setFixedSize(self.size())
        self.settingsLayout.setAlignment(Qt.AlignTop)
        parent = self.settingsLayout

        #!----------------------------------
        self.settingsLayout.addWidget(CenteredLabel(text="Ustawienia", objectName="projectManagerTitle"))
        self.settingsLayout.addWidget(Divider(True))
        #?-
        self.theme = SettingWidget(parent, text="Motyw", clickableWidget=QComboBox(), widgetWidth=100)
        self.settingsLayout.addWidget(Divider(True))
        #?-
        self.settingsLayout.addWidget(CenteredLabel(text="Siatka"))
        self.gridEnabled = SettingWidget(parent, text="Wlaczona", clickableWidget=QCheckBox(layoutDirection=Qt.RightToLeft), widgetWidth=100)
        self.gridColor = SettingWidget(parent, text="Kolor", clickableWidget=ColorChangeWidget())
        self.gridVisibility = SettingWidget(parent, text="Widocznosc (od ilu %)", clickableWidget=QSpinBox(), widgetWidth=100)
        self.settingsLayout.addWidget(Divider(True))
        #?-
        self.settingsLayout.addWidget(CenteredLabel(text="Tworzenie projektow"))
        self.defaultColor = SettingWidget(parent, text="Domyslny kolor", clickableWidget=ColorChangeWidget())
        self.defaultLocation = SettingWidget(parent, text="Domyslna lokalizacja", clickableWidget=QLineEdit(), widgetWidth=100)
        #!----------------------------------

        self.refreshSettings()

    def loadStyleSheet(self, color: str) -> None:
        with open(f"styles/{color}.qss", "r") as file:
            self.setStyleSheet(file.read())

    def refreshSettings(self) -> None:
        with open("settings.json", "r") as file:
            settings = json.loads(file.read())

        self.loadStyleSheet(settings["theme"])
        self.gridEnabled.clickableWidget.setChecked(settings["gridEnabled"])
        self.gridColor.clickableWidget.setColor(settings["gridColor"])
        self.gridVisibility.clickableWidget.setValue(settings["gridVisibility"])
        self.defaultColor.clickableWidget.setColor(settings["defaultColor"])
        self.defaultLocation.clickableWidget.setText(settings["defaultSaveLocation"])