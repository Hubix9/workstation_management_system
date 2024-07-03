from django.apps import AppConfig
import os


class MainServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_server'


    def ready(self) -> None:
        if os.environ.get('RUN_COORDINATOR', None) != True:
            return
        from workstation_coordinator.coordinator import WorkstationCoordinator
        coordinator = WorkstationCoordinator()
        coordinator.start() 
