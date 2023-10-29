from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy  # noqa: E501
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal
import time
from functions import time_time_to_formatted_time

class ImageDisplayWidget(QWidget):
    """Віджет зображень

    Args:
        QWidget (_type_): _description_
    """
    imageClosed = pyqtSignal()

    def __init__(self, image_array, parent=None):
        super().__init__(parent)
        self.screen_full = QApplication.desktop().screenGeometry()
        self.image_label = QLabel()
        self.close_button = QPushButton("Закрити")
        self.image_array = image_array
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.show_image()
        
        spacer_left = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacer_right = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.close_button.setStyleSheet("background-color: white;")
        
        button_layout = QHBoxLayout()
        button_layout.addItem(spacer_left)
        button_layout.addWidget(self.close_button)
        button_layout.addItem(spacer_right)
        
        layout.addWidget(self.image_label)
        #layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.setGeometry(0, 0, self.screen_full.width(), self.screen_full.height())
        self.close_button.clicked.connect(self.close)
        self.setStyleSheet("background-color: #808080;")

    def show_image(self):
        if self.image_array is not None:
            screen_width = self.screen_full.width()
            screen_height = self.screen_full.height()
            scaled_pixmap = QPixmap.fromImage(
                QImage(
                    self.image_array.data,
                    self.image_array.shape[1],
                    self.image_array.shape[0],
                    QImage.Format_RGB888
                )
            ).scaled(
                screen_width,
                screen_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def on_image_closed(self):
        self.image_shown = False
        self.imageClosed.emit()


class HoverLabel(QLabel):
    """Лейб який реалізовує показ зображення при натиску на нього

    Args:
        QLabel (_type_): _description_
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(50, 50)
        self.setAlignment(Qt.AlignCenter)
        self.setMouseTracking(True)
        self.image_shown = False
        self.image_array = None
        self.my_text = ""
        self.setStyleSheet("background-color: green;")

    def mousePressEvent(self, event):
        if not self.image_shown:
            self.show_image()
            self.image_shown = True
        else:
            self.hide_image()
            self.image_shown = False

    def set_image_array(self, image_array):
        self.image_array = image_array

    def show_image(self):
        self.my_text = self.text()
        if self.image_array is not None:
            self.image_display = ImageDisplayWidget(self.image_array)
            self.image_display.imageClosed.connect(self.on_image_closed)
            self.image_display.showFullScreen()

    def hide_image(self):
        self.clear()
        self.setText(self.my_text)

    def on_image_closed(self):
        self.image_shown = False


class CustomWidgetSingleLog(QWidget):
    """Реалізує віджет строку логу що візуально показується користувачеві

    Args:
        QWidget (_type_): _description_
    """
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.uid_log = None
        self.time_create = time.time()
        
    def init_ui(self):
        layout = QHBoxLayout()
        self.time_label = QLabel()
        self.time_label.setMinimumSize(50, 50)
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        self.text_label = QLabel()
        self.text_label.setMinimumSize(50, 50)
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)
        
        self.info_label = QLabel()
        self.info_label.setMinimumSize(50, 50)
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        self.image_label1 = HoverLabel()
        self.image_label1.setText("Human")
        layout.addWidget(self.image_label1)
        self.image_label2 = HoverLabel()
        self.image_label2.setText("Bag")
        layout.addWidget(self.image_label2)
        self.setLayout(layout)
        self.setFixedHeight(60)
        self.setStyleSheet("background-color: #808080; border: 2px solid gray;")
    
    def set_time(self, time_current, convert=True):
        if convert is True:
            self.time_label.setText(time_time_to_formatted_time(time_current))
        else:
            self.time_label.setText(time_current)
    
    def set_info(self, text):
        self.info_label.setText(text)
        
    def set_text(self, text):
        self.text_label.setText(text)

    def set_images(self, image1, image2):
        self.image_label1.set_image_array(image1)
        self.image_label2.set_image_array(image2)


