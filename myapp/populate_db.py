import os
import random
import string
from datetime import datetime, timedelta
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapp.settings") 
django.setup()

from myapp.models import Veicolo, Targa, Attiva, Restituita, Revisione

NUM_VEICOLI = 500
PERCENT_ACTIVE = 80
MAX_ROTATIONS = 2

marche_modelli = {
    'Fiat': ['Panda','500','Tipo','Punto','Bravo'],
    'Ford': ['Fiesta','Focus','Kuga','Mustang','EcoSport'],
    'Volkswagen': ['Golf','Polo','Tiguan','Passat','Up!'],
    'Toyota': ['Corolla','Yaris','RAV4','Prius','Camry'],
    'Renault': ['Clio','Megane','Captur','Kadjar','Talisman'],
    'Opel': ['Corsa','Astra','Mokka','Insignia','Grandland'],
    'Peugeot': ['208','308','3008','2008','508'],
    'BMW': ['Serie 1','Serie 3','Serie 5','X3','X5'],
    'Mercedes': ['Classe A','Classe C','Classe E','GLA','GLE'],
    'Audi': ['A3','A4','Q5','Q7','TT'],
    'Honda': ['Civic','Accord','CR-V','Jazz','HR-V'],
    'Hyundai': ['i10','i20','Tucson','Santa Fe','Kona'],
    'Kia': ['Rio','Ceed','Sportage','Sorento','Stonic'],
    'Nissan': ['Micra','Qashqai','Juke','Leaf','X-Trail'],
    'Chevrolet': ['Spark','Aveo','Cruze','Captiva','Camaro'],
    'Citroen': ['C1','C3','C4','C5','C3 Aircross'],
    'Skoda': ['Fabia','Octavia','Kodiaq','Superb','Kamiq'],
    'Seat': ['Ibiza','Leon','Ateca','Arona','Tarraco'],
    'Mazda': ['2','3','CX-5','MX-5','CX-30'],
    'Subaru': ['Impreza','Forester','Outback','XV','BRZ'],
    'Tesla': ['Model S','Model 3','Model X','Model Y'],
    'Volvo': ['V40','S60','XC60','XC90','V90'],
    'LandRover': ['Discovery','Range Rover','Defender','Evoque'],
    'Jaguar': ['XE','XF','F-Pace','I-Pace'],
    'Mitsubishi': ['ASX','Outlander','L200','Space Star'],
    'Suzuki': ['Swift','Baleno','Vitara','Ignis'],
    'AlfaRomeo': ['Giulietta','Giulia','Stelvio','MiTo'],
    'Lancia': ['Ypsilon','Delta','Kappa','Musa'],
    'Dacia': ['Sandero','Duster','Logan','Lodgy'],
    'Jeep': ['Renegade','Compass','Cherokee','Wrangler'],
}

def random_plate():
    letters = 'ABCDEFGHJKLMNPRSTUVWXYZ'
    return ''.join(random.choices(letters, k=2)) + \
           ''.join(random.choices(string.digits, k=3)) + \
           ''.join(random.choices(letters, k=2))

def random_date(start_year=1950, end_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def random_telaio():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))

storage_targhe = []
active_targhe = []

for _ in range(NUM_VEICOLI):
    telaio = random_telaio()
    marca = random.choice(list(marche_modelli.keys()))
    modello = random.choice(marche_modelli[marca])
    data_prod = random_date()
    veicolo = Veicolo.objects.create(
        telaio=telaio,
        marca=marca,
        modello=modello,
        data_produzione=data_prod
    )

    # Targa “attiva”
    if random.randint(1, 100) <= PERCENT_ACTIVE:
        targa = random_plate()
        data_em = (data_prod + timedelta(days=random.randint(30, 730))).date()
        t = Targa.objects.create(
            numero=targa,
            
            dataEm=data_em
        )
        Attiva.objects.create(targaNumero=t, veicoloTelaio=veicolo)
        storage_targhe.append({'numero': targa, 'dataEm': data_em})
        active_targhe.append({'numero': targa, 'dataEm': data_em})

    # Targhe di rotazione / restituite
    for _ in range(random.randint(0, MAX_ROTATIONS)):
        d_em2 = random_date(data_prod.year, data_prod.year + 5).date()
        d_res2 = d_em2 + timedelta(days=random.randint(30, 1000))
        t2 = random_plate()
        Targa.objects.create(
            numero=t2,
            dataEm=d_em2
        )
        Restituita.objects.create(
            targaNumero_id=t2,
            veicoloTelaio=veicolo,
            data_restituzione=d_res2
        )
        storage_targhe.append({'numero': t2, 'dataEm': d_em2})

# Generazione revisioni per le targhe attive
for rec in active_targhe:
    targa = rec['numero']
    t = Targa.objects.get(numero=targa)
    next_rev = (rec['dataEm'] + timedelta(days=730))
    while next_rev < datetime.now().date():
        esito = 'Superata' if random.randint(1, 100) <= 90 else 'Non superata'
        motivazione = None if esito == 'Superata' else random.choice(
            ['Freni insufficienti', 'Emissioni eccessive', 'Fari difettosi']
        )
        Revisione.objects.create(
            targaNumero=t,
            dataRev=next_rev,
            esito=esito,
            motivazione=motivazione
        )
        next_rev += timedelta(days=int(730 + random.uniform(-60, 60)))

print("✅ Database popolato con successo!")
