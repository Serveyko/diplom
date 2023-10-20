#ruff: noqa: E501
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QListWidgetItem, QLabel, QHBoxLayout, QFileDialog  # noqa: E501
from PyQt5.QtWidgets import QMessageBox, QScrollArea
from PyQt5.QtGui import QImage
from create_human_ui import Ui_Form
from deepface import DeepFace
import cv2
from functions import overlay_image_on_black_bg

          
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

class CreateHumanView(QWidget, Ui_Form):
    image_push = pyqtSignal(list, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        # Встановлюємо стиль для вікна
        self.setWindowFlags(Qt.Dialog)  # або Qt.Dialog, якщо потрібно модальне вікно
        self.setWindowFlag(Qt.FramelessWindowHint, False)  # Забираємо відсутність рамок

        self.toolButton.clicked.connect(self.add_images)
        
        self.image_paths = [] 
        
        self.done_Button.clicked.connect(self.done_process)
    
    def done_process(self):
        if len(self.image_paths) > 0:
            for i, spath in enumerate(self.image_paths):
                obj_find = None
                
                try:
                    image = cv2.imread(spath)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    self.image_paths[i] = image
                    obj_find = DeepFace.extract_faces(  # noqa: F841
                        image, 
                        detector_backend = 'retinaface'
                    )
                    pass
                except Exception as ex:
                    if spath is not None:
                        #image_display = ImageDisplayWidget(spath, self)
                        #image_display.show()
                        pass 
                    
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Information)
                    msg_box.setText("На зображенні немає обличчя.")
                    msg_box.setInformativeText(f"Шлях до зображення: {spath}")
                    msg_box.setWindowTitle("Інформація")
                    msg_box.exec_()
                    print(str(ex))
                    
            self.image_push.emit(list(self.image_paths), str(self.lineEdit.text()))
        
        self.image_paths = []
        self.listWidget.clear()
        self.lineEdit.clear() 
        self.close()
        
    
    def closeEvent(self, event):
        super().closeEvent(event)

    def add_images(self):
        # Діалогове вікно для вибору файлів
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                self.image_paths.append(file_path)

                # Створення віджета, який включає кнопку "Видалити" і лейбл для відображення шляху  # noqa: E501
                item_widget = QWidget()
                item_layout = QHBoxLayout()
                remove_button = QPushButton("Видалити")
                remove_button.clicked.connect(self.remove_image)
                label = QLabel(file_path)  # Відображення шляху
                item_layout.addWidget(remove_button)
                item_layout.addWidget(label)
                item_widget.setLayout(item_layout)

                # Визначення розміру кнопки на основі її тексту
                button_size = remove_button.sizeHint()
                remove_button.setFixedWidth(button_size.width())

                # Додавання віджета до списку
                item = QListWidgetItem(self.listWidget)
                item.setSizeHint(item_widget.sizeHint())  # Задаємо розмір віджета
                self.listWidget.setItemWidget(item, item_widget)
                self.listWidget.addItem(item)

    def remove_image(self):
        button = self.sender()  # Отримати кнопку, яка була натиснута
        if button:
            item = self.listWidget.itemAt(button.pos())  # Отримати елемент списку, якому належить кнопка  # noqa: E501
            if item:
                index = self.listWidget.row(item)
                del self.image_paths[index]
                self.listWidget.takeItem(index)


