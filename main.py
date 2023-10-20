# ruff: noqa: E501

import sys

import torch

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QFileDialog
from main_form import Ui_MainWindow

from functions import find_all_cameras
from available_camera_widget import AvailableCameraWidget
from available_camera_widget_is_file import AvailableCameraWidgetIsFile
from camera_widget_view import CameraWidgetView
from camera_widget_view_is_file import CameraWidgetViewIsFile
from settings_view import SettingsView
from frame_data import FrameData
from PyQt5.QtWidgets import QMessageBox
from config import (
    main_process_count_frames, 
    main_process_timer_small_timestep, 
    main_process_timer_timestep
)

from base import FrameDataContainer
from function_caller_thread import FunctionCallerThread
from PyQt5.QtCore import QMutex
from PyQt5.QtCore import QTimer

from framework import EntityManager

from PyQt5 import QtWidgets

from single_widget_log import CustomWidgetSingleLog

from single_widget_human import CustomWidgetSingleHuman

from create_human_view import CreateHumanView

from db import HumanDB, add_human_to_db, load_humans, session, delete_human_from_db
from db import Human as db_Human
from framework import Human, Bag, Entity
import cv2
import matplotlib.pyplot as plt
import numpy as np
from plot_entity import PlotEntity
from finder_deepface import work_plot_entity
from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
from config import timer_log_update_update_interval, timer_human_update_update_interval, timer_merge_by_face_timestep
torch.set_num_threads(1)

class MyMainWindow(QMainWindow, Ui_MainWindow):
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.process_count_frames = main_process_count_frames
        self.process_timer_timestep = main_process_timer_timestep
        self.process_timer_small_timestep = main_process_timer_small_timestep
        
        self.action_find_cameras.triggered.connect(self.find_cameras_button_f)
        self.action_imitation_camera_is_file.triggered.connect(self.imitation_camera_is_file)
        
        self.action_settings.triggered.connect(self.open_settings)
        
        self.create_humans_button.clicked.connect(self.create_humans)
        
        self.settings_dialog = SettingsView(self)
        self.settings_dialog.close()
        
        self.create_human_dialog = CreateHumanView(self)
        self.create_human_dialog.close()
        self.create_human_dialog.image_push.connect(self.create_push_human_slot)

        self.lock_mutex = QMutex()
        
        self.fdc = FrameDataContainer()
        
        self.pt_time = FunctionCallerThread(self.process_frames)
        self.pt_time.set_time_interval(self.process_timer_small_timestep)
        self.pt_time.start()
        
        self.global_workers_index = 0
        
        self.array_frames_logs_images_human_and_bags = []
        self.array_all_humans_and_bags = []
        self.entities = []
        
        self.timer_log_update = QTimer(self)
        self.timer_log_update.timeout.connect(self.show_logs)
        self.timer_log_update_update_interval = timer_log_update_update_interval  # Інтервал оновлення у мілісекундах (1 секунда)

        # Встановлюємо таймер у стан паузи
        self.timer_log_update.stop()
        
        self.timer_human_update = QTimer(self)
        self.timer_human_update.timeout.connect(self.show_humans)
        self.timer_human_update_update_interval = timer_human_update_update_interval  # Інтервал оновлення у мілісекундах (1 секунда)

        # Встановлюємо таймер у стан паузи
        self.timer_human_update.stop()
        
        self.tabWidget.currentChanged.connect(self.tab_changed)
        
        self.array_humans_db = []
        
        self.plot_humans = []
        self.timer_merge_by_face_timestep = timer_merge_by_face_timestep
        self.timer_merge_by_face = FunctionCallerThread(self.compare_faces_plot_human)
        self.timer_merge_by_face.set_time_interval(self.timer_merge_by_face_timestep)
        self.timer_merge_by_face.start()
        
        self.locker_merge = QMutex()
        
        self.load_humans_db()
    
    def closeEvent(self, event):
        self.pt_time.stop()
        self.save_humans_db()
        super().closeEvent(event)
    
    def push_plot_humans(self, plot_human):
        try:
            self.locker_merge.lock()
            self.plot_humans.append(plot_human)
        finally:
            self.locker_merge.unlock()
    
    def compare_faces_plot_human(self):
        try:
            self.plot_humans = work_plot_entity(self.plot_humans)
        except Exception as ex:
            print(ex)
    
    def load_humans_db(self):
        humans = load_humans(session)
        for human in humans:
            if isinstance(human, db_Human):
                hdb = HumanDB ()
                hdb.db_id = human.id
                hdb.images_face = human.images_face
                hdb.name = human.name 
                hdb.log_images = human.log_images
                hdb.idx = human.idx
                self.array_humans_db.append(hdb)
                pe = PlotEntity()
                pe.push_human_db(hdb)
                self.push_plot_humans(pe)
        pass
    
    def save_humans_db(self):
        for ph in self.plot_humans:
            if isinstance(ph, PlotEntity):
                if ph.hdb is not None:
                    add_human_to_db(session, ph.hdb.name , ph.hdb.images_face, ph.hdb.log_images, ph.hdb.idx, ph.hdb.db_id)
        pass
    
    def create_push_human_slot(self, images, name):
        """HumanDB є тільки в PlotEntity того хто створений людиною і має фото лиця.
        Але його не буде в того PlotEntity який створено автоматично признайденні.

        Args:
            images (_type_): _description_
            name (_type_): _description_
        """
        hdb = HumanDB ()
        hdb.images_face = images
        hdb.name = name 
        self.array_humans_db.append(hdb)
        pe = PlotEntity()
        pe.push_human_db(hdb)
        self.push_plot_humans(pe)
        pass
    
    def tab_changed(self, index):
        active_tab_index = self.tabWidget.currentIndex()
        
        if active_tab_index == 1:
            self.timer_log_update.start(self.timer_log_update_update_interval) 
        elif active_tab_index != 1:
            self.timer_log_update.stop()
        
        if active_tab_index == 2:
            self.timer_human_update.start(self.timer_human_update_update_interval) 
        elif active_tab_index != 2:
            self.timer_human_update.stop()
    
    def show_logs(self):
        active_tab_index = self.tabWidget.currentIndex()
        
        if active_tab_index == 1:
            array_widget_uid_log = []
            for i in reversed(range(self.verticalLayout_4.count())):
                widget = self.verticalLayout_4.itemAt(i).widget()
                if isinstance(widget, CustomWidgetSingleLog):
                    array_widget_uid_log.append(widget.uid_log)
                """
                if widget is not None:
                    widget.deleteLater()
                """
                
            for a_f_l_i_h_a_b in self.array_frames_logs_images_human_and_bags:
                (log_, uid_elem_, image_human_, image_bag_) = a_f_l_i_h_a_b
                if isinstance(log_, EntityManager.ELog):
                    if (log_.local_id not in array_widget_uid_log and uid_elem_ is not None):
                        c_w_s_l = CustomWidgetSingleLog()
                        c_w_s_l.uid_log = log_.local_id
                        c_w_s_l.set_time(c_w_s_l.time_create)
                        c_w_s_l.set_text(str(uid_elem_))
                        c_w_s_l.set_images(image_human_, image_bag_)
                        
                        if isinstance(self.verticalLayout_4, QtWidgets.QVBoxLayout):
                            self.verticalLayout_4.addWidget(c_w_s_l)
            
            self.sort_logs(self.verticalLayout_4)
    
    def delete_button_clicked_custom_widget_single_human(self, id_custom_widget_single_human = -1):
        if id_custom_widget_single_human is not None and id_custom_widget_single_human != -1:
            is_rm = False
            for i in reversed(range(self.verticalLayout_6.count())):
                widget = self.verticalLayout_6.itemAt(i).widget()
                if isinstance(widget, CustomWidgetSingleHuman):
                    if id_custom_widget_single_human == widget.current_id:
                        ph = widget.get_plot_human()
                        if ph is not None and isinstance(ph, PlotEntity):
                            idx_remove = None
                            id_db_remove = None
                            for irm, lph in enumerate(self.plot_humans):
                                if lph is not None and isinstance(lph, PlotEntity):
                                    if ph.current_id == lph.current_id:
                                        idx_remove = irm
                                        try:
                                            id_db_remove = lph.hdb.db_id
                                        finally:
                                            pass
                                        break
                            if idx_remove is not None:
                                self.plot_humans.pop(idx_remove)
                            if id_db_remove is not None:
                                delete_human_from_db(session, id_db_remove)
                            
                        if widget is not None:
                            widget.deleteLater()
                        is_rm = True
                if is_rm is True:
                    break
        pass
    
    def show_humans(self):
        active_tab_index = self.tabWidget.currentIndex()
        
        if active_tab_index == 2:
            pass
            array_widget_uid_human_exist = []
            for i in reversed(range(self.verticalLayout_6.count())):
                widget = self.verticalLayout_6.itemAt(i).widget()
                if isinstance(widget, CustomWidgetSingleHuman):
                    widget.update_images()
                    ph = widget.get_plot_human()
                    if ph is not None and isinstance(ph, PlotEntity):
                        array_widget_uid_human_exist.append(ph.current_id)
    
            for plh in self.plot_humans:
                if isinstance(plh, PlotEntity):
                    if (plh.current_id not in array_widget_uid_human_exist and plh is not None):
                        c_w_s_l = CustomWidgetSingleHuman()
                        c_w_s_l.delete_signal.connect(self.delete_button_clicked_custom_widget_single_human)
                        c_w_s_l.push_plot_human(plh)
                        
                        if isinstance(self.verticalLayout_6, QtWidgets.QVBoxLayout):
                            self.verticalLayout_6.addWidget(c_w_s_l)
            
            array_id_plh = []
            for plh in self.plot_humans:
                if isinstance(plh, PlotEntity):
                    array_id_plh.append(plh.current_id)
            
            not_in = []
            for awuxe in array_widget_uid_human_exist:
                if awuxe not in array_id_plh:
                    not_in.append(awuxe)
            
            for i in reversed(range(self.verticalLayout_6.count())):
                widget = self.verticalLayout_6.itemAt(i).widget()
                if isinstance(widget, CustomWidgetSingleHuman):
                    widget.update_images()
                    ph = widget.get_plot_human()
                    if ph is not None and isinstance(ph, PlotEntity):
                        if ph.current_id in not_in:
                            if widget is not None:
                                widget.deleteLater()
            
            self.sort_humans(self.verticalLayout_6)
    
    def get_new_id_worker(self):
        id = self.global_workers_index
        self.global_workers_index += 1
        return id
    
    def push_logs(self, frames, frames_logs_images_human_and_bags, frames_array_all_humans_and_bags, entities):
        #single element array input [(log, uid_elem, image_human, image_bag)]
        
        array_log_idx_exist = []
        for a_f_l_o_h_a_b in self.array_frames_logs_images_human_and_bags:
            (log_, uid_elem_, image_human_, image_bag_) = a_f_l_o_h_a_b
            if isinstance(log_, EntityManager.ELog):
                array_log_idx_exist.append(log_.local_id)
        
        one_dimensional = []
        for row in frames_logs_images_human_and_bags:
            for item in row:
                one_dimensional.append(item)
        
        is_not_exist = []
        for f_l_i_h_a_b in one_dimensional:
            (log_, uid_elem_, image_human_, image_bag_) = f_l_i_h_a_b
            if isinstance(log_, EntityManager.ELog):
                if log_.local_id not in array_log_idx_exist:
                    is_not_exist.append(f_l_i_h_a_b)
        
        for i_n_e in is_not_exist:
            self.array_frames_logs_images_human_and_bags.append(i_n_e)
        
        if len(self.array_frames_logs_images_human_and_bags) > 2:
            pass
        
        if len(frames_array_all_humans_and_bags) > 0:
            self.array_all_humans_and_bags = frames_array_all_humans_and_bags[-1]
        
        if entities is not None and len(entities) > 0:
            array_entity_idx_exist = []
            for si in self.entities:
                if isinstance(si, Entity):
                    array_entity_idx_exist.append(si.current_id)
            
            
            is_not_exist = []
            is_exist = []
            for si in entities:
                if isinstance(si, Entity):
                    if si.current_id not in array_entity_idx_exist:
                        is_not_exist.append(si)
                    else:
                        is_exist.append(si)
            
            for i_n_e in is_not_exist:
                self.entities.append(i_n_e)
        
        if len(self.entities) > 0:
            
            array_entity_idx_exist = []
            for ph in self.plot_humans:
                if isinstance(ph, PlotEntity):
                    ph_entities = ph.get_entities()
                    for ph_e in ph_entities:
                        if isinstance(ph_e, Entity):
                            array_entity_idx_exist.append(ph_e.current_id)
            
            for si in self.entities:
                if isinstance(si, Entity):
                    if si.current_id not in array_entity_idx_exist:
                        pe = PlotEntity()
                        pe.push_entity(si)
                        self.push_plot_humans(pe)
            
        if frames is not None and len(frames) > 0:
            frame_single = frames[-1]
            if isinstance(frame_single, FrameData):
                dataframe_uid  = frame_single.dataframe_uid
                for single_current_entity in entities:
                    if isinstance(single_current_entity, Entity):
                        
                        
                        best_human, bbox_human, original_ltwh_human = single_current_entity.get_best_human(dataframe_uid)
                        
                        if bbox_human is not None: #and original_ltwh is not None
                            cmap = plt.get_cmap('tab20b')
                            colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]
                            color = colors[int(single_current_entity.current_id) % len(colors)]
                            color = [i * 255 for i in color]
                            real_frame = frame_single.real_frame
                            plot_frame = real_frame.copy()
                            
                            plot_frame = plot_frame[int(bbox_human[1]):int(bbox_human[3]), int(bbox_human[0]):int(bbox_human[2])]
                            single_current_entity.append_image(dataframe_uid, plot_frame)
                        
                        pass
        
        pass
    
    def work_frames(self, frames):
        frames_logs_images_human_and_bags = []
        frames_array_all_humans_and_bags = []
        entities = []
        for single_frame in frames:
            if isinstance(single_frame, FrameData):
                dataframe_uid = single_frame.dataframe_uid
                real_frame = single_frame.real_frame
                timestamp = single_frame.timestamp
                pass
                logs_images_human_and_bags = []
                if single_frame.logs is not None:
                    for log in single_frame.logs:
                        uid_elem = None
                        image_human = None 
                        image_bag = None
                        
                        if isinstance(log, EntityManager.ELog):
                            
                            log_state = str("create" if log.create_elem is not None else "remove" if log.remove_elem is not None else "other")
                            
                            r_humans = []
                            r_bags = []
                            
                            if single_frame.humans_and_bags is not None:
                                
                                for hab in single_frame.humans_and_bags:
                                    humans, bags = hab
                                    
                                    for h_ in humans:
                                        if isinstance(h_, Human):
                                            if h_.human_id in log.human_idx:
                                                r_humans.append(h_)
                                    
                                    for b_ in bags:
                                        if isinstance(b_, Bag):
                                            if b_.bag_id in log.bag_idx:
                                                r_bags.append(b_)
                                
                                log_human = None 
                                log_bag = None 
                                
                                time_delta = float("inf")
                                
                                for h_el in r_humans:
                                    if isinstance(h_el, Human):
                                        gpts = h_el.get_points(dataframe_uid)
                                        if gpts is not None:
                                            (current_timestamp, data_pts) = gpts[-1]
                                            delta = abs(current_timestamp - timestamp)
                                            if delta < time_delta:
                                                time_delta = delta
                                                log_human = h_el
                                        pass 
                                
                                time_delta = float("inf")
                                
                                for b_el in r_bags:
                                    if isinstance(b_el, Bag):
                                        gpts = b_el.get_points(dataframe_uid)
                                        if gpts is not None:
                                            (current_timestamp, data_pts) = gpts[-1]
                                            delta = abs(current_timestamp - timestamp)
                                            if delta < time_delta:
                                                time_delta = delta
                                                log_bag = b_el
                                        pass
                                
                                if log_human is not None and log_bag is not None:
                                    gpts = log_human.get_points(dataframe_uid)
                                    if gpts is not None:
                                        (t_, human_pts) = gpts[-1]
                                        gpts2 = log_bag.get_points(dataframe_uid)
                                        if gpts2 is not None:
                                            (t_, bag_pts) = gpts2[-1]
                                            bbox_human, original_ltwh_human = human_pts[0], human_pts[1]  # noqa: F841
                                            bbox_bag, original_ltwh_bag = bag_pts[0], bag_pts[1]  # noqa: F841
                                            
                                            h_name = [str(eles) for eles in log.human_idx]
                                            b_name = [str(eles) for eles in log.bag_idx]
                                            uid_elem = str("_".join(h_name)) + "_" + str("_".join(b_name)) + "_" + log_state
                                            image_human = real_frame.copy()
                                            image_bag = real_frame.copy()
                                            cmap = plt.get_cmap('tab20b')
                                            colors = [cmap(i)[:3] for i in np.linspace(0, 1, 20)]
                                            color = colors[int(log_human.human_id) % len(colors)]
                                            color = [i * 255 for i in color]
                                            
                                            cv2.rectangle(
                                                image_human, 
                                                (int(bbox_human[0]), int(bbox_human[1])), 
                                                (int(bbox_human[2]), int(bbox_human[3])), 
                                                color,
                                                2
                                            )
                                            
                                            color = colors[int(log_bag.bag_id) % len(colors)]
                                            color = [i * 255 for i in color]
                                            
                                            cv2.rectangle(
                                                image_bag, 
                                                (int(bbox_bag[0]), int(bbox_bag[1])), 
                                                (int(bbox_bag[2]), int(bbox_bag[3])), 
                                                color,
                                                2
                                            )
                                
                            pass  
                        
                        logs_images_human_and_bags.append((log, uid_elem, image_human, image_bag))  
                        
                frames_logs_images_human_and_bags.append(logs_images_human_and_bags)
                frames_array_all_humans_and_bags.append(single_frame.array_all_humans_and_bags)
                                
            pass
        
        if frames is not None and len(frames) > 0:
            entities = frames[-1].entities
            
        self.push_logs(frames, frames_logs_images_human_and_bags, frames_array_all_humans_and_bags, entities)


    
    def process_frames(self):
        with self.pt_time:
            if (
                self.fdc.empty() is not True and 
                self.fdc.limit_size(self.process_count_frames)
            ):
                arrays_frames = []
                try:
                    self.lock_mutex.lock()
                    arrays_frames = self.fdc.get(max_count=self.process_count_frames)
                    #print("process")
                finally:
                    self.lock_mutex.unlock()
                    
                self.work_frames(arrays_frames)
                
                if self.fdc.limit_size(self.process_count_frames):
                    self.pt_time.set_time_interval(self.process_timer_small_timestep)
                else:
                    self.pt_time.set_time_interval(self.process_timer_timestep)
            else:
                self.pt_time.set_time_interval(self.process_timer_timestep)
            
    
    def do_work_frame_data(self, frame_data_loc:FrameData):
        try:
            self.lock_mutex.lock()
            self.fdc.put(frame_data_loc)
            #print("work frame_data")
        finally:
            self.lock_mutex.unlock()
    
    def open_settings(self):
        self.settings_dialog.show()
    
    def create_humans(self):
        self.create_human_dialog.show()

    def open_file_dialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            'Open Video File', 
            '', 
            'Video Files (*.mp4);;All Files (*)', 
            options=options
        )

        if file_name:
            print(f'Selected video file: {file_name}')
        return file_name
    
    def imitation_camera_is_file(self):
        file_name = self.open_file_dialog()
        if file_name:
            if file_name != "":
                
                widget_to_add = AvailableCameraWidgetIsFile()
                widget_to_add.set_filepath(file_name)
                
                widget_to_add.createWidgetSignal.connect(self.create_camera_check_is_file)
                widget_to_add.deleteWidgetSignal.connect(self.remove_camera_uncheck_is_file)
                
                #widget_to_add.show_processing_result_Signal.connect(self.show_processing_result)
                
                widget_to_add.loop_Signal.connect(self.loop_video_file)
                
                self.verticalLayout_3.addWidget(widget_to_add)
                self.reorder_widgets(self.verticalLayout_3)
                self.create_camera_check_is_file(file_name)
    
    def sort_logs(self, layout):
        spacer = None
        widgets = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if isinstance(item, QSpacerItem):
                spacer = item
            else:
                widget = item.widget()
                if widget:
                    widgets.append(widget)

        # Очистіть Layout
        while layout.count():
            item = layout.takeAt(0)
        
        sorted_widgets  = sorted(widgets, key=lambda x: x.time_create if x.time_create is not None else float("inf"), reverse=True)
        
        # Додайте всі віджети зі списку зі збереженням їхнього порядку
        for widget in sorted_widgets :
            layout.addWidget(widget)

        # Додайте спейсер
        if spacer:
            layout.addItem(spacer)
        else:
            new_spacer = QSpacerItem(40, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addItem(new_spacer)
    
    def sort_humans(self, layout):
        spacer = None
        widgets = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is not None:
                if isinstance(item, QSpacerItem):
                    spacer = item
                else:
                    widget = item.widget()
                    if widget is not None and isinstance(widget, CustomWidgetSingleHuman):
                        widgets.append(widget)

        # Очистіть Layout
        while layout.count():
            item = layout.takeAt(0)
        
        sorted_widgets = sorted(widgets, key=lambda x: x.time_current if x.time_current is not None else float("inf"), reverse=True)
        
        # Додайте всі віджети зі списку зі збереженням їхнього порядку
        for widget in sorted_widgets :
            if widget is not None:
                layout.addWidget(widget)

        # Додайте спейсер
        if spacer:
            layout.addItem(spacer)
        else:
            new_spacer = QSpacerItem(40, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addItem(new_spacer)
            
    
    def reorder_widgets(self, layout):
        # Шукайте спейсер в Layout
        spacer = None
        widgets = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if isinstance(item, QSpacerItem):
                spacer = item
            else:
                widget = item.widget()
                if widget:
                    widgets.append(widget)

        # Очистіть Layout
        while layout.count():
            item = layout.takeAt(0)

        # Додайте всі віджети зі списку зі збереженням їхнього порядку
        for widget in widgets:
            layout.addWidget(widget)

        # Додайте спейсер
        if spacer:
            layout.addItem(spacer)
        else:
            new_spacer = QSpacerItem(40, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addItem(new_spacer)
    
    def find_widget_on_camera(self, index):
        for i in range(self.verticalLayout_2.count()):
            widget_item = self.verticalLayout_2.itemAt(i)
            widget = widget_item.widget()
            if widget:
                if isinstance(widget, CameraWidgetView):
                    if widget.index_camera == index:
                        return widget
        return None 
    
    def find_available_camera_widget(self, index, all_widgets):
        for i, wi in enumerate(all_widgets):
            if isinstance(wi, AvailableCameraWidget):
                if wi.get_index() == index:
                    return True
        return False 

    def find_cameras_button_f(self):
        cameras = find_all_cameras()
        new_camera_index = []
        all_widgets = []
        for i in range(self.verticalLayout_3.count()):
            widget_item = self.verticalLayout_3.itemAt(i)
            widget = widget_item.widget()
            if widget:
                all_widgets.append(widget)   
            
        for i, wi in enumerate(cameras):
            if self.find_available_camera_widget(wi, all_widgets) is False:
                new_camera_index.append(i)
        
        for i, wi in enumerate(new_camera_index):
            widget_to_add = AvailableCameraWidget()
            widget_to_add.set_index(wi)
            widget_to_add.createWidgetSignal.connect(self.create_camera_check)
            widget_to_add.deleteWidgetSignal.connect(self.remove_camera_uncheck)
            self.verticalLayout_3.addWidget(widget_to_add)
            self.reorder_widgets(self.verticalLayout_3)
            
            camera_widget = CameraWidgetView(self.get_new_id_worker())
            camera_widget.frame_data.connect(self.do_work_frame_data)
            camera_widget.create_connect_online(wi)
            self.verticalLayout_2.addWidget(camera_widget)
        
        if len(new_camera_index) <= 0:
            msgBox = QMessageBox(self)
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText("Камери не знайдено")
            msgBox.setWindowTitle("Помилка")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.show()
    
    def remove_camera_uncheck(self, index_remove):
        widget = self.find_widget_on_camera(index_remove)
        if widget is not None:
            self.verticalLayout_2.removeWidget(widget)
            widget.deleteLater()
    
    def create_camera_check(self, index_create):
        camera_widget = CameraWidgetView(self.get_new_id_worker())
        camera_widget.create_connect_online(index_create)
        camera_widget.frame_data.connect(self.do_work_frame_data)
        self.verticalLayout_2.addWidget(camera_widget)
    
    def find_widget_on_is_file(self, file_path):
        for i in range(self.verticalLayout_2.count()):
            widget_item = self.verticalLayout_2.itemAt(i)
            widget = widget_item.widget()
            if widget:
                if isinstance(widget, CameraWidgetViewIsFile):
                    if widget.file_path == file_path:
                        return widget
        return None 
    
    """def show_processing_result(self, file_path, state):
        widget = self.find_widget_on_is_file(file_path)
        if widget is not None:
            widget.update_show_processing_result(state)
                    """
    def loop_video_file(self, file_path, state):
        widget = self.find_widget_on_is_file(file_path)
        if widget is not None:
            widget.update_loop(state)
    
    
    def remove_camera_uncheck_is_file(self, file_path):
        widget = self.find_widget_on_is_file(file_path)
        if widget is not None:
            widget.stop()
            self.verticalLayout_2.removeWidget(widget)
            widget.deleteLater()
                
    def create_camera_check_is_file(self, file_path):
        
        camera_widget = CameraWidgetViewIsFile(self.get_new_id_worker())
        camera_widget.frame_data.connect(self.do_work_frame_data)
        camera_widget.create_file_stream(file_path)
        self.verticalLayout_2.addWidget(camera_widget)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())
