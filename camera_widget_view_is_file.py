from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
import cv2
from frame_data import FrameData, get_new_id_frame_data
from camera_widget_is_file_ui import Ui_Form as CameraWidgetIsFileImport
from functions import resize_with_aspect_ratio
from finder import find as find_humans

from config import standart_height, standart_width, timeout_is_file_widget

from function_caller_thread import FunctionCallerThread

from functions import print_exception_info

class CameraWidgetViewIsFile(QWidget, CameraWidgetIsFileImport):
    frame_data = pyqtSignal(FrameData)
    
    def __init__(self, inid):
        super().__init__()
        self.setupUi(self) 
        self.current_id = inid
        self.file_path = ""
        self.is_file = True
        self.is_looping = True
        self.show_processing_result = True
        self.standart_width = standart_width
        self.standart_height = standart_height
        
        self.dataframe_uid = get_new_id_frame_data()

    def create_file_stream(self, file_path, loop=True):
        self.file_path = file_path
        self.video_stream = cv2.VideoCapture(file_path)
        
        self.pt_time = FunctionCallerThread(self.update_frame)
        self.pt_time.set_time_interval(timeout_is_file_widget)
        self.pt_time.start()
        
        self.is_looping = loop
        self.label_2.setText(self.file_path)
    
    def update_frame(self):
        with self.pt_time:
            ret, frame = self.video_stream.read()
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
                    print_exception_info(ex)
                    
                self.pt_time.set_time_interval(timeout_is_file_widget)
            else:
                if self.is_looping:
                    self.video_stream.set(cv2.CAP_PROP_POS_FRAMES, 0)  
                else:
                    self.pt_time.stop()
            
    
    def update_show_processing_result(self, show_processing_result_state):
        self.show_processing_result = show_processing_result_state
    
    def update_loop(self, loop_state):
        #before = self.is_looping
        self.is_looping = loop_state
        """if before is False and self.is_looping is True:
            self.video_stream.set(cv2.CAP_PROP_POS_FRAMES, 0)

            self.pt_time.set_time_interval(timeout_is_file_widget)
            self.pt_time.start()
            
        elif before is True and self.is_looping is False:

            self.pt_time.stop()"""
    
    def stop(self):
        try:
            self.video_stream.release()

            self.pt_time.stop()
        except Exception as ex:
            print(str(ex))
        
    def closeEvent(self, event):
        self.stop()
        event.accept()
