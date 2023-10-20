from datetime import datetime

global_id_frame_data = 0

def get_new_id_frame_data():
    global global_id_frame_data
    c = global_id_frame_data
    global_id_frame_data += 1
    return c

class FrameData:
    def __init__(self) -> None:
        self.id_worker = -1
        self.name = ""
        self.data = {}
        self.other_data = None
        self.timestamp = None
        self.yolov8 = None
        self.index_name_yolov8 = None
        self.retinaface = None
        self.real_frame = None
        self.dataframe_uid = 0
        self.logs = None
        self.humans_and_bags = None
        self.array_all_humans_and_bags = None
        self.entities = None
        
        
    def set_frame(self, data):
        self.data=data
        now = datetime.now()
        self.timestamp = datetime.timestamp(now)
        
    def get_frame(self):
        return self.data

    def set_data(self, data):
        self.other_data = data
    
    def get_data(self):
        return self.other_data


