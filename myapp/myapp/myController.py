# ---------------------------- IMPORT ----------------------------

import json
import re
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import transaction
from django.db.models import Q, Exists, OuterRef
from django.utils.html import escape
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import Targa, Attiva, Restituita, Veicolo, Revisione


# ---------------------------- VISTA MODIFICA ----------------------------

def modifica(request, table, id):
    context = {'table': table}

    # Recupero oggetto in base alla tabella
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

    # Gestione form POST (modifica)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                if table == 'veicolo':
                    lista = request.POST.getlist('telaio[]')
                    nuovo_telaio = ''.join(lista).upper()

                    if nuovo_telaio != id and Veicolo.objects.filter(telaio=nuovo_telaio).exists():
                        messages.error(request, f"Telaio '{escape(nuovo_telaio)}' già presente.")
                    else:
                        obj.marca = request.POST.get('marca').strip()
                        obj.modello = request.POST.get('modello').strip()
                        obj.data_produzione = request.POST.get('dataProd')

                        # Aggiorna FK se il telaio cambia
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
                        obj.dataEm = request.POST.get('dataEm')

                        if nuovo_numero != id:
                            Revisione.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)
                            Attiva.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)
                            Restituita.objects.filter(targaNumero=id).update(targaNumero=nuovo_numero)

                            # Clona oggetto con nuova PK
                            old_values = {
                                field.name: getattr(obj, field.name)
                                for field in obj._meta.fields if field.name != 'numero'
                            }
                            nuovo_obj = Targa(numero=nuovo_numero, **old_values)
                            nuovo_obj.save()
                            obj.delete()
                            obj = nuovo_obj
                        else:
                            obj.save()

                        messages.success(request, "Targa aggiornata con successo.")
                        return redirect('dettaglio_record', table='targa', id=obj.numero)

                elif table == 'revisione':
                    obj.dataRev = request.POST.get('dataRev')
                    obj.esito = request.POST.get('esito')
                    obj.motivazione = request.POST.get('motivazione', '').strip() if obj.esito == 'Non superata' else ''
                    obj.save()
                    messages.success(request, "Revisione aggiornata con successo.")
                    return redirect('dettaglio_record', table='revisione', id=obj.numero)

        except Exception as e:
            messages.error(request, f"Errore durante la modifica: {e}")

    return render(request, 'modifica.html', context)


# ---------------------------- DETTAGLIO RECORD ----------------------------

def dettagli_record(request, table, id):
    message = ''
    data = {}
    related = {}

    table = table.lower()
    if table not in ['veicolo', 'targa', 'revisione']:
        return redirect('home')

    # Restituzione targa (POST)
    if request.method == 'POST' and 'targa_numero' in request.POST:
        try:
            targa = Targa.objects.get(numero=request.POST['targa_numero'])
            attiva = Attiva.objects.get(targaNumero=targa)
            Restituita.objects.create(
                targaNumero=targa,
                data_restituzione=date.today(),
                veicoloTelaio=attiva.veicoloTelaio
            )
            attiva.delete()
            message = 'Targa restituita con successo.'
        except Exception as e:
            message = f'Errore nella restituzione: {e}'

    # Recupero dati specifici in base alla tabella
    if table == 'veicolo':
        data = get_object_or_404(Veicolo, pk=id)
        related['attive'] = Attiva.objects.filter(veicoloTelaio=data)
        related['restituite'] = Restituita.objects.filter(veicoloTelaio=data)

    elif table == 'targa':
        data = get_object_or_404(Targa, pk=id)
        attiva = Attiva.objects.filter(targaNumero=data).first()
        if attiva:
            related['stato'] = 'Attiva'
            related['veicolo'] = attiva.veicoloTelaio
        else:
            related['stato'] = 'Restituita'
            related['restituzione'] = Restituita.objects.filter(targaNumero=data).first()
        related['revisioni'] = Revisione.objects.filter(targaNumero=data).order_by('-dataRev')

    elif table == 'revisione':
        data = get_object_or_404(Revisione, pk=id)

    return render(request, 'read.html', {
        'table': table,
        'id': id,
        'data': data,
        'related': related,
        'message': message
    })


# ---------------------------- HOMEPAGE ----------------------------

def home(request):
    context = {
        'count_veicoli': Veicolo.objects.count(),
        'count_targhe': Targa.objects.count(),
        'count_revisioni': Revisione.objects.count(),
        'attive_targhe': Attiva.objects.count(),
        'restituite_targhe': Restituita.objects.count(),
        'rev_superate': Revisione.objects.filter(esito='Superata').count(),
        'rev_non_superate': Revisione.objects.exclude(esito='Superata').count(),
        'veicoli_con_attiva': Attiva.objects.values('veicoloTelaio').distinct().count(),
        'veicoli_senza': Veicolo.objects.count() - Attiva.objects.values('veicoloTelaio').distinct().count(),
        'show_sidebar': False,
    }
    return render(request, 'home.html', context)


# ---------------------------- GESTIONE REVISIONI ----------------------------

def gestioneRevisione(request):
    # Eliminazione revisione via POST
    if request.method == 'POST' and request.POST.get('table') == 'revisione' and request.POST.get('id'):
        try:
            revisione = Revisione.objects.get(pk=request.POST['id'])
            revisione.delete()
            messages.success(request, "Revisione eliminata con successo.")
        except Revisione.DoesNotExist:
            messages.error(request, "Revisione non trovata.")
        return redirect('gestione_revisioni')

    # Reset filtri (clear)
    if 'clear_filters' in request.GET:
        request.session.pop('filters_revisioni', None)
        return redirect('gestione_revisioni')

    # Parsing parametri da GET
    current_params = request.GET.dict()
    filters = {k: v for k, v in current_params.items() if k not in ['sort', 'dir', 'clear_filters'] and v}
    sort_param = request.GET.get('sort', 'numero')
    dir_param = request.GET.get('dir', 'asc')

    # Salvataggio filtri in sessione
    if filters:
        request.session['filters_revisioni'] = filters
    elif 'filters_revisioni' in request.session and not any(k in current_params for k in ['sort', 'dir']):
        saved_filters = request.session['filters_revisioni']
        return redirect(f"{reverse('gestione_revisioni')}?{'&'.join([f'{k}={v}' for k,v in saved_filters.items()])}")
    elif 'filters_revisioni' in request.session:
        filters = request.session['filters_revisioni']

    # Costruzione queryset con filtri
    queryset = Revisione.objects.select_related('targaNumero')

    if 'id_revisione' in filters:
        queryset = queryset.filter(numero=filters['id_revisione'])

    if 'dataRev' in filters:
        queryset = queryset.filter(dataRev=filters['dataRev'])

    if 'stato' in filters:
        stato = filters['stato']
        if stato == 'superata':
            queryset = queryset.filter(esito='Superata')
        elif stato == 'non_superata':
            queryset = queryset.filter(esito='Non superata')

    # Ordinamento valido
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
        'current_filters': filters,
        'pagina_attiva': 'revisione',
        'show_sidebar': True,
    })
# ---------------------------- CREATE GENERICO ----------------------------

@require_http_methods(["GET", "POST"])
def create(request):
    table = request.POST.get('table') or request.GET.get('table')
    if not table:
        return HttpResponseBadRequest("Parametro 'table' mancante. Usa ?table=veicolo, ?table=targa o ?table=revisione.")

    message = ''
    success = False

    # Form inviato via POST
    if request.method == 'POST':
        if table == 'veicolo':
            telaio = ''.join(request.POST.getlist('telaio[]')).upper()
            if len(telaio) != 17:
                message = f"Errore: Il numero di telaio deve contenere esattamente 17 caratteri. Ricevuto: {len(telaio)}"
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
                    message = f"Errore durante la creazione del veicolo: {e}"

        elif table == 'targa':
            numero = ''.join(request.POST.getlist('targa[]')).upper()
            if len(numero) != 7:
                message = f"Errore: La targa deve contenere 7 caratteri. Ricevuto: {len(numero)}"
            elif not re.match(r'^[A-HJ-NPR-Z]{2}[0-9]{3}[A-HJ-NPR-Z]{2}$', numero):
                message = "Errore: formato targa non valido."
            elif Targa.objects.filter(numero=numero).exists():
                message = "Errore: Esiste già una targa con questo numero."
            else:
                veicolo_telaio = request.POST.get('veicolo_telaio')
                if not veicolo_telaio:
                    message = "Errore: Devi selezionare un veicolo."
                else:
                    try:
                        veicolo = Veicolo.objects.get(telaio=veicolo_telaio)
                        if Attiva.objects.filter(veicoloTelaio=veicolo).exists():
                            message = "Errore: Il veicolo ha già una targa attiva."
                        else:
                            t = Targa.objects.create(
                                numero=numero,
                                dataEm=request.POST['dataEm']
                            )
                            Attiva.objects.create(
                                targaNumero=t,
                                veicoloTelaio=veicolo
                            )
                            message = "Targa aggiunta con successo."
                            success = True
                    except Veicolo.DoesNotExist:
                        message = "Errore: Veicolo non trovato."
                    except Exception as e:
                        message = f"Errore durante la creazione della targa: {e}"

        elif table == 'revisione':
            numero_targa = request.POST.get('numero_targa')
            dataRev = request.POST.get('dataRev')
            esito = request.POST.get('esito')
            if not (numero_targa and dataRev and esito):
                message = "Errore: tutti i campi sono obbligatori."
            else:
                try:
                    kwargs = {
                        'targaNumero_id': numero_targa,
                        'dataRev': dataRev,
                        'esito': esito,
                    }
                    if esito == 'Non superata':
                        kwargs['motivazione'] = request.POST.get('motivazione', '')
                    Revisione.objects.create(**kwargs)
                    message = "Revisione aggiunta con successo."
                    success = True
                except Exception as e:
                    message = f"Errore durante la creazione della revisione: {e}"

        else:
            return HttpResponseBadRequest(f"Tipo non supportato: {table}")

    # Preparazione contesto per form GET
    context = {
        'table': table,
        'message': message,
        'success': success,
    }

    if table == 'targa':
        veicoli_disponibili = Veicolo.objects.exclude(
            telaio__in=Attiva.objects.values_list('veicoloTelaio_id', flat=True)
        ).order_by('marca', 'modello', 'telaio')

        context['veicoli_disponibili'] = veicoli_disponibili
        context['veicoli_disponibili_json'] = json.dumps([
            {
                'telaio': v.telaio,
                'marca': v.marca,
                'modello': v.modello,
                'dataProd': v.data_produzione.strftime('%Y-%m-%d') if v.data_produzione else ''
            } for v in veicoli_disponibili
        ])

    elif table == 'revisione':
        context['targhe'] = Targa.objects.all()

    return render(request, 'create.html', context)

def gestioneTarghe(request):
    # Eliminazione targa via POST
    if request.method == 'POST' and request.POST.get('table') == 'targa' and request.POST.get('id'):
        try:
            numero = request.POST['id']
            Revisione.objects.filter(targaNumero__numero=numero).delete()
            Attiva.objects.filter(targaNumero__numero=numero).delete()
            Restituita.objects.filter(targaNumero__numero=numero).delete()
            Targa.objects.get(numero=numero).delete()
            messages.success(request, "Targa eliminata con successo.")
        except Exception as e:
            messages.error(request, f"Errore durante l'eliminazione: {e}")
        return redirect('gestione_targhe')

    # Gestione filtri
    if 'clear_filters' in request.GET:
        request.session.pop('filters_targa', None)
        return redirect('gestione_targhe')

    current_params = request.GET.dict()
    filters = {k: v for k, v in current_params.items() if k not in ['sort', 'dir', 'clear_filters'] and v}
    sort_param = request.GET.get('sort', 'numero')
    dir_param = request.GET.get('dir', 'asc')

    if filters:
        request.session['filters_targa'] = filters
    elif 'filters_targa' in request.session and not any(k in current_params for k in ['sort', 'dir']):
        saved_filters = request.session['filters_targa']
        return redirect(f"{reverse('gestione_targhe')}?{'&'.join([f'{k}={v}' for k,v in saved_filters.items()])}")
    elif 'filters_targa' in request.session:
        filters = request.session['filters_targa']

    targhe = Targa.objects.annotate(
        ha_attiva=Exists(Attiva.objects.filter(targaNumero=OuterRef('pk'))),
        ha_restituita=Exists(Restituita.objects.filter(targaNumero=OuterRef('pk')))
    )

    if 'numero' in filters:
        targhe = targhe.filter(numero__icontains=filters['numero'])
    if 'dataEm' in filters:
        targhe = targhe.filter(dataEm=filters['dataEm'])
    if 'statoTarga' in filters:
        if filters['statoTarga'] == 'Attiva':
            targhe = targhe.filter(ha_attiva=True)
        elif filters['statoTarga'] == 'Restituita':
            targhe = targhe.filter(ha_restituita=True)
        elif filters['statoTarga'] == 'Non Assegnata':
            targhe = targhe.filter(ha_attiva=False, ha_restituita=False)

    if sort_param not in ['numero', 'dataEm']:
        sort_param = 'numero'
    if dir_param not in ['asc', 'desc']:
        dir_param = 'asc'

    targhe = targhe.order_by(f"-{sort_param}" if dir_param == 'desc' else sort_param)

    return render(request, 'targa.html', {
        'targhe': targhe,
        'sort': sort_param,
        'dir': dir_param,
        'get': request.GET,
        'current_filters': filters,
        'pagina_attiva': 'targa',
        'show_sidebar': True,
    })
def gestioneVeicoli(request):
    # Eliminazione veicolo via POST
    if request.method == 'POST' and request.POST.get('table') == 'veicolo' and request.POST.get('id'):
        try:
            telaio = request.POST['id']
            Attiva.objects.filter(veicoloTelaio__telaio=telaio).delete()
            Restituita.objects.filter(veicoloTelaio__telaio=telaio).delete()
            Veicolo.objects.get(telaio=telaio).delete()
            messages.success(request, "Veicolo eliminato con successo.")
        except Exception as e:
            messages.error(request, f"Errore durante l'eliminazione: {e}")
        return redirect('gestione_veicoli')

    # Gestione filtri
    if 'clear_filters' in request.GET:
        request.session.pop('filters_veicoli', None)
        return redirect('gestione_veicoli')

    current_params = request.GET.dict()
    filters = {k: v for k, v in current_params.items() if k not in ['sort', 'dir', 'clear_filters'] and v}
    sort_param = request.GET.get('sort', 'telaio')
    dir_param = request.GET.get('dir', 'asc')

    if filters:
        request.session['filters_veicoli'] = filters
    elif 'filters_veicoli' in request.session and not any(k in current_params for k in ['sort', 'dir']):
        saved_filters = request.session['filters_veicoli']
        return redirect(f"{reverse('gestione_veicoli')}?{'&'.join([f'{k}={v}' for k,v in saved_filters.items()])}")
    elif 'filters_veicoli' in request.session:
        filters = request.session['filters_veicoli']

    queryset = Veicolo.objects.all()
    if 'telaio' in filters:
        queryset = queryset.filter(telaio__icontains=filters['telaio'])
    if 'marca' in filters:
        queryset = queryset.filter(marca__icontains=filters['marca'])
    if 'modello' in filters:
        queryset = queryset.filter(modello__icontains=filters['modello'])

    if sort_param not in ['telaio', 'marca', 'modello', 'data_produzione']:
        sort_param = 'telaio'
    if dir_param not in ['asc', 'desc']:
        dir_param = 'asc'

    veicoli = queryset.order_by(f"-{sort_param}" if dir_param == 'desc' else sort_param)

    return render(request, 'veicolo.html', {
        'veicoli': veicoli,
        'sort': sort_param,
        'dir': dir_param,
        'get': request.GET,
        'current_filters': filters,
        'pagina_attiva': 'veicolo',
        'show_sidebar': True,
    })
