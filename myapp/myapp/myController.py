import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef
from .models import Targa, Attiva, Restituita,Veicolo, Revisione
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.utils.html import escape
import re
from datetime import date


def modifica(request, table, id):
    # Pre-caricamento oggetto e contest
    context = {'table': table}
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

    # Se POST, elaboro la modifica
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if table == 'veicolo':
                    # ricompongo il telaio da tutti i singoli input
                    lista = request.POST.getlist('telaio[]')
                    nuovo_telaio = ''.join(lista).upper()

                    # controllo unicità
                    if nuovo_telaio != id and Veicolo.objects.filter(telaio=nuovo_telaio).exists():
                        messages.error(request, f"Telaio '{escape(nuovo_telaio)}' già presente.")
                    else:
                        # salvo gli altri campi
                        obj.marca    = request.POST.get('marca').strip()
                        obj.modello  = request.POST.get('modello').strip()
                        obj.data_produzione = request.POST.get('dataProd')

                        # se è cambiato il telaio, aggiorno anche le FK nelle relazioni
                        if nuovo_telaio != id:
                            Attiva.objects.filter(veicoloTelaio=id).update(veicoloTelaio=nuovo_telaio)
                            Restituita.objects.filter(veicoloTelaio=id).update(veicoloTelaio=nuovo_telaio)
                            obj.telaio = nuovo_telaio

                        obj.save()
                        messages.success(request, "Veicolo aggiornato con successo.")
                        return redirect('dettaglio_record', table='veicolo', id=obj.telaio)

                elif table == 'targa':
                    lista = request.POST.getlist('targa[]')
                    nuovo_numero = ''.join(lista).upper()

                    if nuovo_numero != id and Targa.objects.filter(numero=nuovo_numero).exists():
                        messages.error(request, f"Targa '{escape(nuovo_numero)}' già presente.")
                    else:
                        # Aggiorno la data di emissione
                        obj.dataEm = request.POST.get('dataEm')

                        # Se il numero è cambiato, devo gestire la modifica della PK
                        if nuovo_numero != id:
                            # Prima aggiorno tutte le relazioni FK
                            Revisione.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)
                            Attiva.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)
                            Restituita.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)
                            
                            # Ottengo tutti i valori del vecchio oggetto
                            old_values = {}
                            for field in obj._meta.fields:
                                if field.name != 'numero':  # Escludo il campo che sto cambiando
                                    old_values[field.name] = getattr(obj, field.name)
                            
                            # Creo un nuovo oggetto copiando tutti i campi
                            nuovo_obj = Targa(numero=nuovo_numero, **old_values)
                            nuovo_obj.save()
                            
                            # Elimino il vecchio oggetto
                            obj.delete()
                            
                            # Aggiorno il riferimento per il redirect
                            obj = nuovo_obj
                        else:
                            # Se il numero non è cambiato, salvo normalmente
                            obj.save()

                        messages.success(request, "Targa aggiornata con successo.")
                        return redirect('dettaglio_record', table='targa', id=obj.numero)

                elif table == 'revisione':
                    obj.dataRev     = request.POST.get('dataRev')
                    obj.esito       = request.POST.get('esito')
                    # solo se "Non superata" prendo la motivazione
                    if obj.esito == 'Non superata':
                        obj.motivazione = request.POST.get('motivazione', '').strip()
                    else:
                        obj.motivazione = ''
                    obj.save()
                    messages.success(request, "Revisione aggiornata con successo.")
                    return redirect('dettaglio_record', table='revisione', id=obj.numero)

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
            Restituita.objects.create(targaNumero=targa, data_restituzione=oggi, veicoloTelaio=veicolo)
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

    # Gestione clear filters
    if 'clear_filters' in request.GET:
        request.session.pop('filters_revisioni', None)
        return redirect('gestione_revisioni')

    # Ottieni tutti i parametri dalla GET
    current_params = request.GET.dict()
    
    # Separa i filtri dai parametri di ordinamento
    filters = {k: v for k, v in current_params.items() 
              if k not in ['sort', 'dir', 'clear_filters'] and v}
    
    sort_param = request.GET.get('sort', 'numero')
    dir_param = request.GET.get('dir', 'asc')

    # Gestione filtri in sessione
    if filters:
        # Salva i filtri in sessione
        request.session['filters_revisioni'] = filters
    elif 'filters_revisioni' in request.session and not any(k in current_params for k in ['sort', 'dir']):
        # Se non ci sono filtri nella GET e non stiamo ordinando, 
        # recupera i filtri dalla sessione e reindirizza
        saved_filters = request.session['filters_revisioni']
        filter_params = '&'.join([f'{k}={v}' for k, v in saved_filters.items()])
        return redirect(f"{reverse('gestione_revisioni')}?{filter_params}")
    elif 'filters_revisioni' in request.session:
        # Se stiamo ordinando, usa i filtri salvati
        filters = request.session['filters_revisioni']

    queryset = Revisione.objects.select_related('targaNumero')

    # Applica filtri
    if 'id_revisione' in filters and filters['id_revisione']:
        queryset = queryset.filter(numero=filters['id_revisione'])

    if 'dataRev' in filters and filters['dataRev']:
        queryset = queryset.filter(dataRev=filters['dataRev'])

    if 'stato' in filters and filters['stato']:
        if filters['stato'] == 'superata':
            queryset = queryset.filter(esito='Superata')
        elif filters['stato'] == 'non_superata':
            queryset = queryset.filter(esito='Non superata')

    # Validazione e applicazione ordinamento
    valid_columns = ['numero', 'targaNumero__numero', 'dataRev']
    if sort_param not in valid_columns:
        sort_param = 'numero'
    if dir_param not in ['asc', 'desc']:
        dir_param = 'asc'
    
    order = f"-{sort_param}" if dir_param == 'desc' else sort_param
    revisioni = queryset.order_by(order)

    return render(request, 'revisione.html', {
        'revisioni': revisioni,
        'sort': sort_param,
        'dir': dir_param,
        'get': request.GET,
        'current_filters': filters,  # Aggiungi i filtri correnti
        'pagina_attiva': 'revisione',
        'show_sidebar': True,
    })


# ---------------------------- CREATE GENERICO ----------------------------

def create(request):
    # Prova prima da POST (quando si invia il form), poi da GET (primo caricamento)
    table = request.POST.get('table') or request.GET.get('table')
    message = ''
    success = False

    if request.method == 'POST':
        
        if table == 'veicolo':
            telaio = ''.join(request.POST.getlist('telaio[]')).upper()
            if len(telaio) != 17:
                print("Telaio:", telaio)
                message = f"Errore: Il numero di telaio deve contenere esattamente 17 caratteri.{telaio}"
            elif Veicolo.objects.filter(telaio=telaio).exists():
                message = "Errore: Esiste già un veicolo con questo numero di telaio."
            else:
                try:
                    Veicolo.objects.create(
                        telaio=telaio,
                        marca=request.POST['marca'],
                        modello=request.POST['modello'],
                        data_produzione=request.POST['dataProd']
                    )
                    message = "Veicolo aggiunto con successo."
                    success = True
                except Exception as e:
                    message = f"Errore: {str(e)}"

        elif table == 'targa':
            targa_parts = request.POST.getlist('targa[]')
            numero = ''.join(targa_parts).upper()
            
            # Validazione formato targa italiana (esclude lettere I, O, Q, U)
            if not re.match(r'^[A-HJ-NPR-Z]{2}[0-9]{3}[A-HJ-NPR-Z]{2}$', numero):
                message = "❌ Errore: formato targa non valido. Deve essere: 2 lettere + 3 numeri + 2 lettere (escluse I, O, Q, U)."
            elif len(numero) != 7:
                message = f"Errore: La targa deve contenere esattamente 7 caratteri. Ricevuto: {len(numero)} caratteri."
            elif Targa.objects.filter(numero=numero).exists():
                message = "Errore: Esiste già una targa con questo numero."
            else:
                veicolo_telaio = request.POST.get('veicolo_telaio')
                if not veicolo_telaio:
                    message = "Errore: Devi selezionare un veicolo per la targa."
                else:
                    try:
                        # Verifica che il veicolo esista e non abbia già una targa attiva
                        if not Veicolo.objects.filter(telaio=veicolo_telaio).exists():
                            message = "Errore: Il veicolo selezionato non esiste."
                        elif Attiva.objects.filter(veicoloTelaio=veicolo_telaio).exists():
                            message = "Errore: Il veicolo selezionato ha già una targa attiva."
                        else:
                            # Crea la targa
                            targa = Targa.objects.create(
                                numero=numero, 
                                dataEm=request.POST['dataEm']
                            )
                            
                            # Recupera l'oggetto Veicolo
                            veicolo_obj = Veicolo.objects.get(telaio=veicolo_telaio)
                            
                            # Crea la relazione attiva
                            Attiva.objects.create(
                                targaNumero=targa,
                                veicoloTelaio=veicolo_obj  # <- Corretto!
                            )
                            message = "Targa aggiunta con successo."
                            success = True
                    except Exception as e:
                        message = f"Errore durante la creazione della targa: {str(e)}"

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
            return HttpResponseBadRequest(f"Tipo non supportato: {table}")

    # Se table è ancora None, mostra errore
    if not table:
        return HttpResponseBadRequest("Parametro 'table' mancante. Usa ?table=veicolo, ?table=targa, o ?table=revisione nell'URL.")

    context = {'table': table, 'message': message, 'success': success}

    if table == 'targa':
        # Ottieni veicoli disponibili (senza targa attiva)
        veicoli_disponibili = Veicolo.objects.exclude(
            telaio__in=Attiva.objects.values_list('veicoloTelaio_id', flat=True)
        ).order_by('marca', 'modello', 'telaio')
        
        # Converti in formato JSON per JavaScript
        veicoli_list = []
        for veicolo in veicoli_disponibili:
            veicoli_list.append({
                'telaio': veicolo.telaio,
                'marca': veicolo.marca,
                'modello': veicolo.modello,
                'dataProd': veicolo.data_produzione.strftime('%Y-%m-%d') if veicolo.data_produzione else ''
            })
        
        context['veicoli_disponibili'] = veicoli_disponibili
        context['veicoli_disponibili_json'] = json.dumps(veicoli_list)

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

    # Gestione clear filters
    if 'clear_filters' in request.GET:
        request.session.pop('filters_targa', None)
        return redirect('gestione_targhe')

    # Ottieni tutti i parametri dalla GET
    current_params = request.GET.dict()
    
    # Separa i filtri dai parametri di ordinamento
    filters = {k: v for k, v in current_params.items() 
              if k not in ['sort', 'dir', 'clear_filters'] and v}
    
    sort_param = request.GET.get('sort', 'numero')
    dir_param = request.GET.get('dir', 'asc')

    # Gestione filtri in sessione
    if filters:
        # Salva i filtri in sessione
        request.session['filters_targa'] = filters
    elif 'filters_targa' in request.session and not any(k in current_params for k in ['sort', 'dir']):
        # Se non ci sono filtri nella GET e non stiamo ordinando, 
        # recupera i filtri dalla sessione e reindirizza
        saved_filters = request.session['filters_targa']
        filter_params = '&'.join([f'{k}={v}' for k, v in saved_filters.items()])
        return redirect(f"{reverse('gestione_targhe')}?{filter_params}")
    elif 'filters_targa' in request.session:
        # Se stiamo ordinando, usa i filtri salvati
        filters = request.session['filters_targa']

    # Query base
    targhe = Targa.objects.all().annotate(
        ha_attiva=Exists(Attiva.objects.filter(targaNumero=OuterRef('pk'))),
        ha_restituita=Exists(Restituita.objects.filter(targaNumero=OuterRef('pk')))
    )

    # Applica filtri
    if 'numero' in filters and filters['numero']:
        targhe = targhe.filter(numero__icontains=filters['numero'])

    if 'dataEm' in filters and filters['dataEm']:
        targhe = targhe.filter(dataEm=filters['dataEm'])

    if 'statoTarga' in filters and filters['statoTarga']:
        stato = filters['statoTarga']
        if stato == 'Attiva':
            targhe = targhe.filter(ha_attiva=True)
        elif stato == 'Restituita':
            targhe = targhe.filter(ha_restituita=True)
        elif stato == 'Non Assegnata':
            targhe = targhe.filter(ha_attiva=False, ha_restituita=False)

    # Validazione e applicazione ordinamento
    valid_columns = ['numero', 'dataEm']
    if sort_param not in valid_columns:
        sort_param = 'numero'
    if dir_param not in ['asc', 'desc']:
        dir_param = 'asc'
    
    order = f"-{sort_param}" if dir_param == 'desc' else sort_param
    targhe = targhe.order_by(order)

    return render(request, 'targa.html', {
        'targhe': targhe,
        'sort': sort_param,
        'dir': dir_param,
        'get': request.GET,
        'current_filters': filters,  # Aggiungi i filtri correnti
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

    # Gestione clear filters
    if 'clear_filters' in request.GET:
        request.session.pop('filters_veicoli', None)
        return redirect('gestione_veicoli')

    # Ottieni tutti i parametri dalla GET
    current_params = request.GET.dict()
    
    # Separa i filtri dai parametri di ordinamento
    filters = {k: v for k, v in current_params.items() 
              if k not in ['sort', 'dir', 'clear_filters'] and v}
    
    sort_param = request.GET.get('sort', 'telaio')
    dir_param = request.GET.get('dir', 'asc')

    # Gestione filtri in sessione
    if filters:
        # Salva i filtri in sessione
        request.session['filters_veicoli'] = filters
    elif 'filters_veicoli' in request.session and not any(k in current_params for k in ['sort', 'dir']):
        # Se non ci sono filtri nella GET e non stiamo ordinando, 
        # recupera i filtri dalla sessione e reindirizza
        saved_filters = request.session['filters_veicoli']
        filter_params = '&'.join([f'{k}={v}' for k, v in saved_filters.items()])
        return redirect(f"{reverse('gestione_veicoli')}?{filter_params}")
    elif 'filters_veicoli' in request.session:
        # Se stiamo ordinando, usa i filtri salvati
        filters = request.session['filters_veicoli']

    # Costruisci la query
    queryset = Veicolo.objects.all()

    # Applica filtri
    if 'telaio' in filters and filters['telaio']:
        queryset = queryset.filter(telaio__icontains=filters['telaio'])

    if 'marca' in filters and filters['marca']:
        queryset = queryset.filter(marca__icontains=filters['marca'])

    if 'modello' in filters and filters['modello']:
        queryset = queryset.filter(modello__icontains=filters['modello'])

    # Validazione e applicazione ordinamento
    valid_columns = ['telaio', 'marca', 'modello', 'data_produzione']
    if sort_param not in valid_columns:
        sort_param = 'telaio'
    if dir_param not in ['asc', 'desc']:
        dir_param = 'asc'
    
    order = f"-{sort_param}" if dir_param == 'desc' else sort_param
    veicoli = queryset.order_by(order)

    return render(request, 'veicolo.html', {
        'veicoli': veicoli,
        'sort': sort_param,
        'dir': dir_param,
        'get': request.GET,
        'current_filters': filters,  # Aggiungi i filtri correnti
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