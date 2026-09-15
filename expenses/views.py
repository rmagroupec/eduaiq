from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ExpenseHead, Expense
import json

@login_required
def expense_heads_api(request):
    """API for listing and creating Expense Heads"""
    if request.method == 'GET':
        heads = list(ExpenseHead.objects.all().values('id', 'name', 'code', 'description', 'is_active', 'created_at'))
        return JsonResponse({'status': 'success', 'data': heads})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            name = data.get('name')
            code = data.get('code')
            description = data.get('description', '')
            
            if not name or not code:
                return JsonResponse({'status': 'error', 'message': 'Name and Code are required.'}, status=400)
            
            head, created = ExpenseHead.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': description}
            )
            if not created:
                head.name = name
                head.description = description
                head.save()

            return JsonResponse({'status': 'success', 'message': 'Expense Head saved successfully.', 'id': head.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def expenses_api(request):
    """API for listing and adding Expenses"""
    if request.method == 'GET':
        status_filter = request.GET.get('status')
        expenses_qs = Expense.objects.select_related('expense_head', 'requested_by', 'approved_by')
        if status_filter:
            expenses_qs = expenses_qs.filter(status=status_filter)
        
        data = []
        for exp in expenses_qs:
            data.append({
                'id': exp.id,
                'title': exp.title,
                'head_name': exp.expense_head.name,
                'amount': float(exp.amount),
                'expense_date': exp.expense_date.strftime('%Y-%m-%d'),
                'paid_to': exp.paid_to,
                'payment_mode': exp.get_payment_mode_display(),
                'status': exp.status,
                'status_display': exp.get_status_display(),
                'requested_by': exp.requested_by.get_full_name() or exp.requested_by.username,
                'receipt_url': exp.receipt_attachment.url if exp.receipt_attachment else None,
            })
        return JsonResponse({'status': 'success', 'data': data})
    
    elif request.method == 'POST':
        try:
            head_id = request.POST.get('expense_head_id') or request.POST.get('head_id')
            title = request.POST.get('title')
            amount = request.POST.get('amount')
            expense_date = request.POST.get('expense_date') or timezone.now().strftime('%Y-%m-%d')
            paid_to = request.POST.get('paid_to', '')
            payment_mode = request.POST.get('payment_mode', 'cash')
            notes = request.POST.get('notes', '')
            receipt = request.FILES.get('receipt_attachment')

            if not head_id or not title or not amount:
                return JsonResponse({'status': 'error', 'message': 'Expense head, title, and amount are required.'}, status=400)

            head = get_object_or_404(ExpenseHead, id=head_id)
            expense = Expense.objects.create(
                expense_head=head,
                title=title,
                amount=amount,
                expense_date=expense_date,
                paid_to=paid_to,
                payment_mode=payment_mode,
                notes=notes,
                receipt_attachment=receipt,
                requested_by=request.user,
                status='pending'
            )
            return JsonResponse({'status': 'success', 'message': 'Expense recorded successfully and submitted for approval.', 'id': expense.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def approve_expense_api(request, expense_id):
    """Approve or Reject an Expense"""
    if request.method == 'POST':
        expense = get_object_or_404(Expense, id=expense_id)
        data = json.loads(request.body) if request.body else request.POST
        action = data.get('action', 'approve') # 'approve' or 'reject' or 'pay'
        
        if action == 'approve':
            expense.status = 'approved'
            expense.approved_by = request.user
        elif action == 'pay':
            expense.status = 'paid'
            expense.approved_by = request.user
        elif action == 'reject':
            expense.status = 'rejected'
            expense.rejection_reason = data.get('reason', 'Rejected by administrator.')
        
        expense.save()
        return JsonResponse({'status': 'success', 'message': f'Expense status updated to {expense.status}.'})
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
