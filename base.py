from frame_data import FrameData


class FrameDataContainer:
    def __init__(self) -> None:
        self.containers = {}
    
    def find(self, inid):
        if inid in self.containers.keys():
            return True
        return False
    
    def get(self, inid=None, max_count=1):
        arr_frames = []
        if inid is not None:
            if self.find(inid):
                if isinstance(self.containers[inid], list):
                    if len(self.containers[inid]) >= max_count:
                        while len(arr_frames) < max_count:
                            arr_frames.append(self.containers[inid].pop(0))
        else:
            state, key = self.limit_size(max_count, return_tuple=True)
            if state is True:
                while len(arr_frames) < max_count:
                    arr_frames.append(self.containers[key].pop(0))
        return arr_frames
                        
    
    def put(self, frame_data_loc: FrameData):
        id_worker = frame_data_loc.id_worker
        if self.find(id_worker):
            if isinstance(self.containers[id_worker], list):
                self.containers[id_worker].append(frame_data_loc)
                return True
            return False
        else:
            self.containers[id_worker] = []
            if isinstance(self.containers[id_worker], list):
                self.containers[id_worker].append(frame_data_loc)
                return True 
            return False
    
    def empty(self):
        return len(self.containers) == 0
    
    def limit_size(self, max_count, return_tuple=False):
        for key in self.containers.keys():
            if isinstance(self.containers[key], list):
                if len(self.containers[key]) >= max_count:
                    if return_tuple is False:
                        return True
                    else:
                        return (True, key)
        if return_tuple is False:
            return False
        else:
            return (False, None)
