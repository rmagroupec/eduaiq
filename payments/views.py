from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Invoice, InvoiceItem, FeeCollection, Transaction
from accounts.models import User
import json
import uuid

@login_required
def invoices_api(request):
    """API for listing and creating Invoices"""
    if request.method == 'GET':
        invoices = Invoice.objects.select_related('institution', 'student').prefetch_related('items')
        data = []
        for inv in invoices:
            data.append({
                'id': inv.id,
                'invoice_number': inv.invoice_number,
                'invoice_type': inv.get_invoice_type_display(),
                'status': inv.status,
                'status_display': inv.get_status_display(),
                'institution_name': inv.institution.name if inv.institution else 'N/A',
                'student_name': inv.student.get_full_name() if inv.student else 'N/A',
                'subtotal': float(inv.subtotal),
                'tax_amount': float(inv.tax_amount),
                'discount_amount': float(inv.discount_amount),
                'total_amount': float(inv.total_amount),
                'amount_paid': float(inv.amount_paid),
                'due_date': inv.due_date.strftime('%Y-%m-%d') if inv.due_date else None,
                'created_at': inv.created_at.strftime('%Y-%m-%d'),
            })
        return JsonResponse({'status': 'success', 'data': data})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            invoice_type = data.get('invoice_type', 'student_fee')
            student_id = data.get('student_id')
            institution_id = data.get('institution_id')
            due_date = data.get('due_date')
            notes = data.get('notes', '')
            items = data.get('items', [])
            
            subtotal = 0
            for item in items:
                subtotal += float(item.get('unit_price', 0)) * int(item.get('quantity', 1))
            
            tax_amount = float(data.get('tax_amount', 0.00))
            discount_amount = float(data.get('discount_amount', 0.00))
            total_amount = max(0, subtotal + tax_amount - discount_amount)

            inv_no = f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            invoice = Invoice.objects.create(
                invoice_number=inv_no,
                invoice_type=invoice_type,
                student_id=student_id,
                institution_id=institution_id,
                subtotal=subtotal,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                due_date=due_date,
                notes=notes,
                status='issued'
            )

            for item in items:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=item.get('description', 'Fee Item'),
                    unit_price=item.get('unit_price', 0),
                    quantity=item.get('quantity', 1)
                )

            return JsonResponse({'status': 'success', 'message': 'Invoice created successfully.', 'invoice_number': inv_no, 'id': invoice.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def fee_collections_api(request):
    """API for listing and collecting student fees"""
    if request.method == 'GET':
        collections = FeeCollection.objects.select_related('student', 'institution', 'invoice', 'collected_by').order_by('-id')
        data = []
        for fc in collections:
            s_name = fc.student_name or (fc.student.get_full_name() if fc.student else 'N/A')
            data.append({
                'id': fc.id,
                'student_name': s_name,
                'admission_no': fc.admission_no or 'N/A',
                'class_name': fc.class_name or 'N/A',
                'total_amount': float(fc.total_amount),
                'amount_collected': float(fc.amount_collected),
                'due_amount': float(fc.total_amount - fc.amount_collected) if fc.total_amount > fc.amount_collected else 0.0,
                'payment_method': fc.payment_method,
                'created_at': fc.created_at.strftime('%Y-%m-%d'),
            })
        return JsonResponse({'status': 'success', 'data': data})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            student_name = data.get('student_name')
            admission_no = data.get('admission_no', '')
            class_name = data.get('class_name', '')
            amount = data.get('amount_paid') or data.get('amount') or 0
            payment_mode = data.get('payment_mode') or data.get('payment_method') or 'Cash'
            date_str = data.get('collection_date')
            remarks = data.get('remarks', '')

            student = None
            student_id = data.get('student_id')
            if student_id:
                student = User.objects.filter(id=student_id).first()

            fee = FeeCollection.objects.create(
                student=student,
                student_name=student_name,
                admission_no=admission_no,
                class_name=class_name,
                total_amount=float(data.get('total_amount', amount)),
                amount_collected=float(amount),
                payment_method=payment_mode,
                remarks=remarks,
                collected_by=request.user
            )

            return JsonResponse({'status': 'success', 'message': f'Fee of ₹{amount} collected successfully.', 'id': fee.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def transactions_api(request):
    """API for listing and creating Transaction records"""
    if request.method == 'GET':
        transactions = Transaction.objects.all().order_by('-id')
        data = []
        for txn in transactions:
            data.append({
                'id': txn.id,
                'invoice_no': txn.invoice_no or f"INV-{txn.id}",
                'transaction_type': txn.transaction_type,
                'payment_type': txn.payment_type,
                'amount': float(txn.amount),
                'status': txn.status,
                'created_at': txn.created_at.strftime('%Y-%m-%d'),
            })
        return JsonResponse({'status': 'success', 'data': data})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            invoice_no = data.get('invoice_no') or f"INV-{uuid.uuid4().hex[:6].upper()}"
            transaction_type = data.get('transaction_type', 'General')
            payment_type = data.get('payment_type', 'Cash')
            amount = float(data.get('amount', 0))

            txn = Transaction.objects.create(
                invoice_no=invoice_no,
                transaction_type=transaction_type,
                payment_type=payment_type,
                amount=amount,
                payer=request.user if request.user.is_authenticated else None,
                source_type='general',
                status='success'
            )

            return JsonResponse({'status': 'success', 'message': f'Transaction ₹{amount} recorded successfully.', 'id': txn.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

