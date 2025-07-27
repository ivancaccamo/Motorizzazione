"""
URL configuration for myapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from . import myController
urlpatterns = [
    # Gestione revisioni (elenco, filtri, elimina)
    path("revisione/", myController.gestioneRevisione, name="gestione_revisioni"),

    # Interfaccia di amministrazione Django
    path('admin/', admin.site.urls),

    # Creazione generica (veicolo, targa, revisione)
    path('create/', myController.create, name='create'),

    # Gestione targhe (elenco, filtri, elimina)
    path('targhe/', myController.gestioneTarghe, name='gestione_targhe'),

    # Gestione veicoli (elenco, filtri, elimina)
    path('veicoli/', myController.gestioneVeicoli, name='gestione_veicoli'),

    # Shortcut per creare una revisione (non obbligatorio se già incluso in /create/)
    path('revisioni/crea/', myController.create, name='crea_revisione'),

    # Dashboard iniziale
    path('', myController.home, name='home'),

    # Visualizzazione dettagli di un record (GET o POST restituzione)
    path('read/', myController.dettagli_record, name='dettaglio_record'),  # ← può essere ridondante

    # Modifica generica per entità (veicolo, targa, revisione)
    path('modifica/<str:table>/<str:id>/', myController.modifica, name='modifica'),

    # Visualizzazione dettagli tramite URL dinamico (preferibile)
    path('dettagli/<str:table>/<str:id>/', myController.dettagli_record, name='dettaglio_record'),

    # Modifica targa con URL semantico (usato se serve URL specifico)
    path('targhe/<str:numero>/modifica/', myController.modifica, name='modifica_targa'),
]



