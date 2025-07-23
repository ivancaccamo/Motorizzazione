from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages
from .models import Revisione, Targa, Veicolo, Attiva  # Aggiunti per create()

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

def gestione_revisioni(request):
    if request.method == 'POST':
        table = request.POST.get('table')
        id_rev = request.POST.get('id')

        if table != 'revisione':
            messages.error(request, 'Tipo di tabella non valido.')
            return redirect('gestione_revisioni')

        try:
            Revisione.objects.get(numero=id_rev).delete()
            messages.success(request, 'Revisione eliminata con successo.')
        except Revisione.DoesNotExist:
            messages.error(request, 'Revisione non trovata.')
        except Exception as e:
            messages.error(request, f'Errore durante l\'eliminazione: {str(e)}')

        return redirect('gestione_revisioni')

    filters = {}
    if 'id_revisione' in request.GET and request.GET['id_revisione']:
        filters['numero'] = request.GET['id_revisione']
    if 'dataRev' in request.GET and request.GET['dataRev']:
        filters['dataRev'] = request.GET['dataRev']
    if 'stato' in request.GET:
        if request.GET['stato'] == 'superata':
            filters['esito'] = 'Superata'
        elif request.GET['stato'] == 'non_superata':
            filters['esito'] = 'Non superata'

    valid_columns = ['numero', 'targaNumero', 'dataRev']
    order_by = request.GET.get('sort', 'numero')
    order_dir = request.GET.get('dir', 'asc')
    if order_by not in valid_columns:
        order_by = 'numero'
    if order_dir == 'desc':
        order_by = '-' + order_by

    revisioni = Revisione.objects.filter(**filters).order_by(order_by)

    return render(request, 'revisione.html', {
        'revisioni': revisioni,
        'sort': request.GET.get('sort', ''),
        'dir': request.GET.get('dir', ''),
    })


# ---------------------------- CREATE GENERICO ----------------------------

def create(request):
    table = request.GET.get('table')

    if request.method == 'POST':
        if table == 'veicolo':
            telaio = ''.join(request.POST.getlist('telaio')).upper()
            marca = request.POST.get('marca')
            modello = request.POST.get('modello')
            data = request.POST.get('dataProd')

            if len(telaio) != 17:
                messages.error(request, "Il numero di telaio deve essere di 17 caratteri.")
            elif Veicolo.objects.filter(telaio=telaio).exists():
                messages.error(request, "Esiste già un veicolo con questo telaio.")
            else:
                Veicolo.objects.create(telaio=telaio, marca=marca, modello=modello, data_produzione=data)
                messages.success(request, "Veicolo aggiunto con successo.")
                return redirect('gestione_revisioni')

        elif table == 'targa':
            numero = ''.join(request.POST.getlist('targa')).upper()
            data_em = request.POST.get('dataEm')
            telaio = request.POST.get('veicolo_telaio')

            if Targa.objects.filter(numero=numero).exists():
                messages.error(request, "Targa già esistente.")
            else:
                try:
                    Targa.objects.create(numero=numero, dataEm=data_em)
                    Attiva.objects.create(targa_id=numero, veicolo_id=telaio)
                    messages.success(request, "Targa aggiunta con successo.")
                    return redirect('gestione_revisioni')
                except Exception as e:
                    messages.error(request, f"Errore: {e}")

        elif table == 'revisione':
            targa_numero = request.POST.get('numero_targa')
            data_rev = request.POST.get('dataRev')
            esito = request.POST.get('esito')
            motivazione = request.POST.get('motivazione') if esito == 'Non superata' else ''

            Revisione.objects.create(
                targaNumero_id=targa_numero,
                dataRev=data_rev,
                esito=esito,
                motivazione=motivazione
            )
            messages.success(request, "Revisione aggiunta con successo.")
            return redirect('gestione_revisioni')

    context = {
        'table': table,
        'veicoli': Veicolo.objects.exclude(telaio__in=Attiva.objects.values_list('veicolo_id', flat=True)),
        'targhe': Targa.objects.all(),
    }

    return render(request, 'create.html', context)
