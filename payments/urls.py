from django.urls import path
from . import views

urlpatterns = [
    path('api/invoices/', views.invoices_api, name='invoices_api'),
    path('api/fee-collections/', views.fee_collections_api, name='fee_collections_api'),
    path('api/transactions/', views.transactions_api, name='transactions_api'),
]

