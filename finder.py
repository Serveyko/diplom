# ruff: noqa: E501

import torch
from frame_data import FrameData
import matplotlib.pyplot as plt
from initializer_yolov import get_yolov8_model_bags
from functions import get_object_names_with_indices, resize_with_aspect_ratio
import numpy as np
from config import resize_with_width, all_white_list
import cv2
from framework import pman, trackers_capacitor, Entity, DeepSort, box_to_circle, eman, compare_arrays

from framework import EntityManager

torch.set_num_threads(1)

counter_f = 0

def find(
    frame: FrameData, 
    device='cpu'
    ):
    """Основна функція детектування через модель yolov8

    Args:
        frame (FrameData): _description_
        device (str, optional): _description_. Defaults to 'cpu'.

    Returns:
        _type_: _description_
    """
    data_frame = frame.get_frame()
    if data_frame is not None:
        frame_height, frame_width, channels = data_frame.shape
        real_frame = data_frame.copy() 
        real_frame = resize_with_aspect_ratio(real_frame, new_width=700)
        real_frame = cv2.cvtColor(real_frame, cv2.COLOR_BGR2RGB) 
        
        plot_frame = real_frame.copy()
        
        with torch.no_grad():
            results = get_yolov8_model_bags()(real_frame, verbose=False)
            result = results[0]
            boxes = result.boxes 
            names2 = get_yolov8_model_bags().names
            cls_boxes = boxes.cls
            ci = get_object_names_with_indices(cls_boxes, names2)
            annotated_frame = result.plot()  
            annotated_frame = resize_with_aspect_ratio(
                annotated_frame, 
                new_width=resize_with_width
            )
        
        frame.real_frame = real_frame
        frame.yolov8 = result
        frame.index_name_yolov8 = ci
        
        dataframe_uid  = frame.dataframe_uid
            
        yolov8_data = result
        
        boxes = yolov8_data.boxes  
        names2 = get_yolov8_model_bags().names
        cls_boxes = boxes.cls
        conf = boxes.conf
        masks = yolov8_data.masks    # noqa: F841
        keypoints = yolov8_data.keypoints    # noqa: F841
        probs = yolov8_data.probs  # noqa: F841
        
        xywh = boxes.xywh

        dp = []
        conf_shape = conf.shape[0]
        for i in range(conf_shape):
            if int(cls_boxes[i].item()) in all_white_list:
                el = (
                    [
                        xywh[i][0] - int(xywh[i][2] / 2), 
                        xywh[i][1] - int(xywh[i][3] / 2), 
                        xywh[i][2], 
                        xywh[i][3]
                    ], 
                    conf[i].item(), 
                    int(cls_boxes[i].item())
                ) 
                dp.append(el)
        
        tracker = trackers_capacitor.get(dataframe_uid)
        tracks = []
        if isinstance(tracker, DeepSort):
            tracks = tracker.update_tracks(dp, frame=real_frame) 
        else:
            if tracker is None:
                tracker = trackers_capacitor.create_basic_tracker(dataframe_uid)
                if isinstance(tracker, DeepSort):
                    tracks = tracker.update_tracks(dp, frame=real_frame) 
        
        entities = pman.push_tracks(tracks, dataframe_uid, trackers_capacitor)
        
        if len(entities) > 0:
            #print(entities) 
            pass
        
        cmap = plt.get_cmap('tab20b')
        colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]

        for single_entity in entities:
            if isinstance(single_entity, Entity):
                color = colors[int(single_entity.current_id) % len(colors)]
                color = [i * 255 for i in color]

                se_info = single_entity.get_last_info(dataframe_uid)
                
                bbox = se_info["bbox_human"]
                original_ltwh = se_info["original_ltwh_human"]
                array_pts_group = se_info["array_pts_group_bag"]

                if original_ltwh is None:
                    color = [255, 0, 0]
                
                if bbox is not None: #and original_ltwh is not None
                    
                    (circle_ph_last_x, circle_ph_last_y), circle_ph_last_radius = box_to_circle(bbox)
                    
                    thickness = 2
                    cv2.circle(plot_frame, (circle_ph_last_x, circle_ph_last_y), circle_ph_last_radius, color, thickness)
                    
                    cv2.rectangle(
                        plot_frame, 
                        (int(bbox[0]),int(bbox[1])), 
                        (int(bbox[2]),int(bbox[3])), 
                        color,
                        2
                    )
                    cv2.rectangle(
                        plot_frame, 
                        (int(bbox[0]), int(bbox[1]-30)), 
                        (int(bbox[0])+(len("cs") +len(str(single_entity.current_id)))*17, 
                        int(bbox[1])), 
                        color, 
                        -1
                    )
                    cv2.putText(
                        plot_frame, 
                        "e "+"-"+str(single_entity.current_id),
                        (int(bbox[0]), 
                            int(bbox[1]-10)), 
                        0,
                        0.75, 
                        (255, 255, 255),
                        2
                    )
                
            if len(single_entity.pairs) > 0:
                pass

            if len(array_pts_group) > 0:
                pass
            
            for i_si, single_element in enumerate(array_pts_group):
                if len(single_element) > 0:
                    (center_x, center_y), radius = box_to_circle(single_element[0])
                    color = (0, 255, 0)
                    if single_element[1] is None:
                        color = (255, 0, 0)
                    thickness = 2
                    cv2.circle(plot_frame, (center_x, center_y), radius, color, thickness)
                    cv2.putText(
                        plot_frame, 
                        ""+str(i_si), 
                        (int(center_x), int(center_y)), 
                        0, 
                        0.75, 
                        (255, 255, 255),
                        2
                    )
        global counter_f
        if counter_f % 2 == 0:
            frame.set_frame(plot_frame)
        else:
            frame.set_frame(annotated_frame)
        counter_f += 1
        
        logs, humans_and_bags = None, None
        array_keys_entity = []
        array_keys_entity_all = []
        array_all_humans_and_bags = []
        for single_entity in entities:
            if isinstance(single_entity, Entity):
                hk_all, bk_all = single_entity.get_unique_identifiers()
                array_keys_entity_all.append((hk_all, bk_all))
                hk, bk = single_entity.get_unique_identifiers_active_status(dataframe_uid)
                array_keys_entity.append((hk, bk))
                
        if len(array_keys_entity) > 0:
            #print("KEYS START")
            #print(array_keys_entity)        
            #print("KEYS END")
            
            logs, humans_and_bags, array_all_humans_and_bags = compare_arrays(dataframe_uid, pman, eman, array_keys_entity, array_keys_entity_all)
            if len(logs) > 0:
                pass 
            if humans_and_bags is not None:
                if len(humans_and_bags[0]) > 0:
                    pass
        
        
        if logs is not None:
            for single_log in logs:
                if isinstance(single_log, EntityManager.ELog):
                    single_log.camera_id = dataframe_uid
                    
        
        frame.logs = logs
        frame.humans_and_bags = humans_and_bags
        frame.array_all_humans_and_bags = array_all_humans_and_bags
        frame.entities = entities
                   
    return frame

