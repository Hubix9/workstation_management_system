from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from django.contrib.auth.decorators import login_required
import logging
import json

from workstation_coordinator.models import Reservation
from workstation_coordinator.coordinator import WorkstationCoordinator

logger = logging.getLogger('django.server')

@login_required(login_url='login')
def get_tags_compatible_with_tags(request):
    if request.method != 'POST':
        return JsonResponse({'received': False})
    
    coordinator = WorkstationCoordinator()

    raw_tags = json.loads(request.body)['tags'] 
    logger.info(f'Received compatible tags query for tags: {raw_tags}')
    tags = coordinator.template_handler.get_tags_by_string(raw_tags)
    logger.info(f'Parsed tags: {tags}')
    compatible_tags = coordinator.template_handler.get_tags_compatible_with_tags(tags)
    logger.info(f'Compatible tags: {compatible_tags}')
    compatible_tags_names = coordinator.template_handler.get_tag_names(compatible_tags)
    logger.info(f'Compatible tags names: {compatible_tags_names}')
    return JsonResponse({'compatible_tags': compatible_tags_names})

@login_required(login_url='login')
def get_all_tags(request):
    coordinator = WorkstationCoordinator()
    tags = coordinator.template_handler.get_all_tags()
    tag_names = coordinator.template_handler.get_tag_names(tags)
    response = {'data': [{'text': tag_name, 'value': tag_name} for tag_name in tag_names]}
    return JsonResponse(response)

def get_mapping_target_for_reservation_by_token(request, token: str):
    logger.info('Received request for mapping target by token')
    logger.info(f'request method: {request.method}')
    if request.method != 'GET':
        return HttpResponse('Invalid request method') 
    
    coordinator = WorkstationCoordinator()
    try:
        #mapping_id = base64.b64decode(token).decode('utf-8')
        mapping_id = token
    except Exception as e:
        logger.error(f'Error while decoding token: {e}')
        return HttpResponse('Error while decoding token') 
    logger.info(f'Received token: {mapping_id}')
    result = coordinator.reservation_handler.get_mapping_target_by_id(mapping_id)
    logger.info(f'mapping target result: {result}')
    return HttpResponse(result)

@login_required(login_url='login')
def get_all_tags_containing_text(request):
    if request.method != 'POST':
        return JsonResponse({'received': False})
    
    coordinator = WorkstationCoordinator()
    input_text = json.loads(request.body)['text'] 
    tags = coordinator.template_handler.get_tags_containing_string_anycase(input_text)
    tag_names = coordinator.template_handler.get_tag_names(tags)
    response = {'data': [{'text': tag_name, 'value': tag_name} for tag_name in tag_names]}
    return JsonResponse(response)