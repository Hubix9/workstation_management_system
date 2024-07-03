class Workstation:
    def __init__(self) -> None:
        self.id = None
        self.internal_id = None
        self.name = None
        self.ip_address = None
        self.port = None
        self.template = None
        self.username = None
        self.password = None

class Template:
    def __init__(self) -> None:
        self.id = None
        self.internal_id = None  
        self.name = None 

class Engine:
    def __init__(self) -> None:
        self.name = None
        self.workstations = {}
        self.avilaible_resources = {}
        self.max_resources = {}
        self.settings = {}
        self.templates = {}
    
    def create_workstation(self, template_id: str) -> str:
        pass

    def delete_workstation(self, workstation_id: str):
        pass

    def start_workstation(self, workstation_id: str):
        pass

    def stop_workstation(self, workstation_id: str):
        pass

    def get_workstation_status(self, workstation_id: str) -> str:
        pass

    def get_workstation_information(self, workstation_id: str) -> dict:
        pass

    def execute_workstation_command(self, workstation_id: str, command: str) -> str:
        pass

