from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from workstation_coordinator.models import Tag


class NoInput(forms.Widget):
    input_type = "hidden"
    template_name = ""

    def render(self, name, value, attrs=None, renderer=None):
        return ""

class UserCreationFormWithEmail(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class CreateReservation(forms.Form):
    all_tags = [(tag.name, tag.name) for tag in Tag.objects.all()]
    selected_tags = forms.CharField(widget=NoInput)
    start_date = forms.DateTimeField(label='Start date', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})) 
    end_date = forms.DateTimeField(label='End date', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})) 
    user_label = forms.CharField(label='Reservation label', max_length=50, required=False, widget=forms.TextInput(attrs={'placeholder': '(Optional) Enter a label for this reservation'}))