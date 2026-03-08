from django import forms
from .models import Pedido

class PedidoCreateForm(forms.ModelForm):
    class Meta:
        model = Pedido
        # Con lo siguiente le indico a Django qué campos quiero pedirle al usuario
        fields = ['nombre', 'apellido', 'telefono', 'direccion']

        # Le damos algo de estilos CSS a los inputs
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej. Juan'}),
            'apellido': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Perez'}),
            'telefono': forms.TextInput(attrs={'class': 'form-input', 'placehoder': '3512946883'}),
            'direccion': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Calle Falsa 123, Barrio, Ciudad'}),
        }