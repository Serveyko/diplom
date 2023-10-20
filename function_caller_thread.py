from PyQt5.QtCore import QThread, QTimer
import time
from contextlib import contextmanager
from config import function_caller_thread_state

class MainFunctionCallerThread(QThread):
    
    def __init__(self, func):
        super().__init__()
        self.func = func
        self.interval_ms = 1.0
        self.running = True
    
    def run(self):
        while self.running:
            self.func()
            time.sleep(self.interval_ms / 1000.0)
    
    def set_time_interval(self, time_interval):
        self.interval_ms = time_interval
    
    def stop(self):
        self.running = False
        


class FunctionCallerThread():
    
    def __init__(self, func, rtt=function_caller_thread_state):
        self.rtt_variants = ["timer", "thread"]
        self.rtt = rtt
        self.func = func
        self.interval_ms = 1
        self.running = False
        if self.rtt == "thread":
            self.th = MainFunctionCallerThread(self.func)
            self.th.set_time_interval(self.interval_ms)
        elif self.rtt == "timer":
            self.timer = QTimer()
            self.timer.timeout.connect(self.func)
            self.timer.setInterval(self.interval_ms)
    
    def set_time_interval(self, time_interval):
        self.interval_ms = time_interval
        if self.rtt == "thread":
            self.th.set_time_interval(self.interval_ms)
        elif self.rtt == "timer":
            self.timer.setInterval(self.interval_ms)
            
    def start(self):
        if self.rtt == "thread":
            self.th.start()
            self.running = True
        elif self.rtt == "timer":
            self.timer.start(self.interval_ms)
            self.running = True
                
    def stop(self):
        if self.rtt == "thread":
            self.th.stop()
            self.th.quit()
            self.th.wait()
            self.running = False
        elif self.rtt == "timer":
            self.timer.stop()
            self.running = False
    
    def in_function(self):
        if self.rtt == "timer":
            if self.running is True:
                self.timer.stop() 
    
    def out_function(self):
        if self.rtt == "timer":
            if self.running is True:
                self.timer.start(self.interval_ms)
    
    @contextmanager    
    def in_out_context(self): 
        self.in_function()
        yield
        self.out_function()
        
    def __call__(self):
        return self.in_out_context()
    
    def __enter__(self):
        self.in_function() 
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.out_function()
        except Exception as e:
            print(f'Error in __exit__: {e}')

