from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pixel import Pixel
import pickle

class Editor(QMainWindow):
    def __init__(self, url: str) -> None:
        self.pixelSize = 3

        super().__init__()
        self.resize(800, 600)
        self.show()

        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)

        self.loadStyleSheet("light")

        try:
            with open(url, "rb") as f:
                self.projectData = pickle.load(f)

            self.projectSize = self.projectData["size"]
            self.projectType = self.projectData["type"]
            self.projectData = self.projectData["contents"]
        except FileNotFoundError:
            self.errorMessage("Nie mozna otworzyc pliku", "Plik nie istnieje")
            return
        except Exception:
            self.errorMessage("Nie mozna otworzyc pliku", "Struktura pliku jest nieprawidlowa")
            return

        sizeMessage = QLabel(text = f"  Rozmiar: {self.projectSize[0]} x {self.projectSize[1]}  ", objectName="statusBarLabel")
        self.statusBar().addPermanentWidget(sizeMessage)

        self.mainLayout = QHBoxLayout(self.mainWidget)

        self.toolsLayout = QVBoxLayout()
        self.toolsTitle = QLabel(text="tools")
        self.toolsTitle.setMaximumWidth(200)
        self.toolsLayout.addWidget(self.toolsTitle)
        self.toolsLayout.addWidget(QPushButton(text="something", clicked=self.drawPixels))

        self.mainLayout.addLayout(self.toolsLayout)
        self.drawPixels()

    def drawPixels(self) -> None:
        if hasattr(self, "drawingBoard"):
            self.mainLayout.removeWidget(self.drawingBoard)
            del self.drawingBoard

        self.drawingBoard = QWidget(objectName="drawingSpace")
        for location, pixel in self.projectData.items():
            if pixel.color != (255,0,255): print(location)
            pixelObject = QLabel(self.drawingBoard)
            pixelObject.setStyleSheet(f"background-color:rgb{pixel.color}")
            pixelObject.setGeometry(location[0]*self.pixelSize, location[1]*self.pixelSize+200, self.pixelSize, self.pixelSize)
            if location == (0, 0): self.beginLocation = pixelObject.pos()

        self.mainLayout.addWidget(self.drawingBoard)
        self.mainLayout.setStretch(0, 1)
        self.mainLayout.setStretch(1, 3)
        print(self.beginLocation, self.drawingBoard.pos())
        self.beginLocation = (self.beginLocation.x()+self.drawingBoard.geometry().left(), self.beginLocation.y()+self.drawingBoard.geometry().top())

        self.projectData[(10, 10)] = Pixel(10, 10, (255,0,0))

    def errorMessage(self, text: str, informativeText: str) -> None:
        message = QMessageBox(icon=QMessageBox.Critical, text=text, informativeText=informativeText)
        message.setWindowTitle("Blad")
        message.exec_()

    def loadStyleSheet(self, color: str) -> None:
        with open(f"{color}.qss", "r") as file:
            self.setStyleSheet(file.read())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        print(self.beginLocation, event.localPos().x(), event.localPos().y())