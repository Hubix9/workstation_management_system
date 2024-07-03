from typing import Any
from main_server.models import User
from django.db import models
import uuid
from django.utils import timezone

class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class EngineType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

class Engine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    port = models.IntegerField()
    type = models.ForeignKey(EngineType, on_delete=models.SET_NULL, null=True)
    available_resources = models.JSONField()
    max_resources = models.JSONField()

    def __str__(self):
        return self.name

class Host(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField()
    engines = models.ManyToManyField(Engine)

    def __str__(self):
        return self.name

class Template(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    internal_name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    allowed_hosts = models.ManyToManyField(Host)
    allowed_engine_types = models.ManyToManyField(EngineType)
    tags = models.ManyToManyField(Tag)
    resource_requirements = models.JSONField()

    def __str__(self):
        return self.name

class Workstation(models.Model):

    class Status(models.TextChoices):
        Cleanup = 'Cleanup'
        Active = 'Active'
        Setup = 'Setup'
        Archived = 'Archived'
        Scheduled = 'Scheduled'
        Broken = 'Broken'
        Restart = 'Restart'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True) 
    port = models.IntegerField(null=True, blank=True)
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True)
    host = models.ForeignKey(Host, on_delete=models.SET_NULL, null=True)
    engine = models.ForeignKey(Engine, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=200, choices=Status.choices, default=Status.Scheduled)
    engine_internal_name = models.CharField(max_length=200, null=True, blank=True)
    additional_information = models.JSONField(null=True, blank=True)
    last_status_update = models.DateTimeField(auto_now=True)

    def set_workstation_status(self, status: Status):
        self.status = status
        self.last_status_update = timezone.now()
        self.save()

    def __str__(self):
        return f'({self.ip_address}, {self.port}, {self.template}, {self.host}, {self.engine}, {self.status}, {self.engine_internal_name})'
    
    class Meta:
        ordering = ['-last_status_update']

class ProxyMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workstation = models.ForeignKey(Workstation, on_delete=models.SET_NULL, null=True)
    external_path = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    looked_up = models.BooleanField(default=False)

    def __str__(self):
        return f'({self.workstation}, {self.external_path}, {self.created_at}, {self.archived_at}, {"archived" if self.archived else "active"})' 

    class Meta:
        ordering = ['-created_at']

class Reservation(models.Model):

    class Status(models.TextChoices):
        Active = 'Active'
        Pending = 'Pending'
        Completed = 'Completed'
        Rejected = 'Rejected'
        Cancelled = 'Cancelled'
        Approved = 'Approved'
        Broken = 'Broken'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=200, choices=Status.choices, default=Status.Pending)
    request_date = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True)
    workstation = models.ForeignKey(Workstation, on_delete=models.SET_NULL, null=True, blank=True)
    proxy_mapping = models.OneToOneField(ProxyMapping, on_delete=models.SET_NULL, null=True, blank=True)
    additional_information = models.JSONField(null=True, blank=True)
    last_status_update = models.DateTimeField(auto_now=True)
    user_label = models.CharField(max_length=50, null=True, blank=True)

    def set_reservation_status(self, status: Status):
        self.status = status
        self.last_status_update = timezone.now()
        self.save()

    def __str__(self) -> str:
        response = f'({self.user_label}, {self.template}, {self.user}, {self.request_date}, {self.start_date}, {self.end_date}, {self.status})' 
        return response
    
    class Meta:
        ordering = ['-request_date']
    

