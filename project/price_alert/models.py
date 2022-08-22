from django.db import models


class user_email(models.Model):
    email = models.CharField(max_length=255)
    product_link = models.CharField(max_length=2083)
    stock = models.BooleanField(default=True)

    def __str__(self):
        return self.email + " , " + self.product_link[-6:]
