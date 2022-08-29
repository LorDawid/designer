from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
import pickle
import json
import sys
import os

extensionVersion = "1.0"

class Editor(QMainWindow):
    def __init__(self, filepath: str) -> None:
        self.zoom = 1
        self.color = (255, 255, 255)
        self.tool = "brush"
        self.mouseDown = False

        self.mouseDownPosition = (0, 0)

        self.tools = {
            "brush": self.brush,
            "line": self.line
        }

        super().__init__()

        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.setWindowTitle("Edytor")

        self.refreshSettings()
        self.loadStyleSheet(self.settings['theme'])
        self.filepath = filepath
        self.loadProject(self.filepath)

        sizeMessage = QLabel(text = f"  Rozmiar: {self.projectSize[0]} x {self.projectSize[1]}  ", objectName="statusBarLabel")
        self.statusBar().addPermanentWidget(sizeMessage)

        self.zoomIndicator = QLabel(text=f"{self.zoom*100}%", objectName="statusBarLabel")
        self.statusBar().addPermanentWidget(self.zoomIndicator)

        self.mainLayout = QVBoxLayout(self.mainWidget)

        self.toolsLayout = QHBoxLayout()
        self.toolsLayout.setAlignment(Qt.AlignLeft)

        brushButton = QToolButton(text="Brush", clicked=lambda: self.changeTool("brush"))
        brushButton.setMaximumSize(80, 150)
        brushButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        brushButton.setIcon(QIcon(f"icons/{self.settings['theme']}/brush.png"))
        brushButton.setIconSize(QSize(48, 48))
        brushButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolsLayout.addWidget(brushButton)

        lineButton = QToolButton(text="Line", clicked=lambda: self.changeTool("line"))
        lineButton.setMaximumSize(80, 150)
        lineButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lineButton.setIcon(QIcon(f"icons/{self.settings['theme']}/line.png"))
        lineButton.setIconSize(QSize(48, 48))
        lineButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolsLayout.addWidget(lineButton)

        self.colorButton = QToolButton(text="Kolor", clicked=lambda: self.changeColor())
        self.colorButton.setMaximumSize(80, 150)
        self.colorButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        colorIcon = QImage(np.full((48,48,3), self.color, dtype=np.uint8), 48, 48, QImage.Format_RGB888)
        self.colorButton.setIcon(QIcon(QPixmap.fromImage(colorIcon)))
        self.colorButton.setIconSize(QSize(48, 48))
        self.colorButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolsLayout.addWidget(self.colorButton)

        self.drawingBoard = QLabel()
        self.drawingBoardScroll = QScrollArea(self.mainWidget, objectName="drawingSpace")
        self.drawingBoardScroll.setWidgetResizable(True)
        self.drawingBoardScroll.setWidget(self.drawingBoard)
        self.drawingBoardScroll.setAlignment(Qt.AlignCenter)
        self.drawingBoardScroll.setCursor(QCursor(Qt.CrossCursor))

        self.mainLayout.addLayout(self.toolsLayout)
        self.mainLayout.addWidget(self.drawingBoardScroll)
        self.mainLayout.setStretch(0, 1)
        self.mainLayout.setStretch(1, 3)
        self.drawPixels()

        self.resize(800, 600)
        self.show()

    #!Other functions
    def errorMessage(self, text: str, informativeText: str) -> None:
        """Displays and error message in another window

        Args:
            text (str): Upper text on the window
            informativeText (str): Lower text on the window
        """
        message = QMessageBox(icon=QMessageBox.Critical, text=text, informativeText=informativeText)
        message.setWindowTitle("Blad")
        message.exec_()

    def loadStyleSheet(self, color: str) -> None:
        """Loads stylesheet from specified qss file

        Args:
            color (str): file name (no extensions)
        """
        with open(f"{color}.qss", "r") as file:
            self.setStyleSheet(file.read())

    def refreshSettings(self) -> None:
        with open("settings.json", "r") as file:
            self.settings = json.loads(file.read())

    #!Project management functions
    def loadProject(self, project: str) -> None:
        try:
            with open(project, "rb") as f:
                projectData = pickle.load(f)

            if projectData["version"] != extensionVersion:
                self.errorMessage("Moga wystapywac problemy przy wyswietlaniu projektu", "Wersja programu zmienila sie")

            self.projectSize = tuple(int(x) for x in projectData["size"])
            self.projectType = projectData["type"]
            self.projectName = projectData["name"]
            self.projectData = projectData["contents"]
            self.lastState = self.projectData
            self.beforeLineState = self.projectData

            self.updateRecentProjects()
        except FileNotFoundError:
            self.errorMessage("Nie mozna otworzyc pliku", "Plik nie istnieje")
            return
        except Exception:
            self.errorMessage("Nie mozna otworzyc pliku", "Struktura pliku jest nieprawidlowa")
            return

    def saveProject(self, filePath: str) -> None:
        if not os.access(os.path.dirname(filePath), os.W_OK):
            self.errorMessage("Nie mozna zapisac pliku", "Sprawdz, czy lokalizacja pliku jest poprawna")
            return

        toWrite = {
            "version": extensionVersion,
            "type": self.projectType,
            "size": self.projectSize,
            "contents": self.projectData
        }

        try:
            with open(filePath, "wb") as f:
                pickle.dump(toWrite, f)
        except Exception:
            self.errorMessage("Nie mozna zapisac pliku", "Nieznany problem, sprobuj ponownie")

    def updateRecentProjects(self) -> None:
        with open("recentProjects.json", "r") as file:
            recents = json.loads(file.read())

        recents[self.filepath] = {
            "name": self.projectName,
            "type": self.projectType
        }

        with open("recentProjects.json", "w") as file:
            recents = file.write(json.dumps(recents))

    #!Drawing board event functions
    def getPixelXYFromXY(self, coordinates: QPoint) -> tuple[int, int]:
        """Takes pixel coordinates from a mouse event and converts them to a point on the image

        Args:
            coordinates (QPoint): Taken from for example a mouse event

        Returns:
            tuple[int, int]: XY coordinates on image
        """
        imageStartPos = (self.drawingBoard.geometry().topLeft()+self.drawingBoardScroll.geometry().topLeft())
        imageStartPos = imageStartPos.x(), imageStartPos.y()
        if type(coordinates) == QPoint: mousePos = coordinates.x(), coordinates.y()
        else: mousePos = coordinates
        labelPos = mousePos[0]-imageStartPos[0], mousePos[1]-imageStartPos[1]
        pixel = round(labelPos[0]/self.zoom), round(labelPos[1]/self.zoom)
        return pixel

    def pixelXYToNpXY(self, pixel: tuple[int, int]) -> tuple[int, int]:
        """Takes XY coordinates on image and converts them onto pixel coordinates on ndarray

        Args:
            pixel (tuple[int, int]): Pixel location on image

        Returns:
            tuple[int, int]: Pixel location on ndarray
        """
        return pixel[1]*self.projectSize[0]//self.projectSize[1]+pixel[0]//self.projectSize[1], pixel[0]%self.projectSize[1]

    def drawPixels(self) -> None:
        """Draws all pixels onto QLabel
        """
        newImageResolution = (self.projectSize[0]*self.zoom, self.projectSize[1]*self.zoom)
        self.drawingBoard.setFixedSize(*newImageResolution)
        image = QImage(self.projectData, *self.projectSize, QImage.Format_RGB888).scaled(*newImageResolution)
        self.drawingBoard.setPixmap(QPixmap.fromImage(image))

    def checkXYWithinImage(self, pixel: tuple[int, int]) -> bool:
        """Checks if pixel is within the image

        Args:
            pixel (tuple[int, int]): ndarray coordinates of point

        Returns:
            bool: Is the point in the image?
        """
        return (0 <= pixel[0] < self.projectSize[0]) and (0 <= pixel[1] < self.projectSize[1])

    def zoomImage(self, zoomAmount: float) -> None:
        self.zoom += zoomAmount/500
        if self.zoom <= .1:
            self.zoom -= zoomAmount/500
        self.zoomIndicator.setText(str(round(self.zoom*100))+"%")
        self.drawPixels()

    #!Tool functions
    def changeColor(self) -> None:
        x = QColorDialog.getColor()
        self.color = x.getRgb()[:-1]
        colorIcon = QImage(np.full((48,48,3), self.color, dtype=np.uint8), 48, 48, QImage.Format_RGB888)
        self.colorButton.setIcon(QIcon(QPixmap.fromImage(colorIcon)))

    def changeTool(self, tool: str) -> None:
        """Changes tool."""
        self.tool = tool

    def brush(self, pixel: tuple[int, int]) -> None:
        """Function used by brush

        Args:
            pixel (tuple[int, int]): Takes pixel that will become colored
        """
        pixel = self.pixelXYToNpXY(pixel)
        if not self.checkXYWithinImage(pixel): return
        self.projectData[pixel] = self.color
        self.drawPixels()

    def line(self, end: QPoint) -> None:
        """Draws a line from point to point

        Args:
            start (QPoint): Start position of line
            end (QPoint): End position of line
        """
        start = self.getPixelXYFromXY(self.mouseDownPosition)

        if not self.checkXYWithinImage(self.pixelXYToNpXY(start)): return
        if not self.checkXYWithinImage(self.pixelXYToNpXY(end)): return

        from tools.line import getPointListFromCoordinates
        points = getPointListFromCoordinates(start, end)

        if self.mouseDown:
            self.projectData = np.copy(self.beforeLineState)
            for pixel in points:
                self.projectData[self.pixelXYToNpXY(pixel)] = self.color
            self.drawPixels()

    #!Native PyQt5 event functions
    def wheelEvent(self, event: QWheelEvent) -> None:
        super().wheelEvent(event)
        self.zoomImage(event.angleDelta().y())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        self.mouseDown = True
        self.lastState = np.copy(self.projectData)
        self.beforeLineState = np.copy(self.projectData)
        self.mouseDownPosition = event.pos()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.mouseDown = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        pixel = self.getPixelXYFromXY(event.pos())

        self.tools[self.tool](pixel)
        self.drawPixels()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z and (not self.mouseDown):
            self.projectData = np.copy(self.lastState)
            self.drawPixels()

    def closeEvent(self, event: QCloseEvent) -> None:
        print("closing")
        super().closeEvent(event)