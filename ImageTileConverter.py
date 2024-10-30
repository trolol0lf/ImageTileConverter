# This Code creates an user interface that allows the user to select an folder, get the *.png images from that folder and store them in custom classes and display the image list as well as the in the list selected image
# The image preview allows to select an crop area as custom class with user selected pixel size and stores the crop area for final use
# The custom class needs another initialy true boolean to check if it should output.
# Finally the user starts the process by pressing a buttonand for each image it crops it to the user preset size and converts it into .webp as well saves it to another selected folder
from FileHandler import *
from PySide6.QtWidgets import QApplication, QMainWindow, QStyleFactory
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QPainter
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
        
        ##Step3.2.2 Adjust the CurPanelPreviewZoom
        self.Txt_CurPanelPreviewZoom.textChanged.connect(self.UserChangedCurPanelPreviewZoom)
        self.HoSli_CurPanelPreviewZoom.valueChanged.connect(self.UserChangedCurPanelPreviewZoom)

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
        imgs = []

        PanelSize = (good_int(self.Txt_TotalPixelSizeX.text()), good_int(self.Txt_TotalPixelSizeY.text()))
        FrameSize = (good_int(self.Txt_TilePixelSizeX.text()), good_int(self.Txt_TilePixelSizeY.text()))

        for i in self.GridImageList.values():
            if i.TruePixPath != "":
                imgs.append(i.get_img_correct_size())
            else:
                imgs.append(QPixmap(FrameSize[0], FrameSize[1]).toImage())
        
        if not saveindividualy:
            CorrectPanel = QImage(PanelSize[0], PanelSize[1], QImage.Format.Format_ARGB32)

            painter = QPainter(CorrectPanel)
            painter.drawImage(0, 0, imgs[0])
            painter.drawImage(FrameSize[0], 0, imgs[1])
            painter.drawImage(0, FrameSize[1], imgs[2])
            painter.drawImage(FrameSize[0], FrameSize[1], imgs[3])
            painter.end()

            self.SavePanel(CorrectPanel)
        else:
            self.SaveTilesIndividually(imgs)
        
    def SavePanel(self, PanelQImage):
        TargetFileFormat = self.Cmb_FinFileFormat.currentText()
        TargetFileFolder = self.Txt_SelTargetFolder.text()
        TargetFileName = self.Txt_SaveName.text()
        PanelQImage.save(TargetFileFolder + "\\" + TargetFileName + TargetFileFormat)
    
    def SaveTilesIndividually(self, Tiles = None):
        if Tiles == None: return False
        TargetFileFormat = self.Cmb_FinFileFormat.currentText()
        TargetFileFolder = self.Txt_SelTargetFolder.text()
        TargetFileBaseName = self.Txt_SaveName.text()
        TargetFileName = ""

        for i in range(len(Tiles)):
            if TargetFileName == "": 
                TargetFileName = self.get_solid_filename(TargetFileFolder, TargetFileBaseName + "_", TargetFileFormat)
                if TargetFileName[-1] == "_": TargetFileName = TargetFileName + "1"
            TargetFileName = self.get_solid_filename(TargetFileFolder, TargetFileName, TargetFileFormat)
            if not TargetFileName: return False
            Tiles[i].save(os.path.join(TargetFileFolder, TargetFileName + TargetFileFormat))

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
                lastIncrement = re.search(r"(\_|\-)\d+$", basename)
                if not lastIncrement == None:
                    lastIncrement = lastIncrement.group(0)
                    basename = basename[:-len(lastIncrement)]
                    incrementer = int(lastIncrement.replace("_", "").replace("-", ""))
                while os.path.exists(os.path.join(folder, basename + "_" + str(incrementer)  + fileformat)):
                    incrementer += 1
                return basename + "_" + str(incrementer)
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
            self.userIsInputting = False  # Change to true to make things crash
            self.LimitTextToInt(sender)   # limits the input to numbers            
            match sender:                
                case self.Txt_TilePixelSizeX:
                    self.Txt_TotalPixelSizeX.setText(str(good_int(self.Txt_TilePixelSizeX.text()) * 2))
                    if self.Checkb_LinkXY.isChecked():
                        self.Txt_TilePixelSizeY.setText(str(good_int(int(self.Txt_TilePixelSizeX.text()) / self.Var_TilePixelSizeRatio)))
                        self.Txt_TotalPixelSizeY.setText(str(good_int(self.Txt_TilePixelSizeY.text()) * 2))
                case self.Txt_TilePixelSizeY:
                    self.Txt_TotalPixelSizeY.setText(str(good_int(self.Txt_TilePixelSizeY.text()) * 2))
                    if self.Checkb_LinkXY.isChecked():
                        self.Txt_TilePixelSizeX.setText(str(good_int(int(self.Txt_TilePixelSizeY.text()) * self.Var_TilePixelSizeRatio)))
                        self.Txt_TotalPixelSizeX.setText(str(good_int(float(self.Txt_TilePixelSizeX.text()) * 2)))
                case self.Txt_TotalPixelSizeX:
                    self.Txt_TilePixelSizeX.setText(str(good_int(int(self.Txt_TotalPixelSizeX.text()) / 2)))
                    if self.Checkb_LinkXY.isChecked():
                        self.Txt_TilePixelSizeY.setText(str(good_int(int(self.Txt_TilePixelSizeX.text()) / self.Var_TilePixelSizeRatio)))
                        self.Txt_TotalPixelSizeY.setText(str(good_int(int(self.Txt_TilePixelSizeY.text()) * 2)))
                case self.Txt_TotalPixelSizeY:
                    self.Txt_TilePixelSizeY.setText(str(good_int(int(self.Txt_TotalPixelSizeY.text()) / 2)))
                    if self.Checkb_LinkXY.isChecked():
                        self.Txt_TilePixelSizeX.setText(str(good_int(int(self.Txt_TilePixelSizeY.text()) * self.Var_TilePixelSizeRatio)))
                        self.Txt_TotalPixelSizeX.setText(str(good_int(int(self.Txt_TilePixelSizeX.text()) * 2)))
            if not float(self.Txt_TilePixelSizeY.text()) == 0:
                self.Var_TilePixelSizeRatio = float(self.Txt_TilePixelSizeX.text()) / float(self.Txt_TilePixelSizeY.text())
            self.ApplyPixelSize()
            self.userIsInputting = True

    def closeEvent(self, event):
        SaveDic = {}
        SaveDic["Var_TilePixelSizeRatio"] = self.Var_TilePixelSizeRatio
        SaveDic["Txt_TilePixelSizeX"] = self.Txt_TilePixelSizeX.text()
        SaveDic["Txt_TilePixelSizeY"] = self.Txt_TilePixelSizeY.text()
        SaveDic["Txt_CurPanelPreviewZoom"] = self.Txt_CurPanelPreviewZoom.text()
        SaveDic["Checkb_LinkXY"] = self.Checkb_LinkXY.isChecked()
        SaveDic["Txt_SelSourceFolder"] = self.Txt_SelSourceFolder.text()
        SaveDic["Txt_SelTargetFolder"] = self.Txt_SelTargetFolder.text()
        SaveDic["Txt_SaveName"] = self.Txt_SaveName.text()
        SaveDic["Checkb_FinAutoIncrease"] = self.Checkb_FinAutoIncrease.isChecked()
        SaveDic["Cmb_FinFileFormat"] = self.Cmb_FinFileFormat.currentIndex()
        SaveDic["Txt_SaveName"] = self.Txt_SaveName.text()
        self.save_SaveDic(SaveDic)

    def save_SaveDic(self, SaveDic):     
        print(f"Save as " + os.path.join(os.path.dirname(sys.argv[0]), "ImageTileConverterSave.json"))
        savepath = os.path.join(os.path.dirname(sys.argv[0]), "ImageTileConverterSave.json")
        if os.path.exists(savepath):
            os.remove(savepath)
        with open(savepath, "w") as f:
            json.dump(SaveDic, f)
            f.close()
        win32api.SetFileAttributes(savepath,win32con.FILE_ATTRIBUTE_HIDDEN)

    def load_SaveDic(self):   
        print(f"Load as " + os.path.join(os.path.dirname(sys.argv[0]), "ImageTileConverterSave.json"))    
        loadpath = os.path.join(os.path.dirname(sys.argv[0]), "ImageTileConverterSave.json")
        if os.path.exists(loadpath):            
            with open(loadpath, "r") as f:
                SaveDic = json.load(f)
                f.close()
            self.Var_TilePixelSizeRatio = SaveDic["Var_TilePixelSizeRatio"]
            self.Txt_TilePixelSizeX.setText(SaveDic["Txt_TilePixelSizeX"])
            self.Txt_TilePixelSizeY.setText(SaveDic["Txt_TilePixelSizeY"])
            self.Txt_CurPanelPreviewZoom.setText(SaveDic["Txt_CurPanelPreviewZoom"])
            self.Checkb_LinkXY.setChecked(SaveDic["Checkb_LinkXY"])
            self.Txt_SelSourceFolder.setText(SaveDic["Txt_SelSourceFolder"])
            self.Txt_SelTargetFolder.setText(SaveDic["Txt_SelTargetFolder"])
            self.Txt_SaveName.setText(SaveDic["Txt_SaveName"])
            self.Checkb_FinAutoIncrease.setChecked(SaveDic["Checkb_FinAutoIncrease"])
            self.Cmb_FinFileFormat.setCurrentIndex(SaveDic["Cmb_FinFileFormat"])
            self.Txt_SaveName.setText(SaveDic["Txt_SaveName"])
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

