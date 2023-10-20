#ruff: noqa: E501

from plot_entity import PlotEntity

from db import HumanDB

from deepface import DeepFace

from config import deepface_detector_backend

def exstract_faces(image):
    obj_find = None
    try:
        obj_find = DeepFace.extract_faces(
            image, 
            detector_backend = deepface_detector_backend
        )
    except Exception as ex:
        print(str(ex))
    
    return obj_find

def verify_faces(image1, image2) -> bool:
    try:
        result = DeepFace.verify(img1_path = image1, img2_path = image2, detector_backend = deepface_detector_backend)
        if isinstance(result, dict):
            #print("""BEFORE""") 
            #[print(f"   {val}: {result[val]}") for val in result.keys()]
            #print("""AFTER""")
            return result["verified"]
    finally:
        pass 
        #print(ex)
    return False


def work_plot_entity(plot_humans):
    """Попередній етап це зібрати дані про те які фото верифіковані 
    Наступний етап це мержинг груп 

    Args:
        plot_humans (_type_): _description_

    Returns:
        _type_: _description_
    """
    array_state = [] # [(True or False, i, j)]
    seen_indices = []
    for i, elem1 in enumerate(plot_humans):
        for j, elem2 in enumerate(plot_humans):
            if i != j and (i, j) not in seen_indices and (j, i) not in seen_indices:
                seen_indices.append((i, j))
                
                if isinstance(elem1, PlotEntity) and isinstance(elem2, PlotEntity):
                    human_db_1 = elem1.get_human_db()
                    human_db_2 = elem2.get_human_db()
                    if (
                        (human_db_1 is not None and human_db_2 is None) or 
                        (human_db_1 is None and human_db_2 is not None)
                    ):
                        face_images = None 
                        human_images = None 
                        if isinstance(human_db_1, HumanDB):
                            face_images = elem1.get_face_images()
                            human_images = elem2.get_human_images()
                        elif isinstance(human_db_2, HumanDB):
                            human_images = elem1.get_human_images()
                            face_images = elem2.get_face_images()
                            
                        if human_images is not None and face_images is not None:
                            one_true = False
                            for h_image in human_images:
                                for f_image in face_images:
                                    one_true = verify_faces(h_image, f_image)
                                    if one_true is True:
                                        break
                                if one_true is True:
                                    break
                            array_state.append((one_true, i, j))  
                            
    
    array_true_state = []
    for elem in array_state:
        (state_, i_cor, j_cor) = elem[0], elem[1], elem[2]
        if state_ == True:  # noqa: E712
            array_true_state.append(elem)
            #print(f"{state_}, {i_cor}, {j_cor}")
    
    array_none = []
    for ts in array_true_state:
        (state_, i_cor, j_cor) = ts
        p1 = plot_humans[i_cor]
        p2 = plot_humans[j_cor]
        if isinstance(p1, PlotEntity) and isinstance(p2, PlotEntity):
            complete_p = None 
            other_p = None 
            complete_index = -1
            other_index = -1
            if p1.get_human_db() is not None and p2.get_human_db() is None:
                complete_p = p1 
                other_p = p2 
                complete_index = i_cor
                other_index = j_cor
            elif p2.get_human_db() is not None and p1.get_human_db() is None: 
                complete_p = p2
                other_p = p1 
                complete_index = j_cor
                other_index = i_cor 
                
            entities = other_p.get_entities()
            for single_entity in entities:
                complete_p.push_entity(single_entity)
            
            if i_cor == complete_index:
                plot_humans[i_cor] = complete_p
            if j_cor == complete_index:
                plot_humans[j_cor] = complete_p
            
            if i_cor == other_index:
                array_none.append(i_cor)
                #print(f"i_cor = {i_cor} = None")
            if j_cor == other_index:
                array_none.append(j_cor)
                #print(f"j_cor = {j_cor} = None")
    
    for i, el in enumerate(plot_humans):
        if i in array_none:
            plot_humans[i] = None
                              
    result_plot_entity = []
    for ph in plot_humans:
        if ph is not None:
            result_plot_entity.append(ph)
        else:
            pass
    return result_plot_entity
