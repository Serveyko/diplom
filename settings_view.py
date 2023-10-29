#ruff: noqa: E501

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

from Settings_ui import Ui_Settings as Settings_ui_Form

from db import load_all_params_settings, session, params_dict, save_one_params_settings, Parameter

from PyQt5.QtWidgets import QLabel, QLineEdit, QHBoxLayout

class ParamWidget(QWidget):
    """Віджет параметру який показує параметер і обробляє різні типи параметрів

    Args:
        QWidget (_type_): _description_
    """
    def __init__(self, parent=None):
        super(ParamWidget, self).__init__(parent)
        self.label = QLabel(self)
        self.text_edit = QLineEdit(self)
        spacer = QWidget()  # Спейсер
        spacer.setFixedWidth(10)  # Ширина спейсера
        
        # Обчислюємо половину ширини батьківського компонента
        parent_width = self.parent().width()
        half_width = parent_width // 2
        
        # Встановлюємо ширину для лейбла і текстового поля
        self.label.setFixedWidth(half_width)
        self.text_edit.setFixedWidth(half_width)
        
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(spacer)  # Додаємо спейсер
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        
        self.text_input_int = False
        self.text_input_float = False
        self.text_input_bool = False
        
        self.original_value = None
    
    def set_values(self, label_text, text_text, original_value):
        self.original_value = original_value
        
        if isinstance(text_text, int):
            self.text_input_int = True
        elif isinstance(text_text, float):
            self.text_input_float = True
        elif isinstance(text_text, bool):
            self.text_input_bool = True
            
        self.label.setText(str(label_text))
        self.text_edit.setText(str(text_text))
    
    def get_values(self):
        val = None
        if self.text_input_int is True:
            val = int(self.text_edit.text()) 
        elif self.text_input_float is True:
            val = float(self.text_edit.text())
        elif self.text_input_bool is True: 
            val = bool(True if self.text_edit.text() == "True" or self.text_edit.text() == "true" else False)
        else:
            val = str(self.text_edit.text())
        
        if val is None:
            val = self.original_value
        
        return (self.label.text(), val)

class SettingsView(QWidget, Settings_ui_Form):
    """Віджет налаштувань який створює вікно в якому можна налаштовувати різні параметри

    Args:
        QWidget (_type_): _description_
        Settings_ui_Form (_type_): _description_
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        # Встановлюємо стиль для вікна
        self.setWindowFlags(Qt.Window)  # або Qt.Dialog, якщо потрібно модальне вікно
        self.setWindowFlag(Qt.FramelessWindowHint, False)  # Забираємо відсутність рамок
        self.save_settings.clicked.connect(self.func_save_settings)
        self.reset_settings.clicked.connect(self.func_reset_settings)
    
    def func_reset_settings(self):
        loaded_params = load_all_params_settings(session, params_dict)
        for sparam in loaded_params:
            if isinstance(sparam, Parameter):
                sparam.current_value = sparam.original_value
                save_one_params_settings(session, sparam.name, sparam.original_value, sparam.current_value)
                pass
        
        widgets = []
        for i in range(self.verticalLayout.count()):
            item = self.verticalLayout.itemAt(i)
            widget = item.widget()
            if widget:
                widgets.append(widget)

        while self.verticalLayout.count():
            item = self.verticalLayout.takeAt(0)

        for sparam in loaded_params:
            if isinstance(sparam, Parameter):
                pm = ParamWidget(self)
                pm.set_values(sparam.name, sparam.current_value, sparam.original_value)
                self.verticalLayout.addWidget(pm)
        
        self.func_save_settings()
    
    def func_save_settings(self):
        widgets = []
        for i in range(self.verticalLayout.count()):
            item = self.verticalLayout.itemAt(i)
            widget = item.widget()
            if widget:
                widgets.append(widget)
        loaded_params = load_all_params_settings(session, params_dict)
        for pm in widgets:
            if isinstance(pm, ParamWidget):
                label_name, edited_value = pm.get_values()
                finded = False
                sparam_finded = None
                for sparam in loaded_params:
                    if isinstance(sparam, Parameter):
                        if sparam.name == label_name:
                            sparam.current_value = edited_value
                            finded = True 
                            sparam_finded = sparam
                            break
                if finded is True:
                    save_one_params_settings(session, label_name, sparam_finded.original_value, edited_value)
                pass
    
    def showEvent(self, event):
        super().showEvent(event)
        loaded_params = load_all_params_settings(session, params_dict)
        
        widgets = []
        for i in range(self.verticalLayout.count()):
            item = self.verticalLayout.itemAt(i)
            widget = item.widget()
            if widget:
                widgets.append(widget)

        while self.verticalLayout.count():
            item = self.verticalLayout.takeAt(0)

        for sparam in loaded_params:
            if isinstance(sparam, Parameter):
                pm = ParamWidget(self)
                pm.set_values(sparam.name, sparam.current_value, sparam.original_value)
                self.verticalLayout.addWidget(pm)
    
    def closeEvent(self, event):
        super().closeEvent(event)
        
