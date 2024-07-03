from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from .forms import UserCreationFormWithEmail, CreateReservation
from django.utils import timezone
import logging

from workstation_coordinator.models import Reservation
from workstation_coordinator.coordinator import WorkstationCoordinator

logger = logging.getLogger('django.server')

# Create your views here.

def index(request):
    #return HttpResponse('Hello. You\'re at the workstation_management index.')

    template_arguments = {}

    if request.user.is_authenticated:
        logger.info('User is authenticated') 
        logger.info(request.user)
        template_arguments['username'] = request.user.username

    return render(request, 'frontend/index.html', template_arguments)

def register(request):

    if request.method == 'POST':
        form = UserCreationFormWithEmail(request.POST)
        if form.is_valid():
            logger.info("Valid form")
            form.save()
            return render(request, 'frontend/register_redirect.html')
        else:
            logger.info("Invalid form")
            return render(request, 'frontend/register.html', {'form': form})

    return render(request, 'frontend/register.html', {'form': UserCreationFormWithEmail()})

@login_required(login_url='login')
def private(request):
    logger.info('Private page accessed. User is authenticated.')
    return HttpResponse('You are logged in.')


@login_required(login_url='login')
def dashboard(request):
    template_arguments = {}
    logger.info('User is authenticated') 
    logger.info(request.user)
    template_arguments['username'] = request.user.username
    latest_reservations = Reservation.objects\
        .filter(user=request.user)\
        .filter(Q(status=Reservation.Status.Approved) | Q(status=Reservation.Status.Active))\
        .order_by('-start_date')[:2]
    template_arguments['latest_reservations'] = latest_reservations
    return render(request, 'frontend/dashboard.html', template_arguments)

@login_required(login_url='login')
def reservations(request):
    template_arguments = {}
    template_arguments['username'] = request.user.username
    return render(request, 'frontend/reservations.html', template_arguments)

@login_required(login_url='login')
def reservations_table(request, page: int):
    template_arguments = {}
    template_arguments['username'] = request.user.username
    page = page - 1
    start_index = page * 10
    end_index = start_index + 10
    user_reservations = Reservation.objects.filter(user=request.user)
    truncated_reservations = user_reservations[start_index:end_index]
    template_arguments['reservations'] = truncated_reservations
    template_arguments['current_page'] = page + 1
    template_arguments['max_pages'] = len(user_reservations) // 10 + 1

    return render(request, 'frontend/reservations_table.html', template_arguments)

@login_required(login_url='login')
def view_reservation(request, reservation_id):
    template_arguments = {}
    template_arguments['username'] = request.user.username
    reservation = Reservation.objects.get(id=reservation_id)
    template_arguments['reservation'] = reservation

    if reservation.user != request.user:
        return HttpResponse('You are not authorized to view this reservation.')

    return render(request, 'frontend/view_reservation.html', template_arguments)

@login_required(login_url='login')
def view_reservation_table(request, reservation_id):
    template_arguments = {}
    template_arguments['username'] = request.user.username
    reservation = Reservation.objects.get(id=reservation_id)
    template_arguments['reservation'] = reservation

    if reservation.user != request.user:
        return HttpResponse('You are not authorized to view this reservation.')

    return render(request, 'frontend/view_reservation_table.html', template_arguments)

@login_required(login_url='login')
def view_reservation_buttons(request, reservation_id):
    template_arguments = {}
    template_arguments['username'] = request.user.username
    reservation = Reservation.objects.get(id=reservation_id)
    template_arguments['reservation'] = reservation

    if reservation.user != request.user:
        return HttpResponse('You are not authorized to view this reservation.')

    return render(request, 'frontend/view_reservation_buttons.html', template_arguments)

@login_required(login_url='login')
def view_reservation_status(request, reservation_id):
    template_arguments = {}
    template_arguments['username'] = request.user.username
    reservation = Reservation.objects.get(id=reservation_id)
    template_arguments['reservation'] = reservation

    if reservation.user != request.user:
        return HttpResponse('You are not authorized to view this reservation.')

    return render(request, 'frontend/view_reservation_status.html', template_arguments)

@login_required(login_url='login')
def view_reservation_progress(request, reservation_id):
    coordinator = WorkstationCoordinator()
    template_arguments = {}
    template_arguments['username'] = request.user.username
    reservation = Reservation.objects.get(id=reservation_id)
    template_arguments['reservation'] = reservation
    template_arguments['progress'] =  coordinator.reservation_handler.get_progress_for_reservation(reservation)

    if reservation.user != request.user:
        return HttpResponse('You are not authorized to view this reservation.')

    return render(request, 'frontend/view_reservation_progress.html', template_arguments)

@login_required(login_url='login')
def access_reservation(request, reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    coordinator = WorkstationCoordinator()
    coordinator.reservation_handler.archive_mapping_for_reservation_if_exists(reservation)
    coordinator.reservation_handler.get_mapping_for_reservation(reservation) 
    template_arguments = {}
    template_arguments['username'] = request.user.username
    
    template_arguments['reservation'] = reservation
    template_arguments['mapping_target'] = reservation.proxy_mapping.id

    if reservation.user != request.user:
        return HttpResponse('You are not authorized to access this reservation.')

    return render(request, 'frontend/access_reservation.html', template_arguments)

@login_required(login_url='login')
def create_reservation(request):

    if request.method == 'POST':
        form = CreateReservation(request.POST)
        logger.info(f'Form data: {request.body}')
        if form.is_valid():
            logger.info("Valid form")
            selected_tags = form.cleaned_data['selected_tags']
            selected_tags = selected_tags.split('&')
            logger.info(f'Selected tags: {selected_tags}')
            #tags = form.cleaned_data['tags']
            tags = selected_tags
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            coordinator = WorkstationCoordinator()
            reservation = coordinator.reservation_handler.create_reservation(request.user, tags, start_date, end_date)
            if reservation is None:
                logger.info("Reservation not created")
                return HttpResponse('Reservation not created.') 
            return redirect('view_reservation', reservation_id=reservation.id)
        else:
            logger.info("Invalid form")
            return render(request, 'frontend/create_reservation.html', {'form': form})
    else: 
        template_arguments = {}
        template_arguments['username'] = request.user.username
        template_arguments['form'] = CreateReservation()

    return render(request, 'frontend/create_reservation.html', template_arguments)


@login_required(login_url='login')
def create_reservation(request):

    if request.method == 'POST':
        form = CreateReservation(request.POST)
        logger.info(f'Form data: {request.body}')
        if form.is_valid():
            logger.info("Valid form")
            selected_tags = form.cleaned_data['selected_tags']
            selected_tags = selected_tags.split('&')
            logger.info(f'Selected tags: {selected_tags}')
            tags = selected_tags
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            user_label = form.cleaned_data['user_label']
            logger.info(f'User label: {user_label}')

            # Validate end time and start time
            if end_date <= start_date:
                form.add_error('end_date', 'End date must be after start date.')

            if end_date < timezone.now():
                form.add_error('end_date', 'End date must be in the future.')

            if (end_date - start_date) < timezone.timedelta(minutes=15):
                form.add_error('end_date', 'Reservation must be at least 15 minutes long.')

            if len(tags) == 0 or tags is None:
                form.add_error('selected_tags', 'You must select at least one tag.')

            if len(form.errors) > 0:
                return render(request, 'frontend/create_reservation.html', {'form': form})

            coordinator = WorkstationCoordinator()
            reservation = coordinator.reservation_handler.create_reservation(request.user, tags, start_date, end_date, user_label)
            if reservation is None:
                logger.info("Reservation not created")
                return HttpResponse('Reservation not created.') 
            return redirect('view_reservation', reservation_id=reservation.id)
        else:
            logger.info("Invalid form")
            return render(request, 'frontend/create_reservation.html', {'form': form})
    else: 
        template_arguments = {}
        template_arguments['username'] = request.user.username
        template_arguments['form'] = CreateReservation()

    return render(request, 'frontend/create_reservation.html', template_arguments)

@login_required(login_url='login')
def cancel_reservation(request, reservation_id):
    reservation = Reservation.objects.get(id=reservation_id)
    if reservation.user != request.user:
        return HttpResponse('You are not authorized to cancel this reservation.')

    coordinator = WorkstationCoordinator()
    result = coordinator.reservation_handler.cancel_reservation(reservation)
    template_arguments = {}
    template_arguments['result'] = result
    
    if result:
        logger.info('Reservation cancelled')
    else:
        logger.info('Reservation not cancelled')
        
    return render(request, 'frontend/cancel_reservation.html', template_arguments)


@login_required(login_url='login')
def restart_workstation(request, reservation_id):

    reservation = Reservation.objects.get(id=reservation_id)
    if reservation.user != request.user:
        return HttpResponse('You are not authorized to cancel this reservation.')

    coordinator = WorkstationCoordinator()
    result = coordinator.reservation_handler.restart_workstation_for_reservation(reservation)
    if result:
        logger.info('Workstation restarted')
    else:
        logger.info('Workstation not restarted')
    template_arguments = {
        'reservation': reservation,
        'reservation_id': reservation_id
    } 
        
    return render(request, 'frontend/view_reservation.html', template_arguments)