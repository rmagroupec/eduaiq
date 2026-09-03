import os
import re

file_path = r"e:\11-08-2026 backup proje\eduaiq_backup_2026_08_11\frontend\templates\course-detail.html"

with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# Replace from `function openPaymentModal(course) {` to `let currentOrderData = null;`
new_logic = """
  function openPaymentModal(course) {
    currentCourseDetails = course;
    // Show a quick loading spinner while fetching Razorpay order
    const loadingHTML = `
      <div id="paymentGatewayModal" style="position:fixed; inset:0; background:rgba(15,23,42,0.85); z-index:1055; display:flex; justify-content:center; align-items:center; backdrop-filter: blur(8px);">
        <div style="background:#ffffff; padding:30px 40px; border-radius:16px; text-align:center; box-shadow: 0 20px 40px rgba(0,0,0,0.4);">
          <div class="spinner-border mb-3" style="width:3rem; height:3rem; color:#ea580c;" role="status"></div>
          <h5 class="fw-bold text-dark mb-1">Initializing Secure Checkout...</h5>
          <p class="text-muted text-sm mb-0">Please wait while we connect to Razorpay.</p>
        </div>
      </div>
    `;
    let existingModal = document.getElementById('paymentGatewayModal');
    if (existingModal) existingModal.remove();
    document.body.insertAdjacentHTML('beforeend', loadingHTML);

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
        closePaymentModal();
        if (data.status === 'success') {
            openRazorpayModal(currentCourseDetails, data);
        } else {
            alert('Failed to initialize payment: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(err => {
        closePaymentModal();
        console.error(err);
        alert('Payment initialization failed. Please try again.');
    });
  }

  function closePaymentModal() {
    const modal = document.getElementById('paymentGatewayModal');
    if (modal) modal.remove();
  }

  function closeRazorpayModal() {
    const modal1 = document.getElementById('razorpayTestModal');
    if (modal1) modal1.remove();
    const modal2 = document.getElementById('pay-modal-overlay');
    if (modal2) modal2.remove();
    document.body.style.overflow = 'auto';
  }

  let currentOrderData = null;
"""

# We'll use regex to replace the block
start_marker = "function openPaymentModal(course) {"
end_marker = "let currentOrderData = null;"

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    end_idx += len(end_marker)
    new_html = html[:start_idx] + new_logic + html[end_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_html)
    print("Successfully replaced openPaymentModal with direct custom modal logic!")
else:
    print("Error: Could not find markers.")
