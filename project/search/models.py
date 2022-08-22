from django.db import models
from datetime import datetime


class amazon(models.Model):
    asin = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    price = models.CharField(max_length=64)
    product_link = models.CharField(max_length=512)
    image_link = models.CharField(max_length=2048)
    rating = models.CharField(max_length=3, default=0)
    datetime = models.DateTimeField(default=datetime.now, blank=True)
    stock = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ebay(models.Model):
    name = models.CharField(max_length=80)
    price = models.CharField(max_length=16)
    product_link = models.CharField(max_length=700)
    image_link = models.CharField(max_length=512)
    datetime = models.DateTimeField(default=datetime.now, blank=True)
    stock = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class newegg(models.Model):
    name = models.CharField(max_length=512)
    price = models.CharField(max_length=16)
    product_link = models.CharField(max_length=2048)
    image_link = models.CharField(max_length=2048)
    datetime = models.DateTimeField(default=datetime.now, blank=True)
    stock = models.BooleanField(default=True)

    def __str__(self):
        return self.name
