# 📱 WhatsApp Business API Setup Guide

## 🚀 Quick Setup (Free Testing)

### Step 1: Create Meta Developer Account
1. Go to **https://developers.facebook.com/**
2. Click **"Get Started"** → Create account or login
3. Complete account setup

### Step 2: Create New App
1. Click **"My Apps"** → **"Create App"**
2. Select **"Business"** type
3. Enter app name: `Billing Notifications`
4. Enter contact email
5. Click **"Create App"**

### Step 3: Add WhatsApp Product
1. In your app dashboard, scroll to **"Add Products"**
2. Find **"WhatsApp"** → Click **"Set up"**
3. You'll be taken to WhatsApp Getting Started

### Step 4: Get Credentials

#### Phone Number ID:
1. In WhatsApp → **API Setup** → **"From"** section
2. Copy the **Phone Number ID** (numeric, like `123456789012345`)

#### Access Token:
1. Same page, under **"Temporary access token"**
2. Copy the token (starts with `EAA...`)
3. **Note**: This expires in 24 hours

#### For Permanent Token:
1. Go to **App Settings** → **Basic**
2. Copy **App ID** and **App Secret**
3. Use System User Token (doesn't expire)

### Step 5: Update .env File
```env
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 6: Add Test Phone Number
1. In WhatsApp → **API Setup** → **"To"** field
2. Click **"Manage phone number list"**
3. Add your phone number (include country code: `+91xxxxxxxxxx`)
4. You'll receive 6-digit code via WhatsApp
5. Enter code to verify

---

## 🧪 Testing

### Test in Mock Mode (No Setup)
```bash
python test_whatsapp.py
```
- Shows what messages would be sent
- No real WhatsApp messages
- Good for development

### Test with Real WhatsApp (After Setup)
```bash
# Update .env with real credentials first
python test_whatsapp.py
```
- Sends actual WhatsApp messages
- Check your phone for messages
- Free during development (1000 messages/month)

---

## 📊 Meta Business API Features

### Test Mode (Free)
- **1000 conversations/month** free
- Test with up to **5 phone numbers**
- All features available
- No business verification needed

### Production Mode
- **Unlimited messages** (paid)
- Requires business verification
- Must use approved templates
- $0.0045 - $0.092 per conversation

---

## 💬 Message Types

### 1. Text Messages (What we use)
```python
whatsapp.send_message(
    to_phone="+919876543210",
    message="Your bill is ready!"
)
```
✅ Works immediately in test mode  
✅ No approval needed  
✅ Any text content  

### 2. Template Messages (For Production)
```python
whatsapp.send_template_message(
    to_phone="+919876543210",
    template_name="bill_notification",
    parameters=["₹2,311", "30 Nov"]
)
```
❌ Requires template approval from Meta  
✅ Lower cost in production  
✅ Higher delivery rate  

### 3. Media Messages (Images, PDFs)
- Can send bill PDFs
- Requires media upload first
- Good for detailed bills

---

## 🔐 Access Tokens

### Temporary Token (24 hours)
- Good for quick testing
- Found in WhatsApp → API Setup
- Regenerate when expired

### Permanent System User Token
1. **Meta Business Settings** → **System Users**
2. Click **"Add"** → Create system user
3. **Assign Assets** → Select your app
4. **Generate Token** → Select permissions: `whatsapp_business_messaging`
5. Copy token (starts with `EAA...`)
6. This never expires!

---

## 🌐 Webhook Setup (Optional - for 2-way chat)

If you want to receive messages:

1. **Create webhook endpoint** in your app:
```python
@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        # Verify webhook
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == 'YOUR_VERIFY_TOKEN':
            return challenge
        return 'Forbidden', 403
    
    # Handle incoming messages
    data = request.json
    # Process message...
    return 'OK', 200
```

2. **Configure in Meta**:
   - WhatsApp → **Configuration**
   - Callback URL: `https://your-domain.com/webhook/whatsapp`
   - Verify Token: `YOUR_VERIFY_TOKEN`
   - Webhook Fields: Select `messages`

---

## 📝 Template Creation (For Production)

### Create Template:
1. **WhatsApp Manager** → **Message Templates**
2. Click **"Create Template"**
3. Example:
   - Name: `bill_notification`
   - Category: `Utility`
   - Language: `English`
   - Body: `Hello! Your electricity bill of {{1}} is ready. Pay by {{2}}.`
   - Buttons: Add payment link

4. **Submit for Review** (takes 1-2 days)

### Use Template:
```python
whatsapp.send_template_message(
    to_phone="+919876543210",
    template_name="bill_notification",
    parameters=["₹2,311", "30 Nov 2025"]
)
```

---

## 💰 Pricing

| Tier | Messages/Month | Cost per Conversation |
|------|----------------|----------------------|
| **Free (Test)** | 1,000 | $0 |
| **Utility** | Unlimited | $0.0045 - $0.092 |
| **Authentication** | Unlimited | Free |
| **Marketing** | Unlimited | $0.0175 - $0.300 |

**Conversation** = 24-hour window after message

---

## ✅ Quick Start Checklist

- [ ] Create Meta Developer account
- [ ] Create app and add WhatsApp product
- [ ] Get Phone Number ID
- [ ] Get Access Token (temporary or permanent)
- [ ] Update .env file
- [ ] Add test phone number
- [ ] Verify with 6-digit code
- [ ] Run `python test_whatsapp.py`
- [ ] Check your phone for message!

---

## 🔧 Troubleshooting

### "Invalid Phone Number ID"
- Check you copied the numeric ID, not phone number
- ID format: `123456789012345` (15 digits)

### "Invalid Access Token"
- Token expired (get new one)
- Wrong token (check copy-paste)
- Missing `EAA` prefix

### "Recipient not in test numbers"
- Add your number in WhatsApp → API Setup → Manage numbers
- Verify with 6-digit code

### "Message not received"
- Check phone has WhatsApp installed
- Number format: `+[country][number]` (e.g., `+919876543210`)
- No spaces or dashes

---

## 🌟 Alternative: Twilio WhatsApp

Easier setup, fewer features:

```python
from twilio.rest import Client

client = Client(account_sid, auth_token)

message = client.messages.create(
    from_='whatsapp:+14155238886',  # Twilio sandbox
    to='whatsapp:+919876543210',
    body='Your bill is ready!'
)
```

**Pros**: Simpler setup, $15 free credit  
**Cons**: Sandbox limitations, higher cost

---

## 📞 Support

- **Meta Docs**: https://developers.facebook.com/docs/whatsapp
- **Business Manager**: https://business.facebook.com/
- **API Docs**: https://developers.facebook.com/docs/whatsapp/cloud-api

---

Ready to send your first WhatsApp notification? Run:
```bash
python test_whatsapp.py
```
