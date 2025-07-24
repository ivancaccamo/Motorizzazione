from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef
from .models import Targa, Attiva, Restituita,Veicolo, Revisione
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction


def modifica(request, table, id):
    context = {'table': table}
    
    # Pre-caricamento dati
    if table == 'veicolo':
        obj = get_object_or_404(Veicolo, telaio=id)
        context['veicolo'] = obj
    elif table == 'targa':
        obj = get_object_or_404(Targa, numero=id)
        context['targa'] = obj
    elif table == 'revisione':
        obj = get_object_or_404(Revisione, numero=id)
        context['revisione'] = obj
    else:
        messages.error(request, "Operazione non supportata.")
        return redirect('home')

    # Gestione POST
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if table == 'veicolo':
                    nuovo_telaio = request.POST.get('telaio_hidden')
                    if nuovo_telaio != id and Veicolo.objects.filter(telaio=nuovo_telaio).exists():
                        messages.error(request, f"Telaio '{escape(nuovo_telaio)}' già presente.")
                    else:
                        obj.marca = request.POST.get('marca')
                        obj.modello = request.POST.get('modello')
                        obj.dataProd = request.POST.get('dataProd')
                        if nuovo_telaio != id:
                            Attiva.objects.filter(veicoloTelaio=id).update(veicoloTelaio=nuovo_telaio)
                            Restituita.objects.filter(veicoloTelaio=id).update(veicoloTelaio=nuovo_telaio)
                            obj.telaio = nuovo_telaio
                        obj.save()
                        messages.success(request, "Veicolo aggiornato con successo.")
                        return redirect('dettagli_record', table='veicolo', id=obj.telaio)

                elif table == 'targa':
                    nuovo_numero = request.POST.get('numero_hidden')
                    if nuovo_numero != id and Targa.objects.filter(numero=nuovo_numero).exists():
                        messages.error(request, f"Targa '{escape(nuovo_numero)}' già presente.")
                    else:
                        obj.dataEm = request.POST.get('dataEm')
                        if nuovo_numero != id:
                            Revisione.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)
                            Attiva.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)
                            Restituita.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)
                            obj.numero = nuovo_numero
                        obj.save()
                        messages.success(request, "Targa aggiornata con successo.")
                        return redirect('dettagli_record', table='targa', id=obj.numero)

                elif table == 'revisione':
                    obj.dataRev = request.POST.get('dataRev')
                    obj.esito = request.POST.get('esito')
                    obj.motivazione = request.POST.get('motivazione') if obj.esito == 'Non superata' else ''
                    obj.save()
                    messages.success(request, "Revisione aggiornata con successo.")
                    return redirect('dettagli_record', table='revisione', id=obj.numero)

        except Exception as e:
            messages.error(request, f"Errore durante la modifica: {e}")
    
    return render(request, 'modifica.html', context)

def dettagli_record(request, table, id):
    message = ''
    data = {}
    related = {}

    # sicurezza
    table = table.lower()
    if table not in ['veicolo', 'targa', 'revisione']:
        return redirect('home')

    # restituzione targa
    if request.method == 'POST' and 'targa_numero' in request.POST:
        targa_numero = request.POST['targa_numero']
        oggi = date.today()

        try:
            targa = Targa.objects.get(numero=targa_numero)
            attiva = Attiva.objects.get(targaNumero=targa)
            veicolo = attiva.veicoloTelaio
            Restituita.objects.create(targaNumero=targa, dataRes=oggi, veicoloTelaio=veicolo)
            attiva.delete()
            message = 'Targa restituita con successo.'
        except Exception as e:
            message = f'Errore nella restituzione: {e}'

    # logica per tipo di tabella
    if table == 'veicolo':
        veicolo = get_object_or_404(Veicolo, pk=id)
        data = veicolo

        related['attive'] = Attiva.objects.filter(veicoloTelaio=veicolo)
        related['restituite'] = Restituita.objects.filter(veicoloTelaio=veicolo)

    elif table == 'targa':
        targa = get_object_or_404(Targa, pk=id)
        data = targa

        attiva = Attiva.objects.filter(targaNumero=targa).first()
        if attiva:
            related['stato'] = 'Attiva'
            related['veicolo'] = attiva.veicoloTelaio
        else:
            related['stato'] = 'Restituita'
            related['restituzione'] = Restituita.objects.filter(targaNumero=targa).first()

        related['revisioni'] = Revisione.objects.filter(targaNumero=targa).order_by('-dataRev')

    elif table == 'revisione':
        revisione = get_object_or_404(Revisione, pk=id)
        data = revisione

    return render(request, 'read.html', {
        'table': table,
        'id': id,
        'data': data,
        'related': related,
        'message': message
    })
 
def index(request):
    o1 = "<html> <body>"
    o2 = "<p>Welcome to DJANGO</p>"
    o3 = "</body> </html>"
    return HttpResponse(o1 + o2 + o3)

def index2(request):
    response = HttpResponse(content_type="text/html")
    response.write("<html> <body>")
    response.write("<p>Welcome to DJANGO again</p>")
    response.write("</body> </html>")
    return response

# ---------------------------- GESTIONE REVISIONI ----------------------------


def gestioneRevisione(request):
    # Eliminazione revisione
    if request.method == 'POST' and request.POST.get('table') == 'revisione' and request.POST.get('id'):
        try:
            revisione = Revisione.objects.get(pk=request.POST['id'])
            revisione.delete()
            messages.success(request, "Revisione eliminata con successo.")
        except Revisione.DoesNotExist:
            messages.error(request, "Revisione non trovata.")
        return redirect('gestione_revisioni')  # name dell'url

    # Filtri dalla GET o dalla sessione
    if 'clear_filters' in request.GET:
        request.session.pop('filters_revisioni', None)
        return redirect('gestione_revisioni')

    filters = request.GET.dict()
    filters.pop('sort', None)
    filters.pop('dir', None)
    filters.pop('clear_filters', None)

    if filters:
        request.session['filters_revisioni'] = filters
    elif 'filters_revisioni' in request.session:
        filters = request.session['filters_revisioni']
        return redirect(f"{reverse('gestione_revisioni')}?{'&'.join([f'{k}={v}' for k, v in filters.items()])}")

    queryset = Revisione.objects.select_related('targaNumero')

    # Applica filtri
    if 'id_revisione' in request.GET and request.GET['id_revisione']:
        queryset = queryset.filter(numero=request.GET['id_revisione'])

    if 'dataRev' in request.GET and request.GET['dataRev']:
        queryset = queryset.filter(dataRev=request.GET['dataRev'])

    if 'stato' in request.GET and request.GET['stato']:
        if request.GET['stato'] == 'superata':
            queryset = queryset.filter(esito='Superata')
        elif request.GET['stato'] == 'non_superata':
            queryset = queryset.filter(esito='Non superata')

    # Ordinamento
    valid_columns = ['numero', 'targaNumero__numero', 'dataRev']
    order_by = request.GET.get('sort', 'numero')
    direction = request.GET.get('dir', 'asc')
    if order_by not in valid_columns:
        order_by = 'numero'
    if direction not in ['asc', 'desc']:
        direction = 'asc'
    if direction == 'desc':
        order_by = '-' + order_by

    revisioni = queryset.order_by(order_by)

    return render(request, 'revisione.html', {
        'revisioni': revisioni,
        'sort': request.GET.get('sort', ''),
        'dir': request.GET.get('dir', ''),
        'get': request.GET,
        'pagina_attiva': 'revisione',
        'show_sidebar': True,
    })


# ---------------------------- CREATE GENERICO ----------------------------

def create(request):
    table = request.GET.get('table')
    message = ''
    success = False

    if request.method == 'POST':
        if table == 'veicolo':
            telaio = ''.join(request.POST.getlist('telaio')).upper()
            if len(telaio) != 17:
                message = "Errore: Il numero di telaio deve contenere esattamente 17 caratteri."
            elif Veicolo.objects.filter(telaio=telaio).exists():
                message = "Errore: Esiste già un veicolo con questo numero di telaio."
            else:
                try:
                    Veicolo.objects.create(
                        telaio=telaio,
                        marca=request.POST['marca'],
                        modello=request.POST['modello'],
                        dataProd=request.POST['dataProd']
                    )
                    message = "Veicolo aggiunto con successo."
                    success = True
                except Exception as e:
                    message = f"Errore: {str(e)}"

        elif table == 'targa':
            numero = ''.join(request.POST.getlist('targa')).upper()
            if not re.match(r'^[A-HJ-NPR-Z]{2}[0-9]{3}[A-HJ-NPR-Z]{2}$', numero):
                message = "❌ Errore: formato targa non valido."
            elif Targa.objects.filter(numero=numero).exists():
                message = "Errore: Esiste già una targa con questo numero."
            else:
                try:
                    targa = Targa.objects.create(numero=numero, dataEm=request.POST['dataEm'])
                    Attiva.objects.create(
                        targaNumero=targa,
                        veicoloTelaio_id=request.POST['veicolo_telaio']
                    )
                    message = "Targa aggiunta con successo."
                    success = True
                except Exception as e:
                    message = f"Errore: {str(e)}"

        elif table == 'revisione':
            try:
                kwargs = {
                    'targaNumero_id': request.POST['numero_targa'],
                    'dataRev': request.POST['dataRev'],
                    'esito': request.POST['esito']
                }
                if request.POST['esito'] == 'Non superata':
                    kwargs['motivazione'] = request.POST.get('motivazione', '')
                Revisione.objects.create(**kwargs)
                message = "Revisione aggiunta con successo."
                success = True
            except Exception as e:
                message = f"Errore: {str(e)}"

        else:
            return HttpResponseBadRequest("Tipo non supportato.")

    context = {'table': table, 'message': message, 'success': success}

    if table == 'targa':
        context['veicoli_disponibili'] = Veicolo.objects.exclude(
            telaio__in=Attiva.objects.values_list('veicoloTelaio_id', flat=True)
        )
    elif table == 'revisione':
        context['targhe'] = Targa.objects.all()

    return render(request, 'create.html', context)

def gestioneTarghe(request):
    # Eliminazione targa
    if request.method == 'POST' and request.POST.get('table') == 'targa' and request.POST.get('id'):
        numero = request.POST['id']
        try:
            # Cancella tutte le revisioni collegate (e record fittiziamente collegati)
            Revisione.objects.filter(targaNumero__numero=numero).delete()
            Attiva.objects.filter(targaNumero__numero=numero).delete()
            Restituita.objects.filter(targaNumero__numero=numero).delete()
            Targa.objects.get(numero=numero).delete()
            messages.success(request, "Targa eliminata con successo.")
        except Exception as e:
            messages.error(request, f"Errore durante l'eliminazione: {str(e)}")
        return redirect('gestione_targhe')

    # Filtri sessione
    if 'clear_filters' in request.GET:
        request.session.pop('filters_targa', None)
        return redirect('gestione_targhe')

    filters = request.GET.dict()
    filters.pop('clear_filters', None)
    filters.pop('sort', None)
    filters.pop('dir', None)

    if filters:
        request.session['filters_targa'] = filters
    elif 'filters_targa' in request.session:
        filters = request.session['filters_targa']
        return redirect(f"{reverse('gestione_targhe')}?{'&'.join([f'{k}={v}' for k, v in filters.items()])}")

    # Query base
    targhe = Targa.objects.all().annotate(
        ha_attiva=Exists(Attiva.objects.filter(targaNumero=OuterRef('pk'))),
        ha_restituita=Exists(Restituita.objects.filter(targaNumero=OuterRef('pk')))
    )

    # Applica filtri
    if 'numero' in request.GET and request.GET['numero']:
        targhe = targhe.filter(numero__icontains=request.GET['numero'])

    if 'dataEm' in request.GET and request.GET['dataEm']:
        targhe = targhe.filter(dataem=request.GET['dataEm'])

    if 'statoTarga' in request.GET and request.GET['statoTarga']:
        stato = request.GET['statoTarga']
        if stato == 'Attiva':
            targhe = targhe.filter(ha_attiva=True)
        elif stato == 'Restituita':
            targhe = targhe.filter(ha_restituita=True)
        elif stato == 'Non Assegnata':
            targhe = targhe.filter(ha_attiva=False, ha_restituita=False)

    # Ordinamento
    valid_columns = ['numero', 'dataem']
    sort = request.GET.get('sort', 'numero')
    dir = request.GET.get('dir', 'asc')
    if sort not in valid_columns:
        sort = 'numero'
    if dir not in ['asc', 'desc']:
        dir = 'asc'
    order = f"-{sort}" if dir == 'desc' else sort
    targhe = targhe.order_by(order)

    return render(request, 'targa.html', {
        'targhe': targhe,
        'sort': request.GET.get('sort', ''),
        'dir': request.GET.get('dir', ''),
        'get': request.GET,
        'pagina_attiva': 'targa',
        'show_sidebar': True,
    })
def gestioneVeicoli(request):
    # Eliminazione veicolo
    if request.method == 'POST' and request.POST.get('table') == 'veicolo' and request.POST.get('id'):
        telaio = request.POST['id']
        try:
            Attiva.objects.filter(veicoloTelaio__telaio=telaio).delete()
            Restituita.objects.filter(veicoloTelaio__telaio=telaio).delete()
            Veicolo.objects.get(telaio=telaio).delete()
            messages.success(request, "Veicolo eliminato con successo.")
        except Exception as e:
            messages.error(request, f"Errore durante l'eliminazione: {str(e)}")
        return redirect('gestione_veicoli')

    # Gestione filtri in sessione
    if 'clear_filters' in request.GET:
        request.session.pop('filters_veicoli', None)
        return redirect('gestione_veicoli')

    filters = request.GET.dict()
    filters.pop('clear_filters', None)
    filters.pop('sort', None)
    filters.pop('dir', None)

    if filters:
        request.session['filters_veicoli'] = filters
    elif 'filters_veicoli' in request.session:
        filters = request.session['filters_veicoli']
        return redirect(f"{reverse('gestione_veicoli')}?{'&'.join([f'{k}={v}' for k, v in filters.items()])}")

    queryset = Veicolo.objects.all()

    # Filtri
    if 'telaio' in request.GET and request.GET['telaio']:
        queryset = queryset.filter(telaio__icontains=request.GET['telaio'])

    if 'marca' in request.GET and request.GET['marca']:
        queryset = queryset.filter(marca__icontains=request.GET['marca'])

    if 'modello' in request.GET and request.GET['modello']:
        queryset = queryset.filter(modello__icontains=request.GET['modello'])

    # Ordinamento
    valid_columns = ['telaio', 'marca', 'modello', 'data_produzione']
    sort = request.GET.get('sort', 'telaio')
    dir = request.GET.get('dir', 'asc')
    if sort not in valid_columns:
        sort = 'telaio'
    if dir not in ['asc', 'desc']:
        dir = 'asc'
    order = f"-{sort}" if dir == 'desc' else sort
    veicoli = queryset.order_by(order)

    return render(request, 'veicolo.html', {
        'veicoli': veicoli,
        'sort': sort,
        'dir': dir,
        'get': request.GET,
        'pagina_attiva': 'veicolo',
        'show_sidebar': True,
    })
    
def home(request):
    count_veicoli = Veicolo.objects.count()
    count_targhe = Targa.objects.count()
    count_revisioni = Revisione.objects.count()

    attive_targhe = Attiva.objects.count()
    restituite_targhe = Restituita.objects.count()

    rev_superate = Revisione.objects.filter(esito='Superata').count()
    rev_non_superate = Revisione.objects.exclude(esito='Superata').count()

    veicoli_con_attiva = Attiva.objects.values('veicoloTelaio').distinct().count()
    veicoli_senza = count_veicoli - veicoli_con_attiva

    context = {
        'count_veicoli': count_veicoli,
        'count_targhe': count_targhe,
        'count_revisioni': count_revisioni,
        'attive_targhe': attive_targhe,
        'restituite_targhe': restituite_targhe,
        'rev_superate': rev_superate,
        'rev_non_superate': rev_non_superate,
        'veicoli_con_attiva': veicoli_con_attiva,
        'veicoli_senza': veicoli_senza,
        'show_sidebar': False,
    }
    return render(request, 'home.html', context)