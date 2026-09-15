import re
import os

target_file = r"e:\11-08-2026 backup proje\eduaiq_backup_2026_08_11\frontend\templates\course-detail.html"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Replace processCoursePayment and all subsequent dummy Razorpay logic
# until async function goToQuizForLesson(lessonId) {
# We will inject the full Razorpay flow here.

custom_razorpay_logic = """
  function processCoursePayment(slug) {
    closePaymentModal();
    // Fetch order ID from backend
    fetch('/payments/api/payment/create-order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || ''
        },
        body: JSON.stringify({ amount: currentCourseDetails.price })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            openRazorpayModal(currentCourseDetails, data);
        } else {
            alert('Failed to initialize payment: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(err => {
        console.error(err);
        alert('Payment initialization failed. Please try again.');
    });
  }

  let currentOrderData = null;

  function openRazorpayModal(course, orderData) {
    const title = course.title || 'Course Access';
    const price = course.price || '0.00';
    const slug = course.slug || '';
    currentOrderData = orderData;
    
    // Setup Custom Payment Modal (copied from Olympiad)
    const razorpayHTML = `
      <div id="pay-modal-overlay" class="show" style="display:flex; position:fixed; inset:0; background:rgba(15,23,42,0.75); backdrop-filter:blur(6px); z-index:10000; align-items:center; justify-content:center; padding:16px;">
        <div id="pay-modal-box" style="background:#ffffff; border-radius:24px; width:100%; max-width:440px; box-shadow:0 32px 80px rgba(0,0,0,0.3); overflow:hidden;">
          
          <div class="pay-modal-header" style="display:flex; align-items:center; justify-content:space-between; padding:20px 24px 16px; border-bottom:1px solid #f1f5f9;">
            <div class="pay-modal-logo" style="display:flex; align-items:center; gap:10px; font-weight:800; color:#0f172a; font-size:1rem;">
              <span style="background:linear-gradient(135deg, #fd7e14 0%, #ea580c 100%); color:#fff; width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:8px;">E</span>
              EduAiQ Secure Pay
            </div>
            <button id="pay-modal-close" onclick="closeRazorpayModal()" style="background:#f1f5f9; border:none; border-radius:50%; width:32px; height:32px; cursor:pointer; font-size:14px; color:#64748b; display:flex; align-items:center; justify-content:center;">X</button>
          </div>

          <div class="pay-order-summary" style="background:linear-gradient(135deg, #fff7ed, #ffedd5); padding:14px 24px; border-bottom:1px solid #fed7aa;">
            <div class="pay-order-row" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <span class="pay-order-label" style="font-size:0.82rem; color:#92400e; font-weight:600;">Course</span>
              <span class="pay-order-value" style="font-size:0.9rem; color:#431407; font-weight:700;">${title}</span>
            </div>
            <div class="pay-order-divider" style="height:1px; background:#fed7aa; margin:8px 0;"></div>
            <div class="pay-order-row" style="display:flex; justify-content:space-between; align-items:center;">
              <span class="pay-order-label" style="font-size:0.82rem; color:#92400e; font-weight:600;">Total Payable</span>
              <span class="pay-order-fee" style="font-size:1.4rem; font-weight:900; color:#ea580c;">₹${price}</span>
            </div>
          </div>

          <div class="pay-tabs" style="display:flex; padding:16px 24px 0; gap:10px; border-bottom:1px solid #f1f5f9;">
            <button class="pay-tab-btn active" data-tab="upi" style="flex:1; display:flex; align-items:center; justify-content:center; gap:7px; padding:10px; background:#fff7ed; border:2px solid #fd7e14; border-bottom-color:#fff7ed; border-radius:12px; font-weight:700; font-size:0.9rem; color:#c2410c; cursor:pointer; margin-bottom:-1px;">
              UPI
            </button>
            <button class="pay-tab-btn" data-tab="card" style="flex:1; display:flex; align-items:center; justify-content:center; gap:7px; padding:10px; background:#f8fafc; border:2px solid #e2e8f0; border-radius:12px; font-weight:700; font-size:0.9rem; color:#64748b; cursor:pointer; margin-bottom:-1px;">
              Card
            </button>
          </div>

          <!-- UPI Tab -->
          <div class="pay-tab-content active" id="tab-upi" style="display:block; padding:20px 24px 4px;">
            <label style="display:block; font-size:0.8rem; font-weight:700; color:#475569; margin-bottom:7px; text-transform:uppercase;">Enter your UPI ID</label>
            <input type="text" id="upi-id-input" placeholder="yourname@upi (e.g. success@razorpay)" style="width:100%; border:2px solid #e2e8f0; border-radius:12px; padding:12px 14px; font-size:0.95rem; font-weight:600; color:#1e293b; outline:none; transition:border-color 0.2s;" autocomplete="off" spellcheck="false"/>
            <p style="font-size:0.75rem; color:#64748b; margin-top:10px; background:#f8fafc; padding:8px 12px; border-radius:8px; border:1px dashed #cbd5e1;">🧪 <strong>Test Mode:</strong> Use <code>success@razorpay</code></p>
          </div>

          <!-- Card Tab -->
          <div class="pay-tab-content" id="tab-card" style="display:none; padding:20px 24px 4px;">
            <label style="display:block; font-size:0.8rem; font-weight:700; color:#475569; margin-bottom:7px; text-transform:uppercase;">Card Number</label>
            <input type="text" id="card-number" placeholder="4111 1111 1111 1111" maxlength="19" autocomplete="cc-number" style="width:100%; border:2px solid #e2e8f0; border-radius:12px; padding:12px 14px; font-size:0.95rem; font-weight:600; color:#1e293b; outline:none; transition:border-color 0.2s; margin-bottom:12px;"/>
            
            <div style="display:flex; gap:12px; margin-bottom:12px;">
              <div style="flex:1;">
                <label style="display:block; font-size:0.8rem; font-weight:700; color:#475569; margin-bottom:7px; text-transform:uppercase;">Expiry (MM/YY)</label>
                <input type="text" id="card-expiry" placeholder="MM / YY" maxlength="5" autocomplete="cc-exp" style="width:100%; border:2px solid #e2e8f0; border-radius:12px; padding:12px 14px; font-size:0.95rem; font-weight:600; color:#1e293b; outline:none; transition:border-color 0.2s;"/>
              </div>
              <div style="flex:1;">
                <label style="display:block; font-size:0.8rem; font-weight:700; color:#475569; margin-bottom:7px; text-transform:uppercase;">CVV</label>
                <input type="password" id="card-cvv" placeholder="• • •" maxlength="4" autocomplete="cc-csc" style="width:100%; border:2px solid #e2e8f0; border-radius:12px; padding:12px 14px; font-size:0.95rem; font-weight:600; color:#1e293b; outline:none; transition:border-color 0.2s;"/>
              </div>
            </div>
            
            <label style="display:block; font-size:0.8rem; font-weight:700; color:#475569; margin-bottom:7px; text-transform:uppercase;">Cardholder Name</label>
            <input type="text" id="card-name" placeholder="Name on card" autocomplete="cc-name" style="width:100%; border:2px solid #e2e8f0; border-radius:12px; padding:12px 14px; font-size:0.95rem; font-weight:600; color:#1e293b; outline:none; transition:border-color 0.2s; margin-bottom:12px;"/>
            <p style="font-size:0.75rem; color:#64748b; margin-top:0; background:#f8fafc; padding:8px 12px; border-radius:8px; border:1px dashed #cbd5e1;">🧪 <strong>Test card:</strong> <code>4111 1111 1111 1111</code> | Exp: <code>12/28</code> | CVV: <code>123</code></p>
          </div>

          <div id="pay-modal-error" style="display:none; margin:0 24px 16px; padding:10px 14px; background:#fef2f2; border-left:4px solid #ef4444; color:#991b1b; font-size:0.85rem; font-weight:600; border-radius:0 8px 8px 0;"></div>

          <div style="padding:0 24px 24px;">
            <button id="pay-now-btn" style="width:100%; background:linear-gradient(135deg, #fd7e14 0%, #ea580c 100%); color:#fff; border:none; padding:14px; border-radius:12px; font-size:1rem; font-weight:800; cursor:pointer; box-shadow:0 8px 20px rgba(234,88,12,0.3); transition:transform 0.2s, box-shadow 0.2s;">
              Pay Securely Now
            </button>
            <div style="text-align:center; font-size:0.75rem; color:#94a3b8; margin-top:12px;">
              Secured by <strong>Razorpay</strong> · 256-bit SSL Encrypted
            </div>
          </div>

        </div>
      </div>
    `;

    let existing = document.getElementById('razorpayTestModal');
    if (existing) existing.remove();

    document.body.insertAdjacentHTML('beforeend', razorpayHTML);
    document.body.style.overflow = 'hidden';

    // Card number formatting
    const cNum = document.getElementById('card-number');
    if(cNum) {
        cNum.addEventListener('input', function() {
            let v = this.value.replace(/\D/g, '').substring(0, 16);
            this.value = v.replace(/(.{4})/g, '$1 ').trim();
        });
    }
    // Expiry formatting
    const cExp = document.getElementById('card-expiry');
    if(cExp) {
        cExp.addEventListener('input', function() {
            let v = this.value.replace(/\D/g, '').substring(0, 4);
            if (v.length >= 2) v = v.substring(0,2) + '/' + v.substring(2);
            this.value = v;
        });
    }
    // CVV formatting
    const cCvv = document.getElementById('card-cvv');
    if(cCvv) {
        cCvv.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '').substring(0, 4);
        });
    }

    // Tabs logic
    document.querySelectorAll('.pay-tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.pay-tab-btn').forEach(b => {
                b.classList.remove('active');
                b.style.background = '#f8fafc';
                b.style.borderColor = '#e2e8f0';
                b.style.color = '#64748b';
            });
            this.classList.add('active');
            this.style.background = '#fff7ed';
            this.style.borderColor = '#fd7e14';
            this.style.color = '#c2410c';

            const targetId = 'tab-' + this.dataset.tab;
            document.querySelectorAll('#pay-modal-box .pay-tab-content').forEach(c => c.style.display = 'none');
            const target = document.getElementById(targetId);
            if(target) target.style.display = 'block';
        });
    });

    // Submit logic
    document.getElementById('pay-now-btn').addEventListener('click', function() {
        const activeTab = document.querySelector('.pay-tab-btn.active')?.dataset.tab || 'upi';
        const modalError = document.getElementById('pay-modal-error');
        modalError.style.display = 'none';
        
        let prefill = {
            name: "{{ user.get_full_name }}",
            email: "{{ user.email }}",
            contact: "{{ user.phone }}",
        };
        let method = '';

        if (activeTab === 'upi') {
            const upiId = document.getElementById('upi-id-input').value.trim();
            if (!upiId || !upiId.includes('@')) {
                modalError.textContent = 'Please enter a valid UPI ID (e.g. success@razorpay)';
                modalError.style.display = 'block';
                return;
            }
            prefill.vpa = upiId;
            method = 'upi';
        } else {
            const cardNum = document.getElementById('card-number').value.replace(/\s/g, '');
            const cardExp = document.getElementById('card-expiry').value;
            const cardCvv = document.getElementById('card-cvv').value;
            if (!cardNum || cardNum.length < 16) {
                modalError.textContent = 'Please enter a valid 16-digit card number.';
                modalError.style.display = 'block'; return;
            }
            if (!cardExp || !cardExp.includes('/')) {
                modalError.textContent = 'Please enter card expiry (MM/YY).';
                modalError.style.display = 'block'; return;
            }
            if (!cardCvv || cardCvv.length < 3) {
                modalError.textContent = 'Please enter a valid CVV.';
                modalError.style.display = 'block'; return;
            }
            method = 'card';
        }

        executeRazorpayCheckout(course, currentOrderData, method, prefill);
    });
  }

  function executeRazorpayCheckout(course, orderData, method, prefill) {
      closeRazorpayModal();

      const options = {
          key: "{{ razorpay_key_id }}",
          amount: orderData.amount,
          currency: orderData.currency || 'INR',
          name: 'EduAiQ',
          description: 'Course Access: ' + course.title,
          order_id: orderData.order_id,
          prefill: {
              name: prefill.name,
              email: prefill.email,
              contact: prefill.contact,
              method: method
          },
          theme: { color: '#0284c7' },
          handler: function (response) {
              // 1. Verify Payment
              fetch('/payments/api/payment/verify-signature/', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json',
                      'X-CSRFToken': getCookie('csrftoken') || ''
                  },
                  body: JSON.stringify({
                      razorpay_order_id: response.razorpay_order_id,
                      razorpay_payment_id: response.razorpay_payment_id,
                      razorpay_signature: response.razorpay_signature,
                      amount: orderData.amount / 100,
                      description: 'Course Access: ' + course.title,
                      source_type: 'course_enrollment',
                  })
              })
              .then(res => res.json())
              .then(verifyData => {
                  if (verifyData.status === 'success') {
                      // 2. Actually Enroll in the Course
                      fetch(`/courses/courses/${course.slug}/enroll/`, {
                          method: 'POST',
                          headers: {
                              'Content-Type': 'application/json',
                              'X-CSRFToken': getCookie('csrftoken') || ''
                          },
                          body: JSON.stringify({ amount_paid: orderData.amount / 100 })
                      })
                      .then(r => r.json())
                      .then(enrollData => {
                          if (enrollData.success) {
                              showPaymentSuccessModal(response.razorpay_payment_id, orderData.amount / 100, course.title);
                          } else {
                              alert('Payment verified, but enrollment failed: ' + (enrollData.error || 'Unknown error. Contact support.'));
                          }
                      });
                  } else {
                      alert('Payment verification failed: ' + verifyData.message);
                  }
              })
              .catch(err => {
                  console.error(err);
                  alert('Error verifying payment.');
              });
          }
      };

      if (method === 'upi' && prefill.vpa) {
          options.prefill.vpa = prefill.vpa;
      }

      const rzp = new Razorpay(options);
      rzp.on('payment.failed', function (response) {
          alert('Payment Failed: ' + response.error.description);
      });
      rzp.open();
  }

"""

start_str = "function processCoursePayment(slug) {"
end_str = "async function goToQuizForLesson(lessonId) {"

start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + custom_razorpay_logic + content[end_idx:]
    
    # Also inject checkout.js if not present
    if "checkout.razorpay.com/v1/checkout.js" not in new_content:
        new_content = new_content.replace("{% endblock %}", "<script src=\"https://checkout.razorpay.com/v1/checkout.js\"></script>\n{% endblock %}")
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully updated Razorpay logic!")
else:
    print("Error: Could not find start or end strings for replacement.")
