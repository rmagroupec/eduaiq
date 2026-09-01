from django.urls import path
from . import views

urlpatterns = [
    # --- Invoices, Fee Collections, Transactions ---
    path('api/invoices/', views.invoices_api, name='invoices_api'),
    path('api/fee-collections/', views.fee_collections_api, name='fee_collections_api'),
    path('api/transactions/', views.transactions_api, name='transactions_api'),

    # --- Razorpay Payment APIs ---
    path('api/payment/create-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('api/payment/verify-signature/', views.verify_payment_signature, name='verify_payment_signature'),
    path('api/payment/status/<str:payment_id>/', views.payment_status, name='payment_status'),

    # --- Invoice Views ---
    path('invoice/<str:item_type>/<int:item_id>/', views.invoice_view, name='invoice_view'),
    path('api/invoice/<str:item_type>/<int:item_id>/', views.invoice_details_api, name='invoice_details_api'),

    # --- Test Page ---
    path('test-payment/', views.test_payment_page, name='test_payment'),

    # --- Payment Success Page ---
    path('payment-success/', views.payment_success_page, name='payment_success'),
]
