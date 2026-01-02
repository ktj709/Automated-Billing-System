# 💳 Stripe Payment Integration Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Stripe Account
1. Go to **https://stripe.com/**
2. Click **"Start now"** (free account)
3. Enter email and create password
4. Skip business details for now (can add later)

### Step 2: Get Test API Key
1. After login, you'll be in **Test Mode** (see toggle in top right)
2. Go to **Developers** → **API keys** (https://dashboard.stripe.com/test/apikeys)
3. Find **Secret key** (starts with `sk_test_...`)
4. Click **"Reveal test key"** and copy it

### Step 3: Update .env File
```env
STRIPE_API_KEY=sk_test_your_stripe_secret_key_here
```

### Step 4: Install Stripe Package
Already installed! ✅ (We have it in requirements.txt)

---

## 🧪 Test Mode vs Live Mode

### Test Mode (Free Forever)
- **API Key**: `sk_test_...`
- **Test Cards**: Use fake card numbers
- **No Real Money**: All transactions are simulated
- **Perfect for**: Development and testing

#### Test Card Numbers
| Card | Number | Description |
|------|--------|-------------|
| **Visa** | `4242 4242 4242 4242` | Always succeeds |
| **Visa (Decline)** | `4000 0000 0000 0002` | Always fails |
| **Mastercard** | `5555 5555 5555 4444` | Always succeeds |
| **Requires 3D Secure** | `4000 0027 6000 3184` | Requires authentication |

- **Expiry**: Any future date (e.g., 12/34)
- **CVC**: Any 3 digits (e.g., 123)
- **ZIP**: Any 5 digits (e.g., 12345)

### Live Mode (Production)
- **API Key**: `sk_live_...`
- **Real Cards**: Customer's actual cards
- **Real Money**: Actual charges and payouts
- **Fees**: 2.9% + $0.30 per successful charge

---

## 💰 Payment Link vs Payment Intent

Our implementation uses **Payment Links** (best for billing):

### Payment Links
✅ Shareable URL that customers can use to pay  
✅ Works via SMS, Email, WhatsApp  
✅ No code needed on customer side  
✅ Stripe-hosted checkout page  
✅ Perfect for billing notifications  

Example: `https://buy.stripe.com/test_xxxxxx`

### How it Works
1. **Create Payment Link** → Get URL
2. **Send URL** to customer (WhatsApp/SMS/Email)
3. **Customer clicks** → Opens Stripe checkout
4. **Customer pays** → Stripe processes
5. **Webhook notification** → Your system updates bill status

---

## 🔧 Code Configuration

### Current Implementation Status

```python
# payment_service.py already supports:
✅ Create payment link
✅ INR currency (Indian Rupees)
✅ Metadata (bill_id, customer_id, meter_id)
✅ Mock mode fallback
✅ Error handling
```

### What We Need to Add
1. **Webhook endpoint** - To receive payment confirmations
2. **Bill status update** - Mark bill as "paid" automatically
3. **(Optional) Webhook hardening** - Signature verification + richer event logging

---

## 🎯 Testing Payment Flow

### Manual Testing
```python
# Run this to test payment link creation
python test_stripe.py
```

---

## 📊 Stripe Dashboard Features

After you create an account, you can:

1. **Payments** - See all test payments
2. **Products** - View electricity bills as products
3. **Payment Links** - Manage all payment URLs
4. **Webhooks** - Configure webhook endpoints
5. **Logs** - Debug API requests

---

## 🌐 Webhook Setup (For Production)

Webhooks let Stripe notify your system when payments succeed:

### 1. Add Webhook Endpoint to app.py
```python
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            bill_id = session['metadata']['bill_id']
            
            # Update bill status
            db.update_bill_status(bill_id, 'paid')
            
        return {'status': 'success'}
    except Exception as e:
        return {'error': str(e)}, 400
```

### 2. Configure in Stripe Dashboard
1. Go to **Developers** → **Webhooks**
2. Click **"Add endpoint"**
3. URL: `https://your-domain.com/webhook/stripe`
4. Events: Select `checkout.session.completed`
5. Copy **Signing secret** (starts with `whsec_...`)

---

## 💡 Indian Rupees (INR) Support

INR is already supported and is the default in the current implementation.

- `PaymentService.create_payment_link(..., currency="inr")` defaults to INR
- Amounts are converted to the smallest unit (paise) automatically

---

## 🔐 Security Best Practices

1. **Never commit API keys** to git
2. **Use test keys** for development
3. **Use environment variables** (.env file)
4. **Verify webhook signatures** (prevents fake requests)
5. **Use HTTPS** in production

---

## 📈 Cost Calculation

### For 1000 Bills/Month in India

| Service | Cost |
|---------|------|
| Stripe Fee (2.9% + ₹2) | ~₹2,900 (on ₹100k revenue) |
| Payment Success Rate | ~97% |
| Chargeback Protection | Included |
| Dashboard & Analytics | Free |

**Cheaper alternatives for India:**
- **Razorpay**: 2% (better for India)
- **Paytm**: 1.99%
- **PhonePe**: 1.5%

---

## ✅ Quick Start Checklist

- [ ] Create Stripe account
- [ ] Get test API key (sk_test_...)
- [ ] Update .env file
- [ ] Test in Streamlit
- [ ] Create test payment link
- [ ] Use test card to pay
- [ ] Verify webhook (production only)

---

## 🚀 Ready to Test?

Run:
```powershell
python test_stripe.py
```

Or use the Streamlit dashboard!
