import logging
from django.db.models import QuerySet
from django.utils import timezone
from .models import Template, Reservation, Host, Workstation, ProxyMapping
from .reservation_policies import DefaultReservationPolicy

from .engine_handler import EngineHandler

logger = logging.getLogger('workstation_coordinator')

class RevervationHandler:
    def __init__(self) -> None:
        self.policy = DefaultReservationPolicy()

    def _handle_pending(self, reservation: Reservation, engine_handler: EngineHandler):
        logger.info(f'Checking for overlapping reservations')

        reservations_in_same_timeframe = self._get_overlapping(reservation)
        logger.info(f'Reservations in same timeframe: {list(reservations_in_same_timeframe)}')

        logger.info(f'Filtering out reservetions with already assigned workstation') 
        reservations_without_workstation = self._get_without_workstation(reservations_in_same_timeframe)
        filtered_reservations = reservations_in_same_timeframe.exclude(id__in=[r.id for r in reservations_without_workstation])
        logger.info(f'Reservations without workstation: {list(reservations_without_workstation)}')
        logger.info(f'Searching for suitable engine')

        for engine in engine_handler._get_all():
            logger.info(f'Checking engine: {engine}')

            # Check 1: Is engine type supported by template
            allowed_engines = engine_handler._get_supported_engine_types(reservation.template)
            logger.info(f'Allowed engines: {allowed_engines}') 

            # Check 2: Does engine have available resources at the time of reservation
            max_vm_load_at_time = engine_handler._get_max_load_at_time(engine, filtered_reservations)
            max_possible_load = engine_handler._get_max_possible_load(engine)
            template_load = reservation.template.resource_requirements
            cumulative_load = {key: int(max_vm_load_at_time.get(key, 0)) + int(value) for key, value in template_load.items()}

            logger.info(f'Max VM load at time: {max_vm_load_at_time}')
            logger.info(f'Max possible load: {max_possible_load}')
            logger.info(f'Template load: {template_load}')
            logger.info(f'Cumulative load: {cumulative_load}')
            if all([int(cumulative_load[key]) <= int(max_possible_load[key]) for key in cumulative_load.keys()]):
                logger.info(f'Engine {engine} has enough resources for reservation {reservation}')
                host = Host.objects.filter(engines__in=[engine]).first()
                workstation = Workstation.objects.create(
                    template=reservation.template,
                    host=host,
                    engine=engine,
                    status=Workstation.Status.Scheduled
                )
                reservation.workstation = workstation
                reservation.workstation.engine = engine
                reservation.set_reservation_status(Reservation.Status.Approved) 
                reservation.save()
                logger.info(f'Reservation {reservation} approved')
                return
            else:
                logger.info(f'Engine {engine} does not have enough resources for reservation {reservation}')
                continue
        logger.info(f'No suitable engine found for reservation {reservation}')
        reservation.set_reservation_status(Reservation.Status.Rejected)
        logger.info(f'Reservation {reservation} rejected')
            
    def _handle_approved(self, reservation: Reservation, engine_handler: EngineHandler):
        # Check 1: Is reservation start date in the past
        current_time = timezone.now()
        logger.info(f'Current date: {current_time}, reservation start date: {reservation.start_date}')

        if reservation.start_date > current_time:
            logger.info(f'Reservation {reservation} start date is in the future, skipping') 
            return

        # Check 2: Is reservation end date in the future
        if reservation.end_date < current_time:
            logger.info(f'Reservation {reservation} end date is in the past, skipping')
            # Since reservation end date is in the past before it was active it is an unexpected state, set as broken
            reservation.set_reservation_status(Reservation.Status.Broken)
            return 

        
        # Check 3: Does reservation have assigned workstation
        if reservation.workstation is None:
            logger.info(f'Reservation {reservation} does not have assigned workstation, unexpected state')
            logger.info(f'Changing to broken state')
            reservation.set_reservation_status(Reservation.Status.Broken)
            return

        # Handle workstation depending on its status 

        workstation_status = reservation.workstation.status
        if workstation_status == Workstation.Status.Scheduled: 
            # Start setting up workstation
            logger.info(f'Setting up workstation for reservation {reservation}')
            reservation.workstation.set_workstation_status(Workstation.Status.Setup)

            def setup_callback():
                reservation.workstation.set_workstation_status(Workstation.Status.Active)

            engine_handler.setup_workstation_for_reservation(reservation, callback=setup_callback) 

        elif workstation_status == Workstation.Status.Setup:
            # Workstation is actively being setup
            if engine_handler._is_setup_thread_running(reservation):
                logger.info(f'Workstation for reservation {reservation} is already being setup')
            else:
                reservation.workstation.set_workstation_status(Workstation.Status.Scheduled)
                logger.info(f'Workstation for reservation {reservation} is being setup without worker thread, reverting to scheduled state')

        elif workstation_status == Workstation.Status.Active:
            # Workstation is active
            logger.info(f'Workstation for reservation {reservation} is active, reservation can be used')
            reservation.set_reservation_status(Reservation.Status.Active)

        elif workstation_status == Workstation.Status.Restart:
            # Workstation is to be restarted
            def setup_callback():
                reservation.workstation.set_workstation_status(Workstation.Status.Active)

            logger.info(f'Restarting workstation for reservation {reservation}')
            engine_handler.restart_workstation_for_reservation(reservation, callback=setup_callback)
        else:
            logger.info(f'Workstation for reservation {reservation} has invalid status: {workstation_status}')
            return
        
    def _handle_active(self, reservation: Reservation, engine_handler: EngineHandler): 

        # Check 0: Does workstation need a restart
        workstation_status = reservation.workstation.status
        if workstation_status == Workstation.Status.Restart:
            # Workstation is to be restarted
            def setup_callback():
                reservation.workstation.set_workstation_status(Workstation.Status.Active)

            logger.info(f'Restarting workstation for reservation {reservation}')
            engine_handler.restart_workstation_for_reservation(reservation, callback=setup_callback)

        # Check 1: Is reservation end date is in the past
        current_time = timezone.now()
        logger.info(f'Current date: {current_time}, reservation end date: {reservation.end_date}')
        if reservation.end_date > current_time:

            if reservation.workstation is None:
                logger.info(f'Reservation {reservation} does not have assigned workstation, unexpected state')
                logger.info(f'Changing to broken state')
                reservation.set_reservation_status(Reservation.Status.Broken)
                return

            logger.info(f'Reservation {reservation} end date is in the future, skipping')
            return
        
        # Check 2: does reservation have assigned workstation
        if reservation.workstation is None:
            logger.info(f'Reservation {reservation} does not have assigned workstation, skipping')
            return
        
        # Check 3: is workstation status active
        workstation_status = reservation.workstation.status
        if workstation_status != 'Active':
            logger.info(f'Workstation for reservation {reservation} is {workstation_status} which is not active')

        # Perform workstation cleanup
        logger.info(f'Cleaning up workstation for reservation {reservation}')
        reservation.workstation.set_workstation_status(Workstation.Status.Cleanup)

        def cleanup_callback():
            reservation.workstation.set_workstation_status(Workstation.Status.Archived)
            reservation.set_reservation_status(Reservation.Status.Completed)

        engine_handler.start_workstation_cleanup_for_reservation(reservation, 
                                                                 callback=cleanup_callback)
        
        self.archive_mapping_for_reservation_if_exists(reservation)
        
        logger.info(f'Reservation {reservation} completed')

    def _handle_cancelled(self, reservation: Reservation, engine_handler: EngineHandler):
        # Check 1: does reservation have assigned workstation
        if reservation.workstation is None:
            logger.info(f'Reservation {reservation} does not have assigned workstation, skipping')
            return
        
        # Check 2: is workstation status active
        workstation_status = reservation.workstation.status
        if workstation_status != 'Active' and workstation_status != 'Setup' and workstation_status != 'Scheduled':
            #logger.info(f'Workstation for reservation {reservation} is {workstation_status} which is not executing operations, skipping')
            return

        # Perform workstation cleanup
        logger.info(f'Cleaning up workstation for reservation {reservation}')
        reservation.workstation.set_workstation_status(Workstation.Status.Cleanup)
        engine_handler._cleanup_workstation(reservation)
        reservation.workstation.set_workstation_status(Workstation.Status.Archived)
        self.archive_mapping_for_reservation_if_exists(reservation) 
        
        logger.info(f'Reservation {reservation} cancelled')

    def _handle_broken(self, reservation: Reservation, engine_handler: EngineHandler):
        # Broken reservations are to be cleaned up if needed

        # Check 1: Does reservation have assigned workstation
        if reservation.workstation is None:
            logger.info(f'Reservation {reservation} does not have assigned workstation, skipping')
            return
        
        # Check 2: Is workstation status not broken
        if reservation.workstation.status != Workstation.Status.Broken:
            logger.info(f'Workstation for reservation {reservation} is not broken, skipping')
            return
        
        # Check 3: Is workstation status already in cleanup
        if reservation.workstation.status == Workstation.Status.Cleanup:
            logger.info(f'Workstation for reservation {reservation} is already in cleanup, skipping')
            return
        
        # Cleanup workstation forcefully
        # Perform workstation cleanup
        logger.info(f'Cleaning up workstation for reservation {reservation}')
        reservation.workstation.set_workstation_status(Workstation.Status.Cleanup)

        def cleanup_callback():
            reservation.workstation.set_workstation_status(Workstation.Status.Broken)

        engine_handler.start_workstation_cleanup_for_reservation(reservation, 
                                                                 callback=cleanup_callback)
        
    def _handle_reservation(self, reservation: Reservation, engine_handler: EngineHandler):
        if not reservation.status == Reservation.Status.Completed:
            #logger.info(f'Handling reservation: {reservation}')
            pass

        if reservation.status == Reservation.Status.Pending:
            logger.info(f'Reservation {reservation} is pending')
            self._handle_pending(reservation, engine_handler)    
            return
        
        if reservation.status == Reservation.Status.Approved:
            logger.info(f'Reservation {reservation} is approved')
            self._handle_approved(reservation, engine_handler)
            return
        
        if reservation.status == Reservation.Status.Active:
            logger.info(f'Reservation {reservation} is active')
            self._handle_active(reservation, engine_handler)
            return
        
        if reservation.status == Reservation.Status.Cancelled:
            self._handle_cancelled(reservation, engine_handler)
            return
        
        if reservation.status == Reservation.Status.Broken:
            self._handle_broken(reservation, engine_handler)
            return

    def _get_without_workstation(self, reservations: QuerySet) -> QuerySet:
        return reservations.filter(workstation__isnull=True)

    def _get_overlapping(self, reservation: Reservation) -> QuerySet:

        start_overlap = Reservation.objects.filter(start_date__lte=reservation.start_date, end_date__lte=reservation.end_date, end_date__gte=reservation.start_date)
        end_overlap = Reservation.objects.filter(start_date__gte=reservation.start_date, end_date__gte=reservation.end_date, start_date__lte=reservation.end_date)
        outer_overlap = Reservation.objects.filter(start_date__lte=reservation.start_date, end_date__gte=reservation.end_date)
        inner_overlap = Reservation.objects.filter(start_date__gte=reservation.start_date, end_date__lte=reservation.end_date)

        return (start_overlap | end_overlap | outer_overlap | inner_overlap).exclude(id=reservation.id)

    def handle(self, engine_handler: EngineHandler):
        logger.info('=== Handling reservations ===')
        for reservation in Reservation.objects.all().order_by('request_date'):
            self._handle_reservation(reservation, engine_handler)

    def get_with_status(self, status: str) -> list:
        return list(Reservation.objects.filter(status=status))
      
    def list_with_status(self, status: str):
        reservations = Reservation.objects.filter(status=status)
        for reservation in reservations:
            logger.info(f"Reservation: {reservation}")
            logger.info(f"Reservation status: {reservation.status}")
            logger.info(f"Reservation request date: {reservation.request_date}")
            logger.info(f"Reservation start date: {reservation.start_date}")
            logger.info(f'Reervation template: {reservation.template}')
            logger.info(f'Reservation user: {reservation.user}')

    def find_template_with_tags(self, tags: list) -> Template:
        templates = Template.objects.all()
        for template in templates:
            logger.info(f'Template tags: {template.tags.all()}')
            logger.info(list(template.tags.values_list('name', flat=True)))
            if all([tag in list(template.tags.values_list('name', flat=True)) for tag in tags]):
                return template 
        return None

    # A verified mapping is one that is currently NOT archived and can be used to access reservation
    def get_mapping_target_by_id(self, id: str) -> str: 
        mapping = ProxyMapping.objects.filter(id=id).first()
        # Check if token exists in database 
        if mapping is None:
            logger.info(f'Mapping with id {id} not found')
            return "" 
        # Check if mapping is archived
        if mapping.archived:
            logger.info(f'Mapping with id {id} is archived')
            return "" 
        
        # Check if mapping is looked up
        if mapping.looked_up:
            logger.info(f'Mapping with id {id} is already looked up')
            return mapping.external_path
        
        workstation_ip = mapping.workstation.ip_address
        workstation_port = mapping.workstation.port if mapping.workstation.port is not None else 5900
        mapping_target = f'{workstation_ip}:{workstation_port}' 

        mapping.looked_up = True
        mapping.save()

        return mapping_target
    
    def get_mapping_for_reservation(self, reservation: Reservation) -> ProxyMapping:
        self.create_mapping_for_reservation(reservation)
        return reservation.proxy_mapping
    
    def archive_mapping_for_reservation_if_exists(self, reservation: Reservation):
        if reservation.proxy_mapping is None:
            return
        reservation.proxy_mapping.archived = True
        reservation.proxy_mapping.archived_at = timezone.now()
        reservation.proxy_mapping.save()
        reservation.proxy_mapping = None
        reservation.save()
    
    def create_mapping_for_reservation(self, reservation: Reservation):
        self.archive_mapping_for_reservation_if_exists(reservation) 
             
        mapping = ProxyMapping.objects.create(
            workstation = reservation.workstation,
            external_path = f'/novnc/{None}'
        )
        mapping.external_path = f'/novnc/{mapping.id}'
        mapping.save()

        reservation.proxy_mapping = mapping
        reservation.save()

    def create_reservation(self, user, tags, start_date, end_date, user_label) -> Reservation:
        logger.info(f'Creating reservation for user {user} with tags {tags} from {start_date} to {end_date}')
        logger.info(f'Finding template with tags: {tags}')
        template = self.find_template_with_tags(tags)
        if template is None:
            logger.info(f'No template found for tags {tags}')
            return None
        logger.info(f'Found template: {template} for reservation')
        logger.info(f'User label: {user_label}')
        if user_label == "" or user_label is None or len(user_label) == 0:
            logger.info(f'No user label provided, using default')
            user_label = f'{template.name}'
        else:
            logger.info(f'Using user label: {user_label}')
        reservation = Reservation.objects.create(
            status=Reservation.Status.Pending,
            request_date=timezone.now(),
            start_date=start_date,
            end_date=end_date,
            user=user,
            template=template,
            user_label=user_label
        )
        reservation.save()
        logger.info(f'Reservation created: {reservation}')
        return reservation
    
    def cancel_reservation(self, reservation) -> bool:
        reservation_id = reservation.id
        reservation = Reservation.objects.get(id=reservation_id)
        if reservation is not None:
            reservation.set_reservation_status(Reservation.Status.Cancelled)
            return True
        return False
    
    def get_progress_for_reservation(self, reservation: Reservation) -> int:
        if reservation.status in [Reservation.Status.Completed, Reservation.Status.Cancelled, Reservation.Status.Rejected]:
            return 100

        time_between = reservation.end_date - reservation.start_date
        time_left = reservation.end_date - timezone.now()
        progress = int((time_between - time_left) / time_between * 100)
        
        return progress
    
    def restart_workstation_for_reservation(self, reservation: Reservation):
        if reservation.workstation is None:
            return False
        reservation.workstation.set_workstation_status(Workstation.Status.Restart)
        return True

        