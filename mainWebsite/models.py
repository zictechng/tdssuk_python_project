from django.db import models
from django_countries.fields import CountryField

# Create your models here.

class ContactMessage(models.Model):
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    sender_phone = models.CharField(max_length=30, blank=True)
    sender_subject = models.CharField(max_length=200)
    sender_message = models.TextField()
    status = models.CharField(max_length=30,
        choices=[
        ('pending', 'Pending'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('completed', 'Completed'),
        ('close', 'Closed'),
        ],
    default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"


# newsletter class model
class Newsletter(models.Model):
    subscriber_email = models.EmailField()
    status = models.CharField(
        max_length=30,
        choices=[
            ('pending', 'Pending'),
            ('verify', 'Verified'),
            ('deleted', 'Deleted'),
            ('close', 'Closed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subscriber_email


class AllCountries(models.Model):
    country = CountryField()

# Quote request model

class QuoteRequest(models.Model):

    SERVICE_TYPES = [
        ('sea', 'Sea Shipping'),
        ('air', 'Air Freight'),
        ('vehicle', 'Vehicle Shipment'),
        ('other', 'Other Types'),
    ]

    quote_name = models.CharField(max_length=150)
    quote_email = models.EmailField()
    quote_phone = models.CharField(max_length=30)

    quote_serviceType = models.CharField(
        max_length=30,
        choices=SERVICE_TYPES
    )

    quoteFromCountry = models.CharField(max_length=100)
    quoteToCountry = models.CharField(max_length=100)

    quote_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quote_name} - {self.quote_serviceType}"