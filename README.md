# ⚡ Electricity Billing Automation System

A production-ready, AI-powered electricity billing system with automated workflows, payment processing, and real-time notifications. Built with Python, Flask, Streamlit, and integrated with Supabase, Stripe, Auth0, and WhatsApp Business API.

---

## 🎯 Overview

This system automates the complete electricity billing workflow from meter reading to payment collection:

1. **Meter Reading Collection** - Automated or manual meter reading input
2. **AI-Powered Validation** - OpenAI validates readings for anomalies
3. **Smart Bill Calculation** - Tiered tariff calculation with fixed charges
4. **Payment Link Generation** - Stripe payment links in INR
5. **WhatsApp Notifications** - Automated bill notifications via WhatsApp
6. **Payment Tracking** - Real-time payment status updates via webhooks
7. **Scheduled Automation** - Monthly billing cycles, reminders, and collection

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Streamlit  │  │ REST API     │  │  Webhooks    │      │
│  │   Dashboard  │  │ (Flask)      │  │  (Stripe)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Database │ │ Payment  │ │ WhatsApp │ │   Auth   │      │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │AI Agent  │ │ Tariff   │ │ Neo4j    │ │Scheduler │      │
│  │ Service  │ │  Rules   │ │ Service  │ │ Service  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  External Services                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Supabase │ │  Stripe  │ │ WhatsApp │ │  Auth0   │      │
│  │(Postgres)│ │ Payments │ │   API    │ │   JWT    │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐                                               │
│  │  OpenAI  │                                               │
│  │   API    │                                               │
│  └──────────┘                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Core Features
- ✅ **Automated Meter Reading Collection** - Scheduled jobs for periodic collection
- ✅ **AI-Powered Validation** - OpenAI GPT-4 validates reading anomalies
- ✅ **Dynamic Tariff Calculation** - Tiered pricing (₹4.5-9.0/kWh) + fixed charges
- ✅ **Stripe Payment Integration** - Payment links with INR support
- ✅ **WhatsApp Notifications** - Automated bill notifications (with mock mode)
- ✅ **Auth0 Authentication** - JWT-based API security
- ✅ **Payment Tracking** - Real-time status updates via Stripe webhooks
- ✅ **Scheduled Billing Cycles** - APScheduler for monthly automation

### Advanced Features
- ✅ **Error Handling & Retry Logic** - Exponential backoff, circuit breakers
- ✅ **Comprehensive Logging** - Rotating file handlers, error tracking
- ✅ **Neo4j Graph Database** - Optional relationship tracking
- ✅ **Streamlit Dashboard** - Interactive testing interface with 8 tabs
- ✅ **REST API** - Complete Flask API with error handling
- ✅ **Webhook Support** - Stripe payment event handling

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Supabase account (free tier)
- Stripe account (test mode)
- Auth0 account (free tier)
- OpenAI API key
- WhatsApp Business API (optional)

### Installation

1. **Clone the repository**
```bash
cd "E:\Machine Learning Projects\Billing"
```

2. **Create virtual environment**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Edit `.env` with your credentials:

```env
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# OpenAI (Required)
OPENAI_API_KEY=sk-proj-your-key

# Stripe (Required for payments)
STRIPE_API_KEY=sk_test_your-key
STRIPE_WEBHOOK_SECRET=whsec_your-secret  # Optional for testing

# Auth0 (Required for API authentication)
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_API_IDENTIFIER=https://billing-api.example.com

# WhatsApp Business API (Optional)
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxx

# Neo4j (Optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Flask Settings
APP_HOST=0.0.0.0
APP_PORT=5000
DEBUG=True
```

5. **Seed the database**
```bash
.\venv\Scripts\python.exe seed_database.py
```

6. **Run the application**

**Option A: Streamlit Dashboard (Recommended for testing)**
```bash
streamlit run streamlit_app.py
```
Open browser: http://localhost:8501

**Option B: Flask API Server**
```bash
.\venv\Scripts\python.exe app.py
```
API available at: http://localhost:5000

---

## 📖 How It Works

### 1. Meter Reading Workflow

```
Meter Reading Input
        ↓
┌──────────────────┐
│ 1. Authenticate  │ ← Auth0 JWT verification
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 2. Get History   │ ← Fetch last 10 readings from Supabase
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 3. AI Validate   │ ← OpenAI checks for anomalies
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 4. Calculate     │ ← Apply tiered tariff rules
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 5. Store Bill    │ ← Save to Supabase bills table
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 6. Create Link   │ ← Generate Stripe payment link
└────────┬─────────┘
         ↓
┌──────────────────┐
│ 7. Send Notify   │ ← WhatsApp notification to customer
└────────┬─────────┘
         ↓
   Bill Generated ✅
```

### 2. Tariff Calculation

The system uses a **4-tier pricing structure** based on actual residential electricity tariff:

```python
Tier 1: 0-50 kWh    → ₹4.50/kWh
Tier 2: 51-100 kWh  → ₹6.00/kWh
Tier 3: 101-200 kWh → ₹7.50/kWh
Tier 4: 201+ kWh    → ₹9.00/kWh

Fixed Charges:
- Motor Surcharge: ₹12.00
- Grid Maintenance: ₹51.00/KW (based on connected load)
- Maintenance: ₹2,954.00 (annual ÷ 12)
```

**Example Bill Calculation:**
```
Consumption: 150 kWh
Connected Load: 7 KW

Energy Charges:
  50 kWh × ₹4.50  = ₹225.00
  50 kWh × ₹6.00  = ₹300.00
  50 kWh × ₹7.50  = ₹375.00
  Total Energy    = ₹900.00

Fixed Charges:
  Motor           = ₹12.00
  Grid (7 KW)     = ₹357.00
  Maintenance     = ₹246.17
  Total Fixed     = ₹615.17

Total Bill Amount = ₹1,515.17
```

### 3. AI Validation

OpenAI GPT-4 validates meter readings by:
- Analyzing historical patterns (last 10 readings)
- Detecting anomalies (sudden spikes, backwards movement)
- Checking seasonal trends
- Providing confidence scores (0-100%)

### 4. Payment Processing

```
Customer Receives Bill
        ↓
Clicks Payment Link → Stripe Checkout
        ↓
Completes Payment
        ↓
Stripe Sends Webhook → /webhook/stripe
        ↓
Bill Status Updated → "paid"
        ↓
Payment Event Logged
```

### 5. Scheduled Jobs

APScheduler runs background jobs:

| Job | Schedule | Description |
|-----|----------|-------------|
| **Monthly Bills** | 1st @ 2:00 AM | Generate bills for all customers |
| **Payment Reminders** | Daily @ 10:00 AM | Send reminders for pending bills |
| **Overdue Marking** | Daily @ 11:00 AM | Mark overdue bills |
| **Meter Collection** | Sunday @ 8:00 AM | Collect meter readings |

---

## 🖥️ Usage

### Streamlit Dashboard

The Streamlit dashboard provides 8 interactive tabs:

#### **Tab 1: 📊 Dashboard**
- System overview with metrics
- Recent meter readings table
- Consumption trends

#### **Tab 2: 🔄 Full Workflow Test**
- Complete 13-step workflow simulation
- Test meter reading → bill generation
- Real-time validation results
- Step-by-step execution logs

#### **Tab 3: 🔐 Auth0 Testing**
- Test JWT token verification
- Authenticated API requests
- User information display
- Token validation results

#### **Tab 4: 💳 Payment Status**
- **Get Bill Status**: View bill details by ID with metrics
- **Customer Bills**: All bills for a customer with summary
- **Update Status**: Manual status updates (admin/testing)
- **Webhook Simulator**: Test Stripe webhook events

#### **Tab 5: ⏰ Scheduler**
- View scheduled jobs (4 jobs)
- Start/stop scheduler
- Job execution history
- Configure schedules

#### **Tab 6: 🧮 Tariff Calculator**
- Calculate bills manually
- Test different consumption levels
- View detailed tariff breakdown
- Fixed charges calculation

#### **Tab 7: 📋 Meter Readings**
- View historical readings
- Add new readings
- Data visualization
- Reading history table

#### **Tab 8: 💰 Generate Bill**
- Manual bill generation
- Custom parameters (meter ID, consumption, etc.)
- Bill preview
- Payment link generation

### REST API Endpoints

#### **Meter Reading Webhook**
```http
POST /webhook/meter-reading
Authorization: Bearer <auth0_token>
Content-Type: application/json

{
  "user_id": "auth0|user123",
  "meter_id": "METER001",
  "customer_id": "CUST001",
  "customer_phone": "+919876543210",
  "reading_value": 1250.5,
  "reading_date": "2025-11-18",
  "connected_load_kw": 7.0
}
```

**Response:**
```json
{
  "success": true,
  "bill_id": 123,
  "validation": {
    "valid": true,
    "confidence": 95,
    "reason": "Reading is consistent with historical pattern"
  },
  "calculation": {
    "consumption_kwh": 150.5,
    "total_amount": 1515.17,
    "breakdown": {
      "tier_1": {"kwh": 50, "rate": 4.5, "amount": 225.0},
      "tier_2": {"kwh": 50, "rate": 6.0, "amount": 300.0},
      "tier_3": {"kwh": 50.5, "rate": 7.5, "amount": 378.75}
    },
    "fixed_charges": {
      "motor_surcharge": 12.0,
      "grid_maintenance": 357.0,
      "maintenance": 246.17
    }
  },
  "payment_link": "https://buy.stripe.com/test_...",
  "notification_sent": true
}
```

#### **Get Bill Status**
```http
GET /api/bills/123
```

**Response:**
```json
{
  "success": true,
  "bill": {
    "id": 123,
    "customer_id": "CUST001",
    "meter_id": "METER001",
    "amount": 1515.17,
    "consumption_kwh": 150.5,
    "status": "paid",
    "payment_date": "2025-11-18",
    "payment_link": "https://buy.stripe.com/test_...",
    "created_at": "2025-11-01T00:00:00"
  }
}
```

#### **Get Customer Bills**
```http
GET /api/bills/customer/CUST001?limit=10
```

#### **Update Bill Status**
```http
PUT /api/bills/123/status
Content-Type: application/json

{
  "status": "paid",
  "payment_date": "2025-11-18"
}
```

#### **Stripe Webhook**
```http
POST /webhook/stripe
Stripe-Signature: <signature>

{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "metadata": {
        "bill_id": "123"
      },
      "payment_status": "paid"
    }
  }
}
```

---

## 🧪 Testing

### Test Scripts

Run individual test scripts:

```bash
# Test tariff calculation
.\venv\Scripts\python.exe test_tariff.py

# Test Auth0 integration
.\venv\Scripts\python.exe verify_token.py

# Test Stripe payments
.\venv\Scripts\python.exe test_stripe.py

# Test WhatsApp notifications
.\venv\Scripts\python.exe test_whatsapp.py

# Test error handling
.\venv\Scripts\python.exe test_error_handling.py

# Test services with retry logic
.\venv\Scripts\python.exe test_services_with_errors.py
```

### Testing Workflow via Streamlit

1. **Start Streamlit**: `streamlit run streamlit_app.py`
2. Go to **"🔄 Full Workflow Test"** tab
3. Fill in test data:
   - Meter ID: `METER001`
   - Customer ID: `CUST001`
   - Reading Value: `1500`
   - Connected Load: `7` KW
4. Click **"Run Complete Workflow"**
5. View step-by-step results with timing

### Testing Payments

1. **Generate Test Bill** via Streamlit or API
2. **Copy Payment Link** from response
3. **Open in Browser**
4. Use Stripe test card: `4242 4242 4242 4242`
5. View payment confirmation in "Payment Status" tab

### Testing Webhooks Locally

1. **Install ngrok**: `choco install ngrok` (if not installed)
2. **Start Flask**: `python app.py`
3. **Expose port**: `ngrok http 5000`
4. **Copy URL**: `https://abc123.ngrok.io`
5. **Configure Stripe**: 
   - Dashboard → Webhooks → Add endpoint
   - Endpoint URL: `https://abc123.ngrok.io/webhook/stripe`
   - Events: `checkout.session.completed`
6. **Test Payment**: Complete a test payment
7. **View Logs**: Check `logs/app.log` for webhook events

---

## 📊 Database Schema

### Supabase Tables

#### **meter_readings**
```sql
CREATE TABLE meter_readings (
  id SERIAL PRIMARY KEY,
  meter_id VARCHAR(50) NOT NULL,
  customer_id VARCHAR(50) NOT NULL,
  reading_value DECIMAL(10,2) NOT NULL,
  reading_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **bills**
```sql
CREATE TABLE bills (
  id SERIAL PRIMARY KEY,
  customer_id VARCHAR(50) NOT NULL,
  meter_id VARCHAR(50) NOT NULL,
  billing_period_start DATE,
  billing_period_end DATE,
  consumption_kwh DECIMAL(10,2),
  amount DECIMAL(10,2),
  status VARCHAR(20) DEFAULT 'pending',
  payment_link TEXT,
  payment_link_id VARCHAR(100),
  payment_date DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **notifications**
```sql
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  bill_id INTEGER REFERENCES bills(id),
  customer_id VARCHAR(50),
  channel VARCHAR(20),
  message TEXT,
  status VARCHAR(20),
  whatsapp_message_id VARCHAR(100),
  sent_at TIMESTAMP DEFAULT NOW()
);
```

#### **payment_events**
```sql
CREATE TABLE payment_events (
  id SERIAL PRIMARY KEY,
  bill_id INTEGER REFERENCES bills(id),
  event_type VARCHAR(50),
  payment_link_id VARCHAR(100),
  stripe_event_id VARCHAR(100),
  event_data JSONB,
  received_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔐 Security

### Authentication
- **Auth0 JWT** - RS256 signature verification
- **API Keys** - Environment variable management
- **Webhook Signatures** - Stripe signature validation (optional)

### Best Practices
- ✅ No credentials in code
- ✅ Environment variable validation
- ✅ API rate limiting ready
- ✅ Error messages sanitized
- ✅ Logging without sensitive data

---

## 📝 Logging

### Log Files
- `logs/app.log` - All logs (DEBUG+)
- `logs/error.log` - Errors only (ERROR+)

### Log Rotation
- Max file size: 10MB
- Backup count: 5 files
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Monitoring Logs
```bash
# View latest logs
Get-Content logs\app.log | Select-Object -Last 50

# Watch logs in real-time
Get-Content logs\app.log -Wait

# Filter errors only
Get-Content logs\error.log

# Search for specific pattern
Get-Content logs\app.log | Select-String "ERROR"
```

---

## 🛠️ Troubleshooting

### Common Issues

**1. Supabase Connection Error**
```
Error: Could not connect to Supabase
```
**Solution**: 
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Verify Supabase project is active
- Check network connectivity

**2. OpenAI API Error**
```
Error: Invalid API key
```
**Solution**: 
- Verify `OPENAI_API_KEY` is valid
- Check API key has credits
- Ensure key starts with `sk-proj-`

**3. Flask Server Exits Immediately**
```
Server starts then exits without error
```
**Solution**: 
- Use Streamlit for testing instead
- Check `logs/error.log` for startup errors
- Verify all dependencies installed

**4. Stripe Payment Link Error**
```
Error: Stripe error creating payment link
```
**Solution**: 
- Verify `STRIPE_API_KEY` starts with `sk_test_`
- Check Stripe account is active
- Ensure currency (INR) is supported

**5. WhatsApp Mock Mode**
```
WhatsApp service in mock mode
```
**Solution**: 
- This is expected if WhatsApp not configured
- Configure `WHATSAPP_PHONE_NUMBER_ID` and `WHATSAPP_ACCESS_TOKEN`
- Or continue with mock mode for testing (messages logged to console)

**6. Import Errors**
```
ModuleNotFoundError: No module named 'stripe'
```
**Solution**:
- Activate virtual environment: `.\venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`

### Debug Mode

Enable detailed logging:
```python
# In .env
DEBUG=True
```

View detailed error traces in Streamlit dashboard and `logs/app.log`.

---

## 🚀 Deployment

### Production Checklist

- [ ] Update all API keys to production values
- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure Stripe webhook with signing secret
- [ ] Enable WhatsApp Business API (if needed)
- [ ] Set up SSL/TLS for API endpoints
- [ ] Configure rate limiting
- [ ] Set up monitoring (Sentry, New Relic)
- [ ] Configure backup for Supabase
- [ ] Test all scheduled jobs
- [ ] Set up alerts for errors
- [ ] Document deployment process

### Recommended Stack

**Hosting:**
- **API**: Railway, Render, or Heroku
- **Dashboard**: Streamlit Cloud
- **Database**: Supabase (managed PostgreSQL)

**Monitoring:**
- **Logging**: Papertrail or Loggly
- **APM**: New Relic or DataDog
- **Errors**: Sentry

**CI/CD:**
- GitHub Actions for automated testing
- Pre-commit hooks for code quality

---

## 📚 Project Structure

```
Billing/
├── app.py                      # Flask API server
├── streamlit_app.py            # Streamlit dashboard (8 tabs)
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── seed_database.py            # Database seeding script
├── .env                        # Environment variables (not in git)
│
├── services/                   # Service layer
│   ├── __init__.py
│   ├── database_service.py     # Supabase integration
│   ├── ai_agent_service.py     # OpenAI integration
│   ├── payment_service.py      # Stripe integration
│   ├── whatsapp_service.py     # WhatsApp Business API
│   ├── auth_service.py         # Auth0 JWT verification
│   ├── tariff_rules.py         # Billing calculation logic
│   ├── neo4j_service.py        # Graph database (optional)
│   └── billing_scheduler.py    # APScheduler jobs
│
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── sample_data.py          # Test data generation
│   ├── retry_decorator.py      # Error handling & retry
│   └── logger.py               # Logging configuration
│
├── logs/                       # Log files
│   ├── app.log                 # All logs
│   └── error.log               # Errors only
│
├── database/                   # Database schemas
│   ├── schema.sql              # PostgreSQL schema
│   └── neo4j_setup.cypher      # Neo4j graph (optional)
│
├── test_*.py                   # Test scripts
├── verify_token.py             # Auth0 token verification
│
├── docs/                       # Documentation (optional)
│   ├── WHATSAPP_SETUP.md       # WhatsApp setup guide
│   └── ERROR_HANDLING.md       # Error handling details
│
└── README.md                   # This file
```

---

## 🎯 Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Meter Reading Collection | ✅ | Manual + Scheduled |
| AI Validation | ✅ | OpenAI GPT-4 |
| Bill Calculation | ✅ | 4-tier tariff + fixed charges |
| Payment Links | ✅ | Stripe (INR currency) |
| WhatsApp Notifications | ✅ | Mock mode available |
| Payment Tracking | ✅ | Webhook integration |
| Scheduled Jobs | ✅ | APScheduler (4 jobs) |
| Auth0 Authentication | ✅ | JWT RS256 |
| Error Handling | ✅ | Retry + Circuit breaker |
| Logging | ✅ | Rotating files (10MB) |
| Dashboard | ✅ | 8 interactive tabs |
| REST API | ✅ | Complete Flask API |
| Payment Status | ✅ | 4 subtabs in dashboard |
| Database | ✅ | Supabase (PostgreSQL) |

---

## 📖 Additional Documentation

- **WHATSAPP_SETUP.md** - Complete guide for WhatsApp Business API setup
- **ERROR_HANDLING.md** - Details on retry logic, circuit breakers, logging
- **Database Schema** - See `database/schema.sql` for full schema
- **API Examples** - Test scripts in root directory (`test_*.py`)

---

## 🤝 Contributing

This is a demonstration project. For production use:

1. Add comprehensive unit tests
2. Implement CI/CD pipeline
3. Add API documentation (Swagger/OpenAPI)
4. Enhance security (rate limiting, input validation)
5. Add customer management features
6. Implement billing reports and analytics
7. Add email notifications as backup to WhatsApp

---

## 📄 License

MIT License - Feel free to use for learning and commercial projects.

---

## 🔗 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Auth0 Documentation](https://auth0.com/docs)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

## 📞 Support

For issues and questions:
1. Check the **Troubleshooting** section above
2. Review setup guides in root directory
3. Check logs in `logs/` directory
4. Verify environment variables in `.env`
5. Run test scripts to isolate issues

---

## 🎓 Learning Resources

This project demonstrates:
- **Microservices Architecture** - Separate services for each concern
- **Error Handling Patterns** - Retry logic, circuit breakers
- **API Integration** - Multiple third-party services
- **Async Job Processing** - APScheduler for background tasks
- **Security Best Practices** - JWT authentication, environment variables
- **Database Design** - Relational schema for billing
- **Testing Strategies** - Unit tests, integration tests
- **Logging & Monitoring** - Structured logging, error tracking

---

**Built with ❤️ for automated billing management**

*Last Updated: November 18, 2025*
