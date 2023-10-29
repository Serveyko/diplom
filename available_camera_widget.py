from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from available_camera import Ui_Form as AvailableCameraWidgetImport
from available_camera_gen_idx import available_camera_gen_idx_elem

class AvailableCameraWidget(QWidget, AvailableCameraWidgetImport):
    """Віджет контролю який дає можливість контролювати камеру яка була знайдена

    Args:
        QWidget (_type_): _description_
        AvailableCameraWidgetImport (_type_): _description_

    Returns:
        _type_: _description_
    """
    deleteWidgetSignal = pyqtSignal(int)
    createWidgetSignal = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.current_id = available_camera_gen_idx_elem.get_uid()
        self.index = -1
        self.name = "Camera"
        self.checkBox.setChecked(True)
    
        self.checkBox.clicked.connect(self.on_checkbox_clicked)

    def on_checkbox_clicked(self, checked):
        if checked:
            self.createWidgetSignal.emit(self.index)
        else:
            self.deleteWidgetSignal.emit(self.index)
    
    def set_index(self, index):
        self.index = index 
        self.label.setText(self.name + f" {self.index}")
    
    def get_index(self):
        return self.index