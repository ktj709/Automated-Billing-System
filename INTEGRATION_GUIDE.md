---
## NOTE (Source of Truth)

This file is a high-level integration index.

- For WhatsApp setup, see `WHATSAPP_SETUP.md`
- For Stripe setup, see `STRIPE_GUIDE.md`
- For Supabase schema + env setup, see `SUPABASE_SETUP.md` and `database/supabase_schema.sql`

The Streamlit app (`streamlit_app.py`) is the primary UI and talks to Supabase via `services/database_service.py`.
The Flask API (`app.py`) is optional (primarily for webhooks/integrations).

---

# 🔌 WhatsApp & Stripe Integration Guide

## 📱 WhatsApp Business API Setup

### Option 1: Meta (Facebook) WhatsApp Business API (Recommended)

**Step 1: Create Meta Developer Account**
1. Go to https://developers.facebook.com/
2. Create account or login
3. Create new app → Select "Business" type

**Step 2: Add WhatsApp Product**
1. In your app dashboard, click "Add Product"
2. Select "WhatsApp" → Click "Set Up"
3. Go to WhatsApp → Getting Started

**Step 3: Get Credentials**
1. **Phone Number ID**: Copy from "From" phone number section
2. **Access Token**: Copy temporary token (24 hours) or create permanent token:
   - Go to App Settings → Basic
   - Copy App ID and App Secret
   - Generate System User Token (doesn't expire)

**Step 4: Update .env file**
```env
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxx
```

**Step 5: Test Number**
- Add test numbers in WhatsApp → API Setup → "To" field
- Verify with 6-digit code sent via WhatsApp
- Test numbers can receive messages without business verification

**For Production:**
- Submit business verification
- Get approved phone number
- Create message templates (pre-approved messages)

### Option 2: Twilio WhatsApp API (Alternative)

**Step 1: Create Twilio Account**
1. Sign up at https://www.twilio.com/try-twilio
2. Get free credits ($15)

**Step 2: Setup WhatsApp Sandbox**
1. Go to Messaging → Try it out → Send a WhatsApp message
2. Follow instructions to join sandbox (send "join <code>" to Twilio number)

**Step 3: Get Credentials**
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

**Step 4: Modify whatsapp_service.py for Twilio**
```python
from twilio.rest import Client

client = Client(account_sid, auth_token)
message = client.messages.create(
    from_='whatsapp:+14155238886',
    body='Your bill message',
    to='whatsapp:+919876543210'
)
```

---

## 💳 Stripe Payment Link Setup

### Step 1: Create Stripe Account
1. Go to https://stripe.com/
2. Sign up for free account
3. Activate account (provide business details)

### Step 2: Get API Keys
1. Go to Developers → API Keys
2. Copy **Test Mode** keys (for development):
   - **Publishable key**: `pk_test_...` (not needed for backend)
   - **Secret key**: `sk_test_...` (use this)

### Step 3: Update .env file
```env
STRIPE_API_KEY=sk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 4: Test Payment Link
The current code already defaults to INR (`currency="inr"`) and will fall back to mock mode if Stripe is not configured.

### Step 5: Webhook Setup (Optional - for payment confirmation)
1. Go to Developers → Webhooks
2. Add endpoint: `https://your-domain.com/webhook/stripe`
3. Select events: `checkout.session.completed`, `payment_intent.succeeded`
4. Copy webhook signing secret: `whsec_...`

```python
# Add to app.py for payment confirmation
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    event = stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        bill_id = session['metadata']['bill_id']
        # Update bill status to 'paid'
        db.update_bill_status(bill_id, 'paid')
    
    return {'status': 'success'}
```

---

## 🧪 Testing Without Real Setup

### Mock Mode (Current Setup)

**WhatsApp Messages** - Currently logs to console:
```python
# In whatsapp_service.py
if not self.access_token or self.access_token == "your_access_token":
    print(f"📱 MOCK WhatsApp to {to_phone}:")
    print(f"Message: {message}")
    return {"message_id": f"mock_{datetime.now().timestamp()}", "status": "sent", "success": True}
```

**Stripe Payments** - Returns mock links:
```python
# In payment_service.py (already implemented)
if not self.enabled:
    return {
        "url": f"http://localhost:5000/mock-payment/{bill_id}",
        "id": f"mock_link_{bill_id}",
        "active": True
    }
```

### Testing with Actual APIs (Sandbox/Test Mode)

**1. WhatsApp Test Messages (Free)**
- Use Meta temporary token (24 hours)
- Add your number as test recipient
- No business verification needed
- Max 1000 messages/month in test mode

**2. Stripe Test Payments (Free)**
- Use test API key `sk_test_...`
- Test card numbers: `4242 4242 4242 4242` (Visa)
- Any future expiry date, any CVC
- No real money charged

---

## 🚀 Quick Start Checklist

### For Development (Using Test/Mock):
- [ ] ✅ Supabase already configured
- [ ] (Optional) OpenAI configured (only if you use AI validation/messages)
- [ ] Get Meta WhatsApp temporary token (optional)
- [ ] Get Stripe test API key (optional)
- [ ] Update .env with real keys OR keep mock mode
- [ ] Test workflow in Streamlit

### For Production:
- [ ] Complete WhatsApp Business verification
- [ ] Create WhatsApp message templates
- [ ] Activate Stripe account
- [ ] Change Stripe to live mode (`sk_live_...`)
- [ ] Set up Stripe webhook for payment confirmation
- [ ] Add SSL certificate to domain
- [ ] Deploy to production server
- [ ] Test end-to-end with real phone number

---

## 💰 Cost Breakdown

| Service | Free Tier | Paid Pricing |
|---------|-----------|-------------|
| **WhatsApp (Meta)** | 1000 conversations/month | $0.0045 - $0.092 per conversation |
| **Stripe** | Unlimited test transactions | 2.9% + ₹2 per transaction |
| **Twilio WhatsApp** | Free trial credits | $0.005 per message |
| **Supabase** | 500 MB database, 1 GB bandwidth | $25/month (Pro) |
| **OpenAI** | $5 free credits (new accounts) | ~$0.002 per billing calculation |

**Estimated cost for 1000 bills/month**: ₹800 - ₹1200 (~$10-15)

---

## 🔧 Alternative: Free Testing Options

### 1. Discord Bot (For Notifications)
Replace WhatsApp with Discord webhooks:
```python
import requests

def send_discord_notification(webhook_url, message):
    requests.post(webhook_url, json={"content": message})
```

### 2. Email Notifications (Free)
Use Gmail SMTP:
```python
import smtplib

def send_email(to, subject, body):
    # Free 500 emails/day with Gmail
    smtp.sendmail(from_email, to_email, msg.as_string())
```

### 3. Razorpay (Indian Alternative to Stripe)
- Better for Indian customers (UPI, Net Banking)
- 2% transaction fee
- Payment links API similar to Stripe

```python
import razorpay
client = razorpay.Client(auth=(key_id, key_secret))

payment_link = client.payment_link.create({
    "amount": amount_paise,
    "currency": "INR",
    "description": f"Bill for {meter_id}",
})
```

---

## 🎯 Recommendation

**For Testing Now:**
1. Keep mock mode (already working)
2. Add console logging to see messages
3. Test complete workflow in Streamlit

**For Production Later:**
1. Use Razorpay instead of Stripe (better for India)
2. Use WhatsApp Business API (Meta)
3. Set up proper webhooks for payment confirmation
