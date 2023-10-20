import torch
from ultralytics import YOLO

from config import yolov8_detect_model_path

@torch.no_grad()
def init_yolov8_bags(path_model, device='cpu'):
    model = YOLO(path_model)
    return model

yolov8_model_bags = None


def get_yolov8_model_bags():
    global yolov8_model_bags
    if yolov8_model_bags is None:
        yolov8_model_bags = init_yolov8_bags(yolov8_detect_model_path)
    
    return yolov8_model_bags

