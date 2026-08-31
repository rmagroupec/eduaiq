from django.urls import path
from . import views

urlpatterns = [
    path('api/invoices/', views.invoices_api, name='invoices_api'),
    path('api/fee-collections/', views.fee_collections_api, name='fee_collections_api'),
    path('api/transactions/', views.transactions_api, name='transactions_api'),
path(
    'api/payment/create-order/',
    views.create_razorpay_order,
    name='create_razorpay_order'
),
  path('test-payment/', views.test_payment_page, name='test_payment'),

    path('api/payment/create-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('invoice/<str:item_type>/<int:item_id>/', views.invoice_view, name='invoice_view'),
    path('api/invoice/<str:item_type>/<int:item_id>/', views.invoice_details_api, name='invoice_details_api'),

    
]

