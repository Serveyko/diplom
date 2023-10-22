#ruff: noqa: E501
from db import Parameter, session, params_dict, start_load_save_params


yolov8_detect_model_path = r"yolov8n.pt"

main_process_count_frames = 1
main_process_timer_timestep = 300
main_process_timer_small_timestep = 30


standart_width = 600
standart_height = 400

timeout_is_file_widget = 30
timeout_widget = 30


resize_with_width = 600


function_caller_thread_state = "thread" #"timer" or "thread"


deepface_detector_backend = 'retinaface'


person = 0
handbag = 26
suitcase = 28
backpack = 24
white_list_person = [person]
white_list_handbag = [handbag, suitcase, backpack]

all_white_list = []
all_white_list.extend(white_list_person)
all_white_list.extend(white_list_handbag)


pair_maxlen = 10000
pair_magic_one = 0.2 #0.01
pair_magic_two = 0.2 #0.005
pair_threshold_one = 0.20
pair_threshold_two = 0.10


entity_max_len_deque_images_camera = 10
entity_after_reconfig_bag_group_percent_area = 20


pairs_manager_max_len_deque_points_id = 300
pairs_manager_intersection_human_percent_area = 30
pairs_manager_intersection_bag_percent_area = 30


intersection_percent_area = 30
intersection_kad_a = 1


timer_log_update_update_interval = 1000
timer_human_update_update_interval = 1000
timer_merge_by_face_timestep = 1000



push_tracks_state_in_circle_intersection_area = 30
push_tracks_test_pone_limit_len = 1
push_tracks_delta_time_limit = 1


intersection_human_delta_time_limit = 1.0
intersection_bag_delta_time_limit = 1.0

"""param_yolov8_detect_model_path = Parameter(name='yolov8_detect_model_path', original_value=r"D:\MY_WORKS\FindHumans\yolov8n.pt")
    param_main_process_count_frames = Parameter(name='main_process_count_frames', original_value=1)
    param_main_process_timer_timestep = Parameter(name='main_process_timer_timestep', original_value=300)
    param_main_process_timer_small_timestep = Parameter(name='main_process_timer_small_timestep', original_value=30)
    param_standart_width = Parameter(name='standart_width', original_value=600)
    param_standart_height = Parameter(name='standart_height', original_value=400)
    param_timeout_is_file_widget = Parameter(name='timeout_is_file_widget', original_value=30)
    param_timeout_widget = Parameter(name='timeout_widget', original_value=30)
    param_resize_with_width = Parameter(name='resize_with_width', original_value=600)
    param_database_url = Parameter(name='database_url', original_value='sqlite:///people_logs_photos.db')
    param_deepface_detector_backend = Parameter(name='deepface_detector_backend', original_value='retinaface')
    param_person = Parameter(name='person', original_value=0)
    param_handbag = Parameter(name='handbag', original_value=26)
    param_suitcase = Parameter(name='suitcase', original_value=28)
    param_pair_maxlen = Parameter(name='pair_maxlen', original_value=10000)
    param_pair_magic_one = Parameter(name='pair_magic_one', original_value=0.2)
    param_pair_magic_two = Parameter(name='pair_magic_two', original_value=0.2)
    param_pair_threshold_one = Parameter(name='pair_threshold_one', original_value=0.20)
    param_pair_threshold_two = Parameter(name='pair_threshold_two', original_value=0.1)
    param_entity_max_len_deque_images_camera = Parameter(name='entity_max_len_deque_images_camera', original_value=10)
    param_entity_after_reconfig_bag_group_percent_area = Parameter(name='entity_after_reconfig_bag_group_percent_area', original_value=20)
    param_pairs_manager_max_len_deque_points_id = Parameter(name='pairs_manager_max_len_deque_points_id', original_value=300)
    param_pairs_manager_intersection_human_percent_area = Parameter(name='pairs_manager_intersection_human_percent_area', original_value=10)
    param_pairs_manager_intersection_bag_percent_area = Parameter(name='pairs_manager_intersection_bag_percent_area', original_value=30)
    param_intersection_percent_area = Parameter(name='intersection_percent_area', original_value=30)
    param_intersection_kad_a = Parameter(name='intersection_kad_a', original_value=1)
    param_timer_log_update_update_interval = Parameter(name='timer_log_update_update_interval', original_value=1000)
    param_timer_human_update_update_interval = Parameter(name='timer_human_update_update_interval', original_value=1000)
    param_timer_merge_by_face_timestep = Parameter(name='timer_merge_by_face_timestep', original_value=1000)
    #param_ = Parameter(name='', original_value=-1)
    
    session.add(param_yolov8_detect_model_path)
    session.add(param_main_process_count_frames)
    session.add(param_main_process_timer_timestep)
    session.add(param_main_process_timer_small_timestep)
    session.add(param_standart_width)
    session.add(param_standart_height)
    session.add(param_timeout_is_file_widget)
    session.add(param_timeout_widget)
    session.add(param_resize_with_width)
    session.add(param_database_url)
    session.add(param_deepface_detector_backend)
    session.add(param_person)
    session.add(param_handbag)
    session.add(param_suitcase)
    session.add(param_pair_maxlen)
    session.add(param_pair_magic_one)
    session.add(param_pair_magic_two)
    session.add(param_pair_threshold_one)
    session.add(param_pair_threshold_two)
    session.add(param_entity_max_len_deque_images_camera)
    session.add(param_entity_after_reconfig_bag_group_percent_area)
    session.add(param_pairs_manager_max_len_deque_points_id)
    session.add(param_pairs_manager_intersection_human_percent_area)
    session.add(param_pairs_manager_intersection_bag_percent_area)
    session.add(param_intersection_percent_area)
    session.add(param_intersection_kad_a)
    session.add(param_timer_log_update_update_interval)
    session.add(param_timer_human_update_update_interval)
    session.add(param_timer_merge_by_face_timestep)
    session.commit()"""


def load_all_config():
    global yolov8_detect_model_path
    global main_process_timer_timestep
    global main_process_timer_small_timestep
    global standart_width
    global standart_height
    global timeout_is_file_widget
    global timeout_widget
    global resize_with_width
    global deepface_detector_backend
    global pair_maxlen
    global pair_magic_one
    global pair_magic_two
    global pair_threshold_one
    global pair_threshold_two
    global entity_max_len_deque_images_camera
    global entity_after_reconfig_bag_group_percent_area
    global pairs_manager_max_len_deque_points_id
    global pairs_manager_intersection_human_percent_area
    global pairs_manager_intersection_bag_percent_area
    global intersection_percent_area
    global intersection_kad_a
    global timer_log_update_update_interval
    global timer_human_update_update_interval
    global timer_merge_by_face_timestep
    global push_tracks_state_in_circle_intersection_area
    global push_tracks_test_pone_limit_len
    global push_tracks_delta_time_limit
    global intersection_human_delta_time_limit
    global intersection_bag_delta_time_limit
    
    loaded_params = start_load_save_params(session, params_dict)

    for sparam in loaded_params:
        if isinstance(sparam, Parameter):
            name = sparam.name
            if name == 'yolov8_detect_model_path':
                yolov8_detect_model_path = sparam.current_value
                pass
            elif name == 'main_process_timer_timestep':
                main_process_timer_timestep = sparam.current_value
                pass
            elif name == 'main_process_timer_small_timestep':
                main_process_timer_small_timestep = sparam.current_value
                pass
            elif name == 'standart_width':
                standart_width = sparam.current_value
                pass
            elif name == 'standart_height':
                standart_height = sparam.current_value
                pass
            elif name == 'timeout_is_file_widget':
                timeout_is_file_widget = sparam.current_value
                pass
            elif name == 'timeout_widget':
                timeout_widget = sparam.current_value
                pass
            elif name == 'resize_with_width':
                resize_with_width = sparam.current_value
                pass
            elif name == 'deepface_detector_backend':
                deepface_detector_backend = sparam.current_value
                pass
            elif name == 'pair_maxlen':
                pair_maxlen = sparam.current_value
                pass
            elif name == 'pair_magic_one':
                pair_magic_one = sparam.current_value
                pass
            elif name == 'pair_magic_two':
                pair_magic_two = sparam.current_value
                pass
            elif name == 'pair_threshold_one':
                pair_threshold_one = sparam.current_value
                pass
            elif name == 'pair_threshold_two':
                pair_threshold_two = sparam.current_value
                pass
            elif name == 'entity_max_len_deque_images_camera':
                entity_max_len_deque_images_camera = sparam.current_value
                pass
            elif name == 'entity_after_reconfig_bag_group_percent_area':
                entity_after_reconfig_bag_group_percent_area = sparam.current_value
                pass
            elif name == 'pairs_manager_max_len_deque_points_id':
                pairs_manager_max_len_deque_points_id = sparam.current_value
                pass
            elif name == 'pairs_manager_intersection_human_percent_area':
                pairs_manager_intersection_human_percent_area = sparam.current_value
                pass
            elif name == 'pairs_manager_intersection_bag_percent_area':
                pairs_manager_intersection_bag_percent_area = sparam.current_value
                pass
            elif name == 'intersection_percent_area':
                intersection_percent_area = sparam.current_value
                pass
            elif name == 'intersection_kad_a':
                intersection_kad_a = sparam.current_value
                pass
            elif name == 'timer_log_update_update_interval':
                timer_log_update_update_interval = sparam.current_value
                pass
            elif name == 'timer_human_update_update_interval':
                timer_human_update_update_interval = sparam.current_value
                pass
            elif name == 'timer_merge_by_face_timestep':
                timer_merge_by_face_timestep = sparam.current_value
                pass
            elif name == 'push_tracks_state_in_circle_intersection_area':
                push_tracks_state_in_circle_intersection_area = sparam.current_value
                pass
            elif name == 'push_tracks_test_pone_limit_len':
                push_tracks_test_pone_limit_len = sparam.current_value
                pass
            elif name == 'push_tracks_delta_time_limit':
                push_tracks_delta_time_limit = sparam.current_value
                pass
            elif name == 'intersection_human_delta_time_limit':
                intersection_human_delta_time_limit = sparam.current_value
                pass
            elif name == 'intersection_bag_delta_time_limit':
                intersection_bag_delta_time_limit = sparam.current_value
                pass
                

load_all_config()


