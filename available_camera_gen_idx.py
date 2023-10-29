
from framework import QMutexContextManager

class AvailableCameraGenIdx:
    """Дає індекси і зберігає їх для контролеру камер і потоків із файлів
    """
    def __init__(self):
        self.locker = QMutexContextManager()
        self.already_created_index = {}
        
    def get_uid(self):
        with self.locker:
            new_idx = len(self.already_created_index)
            key = (new_idx)
            self.already_created_index[key] = new_idx
            return new_idx
    

available_camera_gen_idx_elem = AvailableCameraGenIdx()

