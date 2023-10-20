from framework import Entity, Human, test_multy_issubset

from db import HumanDB
import time


class PlotEntity:
    """
    Загально тут стоїть масив entities так як потім може бути мержинг між сутностями 
    через те що то одна людина і визначена як різні сутності але лице одне і тому так.
    Сам клас відповідає за стуності і елементи що виводитимуться і будуть в бд.
    """
    global_id = 0
    def __init__(self) -> None:
        self.current_id = PlotEntity.global_id
        PlotEntity.global_id += 1
        self.entities = []
        self.hdb: HumanDB | None = None
        self.time_create = time.time()
    
    def push_entity(self, entity:Entity):
        if isinstance(entity, Entity):
            self.entities.append(entity)
    
    def get_human_idx_in_entities(self):
        retarr = []
        if len(self.entities) > 0:
            for en in self.entities:
                arr_single_en = []
                if isinstance(en, Entity):
                    humans = en.humans
                    for h in humans:
                        if isinstance(h, Human):
                            arr_single_en.append(h.human_id)
                retarr.append(arr_single_en)
        return retarr
    
    def push_human_images(self, id_camera, idx_human, images):
        if len(self.entities) > 0:
            for en in self.entities:
                if isinstance(en, Entity):
                    ehidx = en.get_human_idx()
                    if test_multy_issubset(ehidx, idx_human) is True:
                        for image in images:
                            en.append_image(id_camera, image)
    
    def push_human_db(self, hdb):
        self.hdb = hdb 
    
    def get_human_db(self):
        return self.hdb
    
    def get_entities(self):
        return self.entities
    
    def get_human_images(self):
        rarr = []
        if len(self.entities) > 0:
            for en in self.entities:
                if isinstance(en, Entity):
                    images_idx_camera_array = en.get_images_idx_camera_array()
                    for elem in images_idx_camera_array:
                        elret = en.get_image(elem)
                        if elret is not None:
                            (current_timestamp, image) = elret
                            rarr.append(image)
        return rarr
    
    def get_face_images(self):
        if self.hdb is not None:
            return self.hdb.images_face
        else:
            return None
    
