# ruff: noqa: E501
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, PickleType

database_url = 'sqlite:///people_logs_photos.db'

# Створення з'єднання з базою даних SQLite
engine = create_engine(database_url)

# Створення базового класу для визначення моделі
Base = declarative_base()


class Human(Base):
    __tablename__ = 'humans'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    images_face = Column(PickleType)
    log_images = Column(PickleType)
    idx = Column(PickleType)

class HumanDB:
    
    def __init__(self) -> None:
        self.images_face = []
        self.log_images = []
        self.name = ""
        self.idx = []
        self.db_id = None
        pass
    

class Parameter(Base):
    __tablename__ = 'parameters'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    original_value = Column(PickleType)
    current_value = Column(PickleType)

    def __init__(self, name, original_value, current_value):
        self.name = name
        self.original_value = original_value
        self.current_value = current_value

    def __str__(self):
        return f"Parameter(name='{self.name}', original_value='{self.original_value}', current_value='{self.current_value}')"


Base.metadata.create_all(engine)
SessionM = sessionmaker(bind=engine)
session = SessionM()

def add_human_to_db(session, name, images_face, log_images, idx, db_id):
    human_to_delete = session.query(Human).filter_by(id=db_id).first()
    if human_to_delete:
        delete_human_from_db(session, human_to_delete.id)
        
    new_human = Human(name=name, images_face=images_face, log_images=log_images, idx=idx)
    session.add(new_human)
    session.commit()

def load_humans(session):
    humans = session.query(Human).all()
    return humans

def delete_human_from_db(session, db_id):
    human_to_delete = session.query(Human).filter_by(id=db_id).first()

    if human_to_delete:
        session.delete(human_to_delete)
        session.commit()

params_dict = {
    'yolov8_detect_model_path': r"yolov8n.pt",
    'main_process_timer_timestep': 300,
    'main_process_timer_small_timestep': 30,
    'standart_width': 600,
    'standart_height': 400,
    'timeout_is_file_widget': 30,
    'timeout_widget': 30,
    'resize_with_width': 600,
    'deepface_detector_backend': 'retinaface',
    'pair_maxlen': 10000,
    'pair_magic_one': 0.2,
    'pair_magic_two': 0.2,
    'pair_threshold_one': 0.20,
    'pair_threshold_two': 0.1,
    'entity_max_len_deque_images_camera': 10,
    'entity_after_reconfig_bag_group_percent_area': 20,
    'pairs_manager_max_len_deque_points_id': 300,
    'pairs_manager_intersection_human_percent_area': 10,
    'pairs_manager_intersection_bag_percent_area': 30,
    'intersection_percent_area': 30,
    'intersection_kad_a': 1,
    'timer_log_update_update_interval': 1000,
    'timer_human_update_update_interval': 1000,
    'timer_merge_by_face_timestep': 1000,
    'push_tracks_state_in_circle_intersection_area': 30,
    'push_tracks_test_pone_limit_len': 1,
    'push_tracks_delta_time_limit': 1.0,
    'intersection_human_delta_time_limit': 1.0,
    'intersection_bag_delta_time_limit': 1.0
}

def save_one_params_settings(session, param_name, original_value, current_value):
    param = None
    param = session.query(Parameter).filter_by(name=param_name).first()
    if param and isinstance(param, Parameter):
        param.name = param_name
        param.original_value = original_value
        param.current_value = current_value
    else:
        param = Parameter(name=param_name, original_value=original_value, current_value=current_value)
        
    if param is not None:
        session.add(param)
        session.commit()

def save_params_settings(session, params_dict: dict={}):
    for elem in params_dict.keys():
        param = Parameter(name=elem, original_value=params_dict[elem])
        session.add(param)
        session.commit()

def load_all_params_settings(session, params_to_load:dict={}):
    loaded_params = []
    for param_name in params_to_load.keys():
        param = session.query(Parameter).filter_by(name=param_name).first()
        if param:
            loaded_params.append(param)
    return loaded_params

def start_load_save_params(session, params_to_load:dict={}):
    loaded_params = []
    for param_name in params_to_load.keys():
        param = session.query(Parameter).filter_by(name=param_name).first()
        if param:
            loaded_params.append(param) 
        else:
            param = Parameter(name=param_name, original_value=params_dict[param_name], current_value=params_dict[param_name])
            session.add(param)
            session.commit()
            loaded_params.append(param)
    return loaded_params




