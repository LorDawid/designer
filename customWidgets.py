from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

#stolen from https://stackoverflow.com/a/62401768/18104054
class PickablePixmap(QPixmap):
    def __reduce__(self):
        return type(self), (), self.__getstate__()

    def __getstate__(self):
        ba = QByteArray()
        stream = QDataStream(ba, QIODevice.WriteOnly)
        stream << self
        return ba

    def __setstate__(self, ba):
        stream = QDataStream(ba, QIODevice.ReadOnly)
        stream >> self

class ColorChangeWidget(QHBoxLayout):
    C_CHG_QSS = """
    border: 2px solid lightgray;
    border-top-left-radius: 0px;
    border-bottom-left-radius: 0px;
    """

    C_LBL_QSS = """
    background-color: rgb%;
    border: 2px solid lightgray;
    border-top-left-radius: 15px;
    border-bottom-left-radius: 15px;
    border-right: none;
    padding: 10px;
    """

    def __init__(self, startColor: tuple[int, int, int] = (0, 0, 0)) -> None:
        self.color = startColor
        super().__init__()
        self.setSpacing(0)
        self.colorLabel = QLabel()
        self.colorLabel.setFixedSize(40, 40)
        self.colorChange = QToolButton(text="...", clicked = self.changeColor)
        self.colorChange.setFixedSize(40, 40)
        self.colorChange.setStyleSheet(self.C_CHG_QSS)
        self.addWidget(self.colorLabel)
        self.addWidget(self.colorChange)
        self.refreshStyleSheet()

    def refreshStyleSheet(self) -> None:
        qss = self.C_LBL_QSS.replace("%", str(tuple(self.color)))
        self.colorLabel.setStyleSheet(qss)

    def changeColor(self) -> None:
        x = QColorDialog.getColor()
        self.color = x.getRgb()[:-1]
        self.refreshStyleSheet()

    def setColor(self, color: tuple[int, int, int]) -> None:
        self.color = tuple(color)
        self.refreshStyleSheet()

class Divider(QLabel):
    def __init__(self, horizontal: bool = False):
        super().__init__()
        if horizontal: self.setFixedHeight(2)
        else: self.setFixedWidth(2)
        self.setObjectName("divider")

class CenteredLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignCenter)