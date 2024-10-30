from PySide6.QtCore import (QCoreApplication, QMetaObject, QPoint, QRect, Qt, QMimeData, Signal, QEvent)
from PySide6.QtGui import (QColor, QFont, QImage, QPainter, QPixmap, QTransform, QDrag, QDropEvent, QDragLeaveEvent, QMouseEvent, QCursor, QPalette)
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
    QFrame, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel, QLineEdit,
    QListWidget, QMenu,
    QMenuBar, QPushButton, QSizePolicy, QStatusBar,
    QWidget, QGridLayout, QWidget, QSlider)
import os, time

from networkx import number_weakly_connected_components
from Handler_Formats import *

class DragItem(QLabel):
    def __init__(self, SourceWidget, RootWidget, e, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SourceWidget = SourceWidget
        self.RootWidget = RootWidget
        self.e = e
    def runtime(self):
        self.DragPreview = QDrag(self)
        mime_data = QMimeData()
        transform = QTransform()
        self.DragPreview.setMimeData(mime_data)
        self.RunDrop = True
        if type(self.SourceWidget) == DragList:
            transform.scale(self.RootWidget.PanelScaleFactor, self.RootWidget.PanelScaleFactor)
            item = QPixmap(self.RootWidget.SourceFolderFiles.GetRealItem(self.SourceWidget.currentRow()).fullname).transformed(transform)
            self.XYOffset = (good_int(item.width() // 2), good_int(item.height() // 2))
        elif type(self.SourceWidget) == DragImage:
            transform.scale(self.RootWidget.PanelScaleFactor, self.RootWidget.PanelScaleFactor)
            item = QPixmap(self.SourceWidget.TruePixPath).transformed(transform)
            self.XYOffset = (good_int(item.width() // 2), good_int(item.height() // 2))            
        elif type(self.SourceWidget) == DragGraphicsView: # Has to get current translation of img                
            transform.scale(self.SourceWidget.currentTotalZoomFactor, self.SourceWidget.currentTotalZoomFactor)
            item = self.SourceWidget.ViewPixMap.pixmap().transformed(transform)
            self.XYOffset = (self.e.pos().x() - self.SourceWidget.ViewPixMap.sceneTransform().dx(),self.e.pos().y() - self.SourceWidget.ViewPixMap.sceneTransform().dy())
            
        HotSpot = QPoint(self.XYOffset[0], self.XYOffset[1])
        
        self.DragPreview.setPixmap(item)  # Grafische Darstellung des Drag-Items        
        self.DragPreview.setHotSpot(HotSpot)  # Relative Position des Drag-Items zur Maus
        self.DragPreview.exec_(Qt.DropAction.MoveAction)
        if type(self.SourceWidget) == DragGraphicsView and self.RunDrop:
            self.SourceWidget.dropEvent(self.e, alternativePos=QCursor.pos()) #pyautogui.position())
class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def dragEnterEvent(self, e):    #Event if something is dragged Into the widget
        e.accept()
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Drop:
            self.dropEvent(event)
    def dropEvent(self, event):
        pass

class DragGraphicsView(QGraphicsView):
    def __init__(self, RootParent, FrameSizeX, FrameSizeY, *args, **kwargs):
        ##Custom Class Vars 
        self.RootParent = RootParent
        self.dragStart = None
        self.currentTotalZoomFactor = 1
        self.currentPanelZoomFactor = 1
        self.currentInternalZoomFactor = 1
        self.TruePixMap = None
        self.TruePixPath = ""
        self.ViewPixMap = None
        self.deltaX = 0.0
        self.deltaY = 0.0
        self.Index = (-1,-1)
        self.FrmCenter = (-1,-1)
        self.FrameSizeX = FrameSizeX
        self.FrameSizeY = FrameSizeY
        self.xyPos = None
        self.DragItem = None

        ##Init
        super(DragGraphicsView, self).__init__(*args, **kwargs)
        self.theScene = GraphicsScene()
        self.setScene(self.theScene)        
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def xeventFilter(self, obj, event):
        match event.type():
            case QEvent.DragEnter:
                self.dragEnterEvent(event)
            case QEvent.Drop:
                self.dropEvent(event)
            case QEvent.MouseMove:
                self.mouseMoveEvent(event)
            case QEvent.MouseButtonPress:
                self.mousePressEvent(event)
            case QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)
            case QEvent.Wheel:
                self.wheelEvent(event)
            case QEvent.DragEnter:
                self.dragEnterEvent(event)
            case QEvent.DragMove:
                self.dragMoveEvent(event)
            case QEvent.DragLeave:
                self.dragLeaveEvent(event)
            case QEvent.Drop:
                self.dropEvent(event)
            case _:
                return False
        return True
    def mousePressEvent(self, e):
        if e.buttons() == Qt.MouseButton.RightButton:
            self.removeImage()            
            self.dragStart = None
            e.accept()
        elif e.buttons() == Qt.MouseButton.LeftButton:
            if self.dragStart == None and not self.ViewPixMap == None:
                self.dragStart = self.mapToGlobal(e.position())
                self.DragItem = DragItem(self, self.RootParent, e)
                self.DragItem.runtime()
        else:
            pass
    def mouseReleaseEvent(self, e):
        if e.type() == QEvent.MouseButtonRelease and not self.dragStart == None:
            deltaX = e.position().x() - self.dragStart.x()
            deltaY = e.position().y() - self.dragStart.y()
            self.move_img_delta(deltaX, deltaY)
            self.dragStart = None

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:   
            pass        
        elif not self.dragStart == None:
            self.dropEvent(e)
            self.dragStart = None   
        else:
            pass
        if e.source() != Qt.MouseEventSource.MouseEventNotSynthesized:
            e.source().dragStart = None

    def wheelEvent(self, e):
        self.currentInternalZoomFactor = clamp_float(self.currentInternalZoomFactor * (1 + (e.angleDelta().y() / 1200)), 0.1, 10)
        self.ApplyZoomFactors(True)
        
    def dragEnterEvent(self, e):    #Event if something is dragged Into the widget
        e.accept()
        e.acceptProposedAction()

    def dragMoveEvent(self, e):
        self.xyPos = self.mapToGlobal(e.position())
        e.accept()
        e.acceptProposedAction()
    
    def dragLeaveEvent(self, e):
        e.accept()

    def dropEvent(self, e, alternativePos = None):
        if self.objectName() == "ImgLbl_CurSelOrDrag":      #ImgLbl_CurSelOrDrag gets updated via list!
            try:
                e.source().dragStart = None
            except:
                pass
            self.dragStart = None
            return
        if alternativePos == None:
            if type(e) == QDropEvent:
                DropPos = e.position()
            elif type(e) == QDragLeaveEvent:
                DropPos = alternativePos
            elif type(e) == QMouseEvent:
                DropPos = QPoint(alternativePos.x, alternativePos.y) #self.mapToGlobal(e.position())
        else:
            if type(e) == QMouseEvent:
                DropPos = alternativePos
            else:
                DropPos = alternativePos
        if type(e) == QDropEvent:
            widget = e.source()
            if type(widget) == DragItem:
                if type(widget.SourceWidget) == DragList:            
                    widget.SourceWidget.dragStart = None
                    self.dragStart = None
                    self.AddImage(self.RootParent.SourceFolderFiles.GetRealItem(self.RootParent.Lis_SourceFiles.currentIndex().row()).fullname, DropPos.x(), DropPos.y(), e)
                elif type(widget.SourceWidget) == DragImage:
                    self.AddImage(widget.SourceWidget.TruePixPath, DropPos.x(), DropPos.y(), e)
                elif type(widget.SourceWidget) == DragGraphicsView:
                    if alternativePos == None:
                        DropPos = self.mapToGlobal(e.position())
                    else:
                        DropPos = alternativePos
                    if widget.SourceWidget == self:
                        dx = DropPos.x() - self.dragStart.x()
                        dy = DropPos.y() - self.dragStart.y()
                        self.move_img_delta(dx, dy)
                    else:
                        widget.SourceWidget.dropEvent(e, DropPos)
            self.dragStart = None
            if not self.DragItem == None: self.DragItem.RunDrop = False
        elif type(e) == QMouseEvent:
            dx = DropPos.x() - self.dragStart.x()
            dy = DropPos.y() - self.dragStart.y()
            self.move_img_delta(dx, dy)
            self.dragStart = None

        e.accept()

    def AddImage(self, image, deltaX = 0, deltaY = 0, e = None):
        if type(image) == str:            
            if os.path.exists(image):
                self.TruePixMap = QPixmap(image)
                self.ViewPixMap = None
                self.TruePixPath = image
                self.deltaX = deltaX
                self.deltaY = deltaY
        elif type(image) == QPixmap:
            self.TruePixMap = QPixmap(image)
            self.deltaX = deltaX
            self.deltaY = deltaY
        self.ApplyZoomFactors(e = e)

    def removeImage(self):
        self.TruePixMap = None
        self.TruePixPath = ""
        self.ViewPixMap = None
        self.deltaX = 0
        self.deltaY = 0
        self.ApplyZoomFactors()
    
    def move_img_delta(self, deltaX, deltaY):
        self.currentTotalZoomFactor = self.currentInternalZoomFactor * self.currentPanelZoomFactor
        self.deltaX += deltaX / self.currentTotalZoomFactor
        self.deltaY += deltaY / self.currentTotalZoomFactor      
        self.ApplyZoomFactors()

    def ApplyZoomFactors(self, MWheelInduced = False, e = None):        
        if len(self.theScene.items()) > 0:  #Clean old items from Scene
            self.theScene.removeItem(self.theScene.items()[0])
        if self.TruePixMap is not None:
            self.currentTotalZoomFactor = self.currentInternalZoomFactor * self.currentPanelZoomFactor
            realSource = None
            if e:
                try:
                    realSource = e.source().SourceWidget
                except:
                    realSource = e.source()
            if type(e) == QDropEvent:
                if type(realSource) == DragList or type(realSource) == DragImage:
                    curDragPixMap = e.source().XYOffset
                    self.deltaX = self.deltaX-curDragPixMap[0]
                    self.deltaY = self.deltaY-curDragPixMap[1]
            
            self.curtransform = QTransform().translate(self.deltaX*self.currentTotalZoomFactor, self.deltaY*self.currentTotalZoomFactor)
            self.curtransform.scale(self.currentTotalZoomFactor, self.currentTotalZoomFactor)
            self.ViewPixMap = QGraphicsPixmapItem(self.TruePixMap.copy())
            self.ViewPixMap.setTransform(self.curtransform)             
            self.theScene.addItem(self.ViewPixMap)  
        startX = self.FrmCenter[0] - self.FrameSizeX
        startY = self.FrmCenter[1] - self.FrameSizeY
        self.theScene.setSceneRect(QRect(QPoint(0, 0), QPoint(self.FrameSizeX,self.FrameSizeY)))
        if True:
            if self.Index == (0,0):
                self.setGeometry(QRect(QPoint(startX, startY), QPoint(self.FrmCenter[0], self.FrmCenter[1])))
            elif self.Index == (0,1):
                self.setGeometry(QRect(QPoint(self.FrmCenter[0], startY), QPoint(self.FrmCenter[0]+self.FrameSizeX, self.FrmCenter[1])))
            elif self.Index == (1,0):
                self.setGeometry(QRect(QPoint(startX, self.FrmCenter[1]), QPoint(self.FrmCenter[0], self.FrmCenter[1] + self.FrameSizeY)))
            elif self.Index == (1,1):
                self.setGeometry(QRect(QPoint(self.FrmCenter[0], self.FrmCenter[1]), QPoint(self.FrmCenter[0]+self.FrameSizeX, self.FrmCenter[1]+self.FrameSizeY)))
        
    def get_img_correct_size(self):
        #Gets the frame of the image as image and applies the current image on it
        if self.ViewPixMap is not None:
            theViewMap = self.ViewPixMap.pixmap()
            trueSize = (good_int(self.RootParent.Txt_TilePixelSizeX.text()), good_int(self.RootParent.Txt_TilePixelSizeY.text()))
            trueOffset = (self.curtransform.dx()/self.currentTotalZoomFactor, self.curtransform.dy()/self.currentTotalZoomFactor)
            CorrectImg = QImage(trueSize[0], trueSize[1], QImage.Format.Format_ARGB32)
            painter = QPainter(CorrectImg)
            painter.drawPixmap(trueOffset[0], trueOffset[1], theViewMap)
            painter.end()
            return CorrectImg
        
class DragImage(QLabel):
    """
    Generic list sorting handler.
    """

    orderChanged = Signal(list)

    def __init__(self, RootParent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.RootParent = RootParent
        self.dragStart = None
        self.currentTotalZoomFactor = 1
        self.currentPanelZoomFactor = 1
        self.currentInternalZoomFactor = 1
        self.TruePixMap = None
        self.TruePixPath = ""
        self.deltaX = 0.0
        self.deltaY = 0.0
        self.DragItem = None
        self.setAcceptDrops(True)

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            if self.dragStart == None:
                self.dragStart = e.position()
            self.DragItem = DragItem(self, self.RootParent, e)
            e.accept()
            self.DragItem.runtime()
        elif not self.dragStart == None:
            self.dragStart = None
        if e.buttons() == Qt.MouseButton.MiddleButton:
            pass
        if e.source() != Qt.MouseEventSource.MouseEventNotSynthesized:
            e.source().dragStart = None
        e.accept()
    def wheelEvent(self, e):
        self.currentInternalZoomFactor = clamp_float(self.currentInternalZoomFactor * (1 + (e.angleDelta().y() / 1200)), 0.1, 10)
        self.ApplyZoomFactors()
        
    def dragEnterEvent(self, e):    #Event if something is dragged Into the widget
        e.accept()

    def dropEvent(self, e):
        if self.objectName() == "ImgLbl_CurSelOrDrag":      #ImgLbl_CurSelOrDrag gets updated via list!
            try:
                e.source().dragStart = None
            except:
                pass
            self.dragStart = None
            return
        pos = e.position()
        widget = e.source()
        if type(widget) == DragList:            
            widget.dragStart = None
            self.dragStart = None
            self.AddImage(self.RootParent.SourceFolderFiles.GetRealItem(self.RootParent.Lis_SourceFiles.currentIndex().row()).fullname)
        elif type(widget) == DragGraphicsView or type(widget) == DragImage:            
            if widget == self:
                dx = pos.x() - self.dragStart.x()
                dy = pos.y() - self.dragStart.y()
                self.move_img_delta(dx, dy)
            else:
                self.AddImage(widget.TruePixPath)
            if 1==0:
                pass
        #self.blayout.insertWidget(n, widget)
        #self.orderChanged.emit(self.get_item_data())

        e.accept()

    def AddImage(self, image):
        if type(image) == str:            
            if os.path.exists(image):
                self.TruePixMap = QPixmap(image)
                self.ViewPixMap = self.TruePixMap.copy()
                self.TruePixPath = image
                self.setPixmap(self.ViewPixMap)
                self.deltaX = 0
                self.deltaY = 0
        elif type(image) == QPixmap:
            self.TruePixMap = image
            self.deltaX = 0
            self.deltaY = 0
            self.setPixmap(self.TruePixMap)
        self.ApplyZoomFactors()
    
    def move_img_delta(self, deltaX, deltaY):
        self.deltaX += deltaX
        self.deltaY += deltaY        
        self.ApplyZoomFactors()

    def ApplyZoomFactors(self):        
        if self.TruePixMap is None: return
        self.currentTotalZoomFactor = self.currentPanelZoomFactor * self.currentInternalZoomFactor
        transform = QTransform().translate(self.deltaX, self.deltaY)
        self.ViewPixMap = self.TruePixMap.transformed(transform)
        transform = QTransform().scale(self.currentTotalZoomFactor, self.currentTotalZoomFactor)        
        self.ViewPixMap = self.ViewPixMap.transformed(transform)
        self.setPixmap(self.ViewPixMap)

class DragList(QListWidget):
    """
    Generic list sorting handler.
    """

    def __init__(self, RootWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.RootWidget = RootWidget
        self.setDragEnabled(True)
        self.lastPressed = None
        self.DragPreview = None
        self.XYOffset = None

    def mousePressEvent(self, e):   
        lastRow = self.currentRow()
        self.setCurrentRow(self.indexAt(e.pos()).row())
        if self.lastPressed == None:
            self.lastPressed = time.time()
        else:
            if time.time() - self.lastPressed < 0.25:
                if self.currentRow() == lastRow:
                    self.RootWidget.addFreeImage()
            self.lastPressed = time.time()
        e.accept()
    def dragMoveEvent(self, e):
        e.accept()
    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            self.DragItem = DragItem(self, self.RootWidget, e)
            e.accept()
            self.DragItem.runtime()


    def add_item(self, item):
        self.blayout.addWidget(item)

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data


class DragWidget(QWidget):
    """
    Generic list sorting handler.
    """

    orderChanged = Signal(list)

    def __init__(self, widget, *args, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = widget
        self.widget.setParent(self)
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        #self.orientation = orientation

        #if self.orientation == Qt.Orientation.Vertical:
            #self.blayout = QVBoxLayout()
        #else:
            #self.blayout = QHBoxLayout()

        #self.setLayout(self.blayout)

    def setWidget(self, widget):
        self.widget = widget
        self.widget.setParent(self)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.position()
        widget = e.source()
        self.blayout.removeWidget(widget)

        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            if self.orientation == Qt.Orientation.Vertical:
                # Drag drop vertically.
                drop_here = pos.y() < w.y() + w.size().height() // 2
            else:
                # Drag drop horizontally.
                drop_here = pos.x() < w.x() + w.size().width() // 2

            if drop_here:
                break

        else:
            # We aren't on the left hand/upper side of any widget,
            # so we're at the end. Increment 1 to insert after.
            n += 1

        self.blayout.insertWidget(n, widget)
        self.orderChanged.emit(self.get_item_data())

        e.accept()

    def add_item(self, item):
        self.blayout.addWidget(item)

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data

class Ui_ImageTilerObj(object):
    def setupUi(self, ImageTilerObj):
        ## Main Window
        if not ImageTilerObj.objectName():
            ImageTilerObj.setObjectName(u"ImageTilerObj")
        ImageTilerObj.resize(1174, 842)
        self.centralwidget = QWidget(ImageTilerObj)
        self.centralwidget.setObjectName(u"centralwidget")

        ## Main Frame
        self.MainFrame = QFrame(self.centralwidget)
        self.MainFrame.setObjectName(u"MainFrame")
        self.MainFrame.setGeometry(QRect(20, 78, 1131, 741))
        self.MainFrame.setFrameShape(QFrame.StyledPanel)
        self.MainFrame.setFrameShadow(QFrame.Raised)

        ## Source Folder Select
        self.Frm_SelSourceFolder = QFrame(self.centralwidget)
        self.Frm_SelSourceFolder.setObjectName(u"Frm_SelSourceFolder")
        self.Frm_SelSourceFolder.setGeometry(QRect(20, 10, 281, 51))
        self.Frm_SelSourceFolder.setFrameShape(QFrame.StyledPanel)
        self.Frm_SelSourceFolder.setFrameShadow(QFrame.Raised)
        self.Txt_SelSourceFolder = QLineEdit(self.Frm_SelSourceFolder)
        self.Txt_SelSourceFolder.setObjectName(u"Txt_SelSourceFolder")
        self.Txt_SelSourceFolder.setGeometry(QRect(20, 20, 171, 20))
        self.Txt_SelSourceFolder.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Lab_SelSourceFolder = QLabel(self.Frm_SelSourceFolder)
        self.Lab_SelSourceFolder.setObjectName(u"Lab_SelSourceFolder")
        self.Lab_SelSourceFolder.setGeometry(QRect(10, 0, 121, 16))
        self.Btn_SelSourceFolder = QPushButton(self.Frm_SelSourceFolder)
        self.Btn_SelSourceFolder.setObjectName(u"Btn_SelSourceFolder")
        self.Btn_SelSourceFolder.setGeometry(QRect(200, 20, 75, 23))

        ## Source Files Frame
        self.Frm_SourceFiles = QFrame(self.MainFrame)
        self.Frm_SourceFiles.setObjectName(u"Frm_SourceFiles")
        self.Frm_SourceFiles.setGeometry(QRect(20, 20, 251, 561))
        self.Frm_SourceFiles.setFrameShape(QFrame.StyledPanel)
        self.Frm_SourceFiles.setFrameShadow(QFrame.Raised)
        self.Lab_SourceFiles = QLabel(self.Frm_SourceFiles)
        self.Lab_SourceFiles.setObjectName(u"Lab_SourceFiles")
        self.Lab_SourceFiles.setGeometry(QRect(10, 10, 61, 16))
        self.Lis_SourceFiles = DragList(self, self.Frm_SourceFiles)
        self.Lis_SourceFiles.setObjectName(u"Lis_SourceFiles")
        self.Lis_SourceFiles.setGeometry(QRect(10, 50, 231, 481))
        self.Lis_SourceFiles.setAcceptDrops(False)
        self.Lis_SourceFiles.setDragDropMode(QAbstractItemView.DragOnly)
        self.Lab_SourceFilesDnDInfo = QLabel(self.Frm_SourceFiles)
        self.Lab_SourceFilesDnDInfo.setObjectName(u"Lab_SourceFilesDnDInfo")
        self.Lab_SourceFilesDnDInfo.setGeometry(QRect(40, 30, 141, 16))


        ## Pixel Sizes
        self.Frm_PixelSizes = QFrame(self.MainFrame)
        self.Frm_PixelSizes.setObjectName(u"Frm_PixelSizes")
        self.Frm_PixelSizes.setGeometry(QRect(270, 220, 191, 261))
        self.Frm_PixelSizes.setFrameShape(QFrame.StyledPanel)
        self.Frm_PixelSizes.setFrameShadow(QFrame.Raised)
        self.Var_TilePixelSizeRatio = (3/4)
        self.Txt_TilePixelSizeX = QLineEdit(self.Frm_PixelSizes)
        self.Txt_TilePixelSizeX.setObjectName(u"Txt_TilePixelSizeX")
        self.Txt_TilePixelSizeX.setGeometry(QRect(10, 20, 71, 20))
        self.Txt_TilePixelSizeX.setAutoFillBackground(False)
        self.Txt_TilePixelSizeX.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Txt_TilePixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"480", None))        
        self.Lab_TilePixelSizeX = QLabel(self.Frm_PixelSizes)
        self.Lab_TilePixelSizeX.setObjectName(u"Lab_TilePixelSizeX")
        self.Lab_TilePixelSizeX.setGeometry(QRect(20, 0, 81, 16))
        self.Txt_TilePixelSizeY = QLineEdit(self.Frm_PixelSizes)
        self.Txt_TilePixelSizeY.setObjectName(u"Txt_TilePixelSizeY")
        self.Txt_TilePixelSizeY.setGeometry(QRect(10, 70, 71, 20))
        self.Txt_TilePixelSizeY.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Lab_TilePixelSizeY = QLabel(self.Frm_PixelSizes)
        self.Lab_TilePixelSizeY.setObjectName(u"Lab_TilePixelSizeY")
        self.Lab_TilePixelSizeY.setGeometry(QRect(20, 50, 81, 16))
        self.Txt_TilePixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"640", None))
        self.Checkb_LinkXY = QCheckBox(self.Frm_PixelSizes)
        self.Checkb_LinkXY.setObjectName(u"Checkb_LinkXY")
        self.Checkb_LinkXY.setEnabled(True)
        self.Checkb_LinkXY.setGeometry(QRect(100, 30, 70, 17))
        self.Checkb_LinkXY.setChecked(True)
        self.Txt_TotalPixelSizeX = QLineEdit(self.Frm_PixelSizes)
        self.Txt_TotalPixelSizeX.setObjectName(u"Txt_TotalPixelSizeX")
        self.Txt_TotalPixelSizeX.setGeometry(QRect(10, 170, 71, 20))
        self.Txt_TotalPixelSizeX.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Txt_TotalPixelSizeY = QLineEdit(self.Frm_PixelSizes)
        self.Txt_TotalPixelSizeY.setObjectName(u"Txt_TotalPixelSizeY")
        self.Txt_TotalPixelSizeY.setGeometry(QRect(10, 220, 71, 20))
        self.Txt_TotalPixelSizeY.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Lab_TotalPixelSizeX = QLabel(self.Frm_PixelSizes)
        self.Lab_TotalPixelSizeX.setObjectName(u"Lab_TotalPixelSizeX")
        self.Lab_TotalPixelSizeX.setGeometry(QRect(20, 150, 91, 16))
        self.Lab_TotalPixelSizeY = QLabel(self.Frm_PixelSizes)
        self.Lab_TotalPixelSizeY.setObjectName(u"Lab_TotalPixelSizeY")
        self.Lab_TotalPixelSizeY.setGeometry(QRect(20, 200, 91, 16))
        self.Lin_LinkXY = QFrame(self.Frm_PixelSizes)
        self.Lin_LinkXY.setObjectName(u"Lin_LinkXY")
        self.Lin_LinkXY.setGeometry(QRect(0, 40, 20, 31))
        self.Lin_LinkXY.setFrameShape(QFrame.VLine)
        self.Lin_LinkXY.setFrameShadow(QFrame.Sunken)
        self.Lin_LinkXY2 = QFrame(self.Frm_PixelSizes)
        self.Lin_LinkXY2.setObjectName(u"Lin_LinkXY2")
        self.Lin_LinkXY2.setGeometry(QRect(0, 190, 20, 31))
        self.Lin_LinkXY2.setFrameShape(QFrame.VLine)
        self.Lin_LinkXY2.setFrameShadow(QFrame.Sunken)
        self.Lin_LinkTileTotal = QFrame(self.Frm_PixelSizes)
        self.Lin_LinkTileTotal.setObjectName(u"Lin_LinkTileTotal")
        self.Lin_LinkTileTotal.setGeometry(QRect(0, 90, 20, 81))
        self.Lin_LinkTileTotal.setFrameShape(QFrame.VLine)
        self.Lin_LinkTileTotal.setFrameShadow(QFrame.Sunken)

        #Zoom Grid
        self.Frm_CurPanelPreviewZoom = QFrame(self.MainFrame)
        self.Frm_CurPanelPreviewZoom.setObjectName(u"Frm_CurPanelPreviewZoom")
        self.Frm_CurPanelPreviewZoom.setGeometry(QRect(340, 610, 120, 80))
        self.Frm_CurPanelPreviewZoom.setFrameShape(QFrame.StyledPanel)
        self.Frm_CurPanelPreviewZoom.setFrameShadow(QFrame.Raised)
        self.Lab_CurPanelPreviewZoom = QLabel(self.Frm_CurPanelPreviewZoom)
        self.Lab_CurPanelPreviewZoom.setObjectName(u"Lab_CurPanelPreviewZoom")
        self.Lab_CurPanelPreviewZoom.setGeometry(QRect(10, 10, 91, 16))
        self.Txt_CurPanelPreviewZoom = QLineEdit(self.Frm_CurPanelPreviewZoom)
        self.Txt_CurPanelPreviewZoom.setObjectName(u"Txt_CurPanelPreviewZoom")
        self.Txt_CurPanelPreviewZoom.setGeometry(QRect(30, 30, 71, 20))
        self.Txt_CurPanelPreviewZoom.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.PanelScaleFactor = 0.5
        self.Txt_CurPanelPreviewZoom.setText(QCoreApplication.translate("ImageTilerObj", u"0.5", None))
        self.HoSli_CurPanelPreviewZoom = QSlider(self.Frm_CurPanelPreviewZoom)
        self.HoSli_CurPanelPreviewZoom.setObjectName(u"HoSli_CurPanelPreviewZoom")
        self.HoSli_CurPanelPreviewZoom.setGeometry(QRect(30, 60, 71, 20))
        self.HoSli_CurPanelPreviewZoom.setOrientation(Qt.Horizontal)      

        ## Current Selected Frame Preview
        self.Frm_CurSelOrDrag = QFrame(self.MainFrame)
        self.Frm_CurSelOrDrag.setObjectName(u"Frm_CurSelOrDrag")
        self.Frm_CurSelOrDrag.setGeometry(QRect(270, 20, 191, 201))
        self.Frm_CurSelOrDrag.setFrameShape(QFrame.StyledPanel)
        self.Frm_CurSelOrDrag.setFrameShadow(QFrame.Raised)
        self.Lab_CurSelOrDrag = QLabel(self.Frm_CurSelOrDrag)
        self.Lab_CurSelOrDrag.setObjectName(u"Lab_CurSelOrDrag")
        self.Lab_CurSelOrDrag.setGeometry(QRect(10, 0, 141, 31))
        self.Lab_CurSelOrDrag.setScaledContents(False)
        self.Lab_CurSelOrDrag.setWordWrap(True)
        self.Frm_CurSelOrDragImg = QFrame(self.Frm_CurSelOrDrag)
        self.Frm_CurSelOrDragImg.setObjectName(u"Frm_CurSelOrDragImg")
        self.Frm_CurSelOrDragImg.setGeometry(QRect(10, 40, 171, 151))
        self.Frm_CurSelOrDragImg.setFrameShape(QFrame.StyledPanel)
        self.Frm_CurSelOrDragImg.setFrameShadow(QFrame.Raised)
        
        self.Frm_CurSelOrDragImg_Inner = QFrame(self.Frm_CurSelOrDragImg)
        self.Frm_CurSelOrDragImg_Inner.setObjectName(u"Frm_CurSelOrDragImg_Inner")
        self.Frm_CurSelOrDragImg_Inner.setGeometry(QRect(10, 10, 151, 131))

        self.ImgLbl_CurSelOrDrag = DragImage(self, self.Frm_CurSelOrDragImg_Inner)
        self.ImgLbl_CurSelOrDrag.setObjectName(u"ImgLbl_CurSelOrDrag")
        self.ImgLbl_CurSelOrDrag.setGeometry(QRect(0, 0, 141, 131))

        font = QFont()
        font.setPointSize(23)
        font.setUnderline(True)

        self.ImgLbl_CurSelOrDrag.setFont(font)
        self.ImgLbl_CurSelOrDrag.setAlignment(Qt.AlignCenter)
        self.ImgLbl_CurSelOrDrag.setScaledContents(True)

        ## Create Next Panel
        self.Frm_CreateNextPanel = QFrame(self.MainFrame)
        self.Frm_CreateNextPanel.setObjectName(u"Frm_CreateNextPanel")
        self.Frm_CreateNextPanel.setGeometry(QRect(460, 0, 661, 721))
        self.Frm_CreateNextPanel.setFrameShape(QFrame.StyledPanel)
        self.Frm_CreateNextPanel.setFrameShadow(QFrame.Raised)
        self.Lab_CreateNextPanel = QLabel(self.Frm_CreateNextPanel)
        self.Lab_CreateNextPanel.setObjectName(u"Lab_CreateNextPanel")
        self.Lab_CreateNextPanel.setGeometry(QRect(20, 10, 71, 16))
        ## The New Panel
        TTileX = good_int(int(self.Txt_TilePixelSizeX.text()) * self.PanelScaleFactor)
        TTileY = good_int(int(self.Txt_TilePixelSizeY.text()) * self.PanelScaleFactor)
        self.Frm_TheNewPanel = QFrame(self.Frm_CreateNextPanel)
        self.Frm_TheNewPanel.setObjectName(u"Frm_TheNewPanel")
        self.Frm_TheNewPanel.setGeometry(QRect(40, 50, TTileX * 2, TTileY * 2))
        self.Frm_TheNewPanel.setFixedSize(TTileX * 2, TTileY * 2)
        self.Frm_TheNewPanel.setFrameShape(QFrame.StyledPanel)
        self.Frm_TheNewPanel.setFrameShadow(QFrame.Raised)
        self.Frm_TheNewPanel.setStyleSheet(f"background-color : grey;")

        ## The New Panel Grid
        self.Grid_LayoutWidget = QWidget(self.Frm_TheNewPanel)
        self.Grid_LayoutWidget.setObjectName(u"Grid_LayoutWidget")        
        self.Grid_LayoutWidget.setGeometry(QRect(0, 0, TTileX * 2, TTileY * 2))
        self.Grid_Images = QGridLayout(self.Grid_LayoutWidget)
        self.Grid_Images.setSpacing(0)
        self.Grid_Images.setObjectName(u"Grid_Images")
        self.Grid_Images.setContentsMargins(0, 0, 0, 0)

        ## Images of new Panel        
        font = QFont()
        font.setPointSize(23)
        font.setUnderline(True)

        ImgSizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.GridImageList = {}

        self.ImgLbl_CurSel1 = DragGraphicsView(self, QGraphicsView(self.Grid_LayoutWidget), (TTileX, TTileY))
        self.ImgLbl_CurSel2 = DragGraphicsView(self, QGraphicsView(self.Grid_LayoutWidget), (TTileX, TTileY))
        self.ImgLbl_CurSel3 = DragGraphicsView(self, QGraphicsView(self.Grid_LayoutWidget), (TTileX, TTileY))
        self.ImgLbl_CurSel4 = DragGraphicsView(self, QGraphicsView(self.Grid_LayoutWidget), (TTileX, TTileY))

        self.GridImageList[0] = (self.ImgLbl_CurSel1)
        self.GridImageList[1] = (self.ImgLbl_CurSel2)
        self.GridImageList[2] = (self.ImgLbl_CurSel3)
        self.GridImageList[3] = (self.ImgLbl_CurSel4)


        for i, j in enumerate(self.GridImageList.values()): 
            j.setObjectName(f"ImgLbl_CurSel{i+1}")
            j.setSizePolicy(ImgSizePolicy)
            j.setFrameShape(QFrame.StyledPanel)
            self.ToggleWidgetColor(j, QColor(0, 0, 0))
            j.setLineWidth(6)
            j.setAcceptDrops(True)
            k = int(i % 2 != 0)
            l = int(i > 1) 
            if 1 == 0:
                if i == 0:                    
                    j.setAlignment((Qt.AlignBottom|Qt.AlignRight|Qt.AlignTrailing))  
                elif i == 1:
                    j.setAlignment((Qt.AlignBottom|Qt.AlignLeft|Qt.AlignTrailing))
                elif i == 2:
                    j.setAlignment((Qt.AlignTop|Qt.AlignRight))
                elif i == 3:
                    j.setAlignment((Qt.AlignTop|Qt.AlignLeft))
            j.Index = (l, k)
            
            self.Grid_Images.addWidget(j, l, k)

        #self.Frm_TheNewPanel.raise_()
        #self.Lab_CreateNextPanel.raise_()

            
        ## Target Folder Select
        self.Frm_SelTargetFolder = QFrame(self.centralwidget)
        self.Frm_SelTargetFolder.setObjectName(u"Frm_SelTargetFolder")
        self.Frm_SelTargetFolder.setGeometry(QRect(300, 10, 271, 51))
        self.Frm_SelTargetFolder.setFrameShape(QFrame.StyledPanel)
        self.Frm_SelTargetFolder.setFrameShadow(QFrame.Raised)
        self.Lab_SelTargetFolder = QLabel(self.Frm_SelTargetFolder)
        self.Lab_SelTargetFolder.setObjectName(u"Lab_SelTargetFolder")
        self.Lab_SelTargetFolder.setGeometry(QRect(10, 0, 121, 16))
        self.Btn_SelTargetFolder = QPushButton(self.Frm_SelTargetFolder)
        self.Btn_SelTargetFolder.setObjectName(u"Btn_SelTargetFolder")
        self.Btn_SelTargetFolder.setGeometry(QRect(190, 20, 75, 23))
        self.Txt_SelTargetFolder = QLineEdit(self.Frm_SelTargetFolder)
        self.Txt_SelTargetFolder.setObjectName(u"Txt_SelTargetFolder")
        self.Txt_SelTargetFolder.setGeometry(QRect(10, 20, 171, 20))
        self.Txt_SelTargetFolder.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        ## Finish Frame
        self.Frm_Finish = QFrame(self.centralwidget)
        self.Frm_Finish.setObjectName(u"Frm_Finish")
        self.Frm_Finish.setGeometry(QRect(600, 5, 540, 71))
        self.Frm_Finish.setFrameShape(QFrame.StyledPanel)
        self.Frm_Finish.setFrameShadow(QFrame.Raised)
        self.Lab_FinSave = QLabel(self.Frm_Finish)
        self.Lab_FinSave.setObjectName(u"Lab_FinSave")
        self.Lab_FinSave.setGeometry(QRect(290, 0, 101, 16))
        self.Btn_Save = QPushButton(self.Frm_Finish)
        self.Btn_Save.setObjectName(u"Btn_Save")
        self.Btn_Save.setGeometry(QRect(300, 20, 75, 23))
        self.Btn_SaveIndividualy = QPushButton(self.Frm_Finish)
        self.Btn_SaveIndividualy.setObjectName(u"Btn_SaveIndividualy")
        self.Btn_SaveIndividualy.setGeometry(QRect(385, 20, 150, 23))

        self.Txt_SaveName = QLineEdit(self.Frm_Finish)
        self.Txt_SaveName.setObjectName(u"Txt_SaveName")
        self.Txt_SaveName.setGeometry(QRect(10, 20, 151, 20))
        self.Txt_SaveName.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.Lab_FinSaveNameText = QLabel(self.Frm_Finish)
        self.Lab_FinSaveNameText.setObjectName(u"Lab_FinSaveNameText")
        self.Lab_FinSaveNameText.setGeometry(QRect(10, 0, 101, 16))
        self.Cmb_FinFileFormat = QComboBox(self.Frm_Finish)
        self.Cmb_FinFileFormat.setObjectName(u"Cmb_FinFileFormat")
        self.Cmb_FinFileFormat.setGeometry(QRect(170, 20, 69, 22))
        self.Lab_FinFormat = QLabel(self.Frm_Finish)
        self.Lab_FinFormat.setObjectName(u"Lab_FinFormat")
        self.Lab_FinFormat.setGeometry(QRect(170, 0, 101, 16))
        self.Checkb_FinAutoIncrease = QCheckBox(self.Frm_Finish)
        self.Checkb_FinAutoIncrease.setObjectName(u"Checkb_FinAutoIncrease")
        self.Checkb_FinAutoIncrease.setEnabled(True)
        self.Checkb_FinAutoIncrease.setGeometry(QRect(20, 50, 251, 17))
        self.Checkb_FinAutoIncrease.setChecked(True)

        ## Image Tiler Object
        ImageTilerObj.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(ImageTilerObj)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1174, 22))
        self.menuCustom_Made_Tool_For_Ernest_Programming_is_fun = QMenu(self.menubar)
        self.menuCustom_Made_Tool_For_Ernest_Programming_is_fun.setObjectName(u"menuCustom_Made_Tool_For_Ernest_Programming_is_fun")
        ImageTilerObj.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(ImageTilerObj)
        self.statusbar.setObjectName(u"statusbar")
        ImageTilerObj.setStatusBar(self.statusbar)

        ## Set Tab order
        QWidget.setTabOrder(self.Txt_SelSourceFolder, self.Btn_SelSourceFolder)
        QWidget.setTabOrder(self.Btn_SelSourceFolder, self.Txt_SelTargetFolder)
        QWidget.setTabOrder(self.Txt_SelTargetFolder, self.Btn_SelTargetFolder)
        QWidget.setTabOrder(self.Btn_SelTargetFolder, self.Txt_SaveName)
        QWidget.setTabOrder(self.Txt_SaveName, self.Lis_SourceFiles)
        QWidget.setTabOrder(self.Lis_SourceFiles, self.Txt_TilePixelSizeX)
        QWidget.setTabOrder(self.Txt_TilePixelSizeX, self.Txt_TilePixelSizeY)
        QWidget.setTabOrder(self.Txt_TilePixelSizeY, self.Txt_TotalPixelSizeX)
        QWidget.setTabOrder(self.Txt_TotalPixelSizeX, self.Txt_TotalPixelSizeY)
        QWidget.setTabOrder(self.Txt_TotalPixelSizeY, self.Checkb_LinkXY)
        QWidget.setTabOrder(self.Checkb_LinkXY, self.ImgLbl_CurSelOrDrag)
        QWidget.setTabOrder(self.ImgLbl_CurSelOrDrag, self.Btn_Save)

        self.menubar.addAction(self.menuCustom_Made_Tool_For_Ernest_Programming_is_fun.menuAction())
        self.menuCustom_Made_Tool_For_Ernest_Programming_is_fun.addSeparator()

        self.retranslateUi(ImageTilerObj)
        self.Lis_SourceFiles.itemSelectionChanged.connect(self.ImgLbl_CurSelOrDrag.update)

        QMetaObject.connectSlotsByName(ImageTilerObj)
        
        ## Init Sliders
        self.InitSliders()
        ## Init Combobox
        self.FillImgFormatFileCombobox()

        ## Init Pixel Size        
        self.ApplyPixelSize()
    # setupUi

    def InitSliders(self):
        #Total Scale Slider
        self.userIsInputting = True
        self.UserChangedCurPanelPreviewZoom()

    def retranslateUi(self, ImageTilerObj):
        ImageTilerObj.setWindowTitle(QCoreApplication.translate("ImageTilerObj", u"Image Tiler", None))
        self.Lab_SourceFiles.setText(QCoreApplication.translate("ImageTilerObj", u"Source Files", None))
        self.Lab_SourceFilesDnDInfo.setText(QCoreApplication.translate("ImageTilerObj", u"Drag and Drop into Panel", None))
        self.Lab_CurSelOrDrag.setText(QCoreApplication.translate("ImageTilerObj", u"Preview currently selected", None))
        self.Lab_CreateNextPanel.setText(QCoreApplication.translate("ImageTilerObj", u"Next Panel", None))
        #self.Txt_TilePixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"480", None))
        self.Lab_TilePixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"Tile Pixel Size X", None))
        #self.Txt_TilePixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"640", None))
        self.Lab_TilePixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"Tile Pixel Size Y", None))
        self.Checkb_LinkXY.setText(QCoreApplication.translate("ImageTilerObj", u"Link X-Y", None))
        self.Txt_TotalPixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"960", None))
        self.Txt_TotalPixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"1280", None))
        self.Lab_TotalPixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"Total Pixel Size X", None))
        self.Lab_TotalPixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"Total Pixel Size Y", None))
        self.Lab_SelSourceFolder.setText(QCoreApplication.translate("ImageTilerObj", u"1. Select Source Folder", None))
        self.Btn_SelSourceFolder.setText(QCoreApplication.translate("ImageTilerObj", u"Select", None))
        self.Lab_SelTargetFolder.setText(QCoreApplication.translate("ImageTilerObj", u"2. Select Target Folder", None))
        self.Btn_SelTargetFolder.setText(QCoreApplication.translate("ImageTilerObj", u"Select", None))
        self.Lab_FinSave.setText(QCoreApplication.translate("ImageTilerObj", u"Finnish: Save Panel", None))
        self.Btn_Save.setText(QCoreApplication.translate("ImageTilerObj", u"Save Panel", None))
        self.Btn_SaveIndividualy.setText(QCoreApplication.translate("ImageTilerObj", u"Save Tiles individualy", None))
        self.Lab_FinSaveNameText.setText(QCoreApplication.translate("ImageTilerObj", u"Finish: SaveName", None))
        self.Lab_FinFormat.setText(QCoreApplication.translate("ImageTilerObj", u"Finish: Fileformat", None))
        self.Checkb_FinAutoIncrease.setText(QCoreApplication.translate("ImageTilerObj", u"Auto increase - Prevent File overwrite", None))
        
        
        self.Lab_CurPanelPreviewZoom.setText(QCoreApplication.translate("ImageTilerObj", u"Preview Zoom", None))
        self.menuCustom_Made_Tool_For_Ernest_Programming_is_fun.setTitle(QCoreApplication.translate("ImageTilerObj", u"Custom Made Tool For Ernest. Programming is fun!!", None))
        self.set_all_textfields_and_text_colors()
        self.SetAllFramesBordersSizes(maxlinewidth = 3,maxdepth = 3)
    # retranslateUi

    def ToggleWidgetColor(self, TWidget, alternativecolor = None):
        palette = TWidget.palette()
        currentcolor = palette.color(TWidget.backgroundRole())
        if type(TWidget) == DragGraphicsView:
            if alternativecolor != None:
                palette.setColor(TWidget.backgroundRole(), alternativecolor)
                TWidget.setStyleSheet("border: 1px solid #ff0000;")
            else:
                raise Exception("No alternative color given")
        elif type(TWidget) == QLineEdit:
            if alternativecolor != None:
                try:
                    TWidget.setStyleSheet(f"background-color : {alternativecolor};")
                except:
                    pass
            elif currentcolor == "white":
                TWidget.setStyleSheet(f"background-color : red;")
            else:
                TWidget.setStyleSheet(f"background-color : white;")
        #TWidget.setPalette(palette)

    def ApplyPixelSize(self):
        ###This should get good pixel sizes from text fields
        self.PanelScaleFactor = good_float(self.Txt_CurPanelPreviewZoom.text())
        TileImgSizeX = good_int(int(self.Txt_TilePixelSizeX.text()) * self.PanelScaleFactor)
        TileImgSizeY = good_int(int(self.Txt_TilePixelSizeY.text()) * self.PanelScaleFactor)

        TFrameWidgetSize = self.get_WidgetSize(self.Frm_TheNewPanel)
        self.ApplyGridPositioning(TFrameWidgetSize, TileImgSizeX, TileImgSizeY)
        self.Apply_Image_Zooms(TFrameWidgetSize)

    def ApplyGridPositioning(self, TFrameWidgetSize, TileImgSizeX = None, TileImgSizeY = None):        
        GridWidgetStartX = good_int((TFrameWidgetSize.width()/2 - TileImgSizeX))
        GridWidgetStartY = good_int((TFrameWidgetSize.height()/2 - TileImgSizeY))
        #print(f"Start: {GridWidgetStartX}, {GridWidgetStartY}, size: {TileImgSizeX} , {TileImgSizeY} , scalefactor{self.PanelScaleFactor}")
        self.Grid_LayoutWidget.setBaseSize(TileImgSizeX * 2, TileImgSizeY * 2)
        #self.Grid_LayoutWidget.setGeometry(QRect(GridWidgetStartX, GridWidgetStartY, TileImgSizeX * 2, TileImgSizeY * 2))
        self.Grid_LayoutWidget.setMinimumSize(TileImgSizeX * 2, TileImgSizeY * 2)
        
        
    def Apply_Image_Zooms(self, TFrameWidgetSize, PImgSizeX = None, PImgSizeY = None):
        self.PanelScaleFactor = good_float(self.Txt_CurPanelPreviewZoom.text())
        if PImgSizeX == None:
            PImgSizeX = good_int(int(self.Txt_TilePixelSizeX.text()) * self.PanelScaleFactor)
        if PImgSizeY == None:
            PImgSizeY = good_int(int(self.Txt_TilePixelSizeY.text()) * self.PanelScaleFactor)

        for i in self.GridImageList.values():
            #pass
            #i[1].setGeometry(QRect(0, 0, PImgSizeX, PImgSizeY))
            #i[1].setMinimumSize(QSize(PImgSizeX, PImgSizeY))
            #i[1].setMaximumSize(QSize(PImgSizeX, PImgSizeY))
            i.FrmCenter = (good_int(TFrameWidgetSize.width()/2), good_int(TFrameWidgetSize.height()/2))
            i.FrameSizeX = PImgSizeX
            i.FrameSizeY = PImgSizeY
            i.currentPanelZoomFactor = self.PanelScaleFactor
            i.ApplyZoomFactors()
        
    def FillImgFormatFileCombobox(self):
        self.ImgFormatList = []
        self.ImgFormatList.append(".webp")
        self.ImgFormatList.append(".jpg")
        self.ImgFormatList.append(".png")
        self.ImgFormatList.append(".bmp")
        self.ImgFormatList.append(".tif")
        self.ImgFormatList.append(".tiff")
        self.ImgFormatList.append(".gif")
        self.ImgFormatList.append(".jpeg")
        self.Cmb_FinFileFormat.addItems(self.ImgFormatList)

    def get_WidgetSize(self, widget):
        return widget.size()
    
    def addFreeImage(self):
        SourceImg = self.SourceFolderFiles.GetRealItem(self.Lis_SourceFiles.currentIndex().row()).fullname
        for i in self.GridImageList.values():
            if i.TruePixPath == "":
                i.AddImage(SourceImg)
                return
        #self.AddImage(SourceImg.fullname)

    def set_all_textfields_and_text_colors(self):
        for i in dir(self):
            if type(getattr(self, i)) == QLineEdit:
                palette = getattr(self, i).palette()
                basecolor = palette.window()
                #inverting base color
                textcolor = self.get_foreground(basecolor)
                palette.setColor(QPalette.ColorRole.Text, textcolor)
                getattr(self, i).setPalette(palette)


    def get_channel_value(self, channel):
        """Helper to calculate luminance."""
        channel = channel / 255.0
        if channel <= 0.03928:
            channel = channel / 12.92
        else:
            channel = ((channel + 0.055) / 1.055) ** 2.4
        return channel

    def calculate_color_luminance(self, rgb_tuple):
        """Get color luminance.

        Used formula from w3c guide:
        https://www.w3.org/TR/WCAG20/#relativeluminancedef

        L = 0.2126 * R + 0.7152 * G + 0.0722 * B where R, G and B are defined as:

        if RsRGB <= 0.03928 then R = RsRGB/12.92 else R = ((RsRGB+0.055)/1.055) ^ 2.4
        if GsRGB <= 0.03928 then G = GsRGB/12.92 else G = ((GsRGB+0.055)/1.055) ^ 2.4
        if BsRGB <= 0.03928 then B = BsRGB/12.92 else B = ((BsRGB+0.055)/1.055) ^ 2.4
        """
        r, g, b = rgb_tuple
        r = self.get_channel_value(r)
        g = self.get_channel_value(g)
        b = self.get_channel_value(b)
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return luminance


    def get_foreground(self, background_color, output='hex'):
        """Get foreground font color based on w3c recommendations."""
        rgb_white = QColor(255, 255, 255)
        rgb_black = QColor(0, 0, 0)

        luminance = self.calculate_color_luminance((background_color.color().red(), background_color.color().green(), background_color.color().blue()))
        if (luminance + 0.05) / (0.0 + 0.05) > (1.0 + 0.05) / (luminance + 0.05):
            return rgb_white
        else:
            return rgb_black
        
    def SetAllFramesBordersSizes(self, obj = None, maxlinewidth = 5, maxdepth = 0, depth = 0):
        #recursively sets frame borders for all frames directly contained in other frames of main window
        if obj is None: 
            obj = self.children()[1]
        for i in obj.children():
            if type(i) == QFrame and not i.objectName().startswith("Lin_"):
                newdepth = depth + 1
                i.setFrameShape(QFrame.Shape.Box)
                i.setFrameShadow(QFrame.Shadow.Raised)
                truelinewidth = good_int(maxlinewidth * (1-depth/maxdepth))
                i.setLineWidth(truelinewidth)
                if depth < maxdepth:
                    self.SetAllFramesBordersSizes(i, maxlinewidth, maxdepth, newdepth)