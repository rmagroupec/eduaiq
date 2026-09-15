import os
import re

file_path = r"e:\11-08-2026 backup proje\eduaiq_backup_2026_08_11\frontend\templates\product-checkout.html"

with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Replace the feeCategory dropdown and add custom amount field
dropdown_html = """
<div class="form-group">
<label>What Are You Paying For? <abbr class="label-star">*</abbr></label>
<select id="feeCategory" name="fee_category" onchange="updateFeeSummary()">
<option value="franchise" selected>Franchise Application Fee</option>
<option value="institution">Institution Membership Fee</option>
<option value="skill">Skill Development Custom Dues</option>
<option value="other">Other / Custom Dues</option>
</select>
</div>
</div>
<div class="col-sm-12" id="customAmountWrapper" style="display: none;">
<div class="form-group">
<label>Custom Amount (₹) <abbr class="label-star">*</abbr></label>
<input id="customAmount" name="custom_amount" placeholder="Enter amount to pay" type="number" min="1" oninput="updateFeeSummary()"/>
</div>
"""
# Replace the original dropdown block
html = re.sub(
    r'<div class="form-group">\s*<label>What Are You Paying For\?.*?</select>\s*</div>\s*</div>',
    dropdown_html,
    html,
    flags=re.DOTALL
)

# 2. Add an ID to the Notes field for easy retrieval
html = re.sub(
    r'<textarea placeholder="Anything we should know',
    r'<textarea id="checkoutNotes" placeholder="Anything we should know',
    html
)

# 3. Update the Fee Summary to have span ids
fee_summary_html = """
<tr>
<td>Selected category</td>
<td class="text-right" id="summaryCategory">Franchise Application Fee</td>
</tr>
<tr>
<td><strong>Total Payable</strong></td>
<td class="text-right"><strong style="color: #ea580c;" id="summaryAmount">₹15000</strong></td>
</tr>
"""
html = re.sub(
    r'<tr>\s*<td>Selected category</td>.*?</tr>\s*<tr>\s*<td><strong>Total Payable</strong></td>.*?</tr>',
    fee_summary_html,
    html,
    flags=re.DOTALL
)

# 4. Replace the JS handler logic
js_logic = """
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>

    <script>
        function updateFeeSummary() {
            const cat = document.getElementById('feeCategory');
            const customWrap = document.getElementById('customAmountWrapper');
            const summaryCat = document.getElementById('summaryCategory');
            const summaryAmount = document.getElementById('summaryAmount');
            
            let catName = cat.options[cat.selectedIndex].text;
            summaryCat.innerText = catName;

            let val = cat.value;
            let amount = 0;

            if (val === 'franchise') {
                customWrap.style.display = 'none';
                amount = 15000;
            } else if (val === 'institution') {
                customWrap.style.display = 'none';
                amount = 5000;
            } else {
                customWrap.style.display = 'block';
                let customVal = parseInt(document.getElementById('customAmount').value) || 0;
                amount = customVal;
            }
            summaryAmount.innerText = '₹' + amount;
        }

        document.getElementById("pay-btn").addEventListener("click", async function () {
            
            // Validate Form
            const fullName = document.querySelector('input[name="full_name"]').value.trim();
            const phone = document.querySelector('input[name="phone"]').value.trim();
            const email = document.querySelector('input[name="email"]').value.trim();
            const rollNo = document.querySelector('input[name="roll_number"]').value.trim();
            const institutionName = document.querySelector('input[name="institution"]').value.trim();
            const notes = document.getElementById('checkoutNotes').value.trim();
            
            const cat = document.getElementById('feeCategory');
            const catVal = cat.value;
            const catName = cat.options[cat.selectedIndex].text;

            if (!fullName || !phone || !email) {
                alert("Please fill in all mandatory fields (Name, Phone, Email).");
                return;
            }

            let amount = 0;
            if (catVal === 'franchise') amount = 15000;
            else if (catVal === 'institution') amount = 5000;
            else amount = parseInt(document.getElementById('customAmount').value) || 0;

            if (amount <= 0) {
                alert("Please enter a valid amount greater than 0.");
                return;
            }

            try {
                // Step 1: Create Order
                const response = await fetch("{% url 'create_razorpay_order' %}", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCookie("csrftoken") || ''
                    },
                    body: JSON.stringify({ amount: amount })
                });

                const data = await response.json();
                if (data.status !== "success") {
                    alert(data.message || "Failed to create order.");
                    return;
                }

                // Step 2: Open Razorpay
                const options = {
                    key: data.key_id,
                    amount: data.amount,
                    currency: data.currency,
                    name: "EduAiQ",
                    description: catName,
                    order_id: data.order_id,
                    prefill: {
                        name: fullName,
                        email: email,
                        contact: phone
                    },
                    theme: { color: "#ea580c" },
                    handler: function (paymentResponse) {
                        console.log("Payment Success:", paymentResponse);
                        
                        // Step 3: Verify & Save Transaction
                        fetch("/payments/api/payment/verify-signature/", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                "X-CSRFToken": getCookie("csrftoken") || ''
                            },
                            body: JSON.stringify({
                                razorpay_order_id: paymentResponse.razorpay_order_id,
                                razorpay_payment_id: paymentResponse.razorpay_payment_id,
                                razorpay_signature: paymentResponse.razorpay_signature,
                                amount: amount,
                                description: catName + (notes ? " - " + notes : ""),
                                source_type: "miscellaneous_fee"
                            })
                        })
                        .then(res => res.json())
                        .then(verifyData => {
                            if (verifyData.status === "success") {
                                showPaymentSuccessModal(paymentResponse.razorpay_payment_id, amount, catName);
                            } else {
                                alert("Payment verified but saving failed: " + verifyData.message);
                            }
                        })
                        .catch(err => {
                            console.error(err);
                            alert("Payment verification error!");
                        });
                    }
                };

                const razorpay = new Razorpay(options);
                razorpay.on('payment.failed', function (resp) {
                    alert('Payment Failed: ' + resp.error.description);
                });
                razorpay.open();

            } catch (error) {
                console.error("Payment Error:", error);
                alert("Something went wrong. Check browser console.");
            }
        });

        // Helper to get CSRF token
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

function showPaymentSuccessModal(txnId, price, courseTitle) {
"""

html = re.sub(
    r'<script src="https://checkout.razorpay.com/v1/checkout.js"></script>.*?function showPaymentSuccessModal\(txnId, price, courseTitle\) {',
    js_logic,
    html,
    flags=re.DOTALL
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
    
print("Updated product-checkout.html logic successfully.")
