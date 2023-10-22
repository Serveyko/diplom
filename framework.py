# ruff: noqa: E501

import time

import math 
from deep_sort_realtime.deepsort_tracker import DeepSort
from collections import deque
import cv2
from config import white_list_handbag, white_list_person, pair_maxlen, pair_magic_one, pair_magic_two
from config import pair_threshold_one, pair_threshold_two, entity_max_len_deque_images_camera
from config import pairs_manager_max_len_deque_points_id, entity_after_reconfig_bag_group_percent_area
from config import intersection_percent_area, intersection_kad_a, pairs_manager_intersection_human_percent_area
from config import pairs_manager_intersection_bag_percent_area, push_tracks_state_in_circle_intersection_area
from config import push_tracks_test_pone_limit_len

from PyQt5.QtCore import QMutex

def to_list(elem):
    arr = []
    if isinstance(elem, str):
        arr = [int(el) for el in elem.split(" ")]
    elif isinstance(elem, int) or isinstance(elem, float):
        arr.append(int(elem))         
    elif isinstance(elem, list) or isinstance(elem, tuple):
        arr = list(elem)
    
    variant = 0
    if isinstance(arr, list):
        if len(arr) > 0:
            if isinstance(arr[0], list):
                variant = 1
    if variant == 0:
        arr = [int(el) for el in arr]
    elif variant == 1:
        arr = [[int(item) for item in row] for row in arr]
        
    return arr

def test_multy_issubset(a, b):
    a = to_list(a)
    b = to_list(b)
    a = set(a)
    b = set(b)
    return a.issubset(b) is True or b.issubset(a) is True
    

def distance_between_points(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance

def weighted_average(values):
    n = len(values)
    weights = [i + 1 for i in range(n)]
    total_weight = sum(weights)
    
    weighted_sum = sum(val * weight for val, weight in zip(values, weights))
    
    weighted_avg = weighted_sum / total_weight
    return weighted_avg

def dst_k(points_baggage, points_human):
    all_sum = 0.0
    for pb in points_baggage:
        pb = pb[1]
        
        for ph in points_human:
            ph = ph[1]
            
            all_sum += (pb[0] - ph[0])**2 + (pb[1] - ph[1])**2

    return math.sqrt(all_sum) / len(points_baggage) + len(points_human)

def get_mean_points(points_baggage, points_human):
    pb = points_baggage[-1][1]
    ph = points_human[-1][1]
    len_pp = distance_between_points(pb, ph)
    #len_pp = dst_k(points_baggage, points_human)
    return len_pp, pb, ph

def ltrb_to_ltwh(ltrb):
    left, top, right, bottom = ltrb[0], ltrb[1], ltrb[2], ltrb[3]
    width = right - left
    height = bottom - top
    ltwh = [left, top, width, height]
    return ltwh

def ltwh_to_ltrb(ltwh):
    left, top, width, height = ltwh[0], ltwh[1], ltwh[2], ltwh[3]
    right = left + width
    bottom = top + height
    ltrb = [left, top, right, bottom]
    return ltrb

def calculate_intersection_area_ltwh(ltwh1, ltwh2):
    left1, top1, width1, height1 = ltwh1[0], ltwh1[1], ltwh1[2], ltwh1[3]
    left2, top2, width2, height2 = ltwh2[0], ltwh2[1], ltwh2[2], ltwh2[3]
    
    right1 = left1 + width1
    bottom1 = top1 + height1
    right2 = left2 + width2
    bottom2 = top2 + height2
    
    x_overlap = max(0, min(right1, right2) - max(left1, left2))
    y_overlap = max(0, min(bottom1, bottom2) - max(top1, top2))
    
    intersection_area = x_overlap * y_overlap
    total_area = width1 * height1 + width2 * height2
    
    intersection_percentage = (intersection_area / total_area) * 100.0
    return intersection_percentage

def calculate_intersection_area_ltrb(ltrb1, ltrb2):
    left1, top1, right1, bottom1 = ltrb1[0], ltrb1[1], ltrb1[2], ltrb1[3]
    left2, top2, right2, bottom2 = ltrb2[0], ltrb2[1], ltrb2[2], ltrb2[3]
    
    x_overlap = max(0, min(right1, right2) - max(left1, left2))
    y_overlap = max(0, min(bottom1, bottom2) - max(top1, top2))
    
    intersection_area = x_overlap * y_overlap
    total_area = (right1 - left1) * (bottom1 - top1) + (right2 - left2) * (bottom2 - top2)
    
    intersection_percentage = (intersection_area / total_area) * 100.0
    return intersection_percentage

def resize_with_aspect_ratio(image, new_width=None, new_height=None):
    if new_width is None and new_height is None:
        raise ValueError("At least one of 'new_width' or 'new_height' must be provided.")
    
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

def box_to_circle(ltrb_box):
    left, top, right, bottom = ltrb_box[0],ltrb_box[1],ltrb_box[2],ltrb_box[3]
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    
    diagonal = math.sqrt((right - left)**2 + (bottom - top)**2)
    radius = diagonal / 2
    
    return (int(center_x), int(center_y)), int(radius)

def is_box_inside(box, main_box):
    x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
    mx1, my1, mx2, my2 = main_box[0], main_box[1], main_box[2], main_box[3]
    return mx1 <= x1 and mx2 >= x2 and my1 <= y1 and my2 >= y2

def check_box_relationship(box1, box2):
    if is_box_inside(box1, box2):
        return (True, 2)
    elif is_box_inside(box2, box1):
        return (True, 1)
    else:
        return (False, 0)

def circle_intersection(c1, c2, r1, r2):
    """
    Визначає перетин двох кол з центром і радіусом.

    Аргументи:
    c1: Центр першого кола.
    c2: Центр другого кола.
    r1: Радіус першого кола.
    r2: Радіус другого кола.

    Повертає:
    Точка перетину, якщо вона існує.
    None, якщо перетину немає.
    """

    # Відстань між центрами кіл.
    d = math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

    # Якщо відстань між центрами більше суми радіусів, то перетину немає.
    if d > r1 + r2:
        return None

    # Якщо відстань між центрами менше різниці радіусів, то кола повністю перетинаються.
    elif d < abs(r1 - r2):
        return (c1[0], c1[1])

    # Якщо відстань між центрами дорівнює сумі радіусів, то кола мають одну точку перетину.
    else:
        x = (r1**2 - r2**2 + d**2) / (2 * d)
        y = math.sqrt(r1**2 - x**2)
        return (c1[0] + x * (c2[0] - c1[0]), c1[1] + y * (c2[1] - c1[1]))

def exponential_moving_average(data, alpha):
    ema = [data[0]]
    for value in data[1:]:
        smoothed_value = alpha * value + (1 - alpha) * ema[-1]
        ema.append(smoothed_value)
    return ema

def get_min_len_human_baggage(points, unions, dict_indexs):
    array_pair = []
    for i, point in enumerate(points):
        if len(point) > 0:
            if point[0][0] == dict_indexs['handbag'] or point[0][0] == dict_indexs['suitcase']:
                
                union_index = point [0][2]
                other_index = []
                for ival in unions:
                    if union_index == ival[0]:
                        other_index.append(ival[1])
                    elif union_index == ival[1]:
                        other_index.append(ival[0])
                        
                if len(other_index) > 0:
                    cont = False
                    for i_find, point_find in enumerate(points):
                        if i != i_find:
                            if point_find[0][2] in other_index:
                                if len(point_find) > len(point):
                                    cont = True
                                    break 
                    if cont is True:
                        continue
                    
                for j, point_h in enumerate(points):
                    if len(point_h) > 0:
                        if point_h[0][0] == dict_indexs['person']:
                            
                            pb_last = point[-1][3]
                            ph_last = point_h[-1][3]
                            
                            (circle_pb_last_x, circle_pb_last_y), circle_pb_last_radius = box_to_circle(pb_last)
                            (circle_ph_last_x, circle_ph_last_y), circle_ph_last_radius = box_to_circle(ph_last)
                            
                            state = circle_intersection(
                                (circle_pb_last_x, circle_pb_last_y), 
                                (circle_ph_last_x, circle_ph_last_y), 
                                circle_pb_last_radius, 
                                circle_ph_last_radius    
                            )
                            
                            if state is not None:                 
                                lll, pb, ph = get_mean_points(point, point_h)
                                array_pair.append((i, j, lll, pb, ph, point[0][0], point_h[0][0], pb_last, ph_last ))
    
    unique_data = {}

    for item in array_pair:
        key = (item[0], item[1])
        if key not in unique_data or item[2] < unique_data[key][2]:
            unique_data[key] = item

    array_pair = list(unique_data.values())

    r2 = []
    visited_pairs = set()
    prearr = list(set([val[0] for val in array_pair]))
    for finder_index in prearr:
        
        min_val = float('inf')
        index_val = -1
        
        for i, pair2 in enumerate(array_pair):
            
            key1 = (finder_index, i)
            if key1 not in visited_pairs:
                visited_pairs.add(key1)
            
                if pair2[0] == finder_index and pair2[2] < min_val: 
                    min_val = pair2[2]
                    index_val = i 
                
        if min_val != float('inf') and index_val != -1:
            r2.append(array_pair[index_val])

    if len(r2) >= 2:
        pass
    
    if len(unions) > 0:
        pass
    
    return r2

"""def intersection(points, dict_indexs, kad_a=intersection_kad_a, percent_area=intersection_percent_area):
    
    points_result = []
    for pt in points:
        if len(pt) >= kad_a:
            points_result.append(pt)
    
    result_ = []
    union = []
    visited_pairs = set()

    for id1 in points_result:
        last_point1 = id1[-1]
        for id2 in points_result:
            last_point2 = id2[-1] 
            if last_point1[0] == last_point2[0] and last_point1[2] != last_point2[2]:
                key1 = tuple(sorted([last_point1[2], last_point2[2]]))
                if key1 not in visited_pairs:
                    visited_pairs.add(key1)
                    
                    a = calculate_intersection_area_ltrb(last_point1[3], last_point2[3])
                    cb = check_box_relationship(last_point1[3], last_point2[3])
                    
                    if a >= percent_area or cb[0] is True:
                        result_.append(((last_point1[2], last_point2[2]), last_point1, last_point2, a, cb))
                        union.append((last_point1[2], last_point2[2]))
    
    if len(union) > 0:
        pass
    
    return points_result, union
"""
def circle_intersection_area(radius1, center1, radius2, center2):
    d = math.sqrt((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2)

    if d >= radius1 + radius2:
        # Кола не перетинаються
        return 0, 0
    elif d <= abs(radius1 - radius2):
        # Одне коло міститься в іншому
        intersection_area = math.pi * min(radius1, radius2) ** 2
        percentage_intersection = (intersection_area / (math.pi * radius1 ** 2)) * 100
        return intersection_area, percentage_intersection
    else:
        # Обчислення площі перетину
        theta1 = 2 * math.acos((radius1 ** 2 - radius2 ** 2 + d ** 2) / (2 * radius1 * d))
        theta2 = 2 * math.acos((radius2 ** 2 - radius1 ** 2 + d ** 2) / (2 * radius2 * d))
        area1 = 0.5 * theta1 * radius1 ** 2 - 0.5 * radius1 ** 2 * math.sin(theta1)
        area2 = 0.5 * theta2 * radius2 ** 2 - 0.5 * radius2 ** 2 * math.sin(theta2)
        intersection_area = area1 + area2
        total_area = math.pi * radius1 ** 2 + math.pi * radius2 ** 2
        percentage_intersection = (intersection_area / total_area) * 100
        return intersection_area, percentage_intersection

class QMutexContextManager:
    def __init__(self):
        self.mutex = QMutex()

    def __enter__(self):
        self.mutex.lock()
        return self.mutex

    def __exit__(self, exc_type, exc_value, traceback):
        self.mutex.unlock()
        
    def lock(self):
        self.mutex.lock()
    
    def unlock(self):
        self.mutex.unlock()

class TrackersCapacitor:
    def __init__(self):
        self.trackers = {}
        self.already_created_index_human = {}
        self.already_created_index_bag = {}
        self.already_created_index_elog = {}
        self.already_created_index_ehuman = {}
        self.already_created_index_ebag = {}
        self.already_created_index_entity = {}
        self.already_created_index_pair = {}
        self.locker = QMutexContextManager()

    def put(self, index, value):
        # Додати значення за вказаним індексом
        self.trackers[index] = value

    def get(self, index):
        # Отримати значення за вказаним індексом, або None, якщо індекс відсутній
        return self.trackers.get(index)

    def remove(self, index):
        # Видалити значення за вказаним індексом, якщо індекс існує
        if index in self.tracker:
            del self.trackers[index]
            
    def create_basic_tracker(self, index_create=0):
        if self.get(index_create) is None:
            #embedder = 'clip_ViT-B/16'
            #embedder = 'mobilenet'
            tracker = DeepSort(
                max_age=3, 
                embedder='mobilenet', 
                max_iou_distance=0.9, 
                embedder_gpu=False
            )
            self.put(index_create, tracker )
    
    def get_uid_human(self, id_camera, index1, index2):
        with self.locker:
            key = (id_camera, index1, index2)
            if key in self.already_created_index_human:
                return self.already_created_index_human[key]
            else:
                new_idx = len(self.already_created_index_human)
                self.already_created_index_human[key] = new_idx
                return new_idx
    
    def get_uid_bag(self, id_camera, index1, index2):
        with self.locker:
            key = (id_camera, index1, index2)
            if key in self.already_created_index_bag:
                return self.already_created_index_bag[key]
            else:
                new_idx = len(self.already_created_index_bag)
                self.already_created_index_bag[key] = new_idx
                return new_idx
    
    def get_uid_elog(self):
        with self.locker:
            new_idx = len(self.already_created_index_elog)
            key = (new_idx)
            self.already_created_index_elog[key] = new_idx
            return new_idx
    
    def get_uid_ehuman(self):
        with self.locker:
            new_idx = len(self.already_created_index_ehuman)
            key = (new_idx)
            self.already_created_index_ehuman[key] = new_idx
            return new_idx
    
    def get_uid_ebag(self):
        with self.locker:
            new_idx = len(self.already_created_index_ebag)
            key = (new_idx)
            self.already_created_index_ebag[key] = new_idx
            return new_idx
    
    def get_uid_entity(self):
        with self.locker:
            new_idx = len(self.already_created_index_entity)
            key = (new_idx)
            self.already_created_index_entity[key] = new_idx
            return new_idx
    
    def get_uid_pair(self):
        with self.locker:
            new_idx = len(self.already_created_index_pair)
            key = (new_idx)
            self.already_created_index_pair[key] = new_idx
            return new_idx

trackers_capacitor = TrackersCapacitor()

class Human:
    
    def __init__(self, human_id=-1, det_class=None, max_len_deque_points_id = 300) -> None:
        self.human_id = human_id
        self.det_class = det_class
        self.max_len_deque_points_id = max_len_deque_points_id
        self.pts_bbox_ltrb = []
        self.last_camera_id = -1
        self.enable_last_camera_id = -1
        self.last_cam = deque(maxlen=1000)
    
    def append(self, id_camera=-1, data=None):
        if id_camera != -1:
            while len(self.pts_bbox_ltrb) - 1 < id_camera:
                dq = deque(maxlen=self.max_len_deque_points_id)
                self.pts_bbox_ltrb.append(dq)
            current_timestamp = time.time()
            self.pts_bbox_ltrb[id_camera].append((current_timestamp, data))
            self.last_camera_id = id_camera
            self.last_cam.append(id_camera)
    
    def get_points(self, id_camera=-1):
        if self.exist_camera_track(id_camera) is True:
            pts_m = self.pts_bbox_ltrb[id_camera]
            if pts_m is not None:
                pts_m = list(pts_m)
                if len(pts_m) > 0:
                    return pts_m
        return None
    
    def exist_camera_track(self, id_camera=-1):
        if id_camera != -1 and id_camera >= 0:
            if len(self.pts_bbox_ltrb) - 1 < id_camera:
                return False
            else:
                return True
        return False
    
    def enable_one_camera(self, id_camera=-1):
        if self.exist_camera_track(id_camera) is True:
            self.enable_last_camera_id = id_camera
            return True 
        return False

    def get_last_camera_id(self):
        return self.enable_last_camera_id


class Bag:
    
    def __init__(self, bag_id=-1, det_class=None, max_len_deque_points_id = 300) -> None:
        self.bag_id = bag_id
        self.det_class = det_class
        self.max_len_deque_points_id = max_len_deque_points_id
        self.pts_bbox_ltrb = []
        self.last_camera_id = -1
        self.enable_last_camera_id = -1
        self.last_cam = deque(maxlen=1000)

    def append(self, id_camera=-1, data=None):
        if id_camera != -1:
            while len(self.pts_bbox_ltrb)-1 < id_camera:
                dq = deque(maxlen=self.max_len_deque_points_id)
                self.pts_bbox_ltrb.append(dq)
            current_timestamp = time.time()
            self.pts_bbox_ltrb[id_camera].append((current_timestamp, data))
            self.last_camera_id = id_camera
            self.last_cam.append(id_camera)
    
    def get_points(self, id_camera=-1):
        if self.exist_camera_track(id_camera) is True:
            pts_m = self.pts_bbox_ltrb[id_camera]
            if pts_m is not None:
                pts_m = list(pts_m)
                if len(pts_m) > 0:
                    return pts_m
        return None
    
    def exist_camera_track(self, id_camera=-1):
        if id_camera != -1 and id_camera >= 0:
            if len(self.pts_bbox_ltrb) - 1 < id_camera:
                return False
            else:
                return True
        return False
    
    def enable_one_camera(self, id_camera=-1):
        if self.exist_camera_track(id_camera) is True:
            self.enable_last_camera_id = id_camera
            return True 
        return False
    
    def get_last_camera_id(self):
        return self.enable_last_camera_id


class Pair:
    def __init__(self, id_camera=-1, human=None, bag=None, maxlen=pair_maxlen) -> None:
        
        self.current_id = trackers_capacitor.get_uid_pair()
        
        self.id_camera = id_camera
        
        self.maxlen = maxlen
        
        self.intersection_array = deque(maxlen=self.maxlen)
        self.state_array =        deque(maxlen=self.maxlen)

        self.pair_state = deque(maxlen=self.maxlen)
        
        self.human = human
        self.bag = bag
        
        self.current_state = None

        self.magic_one = pair_magic_one
        self.magic_two = pair_magic_two
        
        self.threshold_one = pair_threshold_one
        self.threshold_two = pair_threshold_two
        
        self.last_time_update = None
        
        #self.pre_cold = False 
        #self.cold = False
    
    def get_len(self):
        return len(self.intersection_array)
    
    def update(self, st, reset_original=False):
        before_state = False
        if reset_original is True:
            self.intersection_array.clear()
            self.state_array.clear()
            self.pair_state.clear()
            self.intersection_array.append(1)
            self.state_array.append(1)
            
            before_state = self.current_state
            self.current_state = True
            self.pair_state.append(self.current_state)
        else:
            if st == 1:
                self.intersection_array.append(1)
            else:
                self.intersection_array.append(0) 
            larr = None
            if len(self.intersection_array) > 0:
                larr = list(self.intersection_array)
                larr = exponential_moving_average(larr, self.magic_one)
            
            if larr is not None:
                if larr[-1] > self.threshold_one:
                    self.state_array.append(1)
                else:
                    self.state_array.append(0)
            else:
                self.state_array.append(0)

            before_state = self.current_state
                
            if len(self.state_array) > 0:
                cr = list(self.state_array)
                cr = exponential_moving_average(cr, self.magic_two)
                
                if cr[-1] > self.threshold_two:
                    #true green
                    self.current_state = True
                else:
                    #false red
                    self.current_state = False
            else:
                #none white
                self.current_state = None
                
            self.pair_state.append(self.current_state)
            
        self.last_time_update = time.time()
        
        return self.current_state, before_state != self.current_state 


class Entity:
    
    def __init__(self) -> None:
        self.current_id = trackers_capacitor.get_uid_entity()
        self.humans = []
        self.bags = []
        self.pairs = []
        
        self.bag_group = []
        
        self.images_with_camera_id = []
        self.max_len_deque_images_camera = entity_max_len_deque_images_camera
    
    def get_best_human(self, id_camera=-1):
        best_human = None 
        bbox_human = None
        original_ltwh_human = None
        if id_camera != -1:
            array_pts = []
            for single_human in self.humans:
                if isinstance(single_human, Human):
                    pts_m = single_human.get_points(id_camera)
                    if pts_m is not None:
                        la = list(pts_m)
                        array_pts.append((single_human, la))
            
            index_max = 0
            for index_i, one_la in enumerate(array_pts):
                single_human = one_la[0]
                points = one_la[1]
                if len(points) > len(array_pts[index_max][1]) or len(array_pts) <= 0:
                    if array_pts[index_i][1][-1][1][1] is not None:
                        index_max = index_i
            if index_max < len(array_pts) and len(array_pts) > 0:
                bbox_human = array_pts[index_max][1][-1][1][0]
                original_ltwh_human = array_pts[index_max][1][-1][1][1]
                best_human = array_pts[index_max][0]
                
        return best_human, bbox_human, original_ltwh_human
    
    def append_image(self, id_camera=-1, image=None):
        if id_camera != -1:
            while len(self.images_with_camera_id) - 1 < id_camera:
                dqc = deque(maxlen=self.max_len_deque_images_camera)
                self.images_with_camera_id.append(dqc)
            current_timestamp = time.time()
            self.images_with_camera_id[id_camera].append((current_timestamp, image))
    
    def get_image(self, id_camera=-1):
        if self.exist_camera_image(id_camera) is True:
            list_l = list(self.images_with_camera_id[id_camera])
            if len(list_l) > 0:
                return list_l[-1]
            else:
                return None
        return None
    
    def exist_camera_image(self, id_camera=-1):
        if id_camera != -1 and id_camera >= 0:
            if len(self.images_with_camera_id) - 1 < id_camera:
                return False
            else:
                return True
        return False 
    
    def get_all_images(self):
        arr_idx = self.get_images_idx_camera_array()
        f_images = []
        for ci in arr_idx:
            im = self.get_image(ci)
            if im is not None:
                f_images.append(im[1])
        return f_images
    
    def get_images_idx_camera_array(self):
        return [val for val in range(len(self.images_with_camera_id))]
    
    def find_human_in_pairs(self, human_id, camera_id):
        for single_pair in self.pairs:
            if isinstance(single_pair, Pair):
                if single_pair.id_camera == camera_id:
                    if isinstance(single_pair.human, Human):
                        if single_pair.human.human_id == human_id:
                            return single_pair 
        return None 
    
    def find_bag_in_pairs(self, bag_id, camera_id):
        for single_pair in self.pairs:
            if isinstance(single_pair, Pair):
                if single_pair.id_camera == camera_id:
                    if isinstance(single_pair.bag, Bag):
                        if single_pair.bag.bag_id == bag_id:
                            return single_pair 
        return None
    
    def get_bbox_best_human(self, camera_id):
        array_pts = []
        for single_human in self.humans:
            if isinstance(single_human, Human):
                #state_human_pair = self.find_human_in_pairs(single_human.human_id, camera_id)
                #if state_human_pair is not None:
                pts = single_human.get_points(camera_id)
                if pts is not None:
                    la = list(pts)
                    array_pts.append(la)
        
        index_max = 0
        for index_i, one_la in enumerate(array_pts):
            if len(one_la) > len(array_pts[index_max]) or len(array_pts) <= 0:
                if array_pts[index_i][-1][1][1] is not None:
                    index_max = index_i
        if index_max < len(array_pts) and len(array_pts) > 0:
            return array_pts[index_max][-1][1][0], array_pts[index_max][-1][1][1]
        return None, None
    
    def get_bbox_best_group_bag(self, camera_id):
        array_pts_group = []
        for index_group, single_group in enumerate(self.bag_group):
            if len(self.bag_group) > 1:
                pass
            array_pts = []
            for single_bag in single_group:
                if isinstance(single_bag, Bag):
                    state_bag_pair = self.find_bag_in_pairs(single_bag.bag_id, camera_id)
                    if state_bag_pair is not None and state_bag_pair.current_state is True:
                        pts_ = single_bag.get_points(camera_id)
                        if pts_ is not None:
                            la = list(pts_)
                            array_pts.append((la, state_bag_pair))
            
            index_max = 0
            for index_i, one_la in enumerate(array_pts):
                if len(one_la[0]) > len(array_pts[index_max][0]):
                    if array_pts[index_i][0][-1][1][1] is not None: #if original_ltwh not none
                        index_max = index_i
            if index_max < len(array_pts):
                array_pts_group.append(
                    (array_pts[index_max][0][-1][1][0], 
                     array_pts[index_max][0][-1][1][1], 
                     array_pts[index_max][1], index_group))
            else:
                array_pts_group.append(())
        return array_pts_group
    
    def get_human_idx(self):
        arr_idx = []
        for one_human in self.humans:
            if isinstance(one_human, Human):
                arr_idx.append(one_human.human_id)
        return arr_idx
    
    def exist_human_id(self, human_id):
        for one_human in self.humans:
            if isinstance(one_human, Human):
                if one_human.human_id == human_id:
                    return True 
        return False
    
    def exist_bag_id(self, bag_id):
        for one_bag in self.bags:
            if isinstance(one_bag, Bag):
                if one_bag.bag_id == bag_id:
                    return True 
        return False

    def exist_pair_id(self, pair_id):
        for one_pair in self.pairs:
            if isinstance(one_pair, Pair):
                if one_pair.current_id == pair_id:
                    return True 
        return False
    
    def push_human(self, human):
        if isinstance(human, Human):
            self.humans.append(human)
    
    def push_bag(self, bag):
        
        if isinstance(bag, Bag):
            self.bags.append(bag)
    
    def after_reconfig_bag_group(self, id_camera,  percent_area = entity_after_reconfig_bag_group_percent_area):
        array_pts_group_bag = self.get_bbox_best_group_bag(id_camera)
        if len(array_pts_group_bag) > 1:
            pass
            result = []
            visited_pairs = set()
            for i_, one_ in enumerate(array_pts_group_bag):
                if len(one_) > 0:
                    for j_, two_ in enumerate(array_pts_group_bag):
                        if len(two_) > 0:
                            if (
                                i_ != j_ and 
                                len(one_[0]) > 0 and 
                                len(two_[0]) > 0 and 
                                isinstance(one_[2].bag, Bag) and 
                                isinstance(two_[2].bag, Bag)
                            ):
                                last_point1 = one_[0]
                                last_point2 = two_[0]
                                a = calculate_intersection_area_ltrb(
                                    last_point1, 
                                    last_point2
                                )
                                cb = check_box_relationship(
                                    last_point1, 
                                    last_point2
                                )
                                if a >= percent_area or cb[0] is True:
                                    key1 = tuple(sorted([one_[2].bag.bag_id, two_[2].bag.bag_id]))
                                    if key1 not in visited_pairs:
                                        visited_pairs.add(key1)
                                        result.append((one_, two_))
            if len(result) > 0:
                pass
            list_merge_groups = [] 
            for elem in result:
                list_merge_groups.append((elem[0][3], elem[1][3]))
            not_merge_groups = []
            for index_group, single_group in enumerate(self.bag_group):
                exist_in_merge = False
                for one_lmg in list_merge_groups:
                    if index_group == one_lmg[0] or index_group == one_lmg[1]:
                        exist_in_merge = True
                        break 
                if exist_in_merge is False:
                    not_merge_groups.append(single_group)
            result_groups = not_merge_groups
            for one_groups in list_merge_groups:
                pre_group = []
                first_group = self.bag_group[one_groups[0]]
                last_group = self.bag_group[one_groups[1]]
                for el1 in first_group:
                    keys = [one_bag.bag_id for one_bag in pre_group if isinstance(one_bag, Bag)]
                    if isinstance(el1, Bag):
                        if el1.bag_id not in keys:
                            pre_group.append(el1)
                for el1 in last_group:
                    keys = [one_bag.bag_id for one_bag in pre_group if isinstance(one_bag, Bag)]
                    if isinstance(el1, Bag):
                        if el1.bag_id not in keys:
                            pre_group.append(el1)
                result_groups.append(pre_group)
                pass
            self.bag_group = result_groups
        pass
                         
    def push_bag_group(self, bag_group, id_camera):
        """
        input bag_group = [bag, bag, bag]
        self bag_group = [[bag, bag, bag], [bag, bag, bag], [bag, bag, bag]]
        """
        input_keys = [one_bag.bag_id for one_bag in bag_group if isinstance(one_bag, Bag)]
        
        one_add = False
        
        for ic, current_self_bag_group in enumerate(self.bag_group):
            keys = [one_bag.bag_id for one_bag in current_self_bag_group if isinstance(one_bag, Bag)]
            exist_in_arr = -1
            for iok, one_key in enumerate(keys):
                if one_key in input_keys:
                    exist_in_arr = iok 
                    break
            if exist_in_arr != -1:
                group_array_add = []
                for add_one_bag in bag_group:
                    if isinstance(add_one_bag, Bag):
                        if add_one_bag.bag_id not in keys:
                            group_array_add.append(add_one_bag)
                for elap in group_array_add:
                    self.bag_group[ic].append(elap)
                one_add = True
        if one_add is False:            
            self.bag_group.append(bag_group)
            one_add = False
            
        self.after_reconfig_bag_group(id_camera)
        
        """print()
        print(f"START PRINT GROUPS {self.current_id}")
        for pri_group in self.bag_group:
            print([elem.bag_id for elem in pri_group if isinstance(elem, Bag)])
        print(f"END PRINT GROUPS {self.current_id}")"""
    
    def push_pair(self, pair):
        if isinstance(pair, Pair):
            self.pairs.append(pair)
    
    def get_unique_identifiers(self):
        human_keys = [one_human.human_id for one_human in self.humans if isinstance(one_human, Human)] 
        bags_keys = []
        for one_group in self.bag_group:
            single_bags_keys = [one_bag.bag_id for one_bag in one_group if isinstance(one_bag, Bag)] 
            bags_keys.append(single_bags_keys)
        
        human_keys = sorted(human_keys)
        for i, elem in enumerate(bags_keys):
            bags_keys[i] = sorted(elem)

        hk = [int(one_key) for one_key in human_keys]
        bk = []
        for i, elem in enumerate(bags_keys):
            bk.append([int(one_key) for one_key in elem])
        
        if len(human_keys) > 0:
            pass 
        if len(bags_keys) > 0:
            pass
        pass  
        return hk, bk
    
    def get_unique_identifiers_active_status(self, camera_id):
        human_keys = [one_human.human_id for one_human in self.humans if isinstance(one_human, Human)] 
        human_keys = sorted(human_keys)
        hk = [int(one_key) for one_key in human_keys]
        
        bags_keys = []
        for one_group in self.bag_group:
            global_state_group = False
            for i_curr, one_bag in enumerate(one_group):
                if isinstance(one_bag, Bag): 
                    single_key = one_bag.bag_id
                    
                    for single_pair in self.pairs:
                        if isinstance(single_pair, Pair):
                            if single_pair.id_camera == camera_id: #test
                                if isinstance(single_pair.bag, Bag):
                                    if single_pair.bag.bag_id == single_key:
                                        if single_pair.current_state is True:
                                            global_state_group = True 
                                            break
                    if global_state_group is True:
                        break 

            if global_state_group is True:
                single_bags_keys = [one_bag.bag_id for one_bag in one_group if isinstance(one_bag, Bag)] 
                bags_keys.append(single_bags_keys)
        
        bk = []
        for i, elem in enumerate(bags_keys):
            bk.append([int(one_key) for one_key in elem])
        
        if len(human_keys) > 0:
            pass 
        if len(bags_keys) > 0:
            pass
        
        pass  
        return hk, bk
        
    def get_last_info(self, camera_id):
        bbox_human, original_ltwh_human = self.get_bbox_best_human(camera_id)
        array_pts_group_bag = self.get_bbox_best_group_bag(camera_id)
        return {
            "bbox_human": bbox_human,
            "original_ltwh_human": original_ltwh_human,
            "array_pts_group_bag": array_pts_group_bag
        }
        

class EntityManager:
    
    class EBag:
        def __init__(self, camera_id) -> None:
            self.local_id = trackers_capacitor.get_uid_ebag()
            self.array_idx = []
            self.camera_id = camera_id
        
        def get_idx(self):
            return self.array_idx
        
        def push_idx(self, idx):
            arr = to_list(idx)
            
            new_arr = []
            new_arr.extend(self.array_idx)
            new_arr.extend(arr)
            new_arr = list(set(new_arr))
            self.array_idx = new_arr
        
    class EHuman:
        def __init__(self, camera_id) -> None:
            self.local_id = trackers_capacitor.get_uid_ehuman()
            self.array_idx = []
            self.bags = []
            self.camera_id= camera_id
        
        def get_idx(self):
            return self.array_idx
        
        def push_idx(self, idx):
            arr = to_list(idx)
            
            new_arr = []
            new_arr.extend(self.array_idx)
            new_arr.extend(arr)
            new_arr = list(set(new_arr))
            self.array_idx = new_arr
        
        def push_bag(self, idx_bag, camera_id):
            arr = to_list(idx_bag)
            
            for elem in arr:
                ebag = EntityManager.EBag(camera_id)
                ebag.push_idx(elem)
                self.bags.append(ebag)
                
        def exist_bag(self, idx_bag, camera_id):
            arr = set(to_list(idx_bag))
            for e_bag in self.bags:
                if isinstance(e_bag, EntityManager.EBag) and e_bag.camera_id == camera_id:
                    e_bag_set = set(e_bag.get_idx())
                    if arr.issubset(e_bag_set) or e_bag_set.issubset(arr): 
                        return True
            return False
        
        def update_bag(self, idx_bag, camera_id):
            arr = set(to_list(idx_bag))
            for e_bag in self.bags:
                if isinstance(e_bag, EntityManager.EBag) and e_bag.camera_id == camera_id:
                    e_bag_set = set(e_bag.get_idx())
                    if arr.issubset(e_bag_set) or e_bag_set.issubset(arr): 
                        e_bag.push_idx(idx_bag)
                        break
                    
        def remove_bag(self, idx_bag, camera_id):
            arr = set(to_list(idx_bag))
            new_arr_bags = []
            for e_bag in self.bags:
                if isinstance(e_bag, EntityManager.EBag) and e_bag.camera_id == camera_id:
                    e_bag_set = set(e_bag.get_idx())
                    if arr.issubset(e_bag_set) or e_bag_set.issubset(arr): 
                        pass 
                    else:
                        new_arr_bags.append(e_bag)
            state = False
            if len(new_arr_bags) != len(self.bags):
                state = True
            self.bags = new_arr_bags
            return state
    
    class ELog:

        def __init__(self, camera_id) -> None:
            self.local_id = trackers_capacitor.get_uid_elog()
            self.human_idx = None
            self.bag_idx = None
            self.create_elem = None
            self.remove_elem = None
            self.camera_id = camera_id
        
        def create(self, human_idx, bag_idx, create=None, remove=None):
            self.human_idx = human_idx
            self.bag_idx = bag_idx
            self.create_elem = create
            self.remove_elem = remove
        
        def get_all(self):
            return self.human_idx, self.bag_idx
    
    global_id_entity_manager = 0
    
    def __init__(self) -> None:
        self.local_id = EntityManager.global_id_entity_manager
        EntityManager.global_id_entity_manager += 1
        self.humans = []
        self.logs = []
        self.old_array_update = None
    
    def get_logs(self):
        return self.logs
    
    def get_human(self, idx, camera_id):
        for i_human, human in enumerate(self.humans):
            if isinstance(human, EntityManager.EHuman) and test_multy_issubset(idx, human.get_idx()):
                if human.camera_id == camera_id:
                    return human
        return None
    
    def update(self, camera_id, array_update, array_all):
        pre_logs = []
        
        if self.old_array_update is not None:
            pass
            for elem in self.old_array_update:
                elem_groups = elem[1]
                exist_human = False 
                exist_elem = None
                for sub_elem in array_update:
                    pass
                    if test_multy_issubset(elem[0], sub_elem[0]):
                        exist_human = True
                        sub_elem_groups = sub_elem[1]
                        exist_elem = sub_elem
                        pass
                        break
                if exist_human is True and exist_elem is not None:
                    sub_elem_groups = exist_elem[1]
                    result_test = []
                    for seg_new in elem_groups:
                        rt = False
                        for seg_old in sub_elem_groups:
                            if test_multy_issubset(seg_new, seg_old):
                                rt = True
                                break
                        #Якщо в новому немає старого то це видалення старого елементу 
                        if rt is False:
                            result_test.append(seg_new)
                    pass
                    for rm_elem in result_test:
                        #тут видалити групу із вбудованих масивів цієї людини 
                        pass
                        for i_human, human in enumerate(self.humans):
                            if isinstance(human, EntityManager.EHuman):
                                if human.camera_id == camera_id:
                                    if test_multy_issubset(elem[0], human.get_idx()): 
                                        human.remove_bag(rm_elem, camera_id)
                                        pre_logs.append((human, rm_elem, "remove"))
                                        print("R1")
                                        break
                else:
                    new_elem = []
                    for i_human, human in enumerate(self.humans):
                        if isinstance(human, EntityManager.EHuman):
                            if human.camera_id == camera_id:
                                if test_multy_issubset(elem[0], human.get_idx()) is False: 
                                    new_elem.append(human)
                    self.humans = new_elem
                pass 
            
            #Це якщо в новому масиві є а в старому немає то створення 
            for i, sub_elem in enumerate(array_update):
                sub_elem_groups = sub_elem[1]
                exist_human = False
                for j, elem in enumerate(self.old_array_update):
                    elem_groups = elem[1] 
                    if test_multy_issubset(sub_elem[0], elem[0]):
                        exist_human = True
                        break
                if exist_human is True:
                    #elem = self.old_array_update[exist_human_index][0]
                    #elem_groups = self.old_array_update[exist_human_index][1]  
                    human = self.get_human(sub_elem[0], camera_id)
                    if human is not None:
                        human.push_idx(sub_elem[0])
                        for bag_s in to_list(sub_elem_groups):
                            if human.exist_bag(bag_s, camera_id) is not True:
                                human.push_bag(bag_s, camera_id)
                                pre_logs.append((human, bag_s, "create"))
                                print("C1")
                            else:
                                human.update_bag(bag_s, camera_id)
                    pass
                elif exist_human is False:
                    human = EntityManager.EHuman(camera_id)
                    human.push_idx(sub_elem[0])
                    for bag_s in to_list(sub_elem_groups):
                        human.push_bag(bag_s, camera_id)
                        pre_logs.append((human, bag_s, "create"))
                        print("C2")
                    self.humans.append(human)
                    pass
            
        else:
            for elem in array_update:
                human = EntityManager.EHuman(camera_id)
                human.push_idx(elem[0])
                for bag_s in to_list(elem[1]):
                    human.push_bag(bag_s, camera_id)
                    pre_logs.append((human, bag_s, "create"))
                    print("C3")
                self.humans.append(human)
            pass
                  
        if len(pre_logs) > 0:
            
            for elem_log in pre_logs:
                elog = EntityManager.ELog(camera_id)
                if isinstance(elem_log[0], EntityManager.EHuman):
                    if elem_log[2] == "create":
                        elog.create(elem_log[0].get_idx(), elem_log[1], create=True)
                    elif elem_log[2] == "remove":
                        elog.create(elem_log[0].get_idx(), elem_log[1], remove=True)
                    self.logs.append(elog)
        if len(self.logs) > 0:
            #print(f"LEN {len(self.logs)}")
            pass
        
        self.old_array_update = array_update
        
        return self.logs
                            

class PairsManager:
    
    def __init__(self) -> None:
        self.human_ids = white_list_person
        self.bag_ids = white_list_handbag
        
        self.humans = []
        self.bags = []
        self.pairs = []
        self.unions_bags = {}
        self.unions_humans = {}
        
        self.entities = []
        
        self.max_len_deque_points_id = pairs_manager_max_len_deque_points_id
        
        self.human_groups = []
        self.bags_groups = []
        self.locker = QMutexContextManager()
    
    def get_bags_and_humans_by_logs(self, logs):
        if len(logs) > 0:
            array_result = []
            for elem in logs:
                if isinstance(elem, EntityManager.ELog):
                    human_idx, bag_idx = elem.get_all()
                    humans = []
                    bags = []
                    
                    for elem_h in human_idx:
                        for sh in self.humans:
                            if isinstance(sh, Human):
                                if sh.human_id == elem_h:
                                    humans.append(sh)
                                    break
                    
                    for elem_b in bag_idx:
                        for sb in self.bags:
                            if isinstance(sb, Bag):
                                if sb.bag_id == elem_b:
                                    bags.append(sb)
                                    break
                    
                    array_result.append((humans, bags))
            return array_result
        return None
    
    def get_bags_by_array_idx(self, bag_idx):
        if len(bag_idx) > 0:
            bags = []
            for elem_b in bag_idx:
                for sb in self.bags:
                    if isinstance(sb, Bag):
                        if sb.bag_id == elem_b:
                            bags.append(sb)
                            break
            return bags
        return None
    
    def get_humans_by_array_idx(self, human_idx):
        if len(human_idx) > 0:
            humans = []
            for elem_h in human_idx:
                for sh in self.humans:
                    if isinstance(sh, Human):
                        if sh.human_id == elem_h:
                            humans.append(sh)
                            break
            return humans
        return None
    
    
    def find_human(self, id_human=-1):
        for hone in self.humans:
            if isinstance(hone, Human):
                if hone.human_id == id_human:
                    return hone
        return None 
    
    def find_bag(self, id_bag=-1):
        for bone in self.bags:
            if isinstance(bone, Bag):
                if bone.bag_id == id_bag:
                    return bone 
        return None 
    
    def find_pair(self, id_camera=-1, id_human=-1, id_bag=-1):
        for pone in self.pairs:
            if isinstance(pone, Pair):
                if pone.id_camera == id_camera:
                    if isinstance(pone.human, Human) and isinstance(pone.bag, Bag):
                        if pone.human.human_id == id_human and pone.bag.bag_id == id_bag:
                            return pone 
        return None 
    
    def find_pair_on_other_cameras(self, id_current_camera=-1):
        array_other = []
        for pone in self.pairs:
            if isinstance(pone, Pair):
                if pone.id_camera != id_current_camera:
                    array_other.append(pone) 
        return array_other 
      
    def append_human(self, data):
        if isinstance(data, Human):
            self.humans.append(data) 
    
    def append_bag(self, data):
        if isinstance(data, Bag):
            self.bags.append(data) 
    
    def append_pair(self, data):
        if isinstance(data, Pair):
            self.pairs.append(data)
    
    def enable_track_camera_id(self, id_camera=-1):
        for hone in self.humans:
            if isinstance(hone, Human):
                hone.enable_one_camera(id_camera)

        for bone in self.bags:
            if isinstance(bone, Bag):
                bone.enable_one_camera(id_camera)
    
    def intersection_human(self, id_camera=-1, percent_area = pairs_manager_intersection_human_percent_area, delta_time_limit=None):
        result_intersection_human = []
        visited_pairs = set()
        for human1 in self.humans:
            if isinstance(human1, Human):
                id1 = human1.get_points(id_camera)
                if id1 is not None:
                    if len(id1) > 0:
                        last_point1 = id1[-1][1][0]
                        time1 =id1[-1][0]
                        for human2 in self.humans:
                            if isinstance(human2, Human):
                                id2 = human2.get_points(id_camera)
                                if id2 is not None:
                                    if len(id2) > 0:
                                        last_point2 = id2[-1][1][0] 
                                        time2 =id2[-1][0]
                                        
                                        delta_time = abs(time2 - time1)
                                        
                                        state_2 = False
                                        if delta_time != 0.0:
                                            pass
                                        if delta_time_limit is not None:
                                            state_2 = delta_time < delta_time_limit
                                        else:
                                            state_2 = True
                                            
                                            
                                        if human1.human_id != human2.human_id and state_2 is True:
                                            key1 = tuple(sorted([human1.human_id, human2.human_id]))
                                            if key1 not in visited_pairs:
                                                visited_pairs.add(key1)
                                                
                                                a = calculate_intersection_area_ltrb(last_point1, last_point2)
                                                cb = check_box_relationship(last_point1, last_point2)
                                                
                                                
                                                """c_1, r__1 = box_to_circle(last_point1)
                                                c_2, r__2 = box_to_circle(last_point2)

                                                intersection_area, percentage_intersection = circle_intersection_area(r__1, c_1, r__2, c_2)
                                                a = percentage_intersection
                                                
                                                """
                                                if a >= percent_area or cb[0] is True:
                                                    result_intersection_human.append((
                                                        (human1.human_id, human2.human_id),
                                                        last_point1, 
                                                        last_point2, 
                                                        a, 
                                                        cb,
                                                        (human1, human2)
                                                        ))
                
        return result_intersection_human                                   
    
    def intersection_bag(self, id_camera=-1, percent_area = pairs_manager_intersection_bag_percent_area, delta_time_limit=None):
        result_intersection_bag = []
        visited_pairs = set()
        for bag1 in self.bags:
            if isinstance(bag1, Bag):
                id1 = bag1.get_points(id_camera)
                if id1 is None:
                    continue
                if len(id1) > 0:
                    last_point1 = id1[-1][1][0]
                    """original_ltwh1 = id1[-1][1][1]
                    
                    if original_ltwh1 is None:
                        continue"""
                    time1 =id1[-1][0]
                    for bag2 in self.bags:
                        if isinstance(bag2, Bag):
                            id2 = bag2.get_points(id_camera)
                            if id2 is None:
                                continue
                            if len(id2) > 0:
                                last_point2 = id2[-1][1][0] 
                                
                                """original_ltwh2 = id2[-1][1][1]
                    
                                if original_ltwh2 is None:
                                    continue"""
                    
                                time2 =id2[-1][0]
                                
                                delta_time = abs(time2 - time1)
                                state_2 = False
                                if delta_time != 0.0:
                                    pass
                                if delta_time_limit is not None:
                                    state_2 = delta_time < delta_time_limit
                                else:
                                    state_2 = True
                                
                                if bag1.bag_id != bag2.bag_id and state_2 is True:
                                    key1 = tuple(sorted([bag1.bag_id, bag2.bag_id]))
                                    if key1 not in visited_pairs:
                                        visited_pairs.add(key1)
                                        
                                        a = calculate_intersection_area_ltrb(
                                            last_point1, 
                                            last_point2
                                        )
                                        cb = check_box_relationship(
                                            last_point1, 
                                            last_point2
                                        )
                                        
                                        """c_1, r__1 = box_to_circle(last_point1)
                                        c_2, r__2 = box_to_circle(last_point2)

                                        intersection_area, percentage_intersection = circle_intersection_area(r__1, c_1, r__2, c_2)
                                        a = percentage_intersection"""

                                        if a >= percent_area or cb[0] is True:
                                            result_intersection_bag.append((
                                                (bag1.bag_id, bag2.bag_id), 
                                                last_point1, 
                                                last_point2, 
                                                a, 
                                                cb,
                                                (bag1, bag2)
                                                ))
        return result_intersection_bag
    
    def find_other_pairs_pre(self, id_current_camera=-1, current_pairs=None):
        result_pairs = []
        if current_pairs is not None and len(current_pairs) > 0:
            # Створюємо множину всіх ID пар у current_pairs для ефективного пошуку
            current_pairs_ids = {pair.current_id for pair in current_pairs if isinstance(pair, Pair)}  # noqa: E501
            
            for pone in self.pairs:
                if isinstance(pone, Pair):
                    if pone.id_camera == id_current_camera:# and not pone.cold:
                        # Перевіряємо, чи ID пари є в current_pairs_ids
                        if pone.current_id not in current_pairs_ids:
                            #pone.pre_cold = True
                            result_pairs.append(pone)
        return result_pairs

    def test_pone(self, current_state, delta, its_new_pair, pone, limit_len, pair_on_other_cameras):
        state_add = False
        if isinstance(pone, Pair):
            if isinstance(pone.bag, Bag) and isinstance(pone.human, Human):
                if len(pone.bag.last_cam) > 2 and len(pone.human.last_cam) > 2:
                    if( 
                        list(pone.bag.last_cam)[-2] != list(pone.human.last_cam)[-2] or 
                        list(pone.bag.last_cam)[-1] != list(pone.human.last_cam)[-1] 
                        ):
                        state_add = True
                        
                if pone.get_len() > limit_len:
                    if delta is True:
                        state_add = True
                        
                if its_new_pair is True and current_state is True:
                    state_exist = False
                    for other_pair in pair_on_other_cameras:
                        if isinstance(other_pair, Pair):
                            if isinstance(other_pair.bag, Bag) and isinstance(other_pair.human, Human):
                                if other_pair.bag.bag_id == pone.bag.bag_id and other_pair.human.human_id == pone.human.human_id:
                                    state_exist = True
                                    break 
                    if state_exist is False:
                        state_add = True
                    
                
                if pone.get_len() == limit_len + 1:
                    for other_pair in pair_on_other_cameras:
                        if isinstance(other_pair, Pair):
                            if isinstance(other_pair.bag, Bag) and isinstance(other_pair.human, Human):
                                if other_pair.bag.bag_id == pone.bag.bag_id and other_pair.human.human_id == pone.human.human_id:
                                    if other_pair.get_len() > limit_len:
                                        if list(other_pair.pair_state)[-1] != current_state:
                                            state_add = True
                                            break
        return state_add

    def get_real_pair(self):
        array_real_pair = []
        for pone in self.pairs:
            if isinstance(pone, Pair):
                if pone.current_state is True or pone.current_state == 1:
                    array_real_pair.append(pone)
        return array_real_pair
    
    def push_tracks(self, tracks, id_camera=-1, trackers_capacitor=None):
        
        if trackers_capacitor is not None and isinstance(trackers_capacitor, TrackersCapacitor):
            
            with self.locker:
                
                for track in tracks:
                    if track.is_confirmed() is False or track.time_since_update > 1:
                        continue
                    bbox = track.to_ltrb()
                    original_ltwh = track.original_ltwh
                
                    if track.det_class in self.human_ids:
                        h = self.find_human(trackers_capacitor.get_uid_human(int(id_camera), int(track.track_id), int(track.det_class)) )
                        if h is None:
                            h = Human(
                                human_id=trackers_capacitor.get_uid_human(int(id_camera), int(track.track_id), int(track.det_class)),
                                det_class=track.det_class
                                )
                            h.append(id_camera, (bbox, original_ltwh))
                            self.append_human(h)
                        else:
                            h.append(id_camera, (bbox, original_ltwh)) 
                            
                    elif track.det_class in self.bag_ids:
                        b = self.find_bag(trackers_capacitor.get_uid_bag(int(id_camera), int(track.track_id), int(track.det_class)))
                        if b is None:
                            b = Bag(
                                bag_id=trackers_capacitor.get_uid_bag(int(id_camera), int(track.track_id), int(track.det_class)),
                                det_class=track.det_class
                                )
                            b.append(id_camera, (bbox, original_ltwh))
                            self.append_bag(b)
                        else:
                            b.append(id_camera, (bbox, original_ltwh))
                
                
                self.enable_track_camera_id(id_camera)
                
                result_intersection_human = self.intersection_human(id_camera)
                
                result_intersection_bag = self.intersection_bag(id_camera)
                
                #щоб дублі видалити
                if len(result_intersection_human) > 0 or len(result_intersection_bag) > 0:

                    for rih in result_intersection_human:
                        key = (rih[0][0], rih[0][1])
                        if key not in self.unions_humans or rih[3] > self.unions_humans[key][3]:
                            self.unions_humans[key] = rih

                    for rib in result_intersection_bag:
                        key = (rib[0][0], rib[0][1])
                        if key not in self.unions_bags or rib[3] > self.unions_bags[key][3]:
                            self.unions_bags[key] = rib 
                    pass
                    
                array_pair = []
                for i, bag1 in enumerate(self.bags):
                    if isinstance(bag1, Bag):
                        bp = bag1.get_points(id_camera)
                        if bp != None:
                            if len(bp) > 0:
                                last_point_bag = bp[-1][1][0]
                                original_ltwh_1 = bp[-1][1][1]
                                if original_ltwh_1 is None:
                                    continue
                                for j, human1 in enumerate(self.humans):
                                    if isinstance(human1, Human):
                                        hp = human1.get_points(id_camera)
                                        if hp != None:
                                            if len(hp) > 0:
                                                last_point_human = hp[-1][1][0]
                                                original_ltwh_2 = hp[-1][1][1]
                                                if original_ltwh_2 is None:
                                                    continue
                                                
                                                                                                
                                                (circle_pb_last_x, circle_pb_last_y), circle_pb_last_radius = box_to_circle(last_point_bag)
                                                (circle_ph_last_x, circle_ph_last_y), circle_ph_last_radius = box_to_circle(last_point_human)
                                                
                                                """state_in = circle_intersection(
                                                    (circle_pb_last_x, circle_pb_last_y), 
                                                    (circle_ph_last_x, circle_ph_last_y), 
                                                    circle_pb_last_radius, 
                                                    circle_ph_last_radius    
                                                )"""
                                                
                                                state_in = circle_intersection_area(
                                                    circle_pb_last_radius, 
                                                    (circle_pb_last_x, circle_pb_last_y), 
                                                    circle_ph_last_radius, 
                                                    (circle_ph_last_x, circle_ph_last_y)
                                                )
                                                
                                                if state_in[1] > push_tracks_state_in_circle_intersection_area:
                                                    state_in = 1
                                                else:
                                                    state_in = 0    
                                                    
                                                center1 = (int(((last_point_bag[0]) + (last_point_bag[2]))/2), 
                                                            int(((last_point_bag[1]) + (last_point_bag[3]))/2))
                                                
                                                center2 = (int(((last_point_human[0]) + (last_point_human[2]))/2), 
                                                            int(((last_point_human[1]) + (last_point_human[3]))/2))
                                                
                                                len_pp = distance_between_points(center1, center2)
                                                
                                                state_original = True 
                                                array_pair.append((
                                                    i, 
                                                    j, 
                                                    len_pp, 
                                                    last_point_bag, 
                                                    last_point_human, 
                                                    bag1.det_class, 
                                                    human1.det_class,
                                                    state_in,
                                                    bag1,
                                                    human1,
                                                    state_original
                                                ))
                                        else:
                                            pass
                        else:
                            pass          
                
                print(array_pair)
                
                unique_data = {}
                #пошук пар мінімальної відстані між сумкою і людиною
                for i_1, item_one in enumerate(array_pair):
                    item_bag = item_one[8]
                    item_human = item_one[9]
                    if isinstance(item_bag, Bag) and isinstance(item_human, Human):
                        for i_2, item_two in enumerate(array_pair):
                            #if i_1 != i_2:
                                item_bag_inline = item_two[8]
                                item_human_inline = item_two[9]
                                if isinstance(item_bag_inline, Bag) and isinstance(item_human_inline, Human):
                                    key = (item_bag.bag_id)
                                    if item_bag.bag_id == item_bag_inline.bag_id:
                                        if key not in unique_data:
                                            if item_one[2] <= item_two[2]:
                                                unique_data[key] = item_one
                                            elif item_one[2] >= item_two[2]:
                                                unique_data[key] = item_two
                                        else:
                                            if item_one[2] <= unique_data[key][2] and item_two[2] > unique_data[key][2]:
                                                unique_data[key] = item_one
                                            elif item_one[2] >= unique_data[key][2] and item_two[2] < unique_data[key][2]:
                                                unique_data[key] = item_two
                                            
                array_pair = list(unique_data.values())
                
                print(array_pair)
                
                if len(array_pair) > 0:
                    pass
                
                unique_data = {}
                    
                for item in array_pair:
                    item_bag = item[8]
                    item_human = item[9]
                    if isinstance(item_bag, Bag) and isinstance(item_human, Human):
                        key = (item_bag.bag_id, item_human.human_id)
                        if key not in unique_data or item[2] < unique_data[key][2]:
                            unique_data[key] = item

                array_pair = list(unique_data.values())
                
                
                #якщо пара є оновити інакше створити 
                pair_on_other_cameras = self.find_pair_on_other_cameras(id_camera)
                array_pair_hot = []
                array_mod = []
                limit_len = push_tracks_test_pone_limit_len
                for one_pair in array_pair:
                    if isinstance(one_pair[9], Human) and isinstance(one_pair[8], Bag):
                        pone = self.find_pair(id_camera, one_pair[9].human_id, one_pair[8].bag_id)
                        its_new_pair = False
                        if pone is None:
                            pone = Pair(id_camera, one_pair[9], one_pair[8])
                            current_state, delta = pone.update(one_pair[7], one_pair[10])
                            self.append_pair(pone)
                            its_new_pair = True
                        else:
                            current_state, delta = pone.update(one_pair[7], one_pair[10])
                        """if pone.cold or pone.pre_cold:
                            pone.cold = False
                            pone.pre_cold = False"""
                        array_pair_hot.append(pone)
                        state_add = self.test_pone(
                            current_state, 
                            delta, 
                            its_new_pair, 
                            pone, 
                            limit_len, 
                            pair_on_other_cameras
                        )
                        
                        if state_add is True:
                            array_mod.append(pone)
                            
                        #print("f")
                        pass
                
                
                array_pair_pre = self.find_other_pairs_pre(id_camera, array_pair_hot)
                
                pass
                
                if len(array_pair_pre) > 0:
                    pass
                
                for pone in array_pair_pre:
                    if isinstance(pone, Pair):
                        its_new_pair = False
                        
                        current_state, delta = pone.update(0)
                        
                        """if delta is True and pone.pre_cold is True:
                            pone.cold = True"""
                        
                        state_add = self.test_pone(current_state, delta, its_new_pair, pone, limit_len, pair_on_other_cameras)
                        
                        if state_add is True:
                            array_mod.append(pone)
                            
                        #print("f")
                        pass
                
                pass
                
                if len(array_mod) > 0:
                    for one_elem in array_mod:
                        if isinstance(one_elem, Pair):
                            if isinstance(one_elem.bag, Bag) and isinstance(one_elem.human, Human):
                                pass
                                #print(f"{one_elem.bag.bag_id} {one_elem.human.human_id}")
                    pass
                
                pass
                
                for one_intersect in result_intersection_human:
                    curr_key = one_intersect[0]
                    if len(self.human_groups) > 0:
                        index_exist_1 = None
                        index_exist_2 = None
                        for i_elem, one_elem_gb in enumerate(self.human_groups):
                            keys = [one_human.human_id for one_human in one_elem_gb if isinstance(one_human, Human)]
                            if curr_key[0] not in keys and curr_key[1] in keys:
                                index_exist_2 = i_elem
                                self.human_groups[i_elem].append(one_intersect[5][0])
                            elif curr_key[0] in keys and curr_key[1] not in keys:
                                index_exist_1 = i_elem
                                self.human_groups[i_elem].append(one_intersect[5][1])
                            elif curr_key[0] not in keys and curr_key[1] not in keys:
                                pass
                        if index_exist_1 is None and index_exist_2 is None:
                            self.human_groups.append([one_intersect[5][0], one_intersect[5][1]])
                    else:
                        self.human_groups.append([one_intersect[5][0], one_intersect[5][1]])
                
                pass
                
                for one_intersect in result_intersection_bag:
                    curr_key = one_intersect[0]    
                    if len(self.bags_groups) > 0:
                        index_exist_1 = None
                        index_exist_2 = None
                        for i_elem, one_elem_gb in enumerate(self.bags_groups):
                            keys = [one_bag.bag_id for one_bag in one_elem_gb if isinstance(one_bag, Bag)]
                            if curr_key[0] not in keys and curr_key[1] in keys:
                                index_exist_2 = i_elem
                                self.bags_groups[i_elem].append(one_intersect[5][0])
                            elif curr_key[0] in keys and curr_key[1] not in keys:
                                index_exist_1 = i_elem
                                self.bags_groups[i_elem].append(one_intersect[5][1])
                            elif curr_key[0] not in keys and curr_key[1] not in keys:
                                pass 
                        if index_exist_1 is None and index_exist_2 is None:
                            self.bags_groups.append([one_intersect[5][0], one_intersect[5][1]])
                    else:
                        self.bags_groups.append([one_intersect[5][0], one_intersect[5][1]])

                pass

                for one_human_glob in self.humans:
                    if isinstance(one_human_glob, Human):
                        curr_key = one_human_glob.human_id
                        is_exist = False
                        if len(self.human_groups) > 0:
                            for i_elem, one_elem_gb in enumerate(self.human_groups):
                                keys = [one_human.human_id for one_human in one_elem_gb if isinstance(one_human, Human)]
                                if curr_key in keys:
                                    is_exist = True 
                                    break
                        if is_exist is False:
                            self.human_groups.append([one_human_glob])
                
                pass    
                
                for one_bag_glob in self.bags:
                    if isinstance(one_bag_glob, Bag):
                        curr_key = one_bag_glob.bag_id  
                        is_exist = False 
                        if len(self.bags_groups) > 0:
                            for i_elem, one_elem_gb in enumerate(self.bags_groups):
                                keys = [one_bag.bag_id for one_bag in one_elem_gb if isinstance(one_bag, Bag)]
                                if curr_key in keys:
                                    is_exist = True 
                                    break
                        if is_exist is False:
                            self.bags_groups.append([one_bag_glob])
                
                pass
                
                for one_group in self.human_groups:
                    if len(self.human_groups) > 1:
                        pass
                    
                    finded_entity = None
                    for single_entity in self.entities:
                        if isinstance(single_entity, Entity):
                            break_is = False
                            for one_elem_group in one_group:
                                if isinstance(one_elem_group, Human):
                                    if single_entity.exist_human_id(one_elem_group.human_id):
                                        finded_entity = single_entity
                                        break_is = True
                            if break_is is True:
                                break
                    
                    if finded_entity is None:
                        entity = Entity()  
                        self.entities.append(entity)
                        finded_entity = entity
                        
                    if finded_entity is not None and isinstance(finded_entity, Entity):
                        for one_elem_group in one_group:
                            if isinstance(one_elem_group, Human):
                                if finded_entity.exist_human_id(one_elem_group.human_id) is False:
                                    finded_entity.push_human(one_elem_group)

                pass
                
                for one_pair in array_mod:
                    if isinstance(one_pair, Pair):
                        if isinstance(one_pair.bag, Bag) and isinstance(one_pair.human, Human): 
                                
                            for single_entity in self.entities:
                                if isinstance(single_entity, Entity):
                                    if single_entity.exist_human_id(one_pair.human.human_id):
                                        
                                        bag_group = []
                                        if len(self.bags_groups) > 0:
                                            curr_key = one_pair.bag.bag_id
                                            for i_elem, one_elem_gb in enumerate(self.bags_groups):
                                                keys = [one_bag.bag_id for one_bag in one_elem_gb if isinstance(one_bag, Bag)]
                                                if curr_key in keys:
                                                    bag_group = one_elem_gb
                                                    break
                                        
                                        single_entity.push_pair(one_pair)
                                        
                                        single_entity.push_bag(one_pair.bag)
                                        
                                        single_entity.push_bag_group(bag_group, id_camera)
                                        
                                        break
                                
            pass
                            
            if len(self.entities) > 0:
                pass
            if len(self.entities) > 1:
                pass
            #print("f")
        return self.entities
            
        
        
def compare_arrays(camera_id, pman, eman, array_current, array_all):
    if isinstance(eman, EntityManager) and isinstance(pman, PairsManager):
        logs = eman.update(camera_id, array_current, array_all)   
        humans_and_bags = pman.get_bags_and_humans_by_logs(logs)
        array_all_humans_and_bags = []
        for elem in array_all:
            human_idx = elem[0]
            humans = pman.get_humans_by_array_idx(human_idx)
            bags_groups = []
            for elem_g in elem[1]:
                bags = pman.get_bags_by_array_idx(elem_g)
                bags_groups.append(bags)
            array_all_humans_and_bags.append((humans, bags_groups))
        return logs, humans_and_bags, array_all_humans_and_bags
    return None, None


pman = PairsManager()
eman = EntityManager()

