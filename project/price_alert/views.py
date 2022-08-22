from django.shortcuts import render
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="root",
    database="database",
)
mycursor = db.cursor()


def pricealert(request):
    if request.GET.get('email') and request.GET.get('url') is not None:
        mycursor.execute(
            "INSERT INTO price_alert_user_email (email, product_link) VALUES (%s, %s)",
            (request.GET.get('email'), request.GET.get('url')))
        db.commit()
        print("Price alert sign up committed!")

    return render(request, 'price_alert/price_alert.html')
