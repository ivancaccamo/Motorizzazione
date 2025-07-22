# app/models.py

from django.db import models

class Veicolo(models.Model):
    telaio = models.CharField(max_length=17, primary_key=True)
    marca = models.CharField(max_length=50)
    modello = models.CharField(max_length=50)
    data_produzione = models.DateField()

    class Meta:
        verbose_name = "Veicolo"
        verbose_name_plural = "Veicoli"

    def __str__(self):
        return f"{self.marca} {self.modello} ({self.telaio})"


class Attiva(models.Model):
    targa = models.ForeignKey('Targa', on_delete=models.CASCADE, to_field='numero')
    veicolo = models.ForeignKey('Veicolo', on_delete=models.CASCADE, to_field='telaio')

    class Meta:
        unique_together = ('targa', 'veicolo')
        db_table = 'Attiva'  # per mantenere il nome della tabella se necessario

    def __str__(self):
        return f'{self.targa.numero} - {self.veicolo.telaio}'
    
class Restituita(models.Model):
    targa = models.ForeignKey('Targa', on_delete=models.CASCADE, to_field='numero')
    data_restituzione = models.DateField()
    veicolo = models.ForeignKey('Veicolo', on_delete=models.CASCADE, to_field='telaio')

    class Meta:
        unique_together = ('targa', 'veicolo')
        db_table = 'Restituita'

    def __str__(self):
        return f'{self.targa.numero} restituita il {self.data_restituzione}'



class Revisione(models.Model):
    numero = models.AutoField(primary_key=True)
    targaNumero = models.ForeignKey(Targa, on_delete=models.CASCADE)
    dataRev = models.DateField()
    esito = models.CharField(
        max_length=20,
        choices=[
            ('', 'In attesa di esito'),
            ('Superata', 'Superata'),
            ('Non superata', 'Non superata'),
        ],
        blank=True,
        default=''
    )