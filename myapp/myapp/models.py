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
    

class Targa(models.Model):
    numero = models.CharField(max_length=10, primary_key=True)
    telaio = models.ForeignKey(Veicolo, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Targa"
        verbose_name_plural = "Targhe"

    def __str__(self):
        return self.numero

class Attiva(models.Model):
    targaNumero = models.ForeignKey('Targa', on_delete=models.CASCADE, to_field='numero')
    veicoloTelaio = models.ForeignKey('Veicolo', on_delete=models.CASCADE, to_field='telaio')

    class Meta:
        unique_together = ('targaNumero', 'veicoloTelaio')
        db_table = 'Attiva'  # per mantenere il nome della tabella se necessario
        verbose_name = "Attiva"
        verbose_name_plural = "Attive"

    def __str__(self):
       return f'{self.targaNumero.numero} – {self.veicoloTelaio.telaio}'
    
class Restituita(models.Model):
    targaNumero = models.ForeignKey('Targa', on_delete=models.CASCADE, to_field='numero')
    data_restituzione = models.DateField()
    veicoloTelaio = models.ForeignKey('Veicolo', on_delete=models.CASCADE, to_field='telaio')

    class Meta:
        unique_together = ('targaNumero', 'veicoloTelaio')
        db_table = 'Restituita'
        verbose_name = "Restituita"
        verbose_name_plural = "Restituite"
       

    def __str__(self):
        return f'{self.targaNumero.numero} – {self.veicoloTelaio.telaio} restituita il {self.data_restituzione}'
    
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
    motivazione = models.TextField(blank=True, null=True)  # ✅ AGGIUNTO
    
    class Meta:
        verbose_name = "Revisione"
        verbose_name_plural = "Revisioni"

    def __str__(self):
        # scegli tu cosa far vedere, ad esempio:
        return f"Rev. {self.numero} – {self.targaNumero.numero} del {self.dataRev}"
    