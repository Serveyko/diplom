#ruff: noqa: E501
import cv2
import numpy as np
import traceback
from datetime import datetime

def find_all_cameras():
    """Функція пошуку камер на компютері

    Returns:
        _type_: _description_
    """
    index = 0
    all_cameras = []

    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            break

        all_cameras.append(index)
        cap.release()
        index += 1

    return all_cameras

def resize_with_aspect_ratio(image, new_width=None, new_height=None):
    """Отримує зображення і змінює йому розмір пропорційно невказаній одиниці висоті або ширині відповідно до вказаних
    але підтримує тільки вказування або тільки ширини нової або висоти нової

    Args:
        image (_type_): _description_
        new_width (_type_, optional): _description_. Defaults to None.
        new_height (_type_, optional): _description_. Defaults to None.

    Raises:
        ValueError: _description_
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    if new_width is None and new_height is None:
        raise ValueError(
            "At least one of 'new_width' or 'new_height' must be provided."
        )
    
    height, width = image.shape[:2]
    if new_width is not None and new_height is None:
        aspect_ratio = new_width / width
        new_height = int(height * aspect_ratio)
    elif new_height is not None and new_width is None:
        aspect_ratio = new_height / height
        new_width = int(width * aspect_ratio)
    else:
        raise ValueError("Only one of 'new_width' or 'new_height' should be provided.")
    
    resized_image = cv2.resize(image, (new_width, new_height))
    return resized_image

def get_object_names_with_indices(class_indices, class_names):
    """По індексах отримує необхідне значення

    Args:
        class_indices (_type_): _description_
        class_names (_type_): _description_

    Returns:
        _type_: _description_
    """
    result = []
    for i, index in enumerate(class_indices):
        class_name = class_names.get(int(index), 'Unknown')
        result.append((int(index), class_name))
    return result

    
def overlay_image_on_black_bg(overlay, bg_width, bg_height):
    """Накладає зображення на чорний фон при вказаній ширині і висоті фону

    Args:
        overlay (_type_): _description_
        bg_width (_type_): _description_
        bg_height (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Створення чорного фону з вказаними розмірами
    black_background = np.zeros((bg_height, bg_width, 3), dtype=np.uint8)

    # Розрахунок розмірів накладеного зображення
    overlay_height, overlay_width, _ = overlay.shape

    # Розрахунок координат для розміщення накладеного зображення у центрі фону
    x_pos = (bg_width - overlay_width) // 2
    y_pos = (bg_height - overlay_height) // 2

    # Перевірка, чи накладене зображення виходить за межі фону і зменшення розміру, якщо потрібно
    if x_pos < 0 or y_pos < 0:
        # Обираємо той параметр, який змінює розмір так, щоб він вміщався у фон
        if overlay_width > overlay_height:
            overlay = resize_with_aspect_ratio(overlay, new_width=bg_width)
        else:
            overlay = resize_with_aspect_ratio(overlay, new_height=bg_height)

        overlay_height, overlay_width, _ = overlay.shape
        x_pos = (bg_width - overlay_width) // 2
        y_pos = (bg_height - overlay_height) // 2

    x_end = x_pos + overlay_width
    y_end = y_pos + overlay_height

    black_background[y_pos:y_end, x_pos:x_end] = overlay
    return black_background



def print_exception_info(ex):
    """Зручно виводить помилку

    Args:
        ex (_type_): _description_
    """
    if isinstance(ex, Exception):
        # Отримуємо всю інформацію про виняток, включаючи рядок та повідомлення
        exception_type = type(ex).__name__  # Тип винятка
        exception_message = str(ex)  # Повідомлення про виняток
        exception_traceback = ex.__traceback__  # Об'єкт відстеження виклику (рядок)

        # Друкуємо інформацію
        print(f"Тип винятка: {exception_type}")
        print(f"Повідомлення про виняток: {exception_message}")

        # Друкуємо рядок та позицію де виник виняток
        tb_info = traceback.extract_tb(exception_traceback)
        if tb_info:
            file_name, line_num, func_name, text = tb_info[-1]  # Беремо інформацію з останнього виклику
            print(f"Виняток виник в файлі '{file_name}', рядок {line_num}, функція '{func_name}'")
            print(f"Код, який викликав виняток: {text}")
    else:
        print("Вхідний об'єкт не є об'єктом Exception")

def time_time_to_formatted_time(timestamp):
    """Конвертує мітку часу в зручний формат який можна прочитати

    Args:
        timestamp (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Перетворюємо час з секунд у об'єкт datetime
    datetime_obj = datetime.fromtimestamp(timestamp)

    # Форматуємо об'єкт datetime у зручний вигляд
    formatted_time = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    
    return formatted_time
