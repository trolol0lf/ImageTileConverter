if __name__ == "__main__":
    import ImageTileConverter, sys
    sys.exit()

from PySide6.QtCore import (QCoreApplication, QMetaObject, QPoint, QPointF, QRect, Qt, QMimeData, Signal, QEvent, QSize, QLocale, QTimer)
from PySide6.QtGui import (QColor, QFont, QImage, QPainter, QPixmap, QTransform, QDrag, QDropEvent, QDragLeaveEvent, QMouseEvent, QCursor, QPalette, QIntValidator)
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
    QFrame, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel, QLineEdit,
    QListWidget, QMenu,
    QMenuBar, QPushButton, QSizePolicy, QStatusBar,
    QWidget, QGridLayout, QWidget, QSlider, QColorDialog)
import os, time

from Handler_Formats import *

def get_delta(a,b):
    return QPoint(a.x() - b.x(), a.y() - b.y())
def get_length(a):
    return (float(a.x()) ** 2 + float(a.y()) ** 2) ** 0.5
def qpointorF(qpointOrF):
    if type(qpointOrF) == QPointF:
        return QPoint(good_int(qpointOrF.x()), good_int(qpointOrF.y()))
    if type(qpointOrF) == QPoint:
        return QPointF(qpointOrF.x(), qpointOrF.y())

def ascolor(color):
    if not isinstance(color, QColor):
        return QColor(*color)
    return color
def asset(color):
    if isinstance(color, QColor):
        return (color.red(), color.green(), color.blue(), color.alpha())
    return color
class ColorPickImageView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        ##Custom Class Vars 
        self.color = (0,0,0,0)
        self.img = None
        self.pixmapItem = None
        ##Init
        super().__init__(*args, **kwargs)
        self.theScene = GraphicsScene()
        self.setScene(self.theScene)
        self.setcolor(self.color)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)      
    
    def setcolor(self, color):
        sze = self.viewport().size()

        if self.img is None or self.img.size() != sze:
            self.img = QImage(
                sze.width(),
                sze.height(),
                QImage.Format.Format_ARGB32
            )

        self.color = ascolor(color)
        self.img.fill(self.color)

        if self.pixmapItem is not None:
            self.theScene.removeItem(self.pixmapItem)

        pixmap = QPixmap.fromImage(self.img)
        self.pixmapItem = self.theScene.addPixmap(pixmap)

        self.theScene.setSceneRect(self.pixmapItem.boundingRect())

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            color = QColorDialog.getColor()
            if color:
                self.setcolor(color)

class DragFrame(QFrame):
    uiimagetiler = None
    rclicked = False
    def mousePressEvent(self, e):
        if self.uiimagetiler and e.button() == Qt.MouseButton.RightButton:
            self.rclicked = True
            self.uiimagetiler.GridImageList[0][0].mousePressEvent(e)
        #super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self.uiimagetiler and self.rclicked:
            self.uiimagetiler.GridImageList[0][0].mouseMoveEvent(e)
        #super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self.uiimagetiler and e.button() == Qt.MouseButton.RightButton:
            self.rclicked = False
            #self.uiimagetiler.GridImageList[0][0].mouseReleaseEvent(e)
        #super().mouseReleaseEvent(e) 
        
    def wheelEvent(self, e):
        if self.uiimagetiler and self.rclicked:
            self.uiimagetiler.GridImageList[0][0].wheelEvent(e)

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
        self.LeftMouseDragStart = None
        self.RightMouseDragStartTime = time.time()
        self.RightMouseDragStart = None
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
        self.FrmCenterOffset = (0,0)
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
        #self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
    rclickpressed = False
    def mousePressEvent(self, e):
        if e.buttons() == Qt.MouseButton.RightButton:
            self.rclickpressed = True
            self.gridogoffset = qpointorF(self.RootParent.Grid_LayoutWidget.geometry().topLeft())
            self.RootParent.rclickpressed = True
            self.RightMouseDragStartTime = time.time()
            self.RightMouseDragStart = QCursor.pos()#self.mapToGlobal(e.position())
            self.RootParent.RightMouseDragStart = self.RightMouseDragStart
            e.accept()
        elif e.buttons() == Qt.MouseButton.LeftButton:
            if self.LeftMouseDragStart == None and not self.ViewPixMap == None:
                self.LeftMouseDragStart = QCursor.pos()#self.mapToGlobal(e.position())
                self.DragItem = DragItem(self, self.RootParent, e)
                self.DragItem.runtime()
        elif e.buttons() == Qt.MouseButton.MiddleButton:
            if self.rclickpressed:
                pass
        else:
            pass
    
    def mouseReleaseEvent(self, e):
        if e.type() == QEvent.MouseButtonRelease:
            if self.LeftMouseDragStart:
                delta = get_delta(self.LeftMouseDragStart, QCursor.pos())#e.position())
                self.move_img_delta(delta.x(), delta.y())
                self.LeftMouseDragStart = None
            elif self.rclickpressed:                
                if time.time() - self.RightMouseDragStartTime < 0.2 and get_length(get_delta(self.RightMouseDragStart, QCursor.pos())) < 2:
                    self.removeImage()
                else:
                    self.RootParent.SetOGGridGeo()                                        
                self.rclickpressed = False
                self.RootParent.rclickpressed = False
                self.RightMouseDragStart = None
                self.RootParent.RightMouseDragStart = None
                self.gridogoffset = None

    def mouseMoveEvent(self, e):
        #print("b:", self.RightMouseDragStart)
        if e.buttons() == Qt.MouseButton.LeftButton:   
            pass        
        elif not self.LeftMouseDragStart == None:
            self.dropEvent(e)
            #self.LeftMouseDragStart = None   
        elif e.buttons() == Qt.MouseButton.RightButton and self.RightMouseDragStart:
            delta = get_delta(QCursor.pos(), self.RootParent.RightMouseDragStart)
            #print(delta)
            self.RootParent.MouseMovesGrid(delta)
        else:
            pass
        if e.source() != Qt.MouseEventSource.MouseEventNotSynthesized:
            e.source().LeftMouseDragStart = None

    def wheelEvent(self, e):
        if self.rclickpressed:
            new = float(self.RootParent.Txt_CurPanelPreviewZoom.text()) + (e.angleDelta().y() / 1500)
            self.RootParent.Txt_CurPanelPreviewZoom.setText(str(round(new,3)))
        else:
            self.currentInternalZoomFactor = clamp_float(self.currentInternalZoomFactor * (1 + (e.angleDelta().y() / 1200)), 0.1, 10)
            self.ApplyZoomFactors(True)
        e.accept()
        
    def dragEnterEvent(self, e):    #Event if something is dragged Into the widget
        e.accept()
        e.acceptProposedAction()

    def dragMoveEvent(self, e):
        self.xyPos = QCursor.pos()
        e.accept()
        e.acceptProposedAction()
    
    def dragLeaveEvent(self, e):
        #print("dragleave:", e)
        e.accept()

    def dropEvent(self, e, alternativePos = None):
        #print("drop:", e)
        if self.objectName() == "ImgLbl_CurSelOrDrag":      #ImgLbl_CurSelOrDrag gets updated via list!
            try:
                e.source().LeftMouseDragStart = None
            except:
                pass
            self.LeftMouseDragStart = None
            return
        if alternativePos == None:
            if type(e) == QDropEvent:
                DropPos = QCursor.pos() - self.mapToGlobal(QPoint(0,0))
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
                    widget.SourceWidget.LeftMouseDragStart = None
                    self.LeftMouseDragStart = None
                    self.AddImage(self.RootParent.SourceFolderFiles.GetRealItem(self.RootParent.Lis_SourceFiles.currentIndex().row()).fullname, DropPos.x(), DropPos.y(), e)
                elif type(widget.SourceWidget) == DragImage:
                    self.AddImage(widget.SourceWidget.TruePixPath, DropPos.x(), DropPos.y(), e)
                elif type(widget.SourceWidget) == DragGraphicsView:
                    if alternativePos == None:
                        DropPos = QCursor.pos()
                    else:
                        DropPos = alternativePos
                    if widget.SourceWidget == self:
                        dx = DropPos.x() - self.LeftMouseDragStart.x()
                        dy = DropPos.y() - self.LeftMouseDragStart.y()
                        self.move_img_delta(dx, dy)
                    else:
                        widget.SourceWidget.dropEvent(e, DropPos)
            self.LeftMouseDragStart = None
            if not self.DragItem == None: self.DragItem.RunDrop = False
        elif type(e) == QMouseEvent:
            dx = DropPos.x() - self.LeftMouseDragStart.x()
            dy = DropPos.y() - self.LeftMouseDragStart.y()
            self.move_img_delta(dx, dy)
            self.LeftMouseDragStart = None

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
        self.currentTotalZoomFactor = self.currentInternalZoomFactor * good_float(self.RootParent.Txt_CurPanelPreviewZoom.text())
        self.deltaX += deltaX / self.currentTotalZoomFactor
        self.deltaY += deltaY / self.currentTotalZoomFactor      
        self.ApplyZoomFactors()

    curtransform = None
    
    def ApplyZoomFactors(self, MWheelInduced = False, e = None):        
        if len(self.theScene.items()) > 0:  #Clean old items from Scene
            self.theScene.removeItem(self.theScene.items()[0])
        panelzoom = good_float(self.RootParent.Txt_CurPanelPreviewZoom.text())
        self.currentTotalZoomFactor = self.currentInternalZoomFactor * panelzoom
        if self.TruePixMap is not None:            
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
            self.curtransform = QTransform()
            self.curtransform.scale(self.currentTotalZoomFactor, self.currentTotalZoomFactor)
            self.curtransform.translate(self.deltaX, self.deltaY)
            self.ViewPixMap = QGraphicsPixmapItem(self.TruePixMap.copy())
            self.ViewPixMap.setTransform(self.curtransform)             
            self.theScene.addItem(self.ViewPixMap)
        
        
        sze = QPoint(good_int(self.RootParent.Txt_TilePixelSizeX.text()), good_int(self.RootParent.Txt_TilePixelSizeY.text()))
        #print("applyzoomfactors:", sze, floor_int(self.RootParent.Txt_PanelDistance_X.text()), self.currentTotalZoomFactor)        
        self.setSceneRect(QRect(QPoint(0, 0), sze))        
        self.theScene.setSceneRect(QRect(QPoint(0, 0), sze))
        
        
    def get_img_correct_size(self):

        trueSize = (
            good_int(self.RootParent.Txt_TilePixelSizeX.text()),
            good_int(self.RootParent.Txt_TilePixelSizeY.text())
        )

        CorrectImg = QImage(trueSize[0], trueSize[1], QImage.Format.Format_ARGB32)
        CorrectImg.fill(ascolor(self.RootParent.GV_Backgroundcolor.color))
        painter = QPainter(CorrectImg)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if self.TruePixMap is not None:
            transform = QTransform()
            transform.scale(self.currentInternalZoomFactor, self.currentInternalZoomFactor)
            transform.translate(self.deltaX, self.deltaY)
            theViewMap = self.TruePixMap
            painter.setTransform(transform)
        else:
            theViewMap = QPixmap()
        painter.drawPixmap(0, 0, theViewMap)
        painter.end()

        return CorrectImg
        
class DragImage(QLabel):

    orderChanged = Signal(list)

    def __init__(self, RootParent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.RootParent = RootParent
        self.LeftMouseDragStart = None
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
            if self.LeftMouseDragStart == None:
                self.LeftMouseDragStart = e.position()
            self.DragItem = DragItem(self, self.RootParent, e)
            e.accept()
            self.DragItem.runtime()
        elif not self.LeftMouseDragStart == None:
            self.LeftMouseDragStart = None
        if e.buttons() == Qt.MouseButton.MiddleButton:
            pass
        if e.source() != Qt.MouseEventSource.MouseEventNotSynthesized:
            e.source().LeftMouseDragStart = None
        e.accept()
    def wheelEvent(self, e):
        self.currentInternalZoomFactor = clamp_float(self.currentInternalZoomFactor * (1 + (e.angleDelta().y() / 1200)), 0.1, 10)
        self.ApplyZoomFactors()
        
    def dragEnterEvent(self, e):    #Event if something is dragged Into the widget
        e.accept()

    def dropEvent(self, e):
        if self.objectName() == "ImgLbl_CurSelOrDrag":      #ImgLbl_CurSelOrDrag gets updated via list!
            try:
                e.source().LeftMouseDragStart = None
            except:
                pass
            self.LeftMouseDragStart = None
            return
        pos = e.position()
        widget = e.source()
        if type(widget) == DragList:            
            widget.LeftMouseDragStart = None
            self.LeftMouseDragStart = None
            self.AddImage(self.RootParent.SourceFolderFiles.GetRealItem(self.RootParent.Lis_SourceFiles.currentIndex().row()).fullname)
        elif type(widget) == DragGraphicsView or type(widget) == DragImage:            
            if widget == self:
                dx = pos.x() - self.LeftMouseDragStart.x()
                dy = pos.y() - self.LeftMouseDragStart.y()
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
        transform = QTransform().scale(self.currentTotalZoomFactor, self.currentTotalZoomFactor).translate(self.deltaX, self.deltaY)
        self.ViewPixMap = self.TruePixMap.transformed(transform)
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
        ImageTilerObj.resize(1174, 896)
        self.centralwidget = QWidget(ImageTilerObj)
        self.centralwidget.setObjectName(u"centralwidget")
        intvalidator = QIntValidator() 
        ## Main Frame
        self.MainFrame = QFrame(self.centralwidget)
        self.MainFrame.setObjectName(u"MainFrame")
        self.MainFrame.setGeometry(QRect(20, 80, 1091, 771))
        self.MainFrame.setFrameShape(QFrame.StyledPanel)
        self.MainFrame.setFrameShadow(QFrame.Raised)

        ## Source Folder Select
        self.Frm_SelSourceFolder = QFrame(self.centralwidget)
        self.Frm_SelSourceFolder.setObjectName(u"Frm_SelSourceFolder")
        self.Frm_SelSourceFolder.setGeometry(QRect(20, 0, 281, 61))
        self.Frm_SelSourceFolder.setFrameShape(QFrame.StyledPanel)
        self.Frm_SelSourceFolder.setFrameShadow(QFrame.Raised)
        self.Txt_SelSourceFolder = QLineEdit(self.Frm_SelSourceFolder)
        self.Txt_SelSourceFolder.setObjectName(u"Txt_SelSourceFolder")
        self.Txt_SelSourceFolder.setGeometry(QRect(20, 30, 171, 20))
        self.Txt_SelSourceFolder.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Lab_SelSourceFolder = QLabel(self.Frm_SelSourceFolder)
        self.Lab_SelSourceFolder.setObjectName(u"Lab_SelSourceFolder")
        self.Lab_SelSourceFolder.setGeometry(QRect(10, 10, 121, 16))
        self.Btn_SelSourceFolder = QPushButton(self.Frm_SelSourceFolder)
        self.Btn_SelSourceFolder.setObjectName(u"Btn_SelSourceFolder")
        self.Btn_SelSourceFolder.setGeometry(QRect(200, 30, 75, 23))

        ## Source Files Frame
        self.Frm_SourceFiles= QFrame(self.MainFrame)
        self.Frm_SourceFiles.setObjectName(u"Frm_SourceFile")
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
        self.Frm_PixelSizes.setGeometry(QRect(270, 220, 191, 461))
        self.Frm_PixelSizes.setFrameShape(QFrame.StyledPanel)
        self.Frm_PixelSizes.setFrameShadow(QFrame.Raised)
        self.Var_TilePixelSizeRatio = (3/4)
        self.Txt_TilePixelSizeX = QLineEdit(self.Frm_PixelSizes)
        self.Txt_TilePixelSizeX.setValidator(intvalidator)
        self.Txt_TilePixelSizeX.setObjectName(u"Txt_TilePixelSizeX")
        self.Txt_TilePixelSizeX.setGeometry(QRect(20, 160, 71, 20))
        self.Txt_TilePixelSizeX.setAutoFillBackground(False)
        self.Txt_TilePixelSizeX.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Txt_TilePixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"480", None))        
        self.Lab_TilePixelSizeX = QLabel(self.Frm_PixelSizes)
        self.Lab_TilePixelSizeX.setObjectName(u"Lab_TilePixelSizeX")
        self.Lab_TilePixelSizeX.setGeometry(QRect(30, 140, 91, 16))
        self.Txt_TilePixelSizeY = QLineEdit(self.Frm_PixelSizes)
        self.Txt_TilePixelSizeY.setValidator(intvalidator)
        self.Txt_TilePixelSizeY.setObjectName(u"Txt_TilePixelSizeY")
        self.Txt_TilePixelSizeY.setGeometry(QRect(20, 210, 71, 20))
        self.Txt_TilePixelSizeY.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Lab_TilePixelSizeY = QLabel(self.Frm_PixelSizes)
        self.Lab_TilePixelSizeY.setObjectName(u"Lab_TilePixelSizeY")
        self.Lab_TilePixelSizeY.setGeometry(QRect(30, 190, 91, 16))
        self.Txt_TilePixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"640", None))
        self.Checkb_LinkXY = QCheckBox(self.Frm_PixelSizes)
        self.Checkb_LinkXY.setObjectName(u"Checkb_LinkXY")
        self.Checkb_LinkXY.setEnabled(True)
        self.Checkb_LinkXY.setGeometry(QRect(110, 170, 70, 17))
        self.Checkb_LinkXY.setChecked(True)
        self.Txt_TotalPixelSizeX = QLineEdit(self.Frm_PixelSizes)
        self.Txt_TotalPixelSizeX.setValidator(intvalidator)
        self.Txt_TotalPixelSizeX.setObjectName(u"Txt_TotalPixelSizeX")
        self.Txt_TotalPixelSizeX.setGeometry(QRect(20, 260, 71, 20))
        self.Txt_TotalPixelSizeX.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Txt_TotalPixelSizeY = QLineEdit(self.Frm_PixelSizes)
        self.Txt_TotalPixelSizeY.setValidator(intvalidator)
        self.Txt_TotalPixelSizeY.setObjectName(u"Txt_TotalPixelSizeY")
        self.Txt_TotalPixelSizeY.setGeometry(QRect(20, 310, 71, 20))
        self.Txt_TotalPixelSizeY.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Lab_TotalPixelSizeX = QLabel(self.Frm_PixelSizes)
        self.Lab_TotalPixelSizeX.setObjectName(u"Lab_TotalPixelSizeX")
        self.Lab_TotalPixelSizeX.setGeometry(QRect(30, 240, 91, 16))
        self.Lab_TotalPixelSizeY = QLabel(self.Frm_PixelSizes)
        self.Lab_TotalPixelSizeY.setObjectName(u"Lab_TotalPixelSizeY")
        self.Lab_TotalPixelSizeY.setGeometry(QRect(30, 290, 91, 16))
        self.Lin_LinkXY = QFrame(self.Frm_PixelSizes)
        self.Lin_LinkXY.setObjectName(u"Lin_LinkXY")
        self.Lin_LinkXY.setGeometry(QRect(10, 160, 20, 71))
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
        
        #Panel Distance 
        self.Frm_PanelDistance = QFrame(self.Frm_PixelSizes)
        self.Frm_PanelDistance.setObjectName(u"Frm_PanelDistance")
        self.Frm_PanelDistance.setGeometry(QRect(0, 349, 191, 111))
        self.Frm_PanelDistance.setFrameShape(QFrame.StyledPanel)
        self.Frm_PanelDistance.setFrameShadow(QFrame.Raised)
        self.Lab_PanelDistance = QLabel(self.Frm_PanelDistance)
        self.Lab_PanelDistance.setObjectName(u"Lab_PanelDistance")
        self.Lab_PanelDistance.setGeometry(QRect(20, 10, 51, 16))
        self.Txt_PanelDistance_X = QLineEdit(self.Frm_PanelDistance)
        self.Txt_PanelDistance_X.setValidator(intvalidator)
        self.Txt_PanelDistance_X.setObjectName(u"Txt_PanelDistance_X")
        self.Txt_PanelDistance_X.setGeometry(QRect(20, 50, 61, 20))
        self.Txt_PanelDistance_X.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Sli_PanelDistance_X = QSlider(self.Frm_PanelDistance)
        self.Sli_PanelDistance_X.setMinimum(0)
        self.Sli_PanelDistance_X.setMaximum(100)
        self.Sli_PanelDistance_X.setObjectName(u"Sli_PanelDistance_X")
        self.Sli_PanelDistance_X.setGeometry(QRect(20, 70, 61, 20))
        self.Sli_PanelDistance_X.setOrientation(Qt.Horizontal)
        self.Txt_PanelDistance_Y = QLineEdit(self.Frm_PanelDistance)
        self.Txt_PanelDistance_Y.setValidator(intvalidator)
        self.Txt_PanelDistance_Y.setObjectName(u"Txt_PanelDistance_Y")
        self.Txt_PanelDistance_Y.setGeometry(QRect(100, 50, 61, 20))
        self.Txt_PanelDistance_Y.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Sli_PanelDistance_Y = QSlider(self.Frm_PanelDistance)
        self.Sli_PanelDistance_Y.setMinimum(0)
        self.Sli_PanelDistance_Y.setMaximum(100)
        self.Sli_PanelDistance_Y.setObjectName(u"Sli_PanelDistance_Y")
        self.Sli_PanelDistance_Y.setGeometry(QRect(100, 70, 61, 20))
        self.Sli_PanelDistance_Y.setOrientation(Qt.Horizontal)
        self.Lab_PanelDistance_X = QLabel(self.Frm_PanelDistance)
        self.Lab_PanelDistance_X.setObjectName(u"Lab_PanelDistance_X")
        self.Lab_PanelDistance_X.setGeometry(QRect(20, 30, 51, 16))
        self.Lab_PanelDistance_Y = QLabel(self.Frm_PanelDistance)
        self.Lab_PanelDistance_Y.setObjectName(u"Lab_PanelDistance_Y")
        self.Lab_PanelDistance_Y.setGeometry(QRect(100, 30, 51, 16))

        #TileCount
        self.Txt_Tiles_Y = QLineEdit(self.Frm_PixelSizes)
        self.Txt_Tiles_Y.setValidator(intvalidator)
        self.Txt_Tiles_Y.setText("2")
        self.Txt_Tiles_Y.setObjectName(u"Txt_Tiles_Y")
        self.Txt_Tiles_Y.setGeometry(QRect(100, 40, 71, 20))
        self.Txt_Tiles_Y.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Lab_Tiles_Y = QLabel(self.Frm_PixelSizes)
        self.Lab_Tiles_Y.setObjectName(u"Lab_Tiles_Y")
        self.Lab_Tiles_Y.setGeometry(QRect(100, 20, 51, 16))
        self.Txt_Tiles_X = QLineEdit(self.Frm_PixelSizes)
        self.Txt_Tiles_X.setValidator(intvalidator)
        self.Txt_Tiles_X.setText("2")
        self.Txt_Tiles_X.setObjectName(u"Txt_Tiles_X")
        self.Txt_Tiles_X.setGeometry(QRect(10, 40, 71, 20))
        self.Txt_Tiles_X.setAutoFillBackground(False)
        self.Txt_Tiles_X.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.Lab_Tiles_X = QLabel(self.Frm_PixelSizes)
        self.Lab_Tiles_X.setObjectName(u"Lab_Tiles_X")
        self.Lab_Tiles_X.setGeometry(QRect(20, 20, 61, 16))
        self.Sli_Tiles_X = QSlider(self.Frm_PixelSizes)
        self.Sli_Tiles_X.setObjectName(u"Sli_Tiles_X")
        self.Sli_Tiles_X.setGeometry(QRect(10, 60, 71, 20))
        self.Sli_Tiles_X.setMinimum(1)
        self.Sli_Tiles_X.setMaximum(20)
        self.Sli_Tiles_X.setValue(2)
        self.Sli_Tiles_X.setOrientation(Qt.Horizontal)
        self.Sli_Tiles_Y = QSlider(self.Frm_PixelSizes)
        self.Sli_Tiles_Y.setObjectName(u"Sli_Tiles_Y")
        self.Sli_Tiles_Y.setGeometry(QRect(100, 60, 71, 20))
        self.Sli_Tiles_Y.setMinimum(1)
        self.Sli_Tiles_Y.setMaximum(20)
        self.Sli_Tiles_Y.setValue(2)
        self.Sli_Tiles_Y.setOrientation(Qt.Horizontal)


        ## Current Selected Frame Preview
        self.Frm_CurSelOrDrag = QFrame(self.MainFrame)
        self.Frm_CurSelOrDrag.setObjectName(u"Frm_CurSelOrDrag")
        self.Frm_CurSelOrDrag.setGeometry(QRect(270, 20, 191, 201))
        self.Frm_CurSelOrDrag.setFrameShape(QFrame.StyledPanel)
        self.Frm_CurSelOrDrag.setFrameShadow(QFrame.Raised)
        self.Lab_CurSelOrDrag = QLabel(self.Frm_CurSelOrDrag)
        self.Lab_CurSelOrDrag.setObjectName(u"Lab_CurSelOrDrag")
        self.Lab_CurSelOrDrag.setGeometry(QRect(10, 0, 171, 31))
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
        self.Frm_CurSelOrDragImg_Inner.setFrameShape(QFrame.StyledPanel)
        self.Frm_CurSelOrDragImg_Inner.setFrameShadow(QFrame.Raised)
        self.ImgLbl_CurSelOrDrag = DragImage(self, self.Frm_CurSelOrDragImg_Inner)
        self.ImgLbl_CurSelOrDrag.setObjectName(u"ImgLbl_CurSelOrDrag")
        self.ImgLbl_CurSelOrDrag.setGeometry(QRect(0, 0, 141, 131))
        self.ImgLbl_CurSelOrDrag.setMaximumSize(QSize(1000, 1000))
        font = QFont()
        font.setPointSize(23)
        font.setUnderline(True)
        self.ImgLbl_CurSelOrDrag.setFont(font)
        self.ImgLbl_CurSelOrDrag.setCursor(QCursor(Qt.SizeAllCursor))
        self.ImgLbl_CurSelOrDrag.setMouseTracking(True)
        self.ImgLbl_CurSelOrDrag.setAutoFillBackground(True)
        self.ImgLbl_CurSelOrDrag.setLocale(QLocale(QLocale.English, QLocale.Germany))
        self.ImgLbl_CurSelOrDrag.setPixmap(QPixmap(u"../Studium/UIWB/Beni/Bachelor/PythonShit/ImageTileConverter/SourceImages/04a.png"))
        self.ImgLbl_CurSelOrDrag.setScaledContents(True)
        self.ImgLbl_CurSelOrDrag.setAlignment(Qt.AlignCenter)

        ## Create Next Panel
        self.Frm_CreateNextPanel = QFrame(self.MainFrame)
        self.Frm_CreateNextPanel.setObjectName(u"Frm_CreateNextPanel")
        self.Frm_CreateNextPanel.setGeometry(QRect(460, 0, 661, 811))
        self.Frm_CreateNextPanel.setFrameShape(QFrame.StyledPanel)
        self.Frm_CreateNextPanel.setFrameShadow(QFrame.Raised)
        self.Lab_CreateNextPanel = QLabel(self.Frm_CreateNextPanel)
        self.Lab_CreateNextPanel.setObjectName(u"Lab_CreateNextPanel")
        self.Lab_CreateNextPanel.setGeometry(QRect(20, 10, 71, 16))
        #Zoom Grid
        self.Frm_CurPanelPreviewZoom = QFrame(self.Frm_CreateNextPanel)
        self.Frm_CurPanelPreviewZoom.setObjectName(u"Frm_CurPanelPreviewZoom")
        self.Frm_CurPanelPreviewZoom.setGeometry(QRect(20, 40, 121, 71))
        self.Frm_CurPanelPreviewZoom.setFrameShape(QFrame.StyledPanel)
        self.Frm_CurPanelPreviewZoom.setFrameShadow(QFrame.Raised)
        self.Lab_CurPanelPreviewZoom = QLabel(self.Frm_CurPanelPreviewZoom)
        self.Lab_CurPanelPreviewZoom.setObjectName(u"Lab_CurPanelPreviewZoom")
        self.Lab_CurPanelPreviewZoom.setGeometry(QRect(20, 10, 91, 16))
        self.Txt_CurPanelPreviewZoom = QLineEdit(self.Frm_CurPanelPreviewZoom)
        self.Txt_CurPanelPreviewZoom.setObjectName(u"Txt_CurPanelPreviewZoom")
        self.Txt_CurPanelPreviewZoom.setGeometry(QRect(50, 30, 61, 20))
        self.Txt_CurPanelPreviewZoom.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.PanelScaleFactor = 0.5
        self.Txt_CurPanelPreviewZoom.setText(QCoreApplication.translate("ImageTilerObj", u"0.5", None))
        self.HoSli_CurPanelPreviewZoom = QSlider(self.Frm_CurPanelPreviewZoom)
        self.HoSli_CurPanelPreviewZoom.setObjectName(u"HoSli_CurPanelPreviewZoom")
        self.HoSli_CurPanelPreviewZoom.setGeometry(QRect(50, 50, 61, 20))
        self.HoSli_CurPanelPreviewZoom.setOrientation(Qt.Horizontal)
        ## The New Panel
        TTileX = good_int(int(self.Txt_TilePixelSizeX.text()) * self.PanelScaleFactor)
        TTileY = good_int(int(self.Txt_TilePixelSizeY.text()) * self.PanelScaleFactor)
        self.Frm_TheNewPanel = DragFrame(self.Frm_CreateNextPanel)
        self.Frm_TheNewPanel.setObjectName(u"Frm_TheNewPanel")
        self.Frm_TheNewPanel.setGeometry(QRect(20, 110, TTileX * 2, TTileY * 2))
        self.Frm_TheNewPanel.setFixedSize(TTileX * 2, TTileY * 2)
        self.Frm_TheNewPanel.setFrameShape(QFrame.StyledPanel)
        self.Frm_TheNewPanel.setFrameShadow(QFrame.Raised)
        self.Frm_TheNewPanel.setStyleSheet(f"background-color : grey;")
        self.Frm_TheNewPanel.uiimagetiler = self

        ## The New Panel Grid
        self.Grid_LayoutWidget = QWidget(self.Frm_TheNewPanel)
        self.Grid_LayoutWidget.setObjectName(u"Grid_LayoutWidget")        
        self.Grid_LayoutWidget.setGeometry(QRect(20, 20, TTileX * int(self.Txt_Tiles_X.text()), TTileY * int(self.Txt_Tiles_X.text())))
        self.Grid_Images = QGridLayout(self.Grid_LayoutWidget)
        self.Grid_Images.setSpacing(0)
        self.Grid_Images.setObjectName(u"Grid_Images")
        self.Grid_Images.setContentsMargins(0, 0, 0, 0)
        self.oggridgeo = self.Grid_LayoutWidget.geometry()
        #print("Init:", self.Grid_LayoutWidget.geometry())

        ## Images of new Panel        
        font = QFont()
        font.setPointSize(23)
        font.setUnderline(True)
        
        #Image Grid
        self.GridImageList = [[]]
        self.UpdateTileGrid()

        #self.Frm_TheNewPanel.raise_()
        #self.Lab_CreateNextPanel.raise_()

            
        ## Target Folder Select
        self.Frm_SelTargetFolder = QFrame(self.centralwidget)
        self.Frm_SelTargetFolder.setObjectName(u"Frm_SelTargetFolder")
        self.Frm_SelTargetFolder.setGeometry(QRect(300, 0, 271, 61))
        self.Frm_SelTargetFolder.setFrameShape(QFrame.StyledPanel)
        self.Frm_SelTargetFolder.setFrameShadow(QFrame.Raised)
        self.Lab_SelTargetFolder = QLabel(self.Frm_SelTargetFolder)
        self.Lab_SelTargetFolder.setObjectName(u"Lab_SelTargetFolder")
        self.Lab_SelTargetFolder.setGeometry(QRect(10, 10, 121, 16))
        self.Btn_SelTargetFolder = QPushButton(self.Frm_SelTargetFolder)
        self.Btn_SelTargetFolder.setObjectName(u"Btn_SelTargetFolder")
        self.Btn_SelTargetFolder.setGeometry(QRect(190, 30, 75, 23))
        self.Txt_SelTargetFolder = QLineEdit(self.Frm_SelTargetFolder)
        self.Txt_SelTargetFolder.setObjectName(u"Txt_SelTargetFolder")
        self.Txt_SelTargetFolder.setGeometry(QRect(10, 30, 171, 20))
        self.Txt_SelTargetFolder.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        ## Finish Frame
        self.Frm_Finish = QFrame(self.centralwidget)
        self.Frm_Finish.setObjectName(u"Frm_Finish")
        self.Frm_Finish.setGeometry(QRect(570, -10, 551, 81))
        self.Frm_Finish.setFrameShape(QFrame.StyledPanel)
        self.Frm_Finish.setFrameShadow(QFrame.Raised)
        self.Lab_FinSave = QLabel(self.Frm_Finish)
        self.Lab_FinSave.setObjectName(u"Lab_FinSave")
        self.Lab_FinSave.setGeometry(QRect(290, 10, 101, 16))
        self.Btn_Save = QPushButton(self.Frm_Finish)
        self.Btn_Save.setObjectName(u"Btn_Save")
        self.Btn_Save.setGeometry(QRect(300, 30, 75, 23))
        self.Btn_SaveIndividualy = QPushButton(self.Frm_Finish)
        self.Btn_SaveIndividualy.setObjectName(u"Btn_SaveIndividualy")
        self.Btn_SaveIndividualy.setGeometry(QRect(420, 30, 75, 23))
        self.Lab_SaveIndividualy = QLabel(self.Frm_Finish)
        self.Lab_SaveIndividualy.setObjectName(u"Lab_SaveIndividualy")
        self.Lab_SaveIndividualy.setGeometry(QRect(400, 10, 141, 16))
        self.Lab_SaveIndividualy.setWordWrap(True)

        self.Txt_SaveName = QLineEdit(self.Frm_Finish)
        self.Txt_SaveName.setObjectName(u"Txt_SaveName")
        self.Txt_SaveName.setGeometry(QRect(10, 30, 151, 20))
        self.Txt_SaveName.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.Lab_FinSaveNameText = QLabel(self.Frm_Finish)
        self.Lab_FinSaveNameText.setObjectName(u"Lab_FinSaveNameText")
        self.Lab_FinSaveNameText.setGeometry(QRect(10, 10, 101, 16))
        self.Cmb_FinFileFormat = QComboBox(self.Frm_Finish)
        self.Cmb_FinFileFormat.setObjectName(u"Cmb_FinFileFormat")
        self.Cmb_FinFileFormat.setGeometry(QRect(170, 30, 69, 22))
        self.Lab_FinFormat = QLabel(self.Frm_Finish)
        self.Lab_FinFormat.setObjectName(u"Lab_FinFormat")
        self.Lab_FinFormat.setGeometry(QRect(170, 10, 101, 16))
        self.Checkb_FinAutoIncrease = QCheckBox(self.Frm_Finish)
        self.Checkb_FinAutoIncrease.setObjectName(u"Checkb_FinAutoIncrease")
        self.Checkb_FinAutoIncrease.setEnabled(True)
        self.Checkb_FinAutoIncrease.setGeometry(QRect(20, 60, 101, 17))
        self.Checkb_FinAutoIncrease.setChecked(True)

        #colors
        self.Frm_Colors = QFrame(self.Frm_CreateNextPanel)
        self.Frm_Colors.setObjectName(u"Frm_Colors")
        self.Frm_Colors.setGeometry(QRect(150, 40, 221, 71))
        self.Frm_Colors.setFrameShape(QFrame.StyledPanel)
        self.Frm_Colors.setFrameShadow(QFrame.Raised)
        self.Lab_Backgroundcolor = QLabel(self.Frm_Colors)
        self.Lab_Backgroundcolor.setObjectName(u"Lab_Backgroundcolor")
        self.Lab_Backgroundcolor.setGeometry(QRect(120, 10, 101, 16))
        self.Lab_Spacingcolor = QLabel(self.Frm_Colors)
        self.Lab_Spacingcolor.setObjectName(u"Lab_Spacingcolor")
        self.Lab_Spacingcolor.setGeometry(QRect(30, 10, 71, 16))
        self.GV_Spacingcolor = ColorPickImageView(self.Frm_Colors)
        self.GV_Spacingcolor.setObjectName(u"GV_Spacingcolor")
        self.GV_Spacingcolor.setGeometry(QRect(40, 40, 51, 21))
        self.GV_Backgroundcolor = ColorPickImageView(self.Frm_Colors)
        self.GV_Backgroundcolor.setObjectName(u"GV_Backgroundcolor")
        self.GV_Backgroundcolor.setGeometry(QRect(130, 40, 51, 21))

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
    userIsInputting = True
    def UpdateTileGrid(self):
        self.PanelScaleFactor = good_float(self.Txt_CurPanelPreviewZoom.text())
        tilesx, tilesy = int(self.Txt_Tiles_X.text()), int(self.Txt_Tiles_Y.text())
  
        ScTileX = good_int(int(self.Txt_TilePixelSizeX.text()) * self.PanelScaleFactor)
        ScTileY = good_int(int(self.Txt_TilePixelSizeY.text()) * self.PanelScaleFactor)

        ImgSizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        gridx, gridy = len(self.GridImageList[0]), len(self.GridImageList) 

        #-> less grid than required tiles = new tiles spawn
        if (gridx <= tilesx): 
            for r in self.GridImageList:
                while (len(r) < tilesx):
                    r.append(None)

        while (len(self.GridImageList) < tilesy): #-> less grid than required tiles = new tiles spawn
            self.GridImageList.append([None for x in range(tilesx)])
        
        gridx, gridy = len(self.GridImageList[0]), len(self.GridImageList)        
        minx, miny = tilesx, tilesy

        for y in range(max(gridy, tilesy)):
            for x in range(max(gridx, tilesx)):                      
                if (tilesy <= y or tilesx <= x ):   #-> more grid than required tiles -> cut later
                    continue
                
                j = self.GridImageList[y][x]
                if j == None:
                    self.GridImageList[y][x] = DragGraphicsView(self, ScTileX, ScTileY)
                    j = self.GridImageList[y][x]
                    self.Grid_Images.addWidget(j, y, x)
                j = self.GridImageList[y][x]
                j.setObjectName(f"ImgLbl_CurSel_{x+1}_{y+1}")
                j.setSizePolicy(ImgSizePolicy)
                j.setFrameShape(QFrame.StyledPanel)
                self.ToggleWidgetColor(j, QColor(0, 0, 0))
                j.setLineWidth(6)
                j.setAcceptDrops(True)
                j.Index = (y, x)
                    
        
        while len(self.GridImageList) > miny:
            a = self.GridImageList.pop()
            a.reverse()
            for w in a:
                self.Grid_Images.removeWidget(w)
                w.setParent(None)
                w.deleteLater()
        for rem in self.GridImageList:
            while len(rem) > minx:
                w = rem.pop()
                self.Grid_Images.removeWidget(w)
                w.setParent(None)
                w.deleteLater()
        
        TileX, TileY = good_int(self.Txt_TilePixelSizeX.text()), good_int(self.Txt_TilePixelSizeY.text())
        DistX, DistY = good_int(self.Txt_PanelDistance_X.text()), good_int(self.Txt_PanelDistance_X.text())

        ptr = QPoint(TileX * tilesx + DistX * max(0,tilesx-1), TileY * tilesy + DistY  * max(0,tilesy-1))
        
        ab = self.userIsInputting
        self.userIsInputting = False
        self.Txt_TotalPixelSizeX.setText(str(ptr.x()))
        self.Txt_TotalPixelSizeY.setText(str(ptr.y()))
        self.userIsInputting = ab
        
        self.ApplyPixelSize()
        self.SetOGGridGeo()

    def InitSliders(self):
        #Total Scale Slider
        self.userIsInputting = True
        self.UserChangedCurPanelPreviewZoom()

    def retranslateUi(self, ImageTilerObj):
        ImageTilerObj.setWindowTitle(QCoreApplication.translate("ImageTilerObj", u"Image Tiler", None))
        self.Lab_SourceFiles.setText(QCoreApplication.translate("ImageTilerObj", u"Source Files", None))
        self.Lab_SourceFilesDnDInfo.setText(QCoreApplication.translate("ImageTilerObj", u"Drag and Drop into Panel", None))
        self.Lab_CurSelOrDrag.setText(QCoreApplication.translate("ImageTilerObj", u"Preview currently selected", None))
        self.ImgLbl_CurSelOrDrag.setText("")
        self.Lab_CreateNextPanel.setText(QCoreApplication.translate("ImageTilerObj", u"Next Panel", None))
        self.Lab_CurPanelPreviewZoom.setText(QCoreApplication.translate("ImageTilerObj", u"Preview Zoom", None))
        self.Txt_CurPanelPreviewZoom.setText(QCoreApplication.translate("ImageTilerObj", u"0.5", None))
        self.Txt_TilePixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"480", None))
        self.Lab_TilePixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"Tile Pixel Size X", None))
        self.Txt_TilePixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"640", None))
        self.Lab_TilePixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"Tile Pixel Size Y", None))
        self.Checkb_LinkXY.setText(QCoreApplication.translate("ImageTilerObj", u"Link X-Y", None))
        self.Txt_TotalPixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"960", None))
        self.Txt_TotalPixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"1280", None))
        self.Lab_TotalPixelSizeX.setText(QCoreApplication.translate("ImageTilerObj", u"Total Pixel Size X", None))
        self.Lab_TotalPixelSizeY.setText(QCoreApplication.translate("ImageTilerObj", u"Total Pixel Size Y", None))
        self.Lab_PanelDistance.setText(QCoreApplication.translate("ImageTilerObj", u"Distance", None))
        self.Txt_PanelDistance_X.setText(QCoreApplication.translate("ImageTilerObj", u"0", None))
        self.Txt_PanelDistance_Y.setText(QCoreApplication.translate("ImageTilerObj", u"0", None))
        self.Lab_PanelDistance_X.setText(QCoreApplication.translate("ImageTilerObj", u"X", None))
        self.Lab_PanelDistance_Y.setText(QCoreApplication.translate("ImageTilerObj", u"Y", None))
        self.Txt_Tiles_Y.setText(QCoreApplication.translate("ImageTilerObj", u"2", None))
        self.Lab_Tiles_Y.setText(QCoreApplication.translate("ImageTilerObj", u"Tiles Y", None))
        self.Txt_Tiles_X.setText(QCoreApplication.translate("ImageTilerObj", u"2", None))
        self.Lab_Tiles_X.setText(QCoreApplication.translate("ImageTilerObj", u"Tiles X", None))
        self.Lab_SelSourceFolder.setText(QCoreApplication.translate("ImageTilerObj", u"1. Select Source Folder", None))
        self.Btn_SelSourceFolder.setText(QCoreApplication.translate("ImageTilerObj", u"Select", None))
        self.Lab_SelTargetFolder.setText(QCoreApplication.translate("ImageTilerObj", u"2. Select Target Folder", None))
        self.Btn_SelTargetFolder.setText(QCoreApplication.translate("ImageTilerObj", u"Select", None))
        self.Lab_FinSave.setText(QCoreApplication.translate("ImageTilerObj", u"Finnish: Save Panel", None))
        self.Btn_Save.setText(QCoreApplication.translate("ImageTilerObj", u"Save", None))
        self.Lab_FinSaveNameText.setText(QCoreApplication.translate("ImageTilerObj", u"Finish: SaveName", None))
        self.Lab_FinFormat.setText(QCoreApplication.translate("ImageTilerObj", u"Finish: Fileformat", None))
        self.Checkb_FinAutoIncrease.setText(QCoreApplication.translate("ImageTilerObj", u"Auto increase", None))
        self.menuCustom_Made_Tool_For_Ernest_Programming_is_fun.setTitle(QCoreApplication.translate("ImageTilerObj", u"Custom Made Tool For Ernest. Programming is fun!!", None))
        self.Btn_SaveIndividualy.setText(QCoreApplication.translate("ImageTilerObj", u"Save", None))
        self.Lab_SaveIndividualy.setText(QCoreApplication.translate("ImageTilerObj", u"Finnish: Save individually", None))
        self.Lab_Backgroundcolor.setText(QCoreApplication.translate("ImageTilerObj", u"Backgroundcolor", None))
        self.Lab_Spacingcolor.setText(QCoreApplication.translate("ImageTilerObj", u"Spacingcolor", None))
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
            bgcol = currentcolor
            if alternativecolor != None:
                bgcol = alternativecolor            
            elif bgcol == "white":
                bgcol = "red"
            else:
                bgcol = "white"
            col = "black"
            try:
                TWidget.setStyleSheet(f"color : {col}; background-color : {bgcol};")
            except:
                pass
        #TWidget.setPalette(palette)

    def ApplyPixelSize(self):
        ###This should get good pixel sizes from text fields
        self.PanelScaleFactor = good_float(self.Txt_CurPanelPreviewZoom.text())

        TFrameWidgetSize = self.get_WidgetSize(self.Grid_Images)
        self.ApplyGridPositioning()
        self.Apply_Image_Zooms(TFrameWidgetSize)

    rclickpressed = False
    gridogoffset = QPointF(10,10)
    lastgriddelta = QPointF(0,0)
    def ApplyGridPositioning(self):
        self.PanelScaleFactor = good_float(self.Txt_CurPanelPreviewZoom.text())
        DistanceX, DistanceY = floor_int(self.Txt_PanelDistance_X.text()) * self.PanelScaleFactor, floor_int(self.Txt_PanelDistance_Y.text()) * self.PanelScaleFactor
        TileImgSizeX, TileImgSizeY = good_int(int(self.Txt_TilePixelSizeX.text()) * self.PanelScaleFactor), good_int(int(self.Txt_TilePixelSizeY.text()) * self.PanelScaleFactor)
        TilesX = int(self.Txt_Tiles_X.text())
        TilesY = int(self.Txt_Tiles_Y.text())

        geo = self.Grid_LayoutWidget.geometry()
        oldSize = geo.size()
        newSize = QSize(TileImgSizeX * TilesX + DistanceX * max(TilesX - 1 , 0), TileImgSizeY * TilesY + DistanceY * max(TilesY - 1 , 0))

        if self.rclickpressed and oldSize.width() > 0 and oldSize.height() > 0:
            mouseGlobal = QCursor.pos()

            oldTopLeftGlobal = self.Grid_LayoutWidget.parentWidget().mapToGlobal(geo.topLeft())

            relX = (mouseGlobal.x() - oldTopLeftGlobal.x()) / oldSize.width()
            relY = (mouseGlobal.y() - oldTopLeftGlobal.y()) / oldSize.height()

            newTopLeftGlobal = QPoint(
                mouseGlobal.x() - int(relX * newSize.width()),
                mouseGlobal.y() - int(relY * newSize.height())
            )

            newTopLeftLocal = self.Grid_LayoutWidget.parentWidget().mapFromGlobal(newTopLeftGlobal)
            self.RightMouseDragStart = mouseGlobal
        else:
            newTopLeftLocal = geo.topLeft()

        self.Grid_LayoutWidget.setGeometry(
            QRect(newTopLeftLocal, newSize)
        )
        #print("applygridpos", DistanceX, DistanceY)
        self.Grid_Images.setHorizontalSpacing(DistanceX)
        self.Grid_Images.setVerticalSpacing(DistanceY)
        #for row in range(self.Grid_Images.rowCount()):
        #    self.Grid_Images.setRowMinimumHeight(row, TileImgSizeY)
        #for col in range(self.Grid_Images.columnCount()):
        #    self.Grid_Images.setColumnMinimumWidth(col, TileImgSizeX)
        self.SetOGGridGeo()
        
        
    def Apply_Image_Zooms(self, TFrameWidgetSize, PImgSizeX = None, PImgSizeY = None):
        self.PanelScaleFactor = good_float(self.Txt_CurPanelPreviewZoom.text())
        if PImgSizeX == None:
            PImgSizeX = good_int(int(self.Txt_TilePixelSizeX.text()) * self.PanelScaleFactor)
        if PImgSizeY == None:
            PImgSizeY = good_int(int(self.Txt_TilePixelSizeY.text()) * self.PanelScaleFactor)

        done = False
        for i in self.GridImageList:            
            for j in i:                
                if not done:
                    done = True
                    
                j.currentPanelZoomFactor = self.PanelScaleFactor
                j.ApplyZoomFactors()
            if not done: done = True

    def FillImgFormatFileCombobox(self):
        self.ImgFormatList = [
        ".webp",
        ".jpg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".gif",
        ".jpeg",
        ]
        self.Cmb_FinFileFormat.addItems(self.ImgFormatList)

    def get_WidgetSize(self, widget):
        try:
            return widget.size()
        except:
            return widget.geometry().size()
    
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