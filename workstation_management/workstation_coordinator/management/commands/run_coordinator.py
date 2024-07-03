from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Run the workstation coordinator'

    def handle(self, *args, **options):
        from workstation_coordinator.coordinator import WorkstationCoordinator
        coordinator = WorkstationCoordinator()
        coordinator._main_loop()