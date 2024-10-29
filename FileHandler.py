import re
import os
from PySide6.QtWidgets import QFileDialog

class xfilelist:
    def __init__(self, initxfiles = [], initfolder = ""):
        self.filelist = []
        self.filelist = self.filelist + get_files_of_folder(initfolder)
        for item in initxfiles:
            self.filelist.append(item)

    def __getitem__(self, index):
        return str(self.filelist[index])
    def GetRealItem(self, index):
        return self.filelist[index]
    def __len__(self):
        return len(self.filelist)
    def append(self, item):
        self.filelist.append(item)
    
class xfile:
    def __init__(self, root, name):  
        if os.path.exists(os.path.join(root,name)):      
            self.root = root
            self.name = name
            self.fullname = os.path.join(root, name)
            self.format = re.search(r"\.[a-z]{1,4}$", name).group()
        else:
            return False
    def __repr__(self):
        return self.name

def select_folder():
    filename = QFileDialog.getExistingDirectory(caption="Select directory", options=QFileDialog.Option.DontUseNativeDialog)
    return filename   #Returns None if invalid?
    


def get_files_of_folder(folder_path, filter = ""):
    # Code to get all files in a folder
    filelist = []
    if os.path.exists(folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if filter == "" or filter in file:
                    filelist.append(xfile(root, file))
    return filelist