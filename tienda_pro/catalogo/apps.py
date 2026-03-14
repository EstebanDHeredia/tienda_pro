from django.apps import AppConfig


class CatalogoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalogo"
    
    def ready(self):
        # Importo las señales para que se registren al iniciar el servidor
        import catalogo.signals
