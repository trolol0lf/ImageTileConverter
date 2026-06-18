# This Code creates an user interface that allows the user to select an folder, get the *.png images from that folder and store them in custom classes and display the image list as well as the in the list selected image
# The image preview allows to select an crop area as custom class with user selected pixel size and stores the crop area for final use
# The custom class needs another initialy true boolean to check if it should output.
# Finally the user starts the process by pressing a buttonand for each image it crops it to the user preset size and converts it into .webp as well saves it to another selected folder
from FileHandler import *
from PySide6.QtWidgets import QApplication, QMainWindow, QStyleFactory
from PySide6.QtCore import Qt, QPointF, QRect
from PySide6.QtGui import QPixmap, QImage, QPainter, QMouseEvent
from ui_ErnestTiler import *    #Ui_ImageTilerObj, good_int
from Handler_Formats import *
import json, win32api, win32con, sys
    


class Window(QMainWindow, Ui_ImageTilerObj):
    def __init__(self):

        super().__init__()
        self.setupUi(self)

        #Step 1 Select Source Folder via Button or Textchange and update Lis_SourceFiles accordingly
        self.Btn_SelSourceFolder.clicked.connect(self.SelectSourceFolder)        
        self.Txt_SelSourceFolder.textChanged.connect(self.SelectSourceFolder) #(self.Txt_SelSourceFolder.text())

        #Step2 Select Target Folder via Button or Textchange
        self.Btn_SelTargetFolder.clicked.connect(self.SelectTargetFolder)
        self.Txt_SelTargetFolder.textChanged.connect(self.SelectTargetFolder)
        self.Cmb_FinFileFormat.currentTextChanged.connect(self.UserChangedSaveName)
        self.Checkb_FinAutoIncrease.stateChanged.connect(self.UserChangedSaveAutoIncrease)

        #Step3.1 Preview in list selected image
        self.Lis_SourceFiles.itemSelectionChanged.connect(self.PreviewImage)
        #self.Lis_SourceFiles.doubleClicked.connect(self.addFreeImage)

        #Step3.2 Adjust the pixel size if Txt_TilePixelSizeX, Txt_TilePixelSizeY, Txt_TotalPixelSizeX, Txt_TotalPixelSizeY is changed
        self.userIsInputting = True # To limit the calls when changes occur
        self.Txt_TilePixelSizeX.textChanged.connect(self.UserChangedPixelSizeText)
        self.Txt_TilePixelSizeX.focusOutEvent = self.UserLeftPixelSizeText

        self.Txt_TilePixelSizeY.textChanged.connect(self.UserChangedPixelSizeText)
        self.Txt_TilePixelSizeY.focusOutEvent = self.UserLeftPixelSizeText

        self.Txt_TotalPixelSizeX.textChanged.connect(self.UserChangedPixelSizeText)
        self.Txt_TotalPixelSizeX.focusOutEvent = self.UserLeftPixelSizeText

        self.Txt_TotalPixelSizeY.textChanged.connect(self.UserChangedPixelSizeText) 
        self.Txt_TotalPixelSizeY.focusOutEvent = self.UserLeftPixelSizeText

        self.Checkb_LinkXY.stateChanged.connect(self.UserChangedPixelSizeLinkXY)
        
        ##Step3.2.1.1 Adjust Tiles 
        self.Txt_Tiles_X.textChanged.connect(self.TileXChanged)
        self.Txt_Tiles_Y.textChanged.connect(self.TileYChanged)
        self.Sli_Tiles_X.valueChanged.connect(self.TileSliderXChanged)
        self.Sli_Tiles_Y.valueChanged.connect(self.TileSliderYChanged)
        
        ##Step3.2.1.2 Adjust Distance
        self.Txt_PanelDistance_X.textChanged.connect(self.DistanceXChanged)
        self.Txt_PanelDistance_Y.textChanged.connect(self.DistanceYChanged)
        self.Sli_PanelDistance_X.valueChanged.connect(self.DistanceSliderXChanged)
        self.Sli_PanelDistance_Y.valueChanged.connect(self.DistanceSliderYChanged)

        ##Step3.2.1.3 Grid Movement
        self.Frm_TheNewPanel.setMouseTracking(True)
        
        ##Step3.2.2 Adjust the CurPanelPreviewZoom
        self.Txt_CurPanelPreviewZoom.textChanged.connect(self.UserChangedCurPanelPreviewZoom)
        self.HoSli_CurPanelPreviewZoom.valueChanged.connect(self.UserChangedCurPanelPreviewZoom)
        ##Step3.2.3 Right click moves grid
        #Step3.3.1 Drag from Lis_SourceFiles to Img_CurSel (1-4) to import an image to the tile
        #Gets managed in Class!

        #Step3.3.2 Drop on Img_Cursel (1-4) to import an image to the tile
        #Gets managed in Class!

        #Step3.4 Drag and Drop the images in Img_CurSel (1-4) to their desired cropping positions
        #Gets managed in Class! But not yet
        
        #Step4.1 Set File Name and Format
        self.Txt_SaveName.textChanged.connect(self.UserChangedSaveName)
        #Step4.2 Save Panel
        self.Btn_Save.clicked.connect(self.FinalSavePanel)
        self.Btn_SaveIndividualy.clicked.connect(self.FinalSavePanelIndiv)

        #Load last settings
        self.load_SaveDic()

    ###Step 1 Select Source Folder (and Refresh Filelist)
    def SelectSourceFolder(self, folder = None):
        # Textcolors are set in refresh filelist
        if folder == None or not folder:
            folder = select_folder()
        self.RefreshFilelist(folder)

    def RefreshFilelist(self, folder = None):
        if (folder is not None and not folder == "") and os.path.exists(folder):            
            self.ToggleWidgetColor(self.Txt_SelSourceFolder, "white")
            self.Txt_SelSourceFolder.setText(folder)
            self.Lis_SourceFiles.clear()
            self.SourceFolderFiles = xfilelist(initfolder = folder)
            for file in self.SourceFolderFiles: #? returns string good?
                self.Lis_SourceFiles.addItem(file)
        else:
            self.ToggleWidgetColor(self.Txt_SelSourceFolder, "red")


    ###Step 2 Select Target Folder
    def SelectTargetFolder(self, folder = None):
        if folder == None or not folder:
            folder = select_folder()
        if os.path.exists(folder):
            self.Txt_SelTargetFolder.setText(folder)
            self.ToggleWidgetColor(self.Txt_SelTargetFolder, "white")
        else:
            self.ToggleWidgetColor(self.Txt_SelTargetFolder, "red")


    ###Step 3.1 Preview
    def PreviewImage(self):
        # Pick xfile object from 
        currentselection = self.SourceFolderFiles.GetRealItem(self.Lis_SourceFiles.currentIndex().row())
        #TPixMap = QPixmap(currentselection.fullname)
        self.ImgLbl_CurSelOrDrag.AddImage(currentselection.fullname)
        self.ImgLbl_CurSelOrDrag.setAlignment(Qt.AlignCenter)
        self.ImgLbl_CurSelOrDrag.setScaledContents(True)

    ###Step 3.2 UserChangedPixelSizeLinkXY
    def UserChangedPixelSizeLinkXY(self):
        if self.Checkb_LinkXY.isChecked():
            self.Var_TilePixelSizeRatio = float(self.Txt_TilePixelSizeX.text()) / float(self.Txt_TilePixelSizeY.text())
            self.Lin_LinkXY.setHidden(False)
            self.Lin_LinkXY2.setHidden(False)
        else:
            self.Lin_LinkXY.setHidden(True)
            self.Lin_LinkXY2.setHidden(True)
        
    def UserLeftPixelSizeText(self, e):
        self.userIsInputting = True
        tRatio = self.Var_TilePixelSizeRatio
        if self.Txt_TilePixelSizeX.text() == "":
            self.Txt_TilePixelSizeX.setText("9")
        elif self.Txt_TilePixelSizeY.text() == "":
            self.Txt_TilePixelSizeY.setText("9")
        elif self.Txt_TotalPixelSizeX.text() == "":
            self.Txt_TotalPixelSizeX.setText("9")
        elif self.Txt_TotalPixelSizeY.text() == "":
            self.Txt_TotalPixelSizeY.setText("9")
        self.Var_TilePixelSizeRatio = tRatio

    ##Step 3.3.1.1 Tile Amount Changed
    internaltilecall = False
    def TileXChanged(self):
        txt = self.Txt_Tiles_X.text()
        if not txt == "" and not self.internaltilecall:
            real = max(min(int(txt), self.Sli_Tiles_X.maximum()), self.Sli_Tiles_X.minimum()) 
            self.internaltilecall = True
            self.Txt_Tiles_X.setText(str(real))
            self.Sli_Tiles_X.setValue(real)
            self.UpdateTileGrid()
            self.internaltilecall = False
    def TileYChanged(self):
        txt = self.Txt_Tiles_Y.text()
        if not txt == "" and not self.internaltilecall:
            real = max(min(int(txt), self.Sli_Tiles_Y.maximum()), self.Sli_Tiles_Y.minimum())
            self.internaltilecall = True
            self.Txt_Tiles_Y.setText(str(real)) 
            self.Sli_Tiles_Y.setValue(real)
            self.UpdateTileGrid()
            self.internaltilecall = False

    def TileSliderXChanged(self):
        if not self.internaltilecall: 
            self.Txt_Tiles_X.setText(str(self.Sli_Tiles_X.value()))
    def TileSliderYChanged(self):
        if not self.internaltilecall: 
            self.Txt_Tiles_Y.setText(str(self.Sli_Tiles_Y.value()))

    ##Step 3.3.1.2 Distance Changed
    internaldistancecall = False
    def DistanceXChanged(self):
        txt = self.Txt_PanelDistance_X.text()
        if not txt == "" and not self.internaldistancecall: 
            self.internaldistancecall = True
            real = max(min(int(txt), self.Sli_PanelDistance_X.maximum() * 100), self.Sli_PanelDistance_X.minimum())
            self.Txt_PanelDistance_X.setText(str(real))
            self.Sli_PanelDistance_X.setValue(real)
            self.UserChangedPixelSizeText()
            self.Apply_Image_Zooms(self.get_WidgetSize(self.Frm_TheNewPanel))
            self.internaldistancecall = False
    def DistanceYChanged(self):
        txt = self.Txt_PanelDistance_Y.text()
        if not txt == "" and not self.internaldistancecall: 
            self.internaldistancecall = True
            real = max(min(int(txt), self.Sli_PanelDistance_Y.maximum() * 100), self.Sli_PanelDistance_Y.minimum())
            self.Txt_PanelDistance_Y.setText(str(real))
            self.Sli_PanelDistance_Y.setValue(real)
            self.UserChangedPixelSizeText()
            self.Apply_Image_Zooms(self.get_WidgetSize(self.Frm_TheNewPanel))
            self.internaldistancecall = False

    def DistanceSliderXChanged(self):
        if not self.internaldistancecall: 
            self.Txt_PanelDistance_X.setText(str(self.Sli_PanelDistance_X.value()))
    def DistanceSliderYChanged(self):
        if not self.internaldistancecall: 
            self.Txt_PanelDistance_Y.setText(str(self.Sli_PanelDistance_Y.value()))

    ##Step 3.3.1 UserChangedCurPanelPreviewZoom
    def UserChangedCurPanelPreviewZoom(self):
        if self.userIsInputting:
            self.userIsInputting = False
            xMax = 1.5
            xMin = 0.1
            sender = self.sender()
            if sender == None: sender = self.Txt_CurPanelPreviewZoom
            if sender == self.HoSli_CurPanelPreviewZoom:
                TState = sender.value()/100
                self.Txt_CurPanelPreviewZoom.setText(str(round(xMin+(xMax-xMin)*TState,2)))
            elif sender == self.Txt_CurPanelPreviewZoom:
                self.LimitTextToFloat(sender)
                self.Txt_CurPanelPreviewZoom.setText(str(round(clamp_float(self.Txt_CurPanelPreviewZoom.text(), xMin, xMax),3)))
                self.HoSli_CurPanelPreviewZoom.setValue(int((float(self.Txt_CurPanelPreviewZoom.text())-xMin)/(xMax-xMin)*100))
            self.ApplyPixelSize()
            self.userIsInputting = True
        
    ##Step 3.3.2 User moved grid    
    def SetOGGridGeo(self):
        self.oggridgeo = self.Grid_LayoutWidget.geometry()
        #print("Reset:", self.Grid_LayoutWidget.geometry())

    def MouseMovesGrid(self, Delta):
        self.gridogoffset = self.oggridgeo.topLeft() + Delta
        self.Grid_LayoutWidget.setGeometry(QRect(self.oggridgeo.topLeft() + Delta, self.oggridgeo.bottomRight() + Delta))
        #print("Move:", self.Grid_LayoutWidget.geometry())

    def UserChangedSaveName(self):
        TrueFileName = None
        if self.Txt_SaveName.text() == "":
            self.ToggleWidgetColor(self.Txt_SaveName, "red")
        else:
            curSaveName = self.Txt_SaveName.text()
            ChangedSaveName = curSaveName            
            forbiddensigns = re.findall("[^a-zA-Z0-9\-\_]", curSaveName)
            for i in forbiddensigns:
                ChangedSaveName = curSaveName.replace(i, "_")            
            TrueFileName = self.get_solid_filename(self.Txt_SelTargetFolder.text(), ChangedSaveName, self.Cmb_FinFileFormat.currentText())
        
        if not TrueFileName:
            self.ToggleWidgetColor(self.Txt_SaveName, "red")
        else:
            self.Txt_SaveName.setText(TrueFileName)
            self.ToggleWidgetColor(self.Txt_SaveName, "white")

    def UserChangedSaveAutoIncrease(self):
        if self.Checkb_FinAutoIncrease.isChecked():
            self.UserChangedSaveName()

    def FinalSavePanelIndiv(self):
        self.FinalSavePanel(saveindividualy = True)
        
    def FinalSavePanel(self, saveindividualy = False):
        if not self.Check_FinalSavePanel_Vars(): return
        imgs = {}

        PanelSize = (good_int(self.Txt_TotalPixelSizeX.text()), good_int(self.Txt_TotalPixelSizeY.text()))
        FrameSize = (good_int(self.Txt_TilePixelSizeX.text()), good_int(self.Txt_TilePixelSizeY.text()))

        for k, i in enumerate(self.GridImageList):
            a = []
            imgs[k] = a
            for j in i:
                imgs[k].append(j.get_img_correct_size())
        
        if saveindividualy:
            self.SaveTilesIndividually(imgs)
        else:
            CorrectPanel = QImage(PanelSize[0], PanelSize[1], QImage.Format.Format_ARGB32)
            
            CorrectPanel.fill(ascolor(self.GV_Spacingcolor.color))
            painter = QPainter(CorrectPanel)

            for i, row in enumerate(imgs.values()):
                for j, img in enumerate(row):
                    painter.drawImage(j * FrameSize[0] + max(0,j) * int(self.Txt_PanelDistance_X.text()), i * FrameSize[1] + max(0,i) * int(self.Txt_PanelDistance_Y.text()), img)
            painter.end()

            self.SavePanel(CorrectPanel)
        
    def SavePanel(self, PanelQImage):
        TargetFileFormat = self.Cmb_FinFileFormat.currentText()
        TargetFileFolder = self.Txt_SelTargetFolder.text()
        TargetFileName = self.Txt_SaveName.text()
        if self.Checkb_FinAutoIncrease.isChecked():
            TargetFileName = self.get_solid_filename(TargetFileFolder, TargetFileName, TargetFileFormat)
        PanelQImage.save(TargetFileFolder + "\\" + TargetFileName + TargetFileFormat)
    
    def SaveTilesIndividually(self, Tiles = None):
        if Tiles == None: return False
        TargetFileFormat = self.Cmb_FinFileFormat.currentText()
        TargetFileFolder = self.Txt_SelTargetFolder.text()
        TargetFileBaseName = self.Txt_SaveName.text()
        TargetFileName = ""

        for i in range(len(Tiles)):            
            for k, j in enumerate(Tiles[i]):
                tileidx = "_" + str(i + 1) + "_" + str(k + 1)
                if TargetFileName == "": 
                    TargetFileName = self.get_solid_filename(TargetFileFolder, TargetFileBaseName + "_", TargetFileFormat)
                    if TargetFileName[-1] == "_": TargetFileName = TargetFileName + "0" 
                TargetFileName = self.get_solid_filename(TargetFileFolder, TargetFileName + tileidx, TargetFileFormat).replace(tileidx, "", 1)
                if not TargetFileName: return False
                j.save(os.path.join(TargetFileFolder, TargetFileName + tileidx + TargetFileFormat))

        return True
    def Check_FinalSavePanel_Vars(self):
        #Folder
        if self.Txt_SelTargetFolder.text() == "":
            self.Txt_SelTargetFolder.setText(select_folder())
        self.SelectTargetFolder(self.Txt_SelTargetFolder.text())
        if not os.path.exists(self.Txt_SelTargetFolder.text()): return False

        #File
        if self.Txt_SaveName.text() == "":
            self.Txt_SaveName.setText("Panel")
        TrueFileName = self.get_solid_filename(self.Txt_SelTargetFolder.text(), self.Txt_SaveName.text(), self.Cmb_FinFileFormat.currentText())
        if not TrueFileName: return False
        self.Txt_SaveName.setText(TrueFileName)
        return True
    
    def get_solid_filename(self, folder, basename, fileformat):
        incrementer = 0
        if os.path.exists(os.path.join(folder, basename + fileformat)):
            if self.Checkb_FinAutoIncrease.isChecked():
                reglastIncrement = re.search(r"(\_|\-)\d+", basename)
                a = ""
                a.replace("","",)
                digits = "0"
                if not reglastIncrement == None:
                    lastIncrement = reglastIncrement.group(0)
                else:
                    basename = basename + "_0"
                    lastIncrement = "_0"
                digits = lastIncrement.replace("_","").replace("-", "")
                incrementer = int(digits)
                while os.path.exists(os.path.join(folder, basename.replace(digits, str(incrementer), 1)  + fileformat)):
                    incrementer += 1
                return basename.replace(digits, str(incrementer), 1)
            else:
                return basename
        else:
            if os.path.exists(folder):
                return basename 
            else:
                return False
    # Utility
    def LimitTextToInt(self, sender = None):
        if not sender == None:
            ttext = sender.text()
            newttext = ttext
            if not ttext.isdigit():
                for i in ttext:
                    if not i.isdigit():
                        newttext = newttext.replace(i,"")
                if sender.objectName() == "Txt_Total" and int(newttext[-1]) % 2 != 0:
                    newttext = newttext[:-1] & str(int(newttext[-1])-1)
            sender.setText(newttext)
    
    def LimitTextToFloat(self, sender = None):
        if not sender == None:
            hadPoint = False
            ttext = sender.text()
            newttext = ttext
            if not ttext.isdigit():
                for i in ttext:
                    if not i.isdigit():
                        if i == "." or i == ",":
                            if hadPoint:
                                newttext = newttext.replace(i,"")
                            else:
                                hadPoint = True
                        else:
                            newttext = newttext.replace(i,"")
                if sender.objectName() == "Txt_Total" and int(newttext[-1]) % 2 != 0:
                    newttext = newttext[:-1] & str(int(newttext[-1])-1)
            sender.setText(newttext)
    
    
    
    def UserChangedPixelSizeText(self):      
        if not self.userIsInputting: return #Dont Change loop!
        sender = self.sender()        
        if not sender == None:            
            if sender.text() == "":#Do really nothing if no text
                return        
            multx = int(self.Txt_Tiles_X.text())
            multy = int(self.Txt_Tiles_Y.text())
            c = self.Checkb_LinkXY.isChecked()
            isX = "Y" not in sender.objectName()
            sendername = sender.objectName()
            distancex, distancey = floor_int(self.Txt_PanelDistance_X.text()), floor_int(self.Txt_PanelDistance_Y.text())
            if "Tile" in sendername:
                tilesizex, tilesizey = floor_int(self.Txt_TilePixelSizeX.text()), floor_int(self.Txt_TilePixelSizeY.text())
                if c:
                    if isX:
                        tilesizey = floor_int(tilesizex * self.Var_TilePixelSizeRatio)
                    else:                    
                        tilesizex = floor_int(tilesizey / self.Var_TilePixelSizeRatio)
                totalsizex, totalsizey = floor_int(tilesizex * multx + distancex * max(0, multx - 1)), floor_int(tilesizey * multy + distancey * max(0, multy - 1))
            elif "Total" in sendername:                
                totalsizex, totalsizey = floor_int(self.Txt_TotalPixelSizeX.text()), floor_int(self.Txt_TotalPixelSizeY.text())
                tilesizex, tilesizey = floor_int(totalsizex / multx - distancex), floor_int(totalsizey / multy - distancey)                
                if c:
                    if isX:
                        totalsizey = floor_int(tilesizex * self.Var_TilePixelSizeRatio * multx + distancex * max(0, multx-1))
                    else:                    
                        totalsizex = floor_int(tilesizey / self.Var_TilePixelSizeRatio * multy + distancey * max(0, multy-1))
                tilesizex, tilesizey = floor_int(totalsizex / multx - distancex), floor_int(totalsizey / multy - distancey)    
            else:   #-> distance changed
                c = False
                tilesizex, tilesizey = floor_int(self.Txt_TilePixelSizeX.text()), floor_int(self.Txt_TilePixelSizeY.text())                
                totalsizex, totalsizey = floor_int(tilesizex * multx + distancex * max(0, multx - 1)), floor_int(tilesizey * multy + distancey * max(0, multy - 1))
            
            self.userIsInputting = False  # Change to true to make things crash
            self.LimitTextToInt(sender)   # limits the input to numbers
            
            
            if c or isX:
                self.Txt_TotalPixelSizeX.setText(str(totalsizex))
                self.Txt_TilePixelSizeX.setText(str(tilesizex))
            if c or not isX:
                self.Txt_TotalPixelSizeY.setText(str(totalsizey))
                self.Txt_TilePixelSizeY.setText(str(tilesizey))

            if not float(self.Txt_TilePixelSizeY.text()) == 0:
                self.Var_TilePixelSizeRatio = float(self.Txt_TilePixelSizeX.text()) / float(self.Txt_TilePixelSizeY.text())
            self.ApplyPixelSize()
            self.userIsInputting = True

    def generate_savedic(self, SaveDic = {}, currwidget = None):
        if not currwidget:
            currwidget = self
        if not "Var_TilePixelSizeRatio" in SaveDic: SaveDic["Var_TilePixelSizeRatio"] = self.Var_TilePixelSizeRatio
        for ele in currwidget.children():
            val = "#None#None#None#None#"
            eletype = type(ele)
            if eletype == QLineEdit:
                val = ele.text()
            elif eletype == QCheckBox:
                val = ele.isChecked()
            elif eletype == QSlider:
                val = ele.value()
            elif eletype == QComboBox:
                val = ele.currentIndex()
            elif eletype == ColorPickImageView:
                SaveDic[ele.objectName()] = asset(ele.color)
            elif eletype == DragGraphicsView:
                SaveDic[ele.objectName()] = (ele.currentInternalZoomFactor, ele.deltaX, ele.deltaY, ele.TruePixPath)
            if val != "#None#None#None#None#":
                SaveDic[ele.objectName()] = val
            self.generate_savedic(SaveDic, ele)
        return SaveDic
    
    def set_from_savedic(self, SaveDic = {str, str}, currwdget = None):
        if not currwdget:
            currwdget = self
        if "Var_TilePixelSizeRatio" in SaveDic:
            self.Var_TilePixelSizeRatio = SaveDic.pop("Var_TilePixelSizeRatio")
        for ele in currwdget.children():
            if ele.objectName() in SaveDic:
                val = SaveDic.pop(ele.objectName())
                eletype = type(ele)
                if eletype == QLineEdit:
                    ele.setText(val) 
                elif eletype == QCheckBox:
                    ele.setChecked(val)
                elif eletype == QSlider:
                    ele.setValue(val)
                elif eletype == QComboBox:
                    ele.setCurrentIndex(val)
                elif eletype == ColorPickImageView:
                    ele.setcolor(val)
                elif eletype == DragGraphicsView:
                    zoom, dx, dy, truepath = val
                    ele.currentInternalZoomFactor = zoom
                    ele.AddImage(truepath, dx, dy)
            if len(ele.children()) != 0:
                self.set_from_savedic(SaveDic, ele)

    def closeEvent(self, event):
        SaveDic = self.generate_savedic()
        self.save_SaveDic(SaveDic)

    def save_SaveDic(self, SaveDic):     
        #print(f"Save as " + os.path.join(os.path.dirname(sys.argv[0]), "ImageTileConverterSave.json"))
        savepath = os.path.join(os.path.dirname(sys.argv[0]), "ImageTileConverterSave.json")
        if os.path.exists(savepath):
            os.remove(savepath)
        with open(savepath, "w") as f:
            json.dump(SaveDic, f)
            f.close()
        win32api.SetFileAttributes(savepath,win32con.FILE_ATTRIBUTE_HIDDEN)

    def load_SaveDic(self):   
        #print(f"Load as " + os.path.join(os.path.dirname(sys.argv[0]), "ImageTileConverterSave.json"))    
        loadpath = os.path.join(os.path.dirname(sys.argv[0]), "ImageTileConverterSave.json")
        if os.path.exists(loadpath):            
            with open(loadpath, "r") as f:
                SaveDic = json.load(f)
                f.close()
            self.set_from_savedic(SaveDic)
            self.ApplyPixelSize()

app = QApplication([])
app.setStyle(QStyleFactory.create("Fusion"))

window = Window()

window.show()
app.exec()

# The def that manages the tkinter user interface
# It has an folder selection field with select button and a list of images in that folder
# The List should also have two additional columns for "use now" and "was used" booleans that can be toggled 
# It also has a preview of the currently selected image
# The user can choose a rectangular crop area with specifiec pixel size relative to the image
# After selecting 4 images the user can press a button to start the process of cropping the images
# The images will be cropped to the user selected pixel size
# The cropped images will be tiled together in the preview area. The user can now decide via buttons h
# and convert it to a .webp and store it in a new folder

