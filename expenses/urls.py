from django.urls import path
from . import views

urlpatterns = [
    path('api/heads/', views.expense_heads_api, name='expense_heads_api'),
    path('api/expenses/', views.expenses_api, name='expenses_api'),
    path('api/expenses/<int:expense_id>/approve/', views.approve_expense_api, name='approve_expense_api'),
]
