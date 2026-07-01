from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('services/container-shipment', views.container, name='container'),
    path('services/air-shipment', views.airCargo, name='airCargo'),
    path('services/vehicle-shipment', views.vehicleCargo, name='vehicleCargo'),
    path('pricing/', views.pricing, name='pricing'),
    path('reviews/', views.reviews, name='reviews'),
    path('faq/', views.faq, name='faq'),
    path('get-quote/', views.getQuote, name='getQuote'),
    path('shipment-photos/', views.photoGallery, name='photoGallery'),
    path('video-gallery/', views.videoGallery, name='videoGallery'),
    path('contact/', views.contact, name='contact'),
    path('terms-conditions', views.termsAndCondition, name='termsAndCondition'),
    path('privacy-policy', views.privacyPolicy, name='privacyPolicy'),
    path('track-shipment', views.trackShipment, name='trackShipment'),
    
    path(
        'newsletter/subscribe/',
        views.newsletter_subscribe,
        name='newsletter_subscribe'
    ),

    path(
        'quote/submit/',
        views.quote_submission,
        name='quote_submission'
    ),

    path(
        'track/parcel/',
        views.trackParcel,
        name='trackParcel'
    ),

]
