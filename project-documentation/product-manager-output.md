# Electricity Billing Automation System MVP PRD
**Date:** December 14, 2025

---

## 1. Executive Summary

**Elevator Pitch:** An AI-powered electricity billing system that automates the complete workflow from meter reading to payment collection with real-time notifications.

**Problem Statement:** Manual electricity billing processes are error-prone, time-consuming, and lack real-time tracking. Utility companies struggle with accurate meter reading validation, timely bill generation, payment collection, and customer communication.

**Target User:** 
- Field engineers who collect meter readings in residential/commercial properties
- Administrators who manage billing operations, track payments, and handle customer accounts

**Proposed Solution:** A role-based billing automation system with AI-powered meter reading validation, automated bill calculation using tiered tariffs, integrated payment processing via Stripe, and real-time notifications via WhatsApp/Discord.

**MVP Success Metric:** 90% reduction in billing cycle time (from reading to payment link delivery under 5 minutes).

---

## 2. Key Features (Max 3)

### Feature 1: Meter Reading Collection & AI Validation

| Attribute | Description |
|-----------|-------------|
| **User Story** | As a field engineer, I want to submit meter readings through a simple interface, so that the system can validate and process them automatically. |
| **Acceptance Criteria** | Given a meter reading is submitted, when the reading is received, then OpenAI validates it against last 10 readings and returns confidence score (0-100%). |
| **Priority** | P0 (Must-have) |
| **Dependencies/Risks** | OpenAI API availability; must handle API rate limits gracefully. |

**Core Flow:**
| Inputs | Actions | Outputs |
|--------|---------|---------|
| Meter ID, Reading Value, Date | Validate via OpenAI → Store in Supabase | Validation result + Confidence score |

---

### Feature 2: Automated Bill Calculation & Payment Link Generation

| Attribute | Description |
|-----------|-------------|
| **User Story** | As an administrator, I want the system to automatically calculate bills using tiered tariffs and generate payment links, so that customers can pay immediately. |
| **Acceptance Criteria** | Given a validated reading, when billing is triggered, then the system calculates using 4-tier pricing (₹4.5-9.0/kWh) + fixed charges and generates a Stripe payment link in INR. |
| **Priority** | P0 (Must-have) |
| **Dependencies/Risks** | Stripe API integration; currency (INR) support. |

**Tariff Structure:**
| Tier | Consumption | Rate |
|------|-------------|------|
| 1 | 0-50 kWh | ₹4.50/kWh |
| 2 | 51-100 kWh | ₹6.00/kWh |
| 3 | 101-200 kWh | ₹7.50/kWh |
| 4 | 201+ kWh | ₹9.00/kWh |

**Fixed Charges:** Motor Surcharge (₹12), Grid Maintenance (₹51/KW), Monthly Maintenance (₹246.17)

---

### Feature 3: Real-time Notifications & Payment Tracking

| Attribute | Description |
|-----------|-------------|
| **User Story** | As a customer, I want to receive my bill via WhatsApp with a payment link, so that I can pay conveniently and get confirmation. |
| **Acceptance Criteria** | Given a bill is generated, when notification is triggered, then customer receives WhatsApp message with bill details and payment link; payment status updates automatically via Stripe webhooks. |
| **Priority** | P1 (Should-have) |
| **Dependencies/Risks** | WhatsApp Business API setup; webhook endpoint availability. |

---

## 3. Requirements Overview

### Functional Requirements (Core Flows)

| Flow | Inputs | Actions | Outputs |
|------|--------|---------|---------|
| Submit Reading | Meter ID, Value, Date, Load | Auth → Validate → Calculate → Store | Bill ID, Amount, Payment Link |
| Generate Bill | Customer ID, Reading | Tariff calculation → Stripe link | Bill with payment URL |
| Process Payment | Stripe webhook event | Update status → Log event | Confirmation notification |
| Send Reminder | Bill ID, Channel | Query pending bills → Send message | Notification status |

### Integration Points
- **Supabase**: PostgreSQL database for readings, bills, notifications, payment_events
- **Stripe**: Payment link generation and webhook handling
- **OpenAI**: GPT-4 for reading validation and message generation
- **Auth0**: JWT-based authentication for API security
- **WhatsApp Business**: Customer notifications (with mock mode fallback)

### Non-Functional Requirements (MVP-Critical)

- **Performance:** API response < 2 seconds for billing operations
- **Security:** Auth0 JWT (RS256) verification on all API endpoints
- **Availability:** System handles scheduled jobs without downtime
- **Accessibility:** Role-based dashboard (Field Engineer / Administrator)

### UX Requirements

**Intended Experience:** Zero-friction meter reading submission; clear visibility into bill status and payments.

**Must-Have UX Principles:**
1. **Simplicity:** Field engineers see only what they need (Add Reading, History, Stats)
2. **Immediate Feedback:** Real-time validation results and bill generation status

---

## 4. Validation Plan

**Core Hypothesis:** Automating the meter-to-payment workflow will reduce billing cycle time by 90% while maintaining accuracy through AI validation.

**Key Assumption:** Field engineers will adopt the digital submission workflow over paper-based processes.

**Next Steps to Validate:**
- Deploy Streamlit dashboard for field engineer testing
- Track time from reading submission to payment link generation
- Monitor AI validation confidence scores and flag low-confidence readings

### Automated Tests
- `test_tariff.py` - Verify tiered tariff calculations
- `test_stripe.py` - Validate Stripe payment link generation
- `test_whatsapp.py` - Test notification delivery (mock mode)
- `test_error_handling.py` - Confirm retry logic and circuit breakers

### Manual Verification
1. Submit test reading via Streamlit dashboard
2. Verify payment link opens Stripe Checkout
3. Complete payment with test card (4242 4242 4242 4242)
4. Confirm bill status updates to "paid"

---

## 5. Critical Questions Checklist

1. **How will reading conflicts be handled?** Multiple readings for same meter on same day need resolution strategy.

2. **What is the fallback when OpenAI is unavailable?** System should proceed with warnings rather than blocking billing.

3. **How are partial payments handled?** Current design assumes full payment only.

4. **What happens to undelivered WhatsApp notifications?** Need retry mechanism or alternative channel (Discord/Email).

5. **How will tariff changes be managed?** Current rates are hardcoded; may need admin configuration.

---

## Out of Scope (Explicitly NOT in MVP)

- Multi-tenant support (single organization only)
- Customer self-service portal
- Mobile native apps (web dashboard only)
- Dispute management workflow
- Advanced analytics and forecasting
- Email notifications
- Offline reading collection
- Integration with smart meters

---

## Technical Architecture

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
│  DatabaseService │ PaymentService │ WhatsAppService         │
│  AIAgentService  │ TariffRules    │ AuthService             │
│  SchedulerService│ Neo4jService   │ DiscordService          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  External Services                           │
│  Supabase │ Stripe │ WhatsApp │ Auth0 │ OpenAI │ Neo4j     │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `readings` | Store all submitted readings with timestamps |
| `bills` | Bill records with status, amount, payment links |
| `notifications` | Log all sent notifications (WhatsApp/Discord) |
| `payment_events` | Track Stripe webhook events for audit |

---

## Scheduled Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Monthly Bills | 1st @ 2:00 AM | Generate bills for all customers |
| Payment Reminders | Daily @ 10:00 AM | Send reminders for pending bills |
| Overdue Marking | Daily @ 11:00 AM | Mark overdue bills |
| Meter Collection | Sunday @ 8:00 AM | Collect meter readings |
