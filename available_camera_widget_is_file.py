from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from available_camera_is_file import Ui_Form as AvailableCameraIsFileWidgetImport

from available_camera_gen_idx import available_camera_gen_idx_elem

class AvailableCameraWidgetIsFile(QWidget, AvailableCameraIsFileWidgetImport):
    """Віджет контролю відео із файлу і його обробку а також зациклення

    Args:
        QWidget (_type_): _description_
        AvailableCameraIsFileWidgetImport (_type_): _description_

    Returns:
        _type_: _description_
    """
    deleteWidgetSignal = pyqtSignal(str)
    createWidgetSignal = pyqtSignal(str)

    loop_Signal = pyqtSignal(str, bool)
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.current_id = available_camera_gen_idx_elem.get_uid()
        self.file_path = ""
        self.checkBox.setChecked(True)
    
        self.checkBox.clicked.connect(self.on_checkbox_work_clicked)
        
        self.checkBox_3.setChecked(True)
        self.checkBox_3.clicked.connect(self.on_checkbox_loop)
        
    def on_checkbox_loop(self, checked):
        if checked:
            self.loop_Signal.emit(self.file_path, checked)
        else:
            self.loop_Signal.emit(self.file_path, checked)
    
    def on_checkbox_work_clicked(self, checked):
        if checked:
            self.createWidgetSignal.emit(self.file_path)
        else:
            self.deleteWidgetSignal.emit(self.file_path)
    
    def set_filepath(self, file_path):
        self.file_path = file_path 
        self.label.setText(f"{self.file_path}")
    
    def get_filepath(self):
        return self.file_path