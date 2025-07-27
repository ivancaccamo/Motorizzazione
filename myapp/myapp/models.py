from django.db import models

# ========================== VEICOLO ==========================

class Veicolo(models.Model):
    # Identificatore primario (17 caratteri)
    telaio = models.CharField(max_length=17, primary_key=True)

    # Marca e modello del veicolo
    marca = models.CharField(max_length=50)
    modello = models.CharField(max_length=50)

    # Data di produzione
    data_produzione = models.DateField()

    class Meta:
        verbose_name = "Veicolo"
        verbose_name_plural = "Veicoli"

    def __str__(self):
        return f"{self.marca} {self.modello} ({self.telaio})"


# ========================== TARGA ==========================

class Targa(models.Model):
    # Identificativo univoco della targa
    numero = models.CharField(max_length=10, primary_key=True)

    # Data di emissione della targa (opzionale)
    dataEm = models.DateField(
        verbose_name="Data di emissione",
        null=True,
        blank=True,
        db_column="data_emissione",
        help_text="Data in cui la targa è stata rilasciata"
    )

    class Meta:
        verbose_name = "Targa"
        verbose_name_plural = "Targhe"

    def __str__(self):
        return self.numero


# ========================== TARGA ATTIVA ==========================

class Attiva(models.Model):
    # Relazione tra targa e veicolo (targa attualmente assegnata)
    targaNumero = models.ForeignKey('Targa', on_delete=models.CASCADE, to_field='numero')
    veicoloTelaio = models.ForeignKey('Veicolo', on_delete=models.CASCADE, to_field='telaio')

    class Meta:
        unique_together = ('targaNumero', 'veicoloTelaio')
        db_table = 'Attiva'
        verbose_name = "Attiva"
        verbose_name_plural = "Attive"

    def __str__(self):
        return f'{self.targaNumero.numero} – {self.veicoloTelaio.telaio}'


# ========================== TARGA RESTITUITA ==========================

class Restituita(models.Model):
    # Relazione tra targa e veicolo (targa restituita)
    targaNumero = models.ForeignKey('Targa', on_delete=models.CASCADE, to_field='numero')
    data_restituzione = models.DateField()
    veicoloTelaio = models.ForeignKey('Veicolo', on_delete=models.CASCADE, to_field='telaio')

    class Meta:
        unique_together = ('targaNumero', 'veicoloTelaio')
        db_table = 'Restituita'
        verbose_name = "Restituita"
        verbose_name_plural = "Restituite"

    def __str__(self):
        return f'{self.targaNumero.numero} – {self.veicoloTelaio.telaio}'


# ========================== REVISIONE ==========================

class Revisione(models.Model):
    # ID auto-incrementale
    numero = models.AutoField(primary_key=True)

    # Collegamento alla targa
    targaNumero = models.ForeignKey(Targa, on_delete=models.CASCADE)

    # Data della revisione
    dataRev = models.DateField()

    # Esito con valori predefiniti
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

    # Motivazione solo se non superata
    motivazione = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Revisione"
        verbose_name_plural = "Revisioni"

    def __str__(self):
        return f"Rev. {self.numero} – {self.targaNumero.numero}"
