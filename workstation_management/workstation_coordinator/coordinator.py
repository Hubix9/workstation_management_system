import logging
from threading import Thread
from utils.singleton import Singleton
import time

from .reservation_handler import RevervationHandler
from .template_handler import TemplateHandler
from .engine_handler import EngineHandler

logger = logging.getLogger('workstation_coordinator')

class WorkstationCoordinator(metaclass=Singleton):
    def __init__(self):
        self.thread = None 

        self.reservation_handler = RevervationHandler()
        self.template_handler = TemplateHandler()
        self.engine_handler = EngineHandler()

    def is_active(self) -> bool:
        if self.thread is None:
            return False
        
        if not self.thread.is_alive():
            return False
        
        return True
    
    def _list_info(self):
        engines = self.engine_handler.get_all_types()
        logger.info(f'Listing all engine types')
        for engine in engines:
            logger.info(f"Engine type: {engine}") 

        templates = self.template_handler.get_all()
        logger.info(f'Listing all templates')
        for template in templates:
            logger.info(f"Template: {template}")

        logger.info('Checking for pending reservations')
        self.reservation_handler.list_with_status('Pending')

    def _main_loop(self):
        self.engine_handler._initialize_clients()
        self._list_info()
        time.sleep(5)
        while True:
            self.reservation_handler.handle(self.engine_handler)
            self.engine_handler._gc_setup_threads()
            self.engine_handler._list_setup_threads()
            self.engine_handler._gc_cleanup_threads()
            self.engine_handler._list_cleanup_threads()
            self.engine_handler._clean_orphaned_workstations()
            time.sleep(5)

    def start(self):
        if self.is_active():
            logger.info('Coordinator is already active, skipping startup')
            return
        t = Thread(target=self._main_loop, args=(), daemon=True)
        self.thread = t
        self.thread.start() 
