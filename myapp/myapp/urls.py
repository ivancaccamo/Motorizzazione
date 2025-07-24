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
path("revisione/", myController.gestioneRevisione,   name="gestione_revisioni"),
path('admin/', admin.site.urls),
path('create/', myController.create, name='create'),
path('targhe/', myController.gestioneTarghe, name='gestione_targhe'),
path('veicoli/', myController.gestioneVeicoli, name='gestione_veicoli'),
path('revisioni/crea/', myController.create, name='crea_revisione'),
path('', myController.home, name='home'),
path('read/', myController.dettagli_record, name='dettaglio_record'),
path('modifica/<str:table>/<str:id>/', myController.modifica, name='modifica'),
path('dettagli/<str:table>/<str:id>/', myController.dettagli_record, name='dettaglio_record'),
path('targhe/<str:numero>/',myController.dettagli_record,name='dettaglio_record'),
path(
        'targhe/<str:numero>/modifica/',
        myController.modifica,           # o chiami un wrapper se serve
        name='modifica_targa'
    ),
#path('read/', myController.read, name='read'),
#path('update/', myController.update, name='update')
 ]

