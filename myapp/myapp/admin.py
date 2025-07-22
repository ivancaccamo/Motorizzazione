from django.contrib import admin
from .models import Veicolo, Targa, Revisione, Attiva, Restituita  # importa tutti i modelli

admin.site.register(Veicolo)
admin.site.register(Targa)
admin.site.register(Revisione)
admin.site.register(Attiva)
admin.site.register(Restituita)
