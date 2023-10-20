from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
import cv2

from camera_widget import Ui_Form as CameraWidgetImport
from frame_data import FrameData, get_new_id_frame_data
from functions import resize_with_aspect_ratio
from finder import find as find_humans

from config import timeout_widget, standart_width, standart_height
from function_caller_thread import FunctionCallerThread

class CameraWidgetView(QWidget, CameraWidgetImport):
    
    frame_data = pyqtSignal(FrameData)
    
    def __init__(self, inid):
        super().__init__()
        self.setupUi(self) 
        self.current_id = inid
        self.index_camera = -1
        self.is_file = False
        self.standart_width = standart_width
        self.standart_height = standart_height
        
        self.dataframe_uid = get_new_id_frame_data()

    def create_connect_online(self, index_camera):
        self.index_camera = index_camera
        self.camera = cv2.VideoCapture(index_camera)
        
        self.pt_time = FunctionCallerThread(self.update_frame)
        self.pt_time.set_time_interval(timeout_widget)
        self.pt_time.start()
        
        self.label_2.setText(f"Camera: {self.index_camera}")
    
    def update_frame(self):
        with self.pt_time:
            ret, frame = self.camera.read()
            if ret:
                try:
                    processed_frame = frame
                    fr = FrameData()
                    fr.dataframe_uid = self.dataframe_uid
                    fr.set_frame(processed_frame)
                    fr = find_humans(fr)
                    processed_frame = fr.get_frame()
                    processed_frame = resize_with_aspect_ratio(
                        processed_frame, 
                        new_width=self.standart_width
                    )

                    h, w, ch = processed_frame.shape
                    bytes_per_line = ch * w
                    processed_qimg = QImage(
                        processed_frame.data, 
                        w, 
                        h, 
                        bytes_per_line, 
                        QImage.Format_RGB888
                    )
                    self.label.setPixmap(QPixmap.fromImage(processed_qimg))
                    
                    fr.id_worker = self.current_id
                    
                    self.frame_data.emit(fr)
                    
                except Exception as ex:
                    print(ex)    
                    
                self.pt_time.set_time_interval(timeout_widget)
            
            
    def closeEvent(self, event):
        self.camera.release()
        self.pt_time.stop()
        #self.pt_time.quit()
        #self.pt_time.wait()
        event.accept()
        
