from PIL import Image, ImageDraw
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
import pickle
import json
import os

import tools.line

extensionVersion = "1.0"

#Those two classes exists to be able to track mouse movement when not pressed
class TrackingScrollArea(QScrollArea):
    def __init__(self, mainWindow, parent, objectName):
        super().__init__()
        self.mainWindow = mainWindow
        self.setParent(parent)
        self.setObjectName(objectName)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.mainWindow.drawingBoardMoveEvent(event)
        super().mouseMoveEvent(event)

class TrackingLabel(QLabel):
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.mainWindow.drawingBoardMoveEvent(event)
        super().mouseMoveEvent(event)

class Editor(QMainWindow):
    def __init__(self, filepath: str) -> None:
        self.zoom = 1
        self.color = (255, 255, 255)
        self.tool = "brush"
        self.mouseDown = False

        self.mouseDownPosition = (0, 0)
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

        self.menu = self.menuBar()

        self.projectSettings = QMenu("Projekt")

        self.projectSettings.addAction(QAction("Zapisz projekt", self, triggered=lambda: self.saveProject(self.filepath), shortcut="Ctrl+S"))

        def saveAs():
            fileName, _ = QFileDialog.getSaveFileName(self,"Wybierz lokalizacje zapisu pliku", self.filepath,"Projekty (*.dpct)")
            self.saveProject(fileName)
            self.filepath = fileName
            self.updateRecentProjects()
        self.projectSettings.addAction(QAction("Zapisz projekt jako", self, triggered=saveAs))

        self.projectSettings.addAction(QAction("Wyeksportuj projekt", self, triggered=self.exportProject, shortcut="Ctrl+E"))
        self.menu.addMenu(self.projectSettings)


        self.mainLayout = QVBoxLayout(self.mainWidget)

        self.toolsLayout = QHBoxLayout()
        self.toolsLayout.setAlignment(Qt.AlignLeft)

        self.tools = {
            "brush":  [self.brush, None],
            "line":   [self.line, None],
            "picker": [self.colorPicker, self.colorPickerMove],
            "bucket": [self.bucket, None],
        }

        brushButton = QToolButton(clicked=lambda: self.changeTool("brush"))
        brushButton.setMaximumSize(48, 48)
        brushButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        brushButton.setIcon(QIcon(f"icons/{self.settings['theme']}/brush.png"))
        brushButton.setIconSize(QSize(32, 32))
        self.toolsLayout.addWidget(brushButton)

        lineButton = QToolButton(clicked=lambda: self.changeTool("line"))
        lineButton.setMaximumSize(48, 48)
        lineButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lineButton.setIcon(QIcon(f"icons/{self.settings['theme']}/line.png"))
        lineButton.setIconSize(QSize(32, 32))
        self.toolsLayout.addWidget(lineButton)

        pickerButton = QToolButton(clicked=lambda: self.changeTool("picker"))
        pickerButton.setMaximumSize(48, 48)
        pickerButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pickerButton.setIcon(QIcon(f"icons/{self.settings['theme']}/picker.png"))
        pickerButton.setIconSize(QSize(32, 32))
        self.toolsLayout.addWidget(pickerButton)

        bucketButton = QToolButton(clicked=lambda: self.changeTool("bucket"))
        bucketButton.setMaximumSize(48, 48)
        bucketButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bucketButton.setIcon(QIcon(f"icons/{self.settings['theme']}/bucket.png"))
        bucketButton.setIconSize(QSize(32, 32))
        self.toolsLayout.addWidget(bucketButton)

        qss = "#colorButton {border: 2px solid lightgray;border-radius: 15px;background-color:rgb%}".replace("%", str(tuple(self.color)))
        colorButton = QToolButton(clicked=lambda: self.changeColor())
        colorButton.setMaximumSize(48, 48)
        colorButton.setStyleSheet(qss)
        colorButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolsLayout.addWidget(colorButton)

        self.toolButtons = {
            "brush": brushButton,
            "line": lineButton,
            "picker": pickerButton,
            "color": colorButton,
            "bucket": bucketButton,
        }

        self.drawingBoard = TrackingLabel(self)
        self.drawingBoard.setMouseTracking(True)
        self.drawingBoardScroll = TrackingScrollArea(self, self.mainWidget, objectName="drawingSpace")
        self.drawingBoardScroll.setMouseTracking(True)
        self.drawingBoardScroll.setWidgetResizable(True)
        self.drawingBoardScroll.setWidget(self.drawingBoard)
        self.drawingBoardScroll.setAlignment(Qt.AlignCenter)
        self.drawingBoardScroll.setCursor(QCursor(Qt.CrossCursor))

        self.toolLabel = QLabel(self, objectName="toolLabel")

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
        """Loads settings from settings.json"""
        with open("settings.json", "r") as file:
            self.settings = json.loads(file.read())

    def refreshStyleSheet(self, widget: QWidget) -> None:
        """Refreshes stylesheet of specified widget"""
        widget.setStyleSheet(widget.styleSheet())

    #!Project management functions
    def loadProject(self, filePath: str) -> None:
        """Loads project from file path

        Args:
            filePath (str): File path
        """
        self.filePath = filePath
        try:
            with open(filePath, "rb") as f:
                projectData = pickle.load(f)

            if projectData["version"] != extensionVersion:
                self.errorMessage("Moga wystapywac problemy przy wyswietlaniu projektu", "Wersja programu zmienila sie")

            self.projectSize = tuple(int(x) for x in projectData["size"])
            self.projectType = projectData["type"]
            self.projectName = projectData["name"]
            self.projectData = projectData["contents"]
            self.lastState = self.projectData
            self.beforeLineState = self.projectData
            self.setWindowTitle("Projektant - "+self.projectName)

            self.updateRecentProjects()
        except FileNotFoundError:
            self.errorMessage("Nie mozna otworzyc pliku", "Plik nie istnieje")
            return
        except Exception:
            self.errorMessage("Nie mozna otworzyc pliku", "Struktura pliku jest nieprawidlowa")
            return

        self.statusBar().showMessage(f"Otworzono projekt z {filePath}")

    def saveProject(self, filePath: str) -> None:
        """Saves project to specified file

        Args:
            filePath (str): File path
        """
        if not os.access(os.path.dirname(filePath), os.W_OK):
            self.errorMessage("Nie mozna zapisac pliku", "Sprawdz, czy lokalizacja pliku jest poprawna")
            return

        toWrite = {
            "version": extensionVersion,
            "type": self.projectType,
            "size": self.projectSize,
            "contents": self.projectData,
            "name": self.projectName
        }

        try:
            with open(filePath, "wb") as f:
                pickle.dump(toWrite, f)
        except Exception:
            self.errorMessage("Nie mozna zapisac pliku", "Nieznany problem, sprobuj ponownie")

        self.statusBar().showMessage(f"Zapisano projekt w {filePath}")

    def updateRecentProjects(self) -> None:
        """Updates recent project list with current project
        """
        with open("recentProjects.json", "r") as file:
            recents = json.loads(file.read())

        recents[self.filepath] = {
            "name": self.projectName,
            "type": self.projectType
        }

        with open("recentProjects.json", "w") as file:
            recents = file.write(json.dumps(recents))

    def exportProject(self) -> None:
        """Exports project to json"""
        suggestedName = "".join(self.filePath.split(".")[:-1])
        fileName, _ = QFileDialog.getSaveFileName(self,"Wybierz lokalizacje zapisu pliku", suggestedName,"Obraz (*.jpg);;Obraz (*.png)")
        if not os.access(os.path.dirname(fileName), os.W_OK):
            self.errorMessage("Nie mozna wyeksportowac projektu", "Sprawdz, czy lokalizacja pliku jest poprawna")
            return
        image = Image.fromarray(self.projectData)
        image.save(fileName)

        self.statusBar().showMessage(f"Wyeksportowano projekt do {fileName}")

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
        image = QImage(self.projectData, *self.projectSize, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        self.drawingBoard.setPixmap(pixmap.scaled(*newImageResolution, Qt.IgnoreAspectRatio, Qt.FastTransformation))

    def checkXYWithinImage(self, pixel: tuple[int, int]) -> bool:
        """Checks if pixel is within the image

        Args:
            pixel (tuple[int, int]): xy coordinates of point

        Returns:
            bool: Is the point in the image?
        """
        x = 0 <= pixel[0] < self.projectSize[0]
        y = 0 <= pixel[1] < self.projectSize[1]
        return x and y 

    def zoomImage(self, zoomAmount: float) -> None:
        """Zooms the image by specified amount

        Args:
            zoomAmount (float): How much to zoom
        """
        self.zoom += zoomAmount/500
        if self.zoom <= .1:
            self.zoom -= zoomAmount/500
        self.zoomIndicator.setText(str(round(self.zoom*100))+"%")
        self.drawPixels()

    #!Tool functions
    def changeColor(self, color: tuple[int,int,int] = None) -> None:
        """Changes tool color to specified value, if not specified, it will display color picker

        Args:
            color (tuple[int,int,int], optional): Chosen color. Defaults to color picker.
        """
        if color is None:
            x = QColorDialog.getColor()
            self.color = x.getRgb()[:-1]
        else:
            self.color = color

        qss = "border: 2px solid lightgray;border-radius: 15px;background-color:rgb%".replace("%", str(tuple(self.color)))
        self.toolButtons["color"].setStyleSheet(qss)

    def changeTool(self, tool: str) -> None:
        """Changes tool."""
        self.toolButtons[self.tool].setObjectName("")
        self.refreshStyleSheet(self.toolButtons[self.tool])
        self.lastTool = self.tool
        self.tool = tool
        self.toolButtons[self.tool].setObjectName("activeButton")
        self.refreshStyleSheet(self.toolButtons[self.tool])

    def brush(self, pixel: tuple[int, int]) -> None:
        """Function used by brush

        Args:
            pixel (tuple[int, int]): Takes pixel that will become colored
        """
        if not self.checkXYWithinImage(pixel): return
        pixel = self.pixelXYToNpXY(pixel)
        self.projectData[pixel] = self.color
        self.drawPixels()

    def line(self, end: tuple[int, int]) -> None:
        """Draws a line from point to point

        Args:
            start (QPoint): Start position of line
            end (QPoint): End position of line
        """
        start = self.getPixelXYFromXY(self.mouseDownPosition)

        if not self.checkXYWithinImage(start): return
        if not self.checkXYWithinImage(end): return

        points = tools.line.getPointListFromCoordinates(start, end)

        if self.mouseDown:
            self.projectData = np.copy(self.beforeLineState)
            for pixel in points:
                self.projectData[self.pixelXYToNpXY(pixel)] = self.color
            self.drawPixels()

    def bucket(self, pixel: tuple[int, int]) -> None:
        """Bucket fills by converting data to image, filling it and converting back to data

        Args:
            pixel (tuple[int, int]): What pixel to color
        """
        image = Image.fromarray(self.projectData)
        ImageDraw.floodfill(image, pixel, tuple(self.color))
        self.projectData = np.array(image) 

    def colorPicker(self, pixel: tuple[int, int]) -> None:
        """Function used by color picker tool

        Args:
            pixel (tuple[int, int]): Pixel that we will take color info from
        """
        self.changeColor(self.projectData[self.pixelXYToNpXY(pixel)])
        self.changeTool(self.lastTool)

    def colorPickerMove(self, event: QMouseEvent) -> None:
        position = event.windowPos().x(), event.windowPos().y() - 23
        arrayPosition = self.getPixelXYFromXY(position)

        if self.checkXYWithinImage(arrayPosition):
            arrayPosition = self.pixelXYToNpXY(arrayPosition)
            color = tuple(self.projectData[arrayPosition])
            self.toolLabel.show()
        else:
            self.toolLabel.hide()
            return

        qss = "background-color: rgb%;border: 2px solid black; border-radius: 16px;".replace("%", str(color))

        labelPosition = position[0]+10, position[1]-10
        self.toolLabel.setGeometry(*labelPosition, 32, 32)
        self.toolLabel.setStyleSheet(qss)

    #!Native PyQt5 event functions
    def wheelEvent(self, event: QWheelEvent) -> None:
        super().wheelEvent(event)
        self.zoomImage(event.angleDelta().y())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        self.mouseDown = True
        self.lastState = np.copy(self.projectData)
        self.beforeLineState = np.copy(self.projectData)
        self.mouseDownPosition = event.pos().x(), event.pos().y()-23
        self.mouseMoveEvent(event)
        self.toolLabel.hide()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.mouseDown = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        pos = event.pos().x(), event.pos().y() - 23
        pixel = self.getPixelXYFromXY(pos)

        self.tools[self.tool][0](pixel)
        self.drawPixels()

    def drawingBoardMoveEvent(self, event: QMouseEvent) -> None:
        if self.tools[self.tool][1] is not None:
            self.tools[self.tool][1](event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z and (not self.mouseDown):
            self.projectData = np.copy(self.lastState)
            self.drawPixels()

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)