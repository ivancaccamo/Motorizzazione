# app/models.py

from django.db import models

class Targa(models.Model):
    numero = models.CharField(max_length=20, primary_key=True)

class Revisione(models.Model):
    numero = models.AutoField(primary_key=True)
    targaNumero = models.ForeignKey(Targa, on_delete=models.CASCADE)
    dataRev = models.DateField()
    esito = models.CharField(max_length=20, choices=[
        ('Superata', 'Superata'),
        ('Non superata', 'Non superata'),
        ('', 'In attesa di esito')
    ], blank=True, default='')
