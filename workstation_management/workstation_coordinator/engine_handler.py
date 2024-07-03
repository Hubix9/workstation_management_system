import logging
from threading import Thread
from django.db.models import QuerySet, Q
from .models import EngineType, Engine, Template, Reservation, Host, Workstation
from engines.generic_client import GenericClient
import time
from typing import Callable
from utils.threading import ThreadWithCallback

logger = logging.getLogger('workstation_coordinator')

class EngineHandler:
    def __init__(self) -> None:
        self.clients = {}
        self.setup_threads = {}
        self.cleanup_threads = {}

    def _initialize_clients(self):
        for host in Host.objects.all():
            for engine in host.engines.all():
                engine: Engine = engine
                self.clients[engine.id] = GenericClient(f'http://{host.ip_address}:{engine.port}/api/v1') 
                logger.info(f'Initialized client for engine {engine}')

        logger.info(f'Initialized clients for following engines: {list(self.clients.keys())}')

    def _spawn_client_for_engine_id(self, engine_id: int) -> GenericClient:
        host = Host.objects.get(engines__id=engine_id)
        engine = Engine.objects.get(id=engine_id)
        client = GenericClient(f'http://{host.ip_address}:{engine.port}/api/v1')
        self.clients[engine.id] = client
        return client

    def get_all_types(self) -> list:
        return list(EngineType.objects.all())
    
    def _get_all(self) -> list:
        return list(Engine.objects.all())
    
    def _get_max_load_at_time(self, engine: Engine, reservations: QuerySet) -> dict:
        # If reservations has an engine assigned it is already approved or active
        reservations_with_engine = reservations\
            .filter(workstation__engine=engine)\
            .exclude(Q(status=Reservation.Status.Pending) | 
                     Q(status=Reservation.Status.Rejected) | 
                     Q(status=Reservation.Status.Completed) | 
                     Q(status=Reservation.Status.Cancelled))
        
        logger.info(f'Reservations with engine {engine}: {list(reservations_with_engine)}')
        sum_vm_load = {}
        logger.info(f'Reservations with engine {engine}: {list(reservations_with_engine)}')
        for reservation in reservations_with_engine:
            reservation: Reservation
            template: Template = reservation.template
            for key, value in template.resource_requirements.items():
                if key not in sum_vm_load:
                    sum_vm_load[key] = 0
                sum_vm_load[key] += int(value)
        logger.info(f'Sum of VM load for engine {engine}: {sum_vm_load}')
        return sum_vm_load
    
    def _get_max_possible_load(self, engine: Engine) -> dict:
        return engine.max_resources
            
    def _get_supported_engine_types(self, template: Template) -> list:
        engs = Engine.objects.filter(type__in=template.allowed_engine_types.all())
        return list(engs)
    
    def _list_cleanup_threads(self):
        logger.info('Listing all cleanup threads')
        for key, value in self.cleanup_threads.items():
            logger.info(f'Reservation {key} has cleanup thread {value}')
    
    def _gc_cleanup_threads(self):
        logger.info('Garbage collecting cleanup threads')

        threads_to_remove = []

        for key, value in self.cleanup_threads.items():
            if not value.is_alive():
                threads_to_remove.append(key) 

        for key in threads_to_remove:
            self.cleanup_threads.pop(key)
            logger.info(f'Removed cleanup thread for reservation {key}')
    
    def start_workstation_cleanup_for_reservation(self, reservation: Reservation, callback: Callable = None):
        t = ThreadWithCallback(target=self._cleanup_workstation, args=(reservation,), daemon=True, callback=callback)
        self.cleanup_threads[reservation.id] = t
        t.start()
        logger.info(f'Started cleanup thread for reservation {reservation}')
    
    def _list_setup_threads(self):
        logger.info('Listing all setup threads')
        for key, value in self.setup_threads.items():
            logger.info(f'Reservation {key} has setup thread {value}')
    
    def _is_setup_thread_running(self, reservation: Reservation) -> bool:
        return reservation.id in self.setup_threads
    
    def _gc_setup_threads(self):
        logger.info('Garbage collecting setup threads')

        threads_to_remove = []

        for key, value in self.setup_threads.items():
            t: Thread
            t, _ = value
            if not t.is_alive():
                threads_to_remove.append(key) 

        for key in threads_to_remove:
            self.setup_threads.pop(key)
            logger.info(f'Removed setup thread for reservation {key}')

    def _generate_name_for_vm(self, reservation: Reservation) -> str:
        username = reservation.user.username.capitalize()
        internal_name = reservation.template.internal_name.capitalize()
        date_as_numbers = str(reservation.request_date).replace(" ", "").replace(":", "").replace("-", "").replace("+", "")
        vm_name = f'{username}{internal_name}{date_as_numbers}'
        return vm_name
    
    def _delete_vm(self, vm_name: str, client: GenericClient):
        if vm_name is None or vm_name == '' or not client.vm_exists(vm_name):
            logger.info(f'VM {vm_name} does not exist, skipping deletion')
            return

        client.stop_vm(vm_name)
        while client.is_vm_running(vm_name):
            logger.info(f'Waiting for VM {vm_name} to stop')
            time.sleep(5)
        try:
            client.delete_vm(vm_name)
        except Exception as e:
            logger.error(f'Error while deleting VM {vm_name}: {e}')
            return
        while client.vm_exists(vm_name):
            logger.info(f'Waiting for VM {vm_name} to be deleted')
            time.sleep(5) 
        logger.info(f'VM {vm_name} deleted successfully')
    
    def setup_workstation_for_reservation(self, reservation: Reservation, callback: Callable = None):
        vm_name = self._generate_name_for_vm(reservation)
        reservation.workstation.engine_internal_name = vm_name
        reservation.workstation.save()
        t = ThreadWithCallback(target=self._setup_workstation, args=(reservation, vm_name), daemon=True, callback=callback)
        self.setup_threads[reservation.id] = (t, vm_name)
        t.start()
        logger.info(f'Started setup thread for reservation {reservation}')
    
    def _setup_workstation(self, reservation: Reservation, vm_name: str): 
        client: GenericClient = self._spawn_client_for_engine_id(reservation.workstation.engine.id) 

        # Check if VM with same name exists, and delete it if so
        if client.vm_exists(vm_name):
            logger.info(f'VM {vm_name} already exists, deleting it')
            self._delete_vm(vm_name, client)

        # Create VM
        client.create_vm(reservation.template.internal_name, vm_name)

        # Start VM
        client.start_vm(vm_name)

        # Wait until VM is running
        while not client.is_vm_running(vm_name):
            logger.info(f'Waiting for VM {vm_name} to start')
            time.sleep(5) 

        # Wait until VM agent is running
        while not client.is_agent_running(vm_name):
            logger.info(f'Waiting for agent to start on VM {vm_name}')
            time.sleep(5)

        logger.info(f'VM {vm_name} is running and agent is running')

        # Get VM network info
        while True:
            ip_address: str = client.get_vm_network_info(vm_name)['ip_address']
            if not ip_address.startswith('169.254'):
                break
            time.sleep(5)
        reservation.workstation.ip_address = ip_address
        logger.info(f'Workstation ip address: {reservation.workstation.ip_address}')
        reservation.workstation.engine_internal_name = vm_name
        reservation.workstation.save()
        logger.info(f'Finished workstation setup for reservation {reservation}, set status to Active') 

    def _cleanup_workstation(self, reservation: Reservation):
        self._delete_vm(reservation.workstation.engine_internal_name, 
                        self.clients[reservation.workstation.engine.id]) 

    def _clean_orphaned_workstations(self):
        logger.info('Cleaning orphaned workstations')

        for engine in Engine.objects.all():
            client: GenericClient = self._spawn_client_for_engine_id(engine.id)
            try:
                all_vm_names = client.get_all_vm_names()
            except Exception as e:
                logger.error(f'Error while getting VM names from engine {engine}: {e}') 
                continue
            for name in all_vm_names:
                logger.info(f'Checking VM {name} for orphaned status')
                if name in [name for _, name in self.setup_threads.values()]:
                    logger.info(f'Found VM {name} in setup threads, skipping')
                    continue
                
                workstation_query = Workstation.objects.filter(engine_internal_name=name)
                reservation_query = Reservation.objects.filter(workstation__engine_internal_name=name)

                if not reservation_query.exists() or not workstation_query.exists():
                    logger.info(f'Found orphaned VM {name}, deleting it')
                    self._delete_vm(name, client)
                    continue

                reservation_handle = reservation_query.first()
                workstation_handle = workstation_query.first()


                reservation_status_as_expected = reservation_handle.status in [Reservation.Status.Approved, 
                                                                               Reservation.Status.Active]

                workstation_status_as_expected = workstation_handle.status in [Workstation.Status.Active, 
                                                                               Workstation.Status.Setup, 
                                                                               Workstation.Status.Cleanup,
                                                                               Workstation.Status.Restart]
                

                if not workstation_status_as_expected or not reservation_status_as_expected:
                    logger.info(f'Found orphaned VM {name}, deleting it')
                    self._delete_vm(name, client)    
                    continue

                logger.info(f'Workstation has DB record and approved status, skipping')
    def _restart_workstation(self, reservation: Reservation):
        logger.info("Restart thread running")
        client: GenericClient = self.clients[reservation.workstation.engine.id]
        vm_name = reservation.workstation.engine_internal_name
        client.reboot_vm(vm_name)
        while not client.is_agent_running(vm_name):
            logger.info(f'Waiting for VM {vm_name} to start')
            time.sleep(5) 
    
    def restart_workstation_for_reservation(self, reservation: Reservation, callback: Callable = None):
        if self.setup_threads.get(reservation.id) is not None:
            logger.info(f'Setup thread for reservation {reservation} is running, skipping restart')
            return

        t = ThreadWithCallback(target=self._restart_workstation, args=(reservation,), daemon=True, callback=callback)
        vm_name = reservation.workstation.engine_internal_name
        self.setup_threads[reservation.id] = (t, vm_name)
        t.start()
        logger.info(f'Started restart thread for reservation {reservation}')