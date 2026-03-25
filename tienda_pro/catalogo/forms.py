from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Pedido

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'tuemail@ejemplo.com'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email')
        labels = {
            'username': 'Usuario',
            'email': 'Email',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre de usuario'
            })
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class PedidoCreateForm(forms.ModelForm):
    class Meta:
        model = Pedido
        # Con lo siguiente le indico a Django qué campos quiero pedirle al usuario
        fields = ['nombre', 'apellido', 'telefono', 'direccion', 'email']

        # Le damos algo de estilos CSS a los inputs
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej. Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Perez'}),
            'telefono': forms.TextInput(attrs={'class': 'form-input', 'placehoder': '3512946883'}),
            'direccion': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Calle Falsa 123, Barrio, Ciudad'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'nombre@mail.com'})
        }