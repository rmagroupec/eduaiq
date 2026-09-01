from django.conf import settings
import razorpay
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone
from .models import Invoice, InvoiceItem, FeeCollection, Transaction
from accounts.models import User
import json
import uuid
import hmac
import hashlib
import random
import string

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


def get_invoice_data_dict(item_type, item_id):
    """Internal helper to build invoice payload for fees, transactions, or invoices"""
    invoice_data = {}

    if item_type == 'fee':
        fee = FeeCollection.objects.filter(id=item_id).first()
        if fee:
            due = max(0.0, float(fee.total_amount - fee.amount_collected))
            status = 'Paid' if due <= 0 else ('Partial' if fee.amount_collected > 0 else 'Unpaid')
            status_class = 'success' if status == 'Paid' else ('warning' if status == 'Partial' else 'danger')

            s_name = fee.student_name or (fee.student.get_full_name() if fee.student else 'Student')
            invoice_data = {
                'invoice_no': f"INV-FEE-{fee.id:05d}",
                'receipt_no': f"REC-{fee.id:05d}",
                'date': fee.created_at.strftime('%d %b %Y'),
                'due_date': fee.created_at.strftime('%d %b %Y'),
                'type': 'Student Fee Collection Receipt',
                'status': status,
                'status_class': status_class,
                'customer_name': s_name,
                'customer_subtext': f"Admission No: {fee.admission_no or 'N/A'} | Class: {fee.class_name or 'N/A'}",
                'customer_email': fee.student.email if fee.student else 'N/A',
                'customer_phone': getattr(fee.student, 'phone', 'N/A') if fee.student else 'N/A',
                'payment_method': fee.payment_method.upper(),
                'reference_no': fee.reference_number or f"REF-FEE-{fee.id}",
                'items': [
                    {
                        'description': f"Academic & Tuition Fee ({fee.class_name or 'Current Term'})",
                        'qty': 1,
                        'rate': float(fee.total_amount),
                        'amount': float(fee.total_amount)
                    }
                ],
                'subtotal': float(fee.total_amount),
                'tax_amount': 0.00,
                'discount_amount': 0.00,
                'total_amount': float(fee.total_amount),
                'amount_paid': float(fee.amount_collected),
                'balance_due': due,
                'remarks': fee.remarks or "Fee collection successfully recorded in system.",
                'collector': fee.collected_by.get_full_name() if fee.collected_by else 'Finance Department'
            }
    elif item_type == 'trx':
        txn = Transaction.objects.filter(id=item_id).first()
        if txn:
            invoice_data = {
                'invoice_no': txn.invoice_no or f"INV-TRX-{txn.id:05d}",
                'receipt_no': f"REC-TRX-{txn.id:05d}",
                'date': txn.created_at.strftime('%d %b %Y'),
                'due_date': txn.created_at.strftime('%d %b %Y'),
                'type': f"Transaction Receipt ({txn.transaction_type})",
                'status': txn.status.capitalize(),
                'status_class': 'success' if txn.status == 'success' else 'danger',
                'customer_name': txn.payer.get_full_name() if txn.payer else 'General Payer / Guest',
                'customer_subtext': f"Payer Account: {txn.payer.username if txn.payer else 'N/A'}",
                'customer_email': txn.payer.email if txn.payer else 'N/A',
                'customer_phone': getattr(txn.payer, 'phone', 'N/A') if txn.payer else 'N/A',
                'payment_method': txn.payment_type,
                'reference_no': txn.gateway_txn_id or f"TRX-REF-{txn.id}",
                'items': [
                    {
                        'description': f"Payment for {txn.transaction_type}",
                        'qty': 1,
                        'rate': float(txn.amount),
                        'amount': float(txn.amount)
                    }
                ],
                'subtotal': float(txn.amount),
                'tax_amount': 0.00,
                'discount_amount': 0.00,
                'total_amount': float(txn.amount),
                'amount_paid': float(txn.amount),
                'balance_due': 0.00,
                'remarks': f"Transaction recorded via {txn.payment_type}.",
                'collector': 'Accounts Department'
            }
    elif item_type == 'inv':
        inv = Invoice.objects.filter(id=item_id).first()
        if inv:
            due = max(0.0, float(inv.total_amount - inv.amount_paid))
            items_list = []
            for item in inv.items.all():
                items_list.append({
                    'description': item.description,
                    'qty': item.quantity,
                    'rate': float(item.unit_price),
                    'amount': float(item.total_price)
                })
            if not items_list:
                items_list.append({
                    'description': inv.get_invoice_type_display(),
                    'qty': 1,
                    'rate': float(inv.total_amount),
                    'amount': float(inv.total_amount)
                })

            invoice_data = {
                'invoice_no': inv.invoice_number,
                'receipt_no': f"REC-{inv.id:05d}",
                'date': inv.created_at.strftime('%d %b %Y'),
                'due_date': inv.due_date.strftime('%d %b %Y') if inv.due_date else inv.created_at.strftime('%d %b %Y'),
                'type': inv.get_invoice_type_display(),
                'status': inv.get_status_display(),
                'status_class': 'success' if inv.status == 'paid' else ('warning' if inv.status in ['issued', 'partially_paid'] else 'secondary'),
                'customer_name': inv.student.get_full_name() if inv.student else (inv.institution.name if inv.institution else 'Customer'),
                'customer_subtext': f"Institution: {inv.institution.name if inv.institution else 'EduAiQ Academy'}",
                'customer_email': inv.student.email if inv.student else 'billing@institution.com',
                'customer_phone': getattr(inv.student, 'phone', 'N/A') if inv.student else 'N/A',
                'payment_method': 'Online / Bank Transfer',
                'reference_no': inv.invoice_number,
                'items': items_list,
                'subtotal': float(inv.subtotal),
                'tax_amount': float(inv.tax_amount),
                'discount_amount': float(inv.discount_amount),
                'total_amount': float(inv.total_amount),
                'amount_paid': float(inv.amount_paid),
                'balance_due': due,
                'remarks': inv.notes or "Official billing invoice.",
                'collector': 'Billing & Revenue Operations'
            }

    if not invoice_data:
        invoice_data = {
            'invoice_no': f"INV-{item_type.upper()}-{item_id:05d}",
            'receipt_no': f"REC-{item_id:05d}",
            'date': timezone.now().strftime('%d %b %Y'),
            'due_date': timezone.now().strftime('%d %b %Y'),
            'type': 'Fee & Payment Tax Invoice',
            'status': 'Paid',
            'status_class': 'success',
            'customer_name': 'Kathryn Murphy',
            'customer_subtext': 'Admission No: AD52365 | Class: Class 1 (A)',
            'customer_email': 'kathryn.m@eduaiq.com',
            'customer_phone': '+91 98765 43210',
            'payment_method': 'Cash / Online UPI',
            'reference_no': f"REF-{item_id:05d}",
            'items': [
                {'description': 'Academic Tuition & Course Fee', 'qty': 1, 'rate': 700.50, 'amount': 700.50}
            ],
            'subtotal': 700.50,
            'tax_amount': 0.00,
            'discount_amount': 0.00,
            'total_amount': 700.50,
            'amount_paid': 700.50,
            'balance_due': 0.00,
            'remarks': 'Official computer-generated fee receipt.',
            'collector': 'EduAiQ Finance Office'
        }

    return invoice_data


@login_required
def invoice_view(request, item_type, item_id):
    """View & Print full page Tax Invoice"""
    invoice_data = get_invoice_data_dict(item_type, item_id)
    return render(request, 'admin_panel/invoice.html', {'invoice': invoice_data})


@login_required
def invoice_details_api(request, item_type, item_id):
    """API endpoint returning invoice details as JSON"""
    invoice_data = get_invoice_data_dict(item_type, item_id)
    return JsonResponse({'status': 'success', 'data': invoice_data})

@csrf_exempt
def create_razorpay_order(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Only POST method is allowed.'
        }, status=405)




    try:
        data = json.loads(request.body) if request.body else request.POST

        amount = float(data.get('amount', 0))

        if amount <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid payment amount.'
            }, status=400)

        # Razorpay amount is always in paise
        amount_paise = int(round(amount * 100))

        client = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        order_data = {
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': 1
        }

        order = client.order.create(data=order_data)

        return JsonResponse({
            'status': 'success',
            'order_id': order['id'],
            'amount': amount_paise,
            'currency': 'INR',
            'key_id': settings.RAZORPAY_KEY_ID
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


# ─────────────────────────────────────────────────────────────
#  STEP 2 ─ Verify Razorpay Signature (HMAC-SHA256)
#  Call this AFTER Razorpay handler fires on the frontend
# ─────────────────────────────────────────────────────────────
@csrf_exempt
def verify_payment_signature(request):
    """
    POST body expected:
      {
        "razorpay_order_id": "order_XXXX",
        "razorpay_payment_id": "pay_XXXX",
        "razorpay_signature": "<hex-signature>",
        "amount": 500,                    # optional – for saving Transaction
        "description": "Test Payment",   # optional
        "registration_data": {...}        # optional – olympiad registration fields
      }
    Returns:
      { status: 'success'|'failed', message, payment_id, transaction_id }
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed.'}, status=405)

    try:
        data = json.loads(request.body) if request.body else {}

        order_id   = data.get('razorpay_order_id', '')
        payment_id = data.get('razorpay_payment_id', '')
        signature  = data.get('razorpay_signature', '')

        if not all([order_id, payment_id, signature]):
            return JsonResponse({'status': 'failed', 'message': 'Missing required fields.'}, status=400)

        # ── Razorpay HMAC-SHA256 verification ──
        key    = settings.RAZORPAY_KEY_SECRET.encode('utf-8')
        msg    = f"{order_id}|{payment_id}".encode('utf-8')
        digest = hmac.new(key, msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(digest, signature.lower()):
            return JsonResponse({
                'status': 'failed',
                'message': 'Signature verification failed. Payment may be tampered.'
            }, status=400)

        # ── Signature valid → Save Transaction record ──
        amount      = float(data.get('amount', 0))
        description = data.get('description', 'Razorpay Online Payment')
        source      = data.get('source_type', 'general')
        reference_id= data.get('reference_id', None)
        inv_no      = f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        txn = Transaction.objects.create(
            invoice_no       = inv_no,
            transaction_type = description,
            payment_type     = 'Online / Razorpay',
            source_type      = source,
            reference_id     = reference_id,
            amount           = amount,
            payer            = request.user if (request.user and request.user.is_authenticated) else None,
            gateway_txn_id   = payment_id,
            status           = 'success'
        )

        # ── If olympiad registration data is present, save it ──
        reg_data = data.get('registration_data')
        roll_number = None
        if reg_data:
            try:
                from olympiad.models import OlympiadRegistration, Olympiad
                olympiad_id = reg_data.get('olympiad_id')
                student_name = reg_data.get('student_name', '')
                email = reg_data.get('email', '')
                guardian_phone = reg_data.get('guardian_phone', '')

                # Get or create a guest user account for the student
                guest_user = None
                if email:
                    guest_user = User.objects.filter(email=email).first()
                    if not guest_user:
                        username_base = email.split('@')[0][:20]
                        username = username_base
                        counter = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{username_base}{counter}"
                            counter += 1
                        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                        guest_user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=temp_password,
                            first_name=student_name.split(' ')[0] if student_name else '',
                            last_name=' '.join(student_name.split(' ')[1:]) if student_name else '',
                        )

                # Generate unique roll number
                roll_number = f"OLY-{timezone.now().strftime('%Y')}-{''.join(random.choices(string.digits, k=6))}"
                while OlympiadRegistration.objects.filter(roll_number=roll_number).exists():
                    roll_number = f"OLY-{timezone.now().strftime('%Y')}-{''.join(random.choices(string.digits, k=6))}"

                if olympiad_id and guest_user:
                    olympiad_obj = Olympiad.objects.filter(id=olympiad_id).first()
                    if olympiad_obj:
                        OlympiadRegistration.objects.get_or_create(
                            olympiad=olympiad_obj,
                            student=guest_user,
                            defaults={
                                'roll_number': roll_number,
                                'transaction': txn,
                                'status': 'registered',
                            }
                        )
            except Exception as reg_err:
                # Don't fail the whole payment if registration saving fails
                pass

        return JsonResponse({
            'status'         : 'success',
            'message'        : 'Payment verified and recorded successfully.',
            'payment_id'     : payment_id,
            'order_id'       : order_id,
            'transaction_id' : txn.id,
            'invoice_no'     : inv_no,
            'roll_number'    : roll_number,
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────
#  STEP 3 ─ Fetch Payment Status from Razorpay Gateway
#  Useful for checking pending / failed payments
# ─────────────────────────────────────────────────────────────
def payment_status(request, payment_id):
    """
    GET /payments/api/payment/status/<payment_id>/
    Fetches live payment status from Razorpay.
    Returns:
      { status: 'success'|'failed'|'pending'|'error', payment_status, amount, method, ... }
    """
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment = client.payment.fetch(payment_id)

        rzp_status = payment.get('status', 'unknown')  # captured / failed / created / authorized

        # Map Razorpay status → our simple status
        status_map = {
            'captured'   : 'success',
            'authorized' : 'pending',
            'created'    : 'pending',
            'failed'     : 'failed',
        }
        mapped_status = status_map.get(rzp_status, 'pending')

        return JsonResponse({
            'status'         : mapped_status,
            'razorpay_status': rzp_status,
            'payment_id'     : payment.get('id'),
            'order_id'       : payment.get('order_id'),
            'amount'         : payment.get('amount', 0) / 100,   # paise → rupees
            'currency'       : payment.get('currency'),
            'method'         : payment.get('method'),            # card / upi / netbanking
            'email'          : payment.get('email'),
            'contact'        : payment.get('contact'),
            'description'    : payment.get('description', ''),
            'created_at'     : payment.get('created_at'),
        })

    except razorpay.errors.BadRequestError as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid payment ID: {payment_id}'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def test_payment_page(request):
    """Test page - no login required for easy testing"""
    return render(request, 'payments/test_payment.html', {
        'razorpay_key_id': settings.RAZORPAY_KEY_ID
    })


def payment_success_page(request):
    """
    Payment Success Page — shown after successful Razorpay payment.
    Reads payment details from GET params passed by frontend after verification.
    """
    context = {
        'payment_id'    : request.GET.get('payment_id', ''),
        'order_id'      : request.GET.get('order_id', ''),
        'transaction_id': request.GET.get('transaction_id', ''),
        'invoice_no'    : request.GET.get('invoice_no', ''),
        'amount'        : request.GET.get('amount', ''),
        'method'        : request.GET.get('method', ''),
        'description'   : request.GET.get('description', 'EduAiQ Payment'),
    }
    return render(request, 'payments/payment_success.html', context)