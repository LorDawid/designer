from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from math import floor, ceil
import pickle
import json
import os

from customWidgets import *
import tools.line

extensionVersion = "2.0"

#Those two classes exists to be able to track mouse movement when not pressed
class TrackingScrollArea(QScrollArea):
    def __init__(self, mainWindow, parent, objectName):
        super().__init__()
        self.mainWindow = mainWindow
        self.setParent(parent)
        self.setObjectName(objectName)

        self.horizontalScrollBar().valueChanged.connect(self.scrollEvent)
        self.verticalScrollBar().valueChanged.connect(self.scrollEvent)

        self.setMouseTracking(True)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(QCursor(Qt.CrossCursor))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.mainWindow.drawingBoardMoveEvent(event)
        super().mouseMoveEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        event.ignore()

    def scrollEvent(self) -> None:
        self.scrollValue = (self.horizontalScrollBar().value(), self.verticalScrollBar().value())
        self.mainWindow.drawingBoardScrollEvent()

class TrackingLabel(QLabel):
    def __init__(self, mainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        self.pen = QPen()
        self.zoom = 1

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self.mainWindow.drawingBoardMoveEvent(event)
        super().mouseMoveEvent(event)

    def scalePixel(self, pixel: tuple[int, int]) -> tuple[int, int]:
        return pixel[0] * self.zoom + self.zoom//2, pixel[1] * self.zoom + self.zoom//2

    def paintPixel(self, pixel: tuple[int, int]) -> None:
        painter = QPainter(self.pixmap())
        painter.setPen(self.pen)
        pixel = self.scalePixel(pixel)
        painter.drawPoint(*pixel)
        painter.end()
        self.mainWindow.projectData = self.pixmap().scaled(*self.mainWindow.projectSize)

    def paintPixels(self, pixels: list) -> None:
        if len(pixels) == 0: return
        painter = QPainter(self.pixmap())
        painter.setPen(self.pen)
        for index, pixel in enumerate(pixels):
            pixels[index] = QPoint(*self.scalePixel(pixel))
        painter.drawPoints(*pixels)
        painter.end()
        self.mainWindow.projectData = self.pixmap().scaled(*self.mainWindow.projectSize)

    #stolen from https://www.pythonguis.com/faq/implementing-qpainter-flood-fill-pyqt5pyside/
    def floodFill(self, x, y) -> None:
        image = self.pixmap().toImage()
        w, h = image.width(), image.height()
        x, y = x * self.zoom, y * self.zoom

        # Get our target color from origin.
        target_color = image.pixel(x, y)

        have_seen = set()
        queue = [(x, y)]

        def get_cardinal_points(have_seen, center_pos):
            points = []
            cx, cy = center_pos
            for x, y in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                xx, yy = cx + x, cy + y
                if (xx >= 0 and xx < w and
                    yy >= 0 and yy < h and
                    (xx, yy) not in have_seen):

                    points.append((xx, yy))
                    have_seen.add((xx, yy))

            return points

        # Now perform the search and fill.
        p = QPainter(self.pixmap())
        p.setPen(self.pen.color())

        while queue:
            x, y = queue.pop()
            if image.pixel(x, y) == target_color:
                p.drawPoint(QPoint(x, y))
                queue[0:0] = get_cardinal_points(have_seen, (x, y))

        self.update()

    def changeColor(self, color: tuple[int, int, int]) -> None:
        self.mainWindow.color = color
        self.pen.setColor(QColor(*color))

    def getPixelColor(self, pixel: tuple[int, int]) -> tuple[int, int, int]:
        self.image = QPixmap.toImage(self.pixmap())
        pixel = self.scalePixel(pixel)
        color = self.image.pixelColor(*pixel)
        return color.getRgb()[:-1]

    def setZoom(self, zoom: int) -> None:
        self.zoom = zoom
        newResolution = (self.mainWindow.projectSize[0]*zoom, self.mainWindow.projectSize[1]*zoom)
        self.setPixmap(self.pixmap().scaled(*newResolution))
        self.setFixedSize(*newResolution)
        self.pen.setWidth(self.zoom)

class ToolChangeButton(QToolButton):
    def __init__(self, window, name: str, connect = None) -> None:
        super().__init__()

        if connect is None: self.clicked.connect(lambda: window.changeTool(name))
        else: self.clicked.connect(connect)
        self.setMaximumSize(48, 48)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setIcon(QIcon(f"icons/{window.settings['theme']}/{name}.png"))
        self.setIconSize(QSize(32, 32))

class Editor(QMainWindow):
    def __init__(self, filepath: str) -> None:
        self.xj = 0
        self.zoom = 1
        self.lastColors = [(255,255,255) for _ in range(0, 8)]
        self.color = (0, 0, 0)
        self.tool = "brush"
        self.mouseDown = False
        self.undoHistory = []
        self.redoHistory = []
        self.undoLength = 20

        self.lastDrawingBoardGeometry = QRect(0, 0, 0, 0)
        self.mouseDownPosition = (0, 0)
        super().__init__()

        #!
        self.gridColor = (50, 50, 50)
        self.gridHideRange = 8

        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.setWindowTitle("Edytor")

        self.drawingBoard = TrackingLabel(self)
        self.drawingBoard.setMouseTracking(True)
        self.drawingBoardScroll = TrackingScrollArea(self, self.mainWidget, objectName="drawingSpace")
        self.drawingBoardScroll.setWidget(self.drawingBoard)

        self.refreshSettings()
        self.loadStyleSheet(self.settings['theme'])
        self.filepath = filepath
        self.loadProject(self.filepath)

        sizeMessage = QToolButton(text = f"  {self.projectSize[0]} x {self.projectSize[1]}  ", objectName="smallLabel")
        sizeMessage.setIcon(QIcon(f"icons/{self.settings['theme']}/size.png"))
        sizeMessage.setIconSize(QSize(12, 12))
        sizeMessage.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.statusBar().addPermanentWidget(sizeMessage)

        self.mouseMessage = QToolButton(text = f"  {self.projectSize[0]} x {self.projectSize[1]}  ", objectName="smallLabel")
        self.mouseMessage.setIcon(QIcon(f"icons/{self.settings['theme']}/move.png"))
        self.mouseMessage.setIconSize(QSize(12, 12))
        self.mouseMessage.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.statusBar().addPermanentWidget(self.mouseMessage)

        self.zoomIndicator = QLabel(text=f"{self.zoom*100}%", objectName="smallLabel")
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

        self.saveTimer = QTimer()
        self.saveTimer.timeout.connect(self.autoSaveProject)
        self.saveTimer.setInterval(60000)
        self.saveTimer.start()

        self.mainLayout = QVBoxLayout(self.mainWidget)

        self.toolsLayout = QHBoxLayout()
        self.toolsLayout.setAlignment(Qt.AlignLeft)

        self.tools = {
            "brush":  [self.brush, None],
            "line":   [self.line, None],
            "picker": [self.colorPicker, self.colorPickerMove],
            "bucket": [self.bucket, None],
        }

        undoButton = ToolChangeButton(self, "undo", self.undo)
        self.toolsLayout.addWidget(undoButton)

        redoButton = ToolChangeButton(self, "redo", self.redo)
        self.toolsLayout.addWidget(redoButton)

        self.toolsLayout.addWidget(Divider())

        brushButton = ToolChangeButton(self, "brush")
        self.toolsLayout.addWidget(brushButton)

        lineButton = ToolChangeButton(self, "line")
        self.toolsLayout.addWidget(lineButton)

        pickerButton = ToolChangeButton(self, "picker")
        self.toolsLayout.addWidget(pickerButton)

        bucketButton = ToolChangeButton(self, "bucket")
        self.toolsLayout.addWidget(bucketButton)

        self.toolsLayout.addWidget(Divider())

        qss = "border: 2px solid lightgray;border-radius: 24px;background-color:rgb%".replace("%", str(tuple(self.color)))
        colorButton = QToolButton(clicked=lambda: self.changeColor())
        colorButton.setMaximumSize(48, 48)
        colorButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        colorButton.setStyleSheet(qss)
        self.toolsLayout.addWidget(colorButton)

        self.lastColorsLayout = QGridLayout()
        self.refreshLastColors()
        self.toolsLayout.addLayout(self.lastColorsLayout)

        self.toolsLayout.addWidget(Divider())

        def switchHSym(): 
            self.hSymmetry = not self.hSymmetry
            if self.hSymmetry: hAlignmentButton.setObjectName("activeButton")
            else: hAlignmentButton.setObjectName("")
            self.refreshStyleSheet(hAlignmentButton)
        hAlignmentButton = ToolChangeButton(self, "hSymmetry", switchHSym)
        self.toolsLayout.addWidget(hAlignmentButton)

        def switchVSym(): 
            self.vSymmetry = not self.vSymmetry
            if self.vSymmetry: vAlignmentButton.setObjectName("activeButton")
            else: vAlignmentButton.setObjectName("")
            self.refreshStyleSheet(vAlignmentButton)
        vAlignmentButton = ToolChangeButton(self, "vSymmetry", switchVSym)
        self.toolsLayout.addWidget(vAlignmentButton)

        self.toolButtons = {
            "brush": brushButton,
            "line": lineButton,
            "picker": pickerButton,
            "color": colorButton,
            "bucket": bucketButton,
        }

        self.hAlignmentWidget = QWidget(self)
        self.hAlignmentWidget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hAlignmentWidget.setStyleSheet("background-color: none")
        self.hAlignmentWidget.hide()
        self.hGridLines = [floor(self.projectSize[0]/2), ceil(self.projectSize[0]/2)]
        self.hSymmetry = False

        self.vAlignmentWidget = QWidget(self)
        self.vAlignmentWidget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.vAlignmentWidget.setStyleSheet("background-color: none")
        self.vAlignmentWidget.hide()
        self.vGridLines = [floor(self.projectSize[1]/2), ceil(self.projectSize[1]/2)]
        self.vSymmetry = False

        self.toolLabel = QLabel(self, objectName="toolLabel")

        self.mainLayout.addLayout(self.toolsLayout)
        self.mainLayout.addWidget(self.drawingBoardScroll)
        self.mainLayout.setStretch(0, 1)
        self.mainLayout.setStretch(1, 3)
        self.generateGrid()
        self.drawPixels()

        self.resize(800, 600)
        self.show()
        self.zoomEvent(0)

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
        with open(f"styles/{color}.qss", "r") as file:
            self.setStyleSheet(file.read())

    def refreshSettings(self) -> None:
        """Loads settings from settings.json"""
        with open("settings.json", "r") as file:
            self.settings = json.loads(file.read())

    def log(self) -> None:
        '''Used for debuggging'''
        return

    #!UI generation and management functions
    def refreshStyleSheet(self, widget: QWidget) -> None:
        """Refreshes stylesheet of specified widget"""
        widget.setStyleSheet(widget.styleSheet())

    def deleteLayoutContents(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.deleteLayoutContents(item.layout())

    def refreshLastColors(self) -> None:
        self.deleteLayoutContents(self.lastColorsLayout)
        for index, color in enumerate(self.lastColors):
            qss = "border: 2px solid lightgray;border-radius: 12px;background-color:rgb%".replace("%", str(tuple(color)))
            row = index//4
            column = index%4
            button = QToolButton()
            button.setStyleSheet(qss)
            button.setMaximumSize(24, 24)
            button.clicked.connect(partial(self.changeColor, color=color))
            self.lastColorsLayout.addWidget(button, row, column)

    def generateGrid(self) -> None:
        self.hGridLayout = QHBoxLayout(self.hAlignmentWidget)
        self.hGridLayout.setAlignment(Qt.AlignLeft)
        self.hGridLayout.setContentsMargins(0,0,0,0)
        self.hGridLayout.setSpacing(0)

        for n in range(0, self.projectSize[0]+1):
            label = QLabel(self, objectName="grid")
            label.setStyleSheet(f"background-color: rgb{self.gridColor}")
            label.setFixedWidth(1)
            self.hGridLayout.addWidget(label)

            if n in [ceil(self.projectSize[0]/2), floor(self.projectSize[0]/2)]:
                label.setStyleSheet(f"background-color: red")

        self.vGridLayout = QVBoxLayout(self.vAlignmentWidget)
        self.vGridLayout.setAlignment(Qt.AlignTop)
        self.vGridLayout.setContentsMargins(0,0,0,0)
        self.vGridLayout.setSpacing(0)

        for n in range(0, self.projectSize[1]+1):
            label = QLabel(self, objectName="grid")
            label.setStyleSheet(f"background-color: rgb{self.gridColor}")
            label.setFixedHeight(1)
            self.vGridLayout.addWidget(label)

            if n in [ceil(self.projectSize[1]/2), floor(self.projectSize[1]/2)]:
                label.setStyleSheet(f"background-color: red")

    def alignLabel(self) -> None:
        geometry = self.drawingBoard.geometry()

        if self.lastDrawingBoardGeometry == geometry: return

        hgeometry = (geometry.x()+8, geometry.y()+93, geometry.width()+1, geometry.height())
        self.hAlignmentWidget.setGeometry(*hgeometry)
        self.hGridLayout.setSpacing(self.zoom-1)

        vgeometry = (geometry.x()+8, geometry.y()+93, geometry.width(), geometry.height()+1)
        self.vAlignmentWidget.setGeometry(*vgeometry)
        self.vGridLayout.setSpacing(self.zoom-1)

        self.lastDrawingBoardGeometry = geometry

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
            self.drawingBoard.setPixmap(projectData["contents"])
            self.lastState = self.drawingBoard.pixmap()
            self.beforeLineState = self.drawingBoard.pixmap()
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
            "contents": PickablePixmap(self.drawingBoard.pixmap().scaled(*self.projectSize)),
            "name": self.projectName
        }

        try:
            with open(filePath, "wb") as f:
                pickle.dump(toWrite, f)
        except Exception:
            self.errorMessage("Nie mozna zapisac pliku", "Nieznany problem, sprobuj ponownie")

        self.statusBar().showMessage(f"Zapisano projekt w {filePath}")

    def autoSaveProject(self) -> None:
        filepath = "".join(self.filepath.split(".")[:-1])+"_autosave.dpct"
        self.saveProject(filepath)
        self.statusBar().showMessage(f"Automatycznie zapisano plik w {filepath}")

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

        pixmap = self.drawingBoard.pixmap().scaled(*self.projectSize)
        pixmap.save(fileName)

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
        pixel = floor(labelPos[0]/self.zoom), floor(labelPos[1]/self.zoom)
        return pixel

    def drawPixels(self) -> None:
        """Draws all pixels onto QLabel
        """
        self.drawingBoard.setZoom(self.zoom)
        self.drawingBoard.update()

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

    def undo(self) -> None:
        if len(self.undoHistory) != 0:
            self.redoHistory.append(QPixmap(self.drawingBoard.pixmap()))
            self.drawingBoard.setPixmap(QPixmap(self.undoHistory[-1]))
            self.undoHistory = self.undoHistory[:-1]
            self.statusBar().showMessage("Cofnieto (Ctrl+Y aby ponowic)")
        else:
            self.statusBar().showMessage("Nie mozna cofnac - historia pusta")

        self.drawPixels()

    def redo(self) -> None:
        if len(self.redoHistory) != 0:
            self.undoHistory.append(QPixmap(self.drawingBoard.pixmap()))
            self.drawingBoard.setPixmap(QPixmap(self.redoHistory[-1]))
            self.redoHistory = self.redoHistory[:-1]
            self.statusBar().showMessage("Ponowiono (Ctrl+Z aby cofnac)")
            self.drawPixels()
        else:
            self.statusBar().showMessage("Nie mozna ponowic - historia pusta")

        if len(self.undoHistory) > self.undoLength:
            self.undoHistory = self.undoHistory[1:]

        self.drawPixels()

    #!Tool functions
    def changeColor(self, color: tuple[int,int,int] = None) -> None:
        """Changes tool color to specified value, if not specified, it will display color picker

        Args:
            color (tuple[int,int,int], optional): Chosen color. Defaults to color picker.
        """
        if color is None:
            x = QColorDialog.getColor()
            color = x.getRgb()[:-1]

        self.lastColors.insert(0, self.color)
        self.lastColors = self.lastColors[:-1]
        self.refreshLastColors()

        self.drawingBoard.changeColor(color)

        qss = "border: 2px solid lightgray;border-radius: 24px;background-color:rgb%".replace("%", str(tuple(self.color)))
        self.toolButtons["color"].setStyleSheet(qss)

    def changeTool(self, tool: str) -> None:
        """Changes tool."""
        self.toolButtons[self.tool].setObjectName("")
        self.refreshStyleSheet(self.toolButtons[self.tool])
        self.lastTool = self.tool
        self.tool = tool
        self.toolButtons[self.tool].setObjectName("activeButton")
        self.refreshStyleSheet(self.toolButtons[self.tool])

    def paintPixel(self, pixel: tuple[int, int]) -> None:
        if not self.checkXYWithinImage(pixel): return
        for pixel in self.symmetrize(pixel):
            self.drawingBoard.paintPixel(pixel)
        self.drawPixels()

    def paintPixels(self, pixels: list) -> None:
        self.drawingBoard.paintPixels(pixels)
        self.drawPixels()

    def symmetrize(self, pixel: tuple[int, int]) -> list:
        pixelList = [pixel]
        if self.vSymmetry:
            pixelList.append((pixel[0], (self.projectSize[1] - 1 - pixel[1])))

        if self.hSymmetry:
            pixelList.append(((self.projectSize[0] - 1 - pixel[0]), pixel[1]))

        if self.vSymmetry and self.hSymmetry:
            pixelList.append(((self.projectSize[0] - 1 - pixel[0]), (self.projectSize[1] - 1 - pixel[1])))

        return pixelList

    def brush(self, pixel: tuple[int, int]) -> None:
        """Function used by brush

        Args:
            pixel (tuple[int, int]): Takes pixel that will become colored
        """
        if not self.checkXYWithinImage(pixel): return
        self.paintPixel(pixel)
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
            self.drawingBoard.setPixmap(QPixmap(self.beforeLineState))
            self.paintPixels(points)
            self.drawPixels()

    def bucket(self, pixel: tuple[int, int]) -> None:
        """Bucket fills by converting data to image, filling it and converting back to data

        Args:
            pixel (tuple[int, int]): What pixel to color
        """
        self.drawingBoard.floodFill(*pixel)

    def colorPicker(self, pixel: tuple[int, int]) -> None:
        """Function used by color picker tool

        Args:
            pixel (tuple[int, int]): Pixel that we will take color info from
        """
        self.changeColor(self.drawingBoard.getPixelColor(pixel))
        self.changeTool(self.lastTool)

    def colorPickerMove(self, event: QMouseEvent) -> None:
        position = event.windowPos().x(), event.windowPos().y() - 23
        arrayPosition = self.getPixelXYFromXY(position)

        if self.checkXYWithinImage(arrayPosition):
            color = self.drawingBoard.getPixelColor(arrayPosition)
            self.toolLabel.show()
        else:
            self.toolLabel.hide()
            return

        qss = "background-color: rgb%;border: 2px solid black; border-radius: 16px;".replace("%", str(color))

        labelPosition = position[0]+10, position[1]-10
        self.toolLabel.setGeometry(*labelPosition, 32, 32)
        self.toolLabel.setStyleSheet(qss)

    #!Event functions
    def wheelEvent(self, event: QWheelEvent) -> None:
        super().wheelEvent(event)
        self.zoomEvent(event.angleDelta().y())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        self.mouseDown = True
        self.mouseDownPosition = event.pos().x(), event.pos().y()-23
        self.undoHistory.append(QPixmap(self.drawingBoard.pixmap()))
        self.beforeLineState = QPixmap(self.drawingBoard.pixmap())
        self.mouseMoveEvent(event)
        self.toolLabel.hide()

        if len(self.undoHistory) > self.undoLength:
            self.undoHistory = self.undoHistory[1:]

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.mouseDown = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        pos = event.pos().x(), event.pos().y() - 23
        pixel = self.getPixelXYFromXY(pos)

        self.mouseMessage.setText(str(pixel))

        self.tools[self.tool][0](pixel)
        self.drawPixels()

        if not self.checkXYWithinImage(pixel): return
        self.redoHistory = []

    def drawingBoardMoveEvent(self, event: QMouseEvent) -> None:
        if self.tools[self.tool][1] is not None:
            self.tools[self.tool][1](event)
        self.alignLabel()

        pixel = self.getPixelXYFromXY((event.pos().x(), event.pos().y() - 23))
        pixel = [str(x) for x in pixel]

        self.mouseMessage.setText("  "+", ".join(pixel))

    def drawingBoardScrollEvent(self) -> None:
        self.alignLabel()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.alignLabel()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z and (not self.mouseDown): self.undo()
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Y and (not self.mouseDown): self.redo()
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_L and (not self.mouseDown):
            self.log()

    def closeEvent(self, event: QCloseEvent) -> None:
        saveDialogue = QMessageBox()
        saveDialogue.setWindowTitle(" ")
        saveDialogue.setText("Projekt mogl byc zedytowany")
        saveDialogue.setInformativeText("Czy chcesz zapisac swoje zmiany?")
        saveDialogue.setStandardButtons(QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
        saveDialogue.setDefaultButton(QMessageBox.Save)
        userChoice = saveDialogue.exec_()
        saveDialogue.deleteLater()

        if userChoice == QMessageBox.Save:
            self.saveProject(self.filepath)
        elif userChoice == QMessageBox.Cancel:
            event.ignore()
            return

        super().closeEvent(event)

    def zoomEvent(self, zoomAmount: float) -> None:
        """Zooms the image by specified amount

        Args:
            zoomAmount (float): How much to zoom
        """
        if zoomAmount > 0:
            self.zoom *= 2
        elif zoomAmount < 0:
            self.zoom /= 2

        if self.zoom < .5:
            self.zoom = abs(self.zoom)
            self.zoom *= 2

        if self.zoom > 64:
            self.zoom /= 2

        if self.zoom < self.gridHideRange:
            self.hAlignmentWidget.hide()
            self.vAlignmentWidget.hide()
        else:
            self.hAlignmentWidget.show()
            self.vAlignmentWidget.show()

        self.zoomIndicator.setText(str(round(self.zoom*100))+"%")
        self.drawPixels()
        self.alignLabel()