#ruff: noqa: E501
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication, QScrollArea
from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal
from plot_entity import PlotEntity
from framework import Entity
from db import HumanDB
import cv2
from functions import overlay_image_on_black_bg, time_time_to_formatted_time
from PyQt5.QtWidgets import QMessageBox

          
class ImageDisplayWidget(QWidget):
    imageClosed = pyqtSignal()

    def __init__(self, image_arrays, parent=None):
        super().__init__(parent)
        self.screen_full = QApplication.desktop().screenGeometry()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.close_button = QPushButton("Закрити")
        self.next_button = QPushButton("Наступне")
        self.prev_button = QPushButton("Попереднє")
        self.image_arrays = image_arrays
        self.current_image_index = 0
        self.init_ui()

    def init_ui(self):
        # Основний лейаут для розміщення зображення та кнопок
        main_layout = QVBoxLayout()

        # Лейаут для зображення та встановлення прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)

        # Додавання зображення до лейауту з прокруткою
        scroll_layout.addWidget(self.image_label)

        # Лейаут для кнопок
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.close_button)
        button_layout.addWidget(self.next_button)

        # Додавання лейауту з кнопками до основного лейауту
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)

        # Встановлення основного лейауту для вікна
        self.setLayout(main_layout)

        self.setGeometry(0, 0, self.screen_full.width() - 100, self.screen_full.height() - 100)
        self.close_button.clicked.connect(self.close)
        self.next_button.clicked.connect(self.next_image)
        self.prev_button.clicked.connect(self.previous_image)
        self.setStyleSheet("background-color: #808080")

        self.show_image()

    def show_image(self):
        if self.image_arrays and 0 <= self.current_image_index < len(self.image_arrays):
            image_array = self.image_arrays[self.current_image_index]
            if image_array is not None:
                screen_width = self.screen_full.width() - 100
                screen_height = self.screen_full.height() - 100
                if isinstance(image_array, str):
                    image_array = cv2.imread(image_array)
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
                image_array = overlay_image_on_black_bg(image_array, screen_width, screen_height)
                scaled_pixmap = QPixmap.fromImage(
                    QImage(
                        image_array.data,
                        image_array.shape[1],
                        image_array.shape[0],
                        QImage.Format_RGB888
                    )
                ).scaled(
                    screen_width,
                    screen_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)

    def next_image(self):
        if self.image_arrays:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_arrays)
            self.show_image()

    def previous_image(self):
        if self.image_arrays:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_arrays)
            self.show_image()

    def on_image_closed(self):
        self.image_shown = False
        self.imageClosed.emit()



class HoverLabel(QLabel):
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

class CustomWidgetSingleHumanCapacitor:
    def __init__(self):
        self.already_created_index = {} 
    
    def get_uid(self):
        new_idx = len(self.already_created_index)
        key = (new_idx)
        self.already_created_index[key] = new_idx
        return new_idx

custom_widget_single_human_capacitor = CustomWidgetSingleHumanCapacitor()

class CustomWidgetSingleHuman(QWidget):
    
    delete_signal = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.plot_human = None
        self.time_current = None
        self.current_id = custom_widget_single_human_capacitor.get_uid()
    
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

        self.image_label1 = HoverLabel()
        self.image_label1.setText("Фото обличчя")
        layout.addWidget(self.image_label1)

        self.image_label2 = HoverLabel()
        self.image_label2.setText("Фото із камери")
        layout.addWidget(self.image_label2)

        self.delete_button = QPushButton("Видалити")
        self.delete_button.setMinimumSize(50, 50)
        layout.addWidget(self.delete_button)
        
        self.setLayout(layout)
        self.setFixedHeight(60)
        self.setStyleSheet("background-color: #808080; border: 2px solid gray;")
        
        self.delete_button.clicked.connect(self.delete_button_clicked)

    def delete_button_clicked(self):
        reply = QMessageBox.question(self, 'Підтвердження видалення', 'Ви впевнені, що хочете видалити ?', 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.delete_signal.emit(self.current_id)
    
    def push_plot_human(self, plot_human):
        self.plot_human = plot_human
        self.update_images()
    
    def update_images(self):
        if self.plot_human is not None and isinstance(self.plot_human, PlotEntity):
            pass 
            self.set_time(self.plot_human.time_create)
            entities = self.plot_human.get_entities()
            f_text = ""
            if len(entities) > 0:
                for si in entities:
                    if isinstance(si, Entity):
                        f_text += str(si.current_id)
            else:
                f_text = str(self.plot_human.current_id)
            
            if self.plot_human.get_human_db() is not None:
                if f_text == "":
                    f_text = self.plot_human.get_human_db().name
                else:
                    f_text = self.plot_human.get_human_db().name + " " + f_text
            
            self.set_text(f_text)
            all_e_images = []
            
            for si in entities:
                if isinstance(si, Entity):
                    all_e_images.extend(si.get_all_images())
            
            all_f_images = []
            if self.plot_human.get_human_db() is not None:
                hdb = self.plot_human.get_human_db()
                if isinstance(hdb, HumanDB):
                    all_f_images = hdb.images_face
            
            self.set_images(all_f_images, all_e_images)
    
    def get_plot_human(self):
        return self.plot_human
    
    def set_time(self, time_current, convert=True):
        self.time_current = time_current
        if convert is True:
            self.time_label.setText(time_time_to_formatted_time(time_current))
        else:
            self.time_label.setText(time_current)
    
    def set_text(self, text):
        self.text_label.setText(text)

    def set_images(self, images1, images2):
        self.image_label1.set_image_array(images1)
        self.image_label2.set_image_array(images2)
