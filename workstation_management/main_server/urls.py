from django.urls import path, include

from . import views, api_views

from django.contrib.auth import views as auth_views



api_patterns = [
    path('get_tags_compatible_with_tags/', api_views.get_tags_compatible_with_tags, name='get_tags_compatible_with_tags'),
    path('get_all_tags/', api_views.get_all_tags, name='get_all_tags'),
    path('get_mapping_target_for_reservation_by_token/<str:token>', api_views.get_mapping_target_for_reservation_by_token, name='get_mapping_target_for_reservation_by_token'),
    path('get_all_tags_containing_text/', api_views.get_all_tags_containing_text, name='get_all_tags_containing_text'),
]


urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='frontend/login.html', next_page='index'), name='login'),
    path('private/', views.private, name='private'),
    path('logout/', auth_views.LogoutView.as_view(template_name='frontend/logout.html', next_page='index'), name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reservations/', views.reservations, name='reservations'),
    path('reservations_table/<int:page>/', views.reservations_table, name='reservations_table'),
    path('view_reservation/<uuid:reservation_id>/', views.view_reservation, name='view_reservation'),
    path('view_reservation_table/<uuid:reservation_id>/', views.view_reservation_table, name='view_reservation_table'),
    path('view_reservation_buttons/<uuid:reservation_id>/', views.view_reservation_buttons, name='view_reservation_buttons'),
    path('access_reservation/<uuid:reservation_id>/', views.access_reservation, name='access_reservation'),
    path('create_reservation/', views.create_reservation, name='create_reservation'),
    path('cancel_reservation/<uuid:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('view_reservation_status/<uuid:reservation_id>/', views.view_reservation_status, name='view_reservation_status'),
    path('view_reservation_progress/<uuid:reservation_id>/', views.view_reservation_progress, name='view_reservation_progress'),
    path('restart_workstation/<uuid:reservation_id>/', views.restart_workstation, name='restart_workstation'),
    path('api/', include(api_patterns)), 
]