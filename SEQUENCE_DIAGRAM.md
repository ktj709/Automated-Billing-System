# Billing System - Sequence Diagrams

This document contains ASCII sequence diagrams for the main workflows in the Electricity Billing System.

Current implementation note:
- Streamlit (`streamlit_app.py`) is the primary UI and calls Python services directly.
- Supabase is accessed via `DatabaseService` in REST mode; meter readings live in the `readings` table.
- Flask (`app.py`) is optional (webhooks/integrations); some diagrams below show the API-centric flow for those cases.

---

## 1. Meter Reading & Bill Generation Workflow (13 Steps)

This diagram shows the complete workflow from meter reading submission to bill generation and notification.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Field Engineer│    │ Streamlit UI │    │  Flask API   │    │Auth0 Service │    │Database Svc  │
│              │    │              │    │              │    │              │    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                  │                   │                   │                   │
       │ 1. Submit Meter  │                   │                   │                   │
       │    Reading       │                   │                   │                   │
       ├─────────────────>│                   │                   │                   │
       │                  │                   │                   │                   │
       │                  │ 2. POST /webhook/ │                   │                   │
       │                  │    meter-reading  │                   │                   │
       │                  ├──────────────────>│                   │                   │
       │                  │                   │                   │                   │
       │                  │                   │ 3. Verify JWT    │                   │
       │                  │                   │    Token         │                   │
       │                  │                   ├──────────────────>│                   │
       │                  │                   │                   │                   │
       │                  │                   │ 4. Token Valid   │                   │
       │                  │                   │<──────────────────┤                   │
       │                  │                   │                   │                   │
       │                  │                   │ 5. Get Historical│                   │
       │                  │                   │    Readings      │                   │
       │                  │                   ├───────────────────────────────────────>│
       │                  │                   │                   │                   │
       │                  │                   │ 6. Historical Data│                   │
       │                  │                   │<───────────────────────────────────────┤
       │                  │                   │                   │                   │
       │                  │                   │ 7. Validate Reading│                   │
       │                  │                   │    (AI Service)   │                   │
       │                  │                   ├───────────────────┐                   │
       │                  │                   │                   │                   │
┌──────┴───────┐          │                   │                   │                   │
│OpenAI API   │          │                   │                   │                   │
│             │          │                   │                   │                   │
└──────┬──────┘          │                   │                   │                   │
       │                  │                   │                   │                   │
       │ 8. Analyze       │                   │                   │                   │
       │    Historical    │                   │                   │                   │
       │    Patterns      │                   │                   │                   │
       │<─────────────────┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │ 9. Validation    │                   │                   │                   │
       │    Result        │                   │                   │                   │
       │─────────────────>┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │                  │                   │ 10. Calculate Bill│                   │
       │                  │                   │     (AI Service)  │                   │
       │                  │                   ├───────────────────┐                   │
       │                  │                   │                   │                   │
       │ 11. Calculate    │                   │                   │                   │
       │     Tariff       │                   │                   │                   │
       │<─────────────────┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │ 12. Bill Details │                   │                   │                   │
       │─────────────────>┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │                  │                   │ 13. Store Bill    │                   │
       │                  │                   │    in Database    │                   │
       │                  │                   ├───────────────────────────────────────>│
       │                  │                   │                   │                   │
       │                  │                   │ 14. Bill Created  │                   │
       │                  │                   │<───────────────────────────────────────┤
       │                  │                   │                   │                   │
       │                  │                   │ 15. Save to Neo4j │                   │
       │                  │                   ├───────────────────┐                   │
       │                  │                   │                   │                   │
┌──────┴───────┐          │                   │                   │                   │
│Neo4j Service│          │                   │                   │                   │
│             │          │                   │                   │                   │
└──────┬──────┘          │                   │                   │                   │
       │                  │                   │                   │                   │
       │ 16. Create       │                   │                   │                   │
       │     Relationship │                   │                   │                   │
       │<─────────────────┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │ 17. Relationship │                   │                   │                   │
       │     Created      │                   │                   │                   │
       │─────────────────>┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │                  │                   │ 18. Create Payment│                   │
       │                  │                   │     Link (Stripe)│                   │
       │                  │                   ├───────────────────┐                   │
       │                  │                   │                   │                   │
┌──────┴───────┐          │                   │                   │                   │
│Stripe API   │          │                   │                   │                   │
│             │          │                   │                   │                   │
└──────┬──────┘          │                   │                   │                   │
       │                  │                   │                   │                   │
       │ 19. Create       │                   │                   │                   │
       │     Payment Link │                   │                   │                   │
       │<─────────────────┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │ 20. Payment URL  │                   │                   │                   │
       │─────────────────>┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │                  │                   │ 21. Update Bill   │                   │
       │                  │                   │     with Payment  │                   │
       │                  │                   │     Link          │                   │
       │                  │                   ├───────────────────────────────────────>│
       │                  │                   │                   │                   │
       │                  │                   │ 22. Generate      │                   │
       │                  │                   │     Notification  │                   │
       │                  │                   │     Message (AI)  │                   │
       │                  │                   ├───────────────────┐                   │
       │                  │                   │                   │                   │
       │ 23. Generate     │                   │                   │                   │
       │     Message      │                   │                   │                   │
       │<─────────────────┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │ 24. Message      │                   │                   │                   │
       │─────────────────>┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │                  │                   │ 25. Send Discord  │                   │
       │                  │                   │     Notification  │                   │
       │                  │                   ├───────────────────┐                   │
       │                  │                   │                   │                   │
┌──────┴───────┐          │                   │                   │                   │
│Discord API  │          │                   │                   │                   │
│             │          │                   │                   │                   │
└──────┬──────┘          │                   │                   │                   │
       │                  │                   │                   │                   │
       │ 26. Send Message │                   │                   │                   │
       │<─────────────────┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │ 27. Message Sent │                   │                   │                   │
       │─────────────────>┼───────────────────┘                   │                   │
       │                  │                   │                   │                   │
       │                  │                   │ 28. Log           │                   │
       │                  │                   │     Notification  │                   │
       │                  │                   ├───────────────────────────────────────>│
       │                  │                   │                   │                   │
       │                  │                   │ 29. Success      │                   │
       │                  │                   │     Response     │                   │
       │                  │<──────────────────┤                   │                   │
       │                  │                   │                   │                   │
       │ 30. Display      │                   │                   │                   │
       │     Results      │                   │                   │                   │
       │<─────────────────┤                   │                   │                   │
       │                  │                   │                   │                   │
```

---

## 2. Payment Processing Workflow (Stripe Webhook)

This diagram shows how payments are processed when a customer completes payment via Stripe.

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Customer │    │  Stripe  │    │Flask API │    │Database  │    │OpenAI API│    │Discord   │
│          │    │          │    │          │    │ Service  │    │          │    │  API     │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │              │                │              │              │              │
     │ 1. Click     │                │              │              │              │
     │    Payment   │                │              │              │              │
     │    Link      │                │              │              │              │
     ├─────────────>│                │              │              │              │
     │              │                │              │              │              │
     │              │ 2. Redirect to │              │              │              │
     │              │    Checkout    │              │              │              │
     │<─────────────┤                │              │              │              │
     │              │                │              │              │              │
     │ 3. Complete  │                │              │              │              │
     │    Payment   │                │              │              │              │
     ├─────────────>│                │              │              │              │
     │              │                │              │              │              │
     │              │ 4. Payment     │              │              │              │
     │              │    Successful  │              │              │              │
     │              │                │              │              │              │
     │              │ 5. Webhook:    │              │              │              │
     │              │    checkout.   │              │              │              │
     │              │    session.    │              │              │              │
     │              │    completed   │              │              │              │
     │              ├───────────────>│              │              │              │
     │              │                │              │              │              │
     │              │                │ 6. Verify    │              │              │
     │              │                │    Signature │              │              │
     │              │                │              │              │              │
     │              │                │ 7. Extract   │              │              │
     │              │                │    Bill ID   │              │              │
     │              │                │    & Amount  │              │              │
     │              │                │              │              │              │
     │              │                │ 8. Update    │              │              │
     │              │                │    Bill     │              │
     │              │                │    Status    │              │
     │              │                ├─────────────>│              │              │
     │              │                │              │              │              │
     │              │                │ 9. Bill      │              │              │
     │              │                │    Updated  │              │              │
     │              │                │<─────────────┤              │              │
     │              │                │              │              │              │
     │              │                │ 10. Log      │              │              │
     │              │                │     Payment  │              │              │
     │              │                │     Event    │              │              │
     │              │                ├─────────────>│              │              │
     │              │                │              │              │              │
     │              │                │ 11. Generate│              │              │
     │              │                │     Thank    │              │              │
     │              │                │     You Msg  │              │              │
     │              │                ├────────────────────────────>│              │
     │              │                │              │              │              │
     │              │                │ 12. Message  │              │              │
     │              │                │     Generated│              │              │
     │              │                │<────────────────────────────┤              │
     │              │                │              │              │              │
     │              │                │ 13. Send     │              │              │
     │              │                │     Discord  │              │              │
     │              │                │     Confirmation│            │              │
     │              │                ├────────────────────────────────────────────>│
     │              │                │              │              │              │
     │              │                │ 14. Message  │              │              │
     │              │                │     Sent     │              │              │
     │              │                │<────────────────────────────────────────────┤
     │              │                │              │              │              │
     │              │                │ 15. Log      │              │              │
     │              │                │     Notification│           │              │
     │              │                ├─────────────>│              │              │
     │              │                │              │              │              │
     │              │                │ 16. Webhook  │              │              │
     │              │                │     Acknowledged│           │              │
     │              │<───────────────┤              │              │              │
     │              │                │              │              │              │
```

---

## 3. Scheduled Jobs Workflow

This diagram shows how automated scheduled jobs work in the system.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│APScheduler   │    │Billing       │    │Database      │    │AI Agent      │    │Discord       │
│              │    │Scheduler     │    │Service       │    │Service       │    │Service       │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │                   │
       │ 1. Trigger:       │                   │                   │                   │
       │    1st @ 2:00 AM  │                   │                   │                   │
       │    (Monthly Bills)│                   │                   │                   │
       ├──────────────────>│                   │                   │                   │
       │                   │                   │                   │                   │
       │                   │ 2. Get Active     │                   │                   │
       │                   │    Meters         │                   │                   │
       │                   ├──────────────────>│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 3. Active Meters  │                   │                   │
       │                   │<──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │                   │ 4. For Each Meter:│                   │                   │
       │                   │    Get Readings   │                   │                   │
       │                   ├──────────────────>│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 5. Readings       │                   │                   │
       │                   │<──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │                   │ 6. Calculate Bill │                   │                   │
       │                   ├───────────────────────────────────────>│                   │
       │                   │                   │                   │                   │
       │                   │ 7. Bill Calculated │                   │                   │
       │                   │<───────────────────────────────────────┤                   │
       │                   │                   │                   │                   │
       │                   │ 8. Create Bill    │                   │                   │
       │                   │    in Database    │                   │                   │
       │                   ├──────────────────>│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 9. Bill Created   │                   │                   │
       │                   │<──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │                   │ 10. Send          │                   │                   │
       │                   │     Notification  │                   │                   │
       │                   ├──────────────────────────────────────────────────────────>│
       │                   │                   │                   │                   │
       │                   │ 11. Notification  │                   │                   │
       │                   │     Sent          │                   │                   │
       │                   │<──────────────────────────────────────────────────────────┤
       │                   │                   │                   │                   │
       │                   │                   │                   │                   │
       │ 12. Trigger:      │                   │                   │                   │
       │    Daily @ 10 AM │                   │                   │                   │
       │    (Reminders)    │                   │                   │                   │
       ├──────────────────>│                   │                   │                   │
       │                   │                   │                   │                   │
       │                   │ 13. Get Bills Due │                   │                   │
       │                   │     in 3 Days     │                   │                   │
       │                   ├──────────────────>│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 14. Upcoming Bills │                   │                   │
       │                   │<──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │                   │ 15. For Each Bill:│                   │                   │
       │                   │     Generate      │                   │                   │
       │                   │     Reminder      │                   │                   │
       │                   ├───────────────────────────────────────>│                   │
       │                   │                   │                   │                   │
       │                   │ 16. Reminder Msg  │                   │                   │
       │                   │<───────────────────────────────────────┤                   │
       │                   │                   │                   │                   │
       │                   │ 17. Send Discord  │                   │                   │
       │                   │     Reminder     │                   │                   │
       │                   ├──────────────────────────────────────────────────────────>│
       │                   │                   │                   │                   │
       │                   │ 18. Reminder Sent │                   │                   │
       │                   │<──────────────────────────────────────────────────────────┤
       │                   │                   │                   │                   │
       │                   │                   │                   │                   │
       │ 19. Trigger:      │                   │                   │                   │
       │    Daily @ 11 AM │                   │                   │                   │
       │    (Overdue)      │                   │                   │                   │
       ├──────────────────>│                   │                   │                   │
       │                   │                   │                   │                   │
       │                   │ 20. Get Overdue   │                   │                   │
       │                   │     Bills         │                   │                   │
       │                   ├──────────────────>│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 21. Overdue Bills │                   │                   │
       │                   │<──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │                   │ 22. Mark as       │                   │                   │
       │                   │     Overdue      │                   │                   │
       │                   ├──────────────────>│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 23. Send Overdue  │                   │                   │
       │                   │     Notice        │                   │                   │
       │                   ├──────────────────────────────────────────────────────────>│
       │                   │                   │                   │                   │
       │                   │ 24. Notice Sent   │                   │                   │
       │                   │<──────────────────────────────────────────────────────────┤
       │                   │                   │                   │                   │
       │                   │                   │                   │                   │
       │ 25. Trigger:      │                   │                   │                   │
       │    Sunday @ 8 AM │                   │                   │                   │
       │    (Meter Read)   │                   │                   │                   │
       ├──────────────────>│                   │                   │                   │
       │                   │                   │                   │                   │
       │                   │ 26. Get Smart     │                   │                   │
       │                   │     Meters        │                   │                   │
       │                   ├──────────────────>│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 27. Smart Meters   │                   │                   │
       │                   │<──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │                   │ 28. For Each Meter:│                   │                   │
       │                   │     Collect       │                   │                   │
       │                   │     Reading       │                   │                   │
       │                   │     (API Call)    │                   │                   │
       │                   │                   │                   │                   │
       │                   │ 29. Store Reading │                   │                   │
       │                   │     in Database   │                   │                   │
       │                   ├──────────────────>│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 30. Reading Stored│                   │                   │
       │                   │<──────────────────┤                   │                   │
       │                   │                   │                   │                   │
```

---

## 4. User Authentication Flow (Auth0)

This diagram shows how users authenticate via Auth0 JWT tokens.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Administrator │    │ Streamlit UI │    │Auth Service  │    │  Auth0 API   │
│              │    │              │    │              │    │              │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │ 1. Enter User ID  │                   │                   │
       │    & JWT Token    │                   │                   │
       ├──────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │ 2. Submit Login   │                   │
       │                   │    Form           │                   │
       │                   │                   │                   │
       │                   │ 3. Verify Token   │                   │
       │                   ├──────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │ 4. Validate JWT │
       │                   │                   │    Token          │
       │                   │                   ├──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 5. Token Valid   │
       │                   │                   │    (Payload)     │
       │                   │                   │<──────────────────┤
       │                   │                   │                   │
       │                   │ 6. Authentication│                   │
       │                   │    Successful     │                   │
       │                   │<──────────────────┤                   │
       │                   │                   │                   │
       │ 7. Access Admin   │                   │                   │
       │    Dashboard      │                   │                   │
       │<─────────────────┤                   │                   │
       │                   │                   │                   │
       │                   │                   │                   │
       │                   │                   │                   │
       │ 8. API Request    │                   │                   │
       │    with JWT       │                   │                   │
       │    (Bearer Token)│                   │                   │
       ├──────────────────┼───────────────────┐                   │
       │                   │                   │                   │
       │                   │ 9. Extract Token  │                   │
       │                   │    from Header    │                   │
       │                   │                   │                   │
       │                   │ 10. Verify Token  │                   │
       │                   │      (Header Auth │                   │
       │                   │       or Auth0)   │                   │
       │                   ├──────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │ 11. Validate JWT │
       │                   │                   │     Token        │
       │                   │                   ├──────────────────>│
       │                   │                   │                   │
       │                   │                   │ 12. Token Valid  │
       │                   │                   │<──────────────────┤
       │                   │                   │                   │
       │                   │ 13. Authorized    │                   │
       │                   │<──────────────────┤                   │
       │                   │                   │                   │
       │ 14. Process       │                   │                   │
       │     Request       │                   │                   │
       │<─────────────────┼───────────────────┘                   │
       │                   │                   │                   │
```

---

## 5. Complete System Architecture Overview

This diagram shows the high-level interaction between all major components.

```
┌──────────────┐
│   User       │
│ (Engineer/   │
│  Admin)     │
└──────┬───────┘
       │
       │ 1. Access Dashboard
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Role         │  │ Field        │  │ Admin        │     │
│  │ Selection    │  │ Engineer     │  │ Dashboard    │     │
│  │              │  │ Dashboard    │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
       │
       │ 2. API Calls / Webhooks
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Flask API Server                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Endpoints:                                           │  │
│  │  - POST /webhook/meter-reading                       │  │
│  │  - POST /webhook/stripe                              │  │
│  │  - GET  /api/bills/<id>                              │  │
│  │  - GET  /api/bills/customer/<id>                     │  │
│  │  - GET  /api/scheduler/status                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
       │
       │ 3. Service Layer
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Database     │  │ AI Agent    │  │ Payment      │      │
│  │ Service      │  │ Service     │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Discord      │  │ WhatsApp    │  │ Auth         │      │
│  │ Service      │  │ Service     │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Neo4j        │  │ Scheduler    │                        │
│  │ Service      │  │ Service     │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
       │
       │ 4. External Services / Data Stores
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              External Services & Data Stores                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Supabase     │  │ Neo4j       │  │ Stripe      │      │
│  │ (PostgreSQL) │  │ (Graph DB)  │  │ (Payments)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ OpenAI API   │  │ Auth0       │  │ Discord      │      │
│  │ (AI/ML)      │  │ (Auth)      │  │ (Notifs)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                          │
│  │ WhatsApp     │                                          │
│  │ Business API │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
       │
       │ 5. Scheduled Jobs (Background)
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    APScheduler                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Scheduled Jobs:                                      │  │
│  │  - Monthly Bill Generation (1st @ 2:00 AM)           │  │
│  │  - Payment Reminders (Daily @ 10:00 AM)              │  │
│  │  - Overdue Marking (Daily @ 11:00 AM)                │  │
│  │  - Meter Reading Collection (Sunday @ 8:00 AM)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Legend

- **Solid Arrow (───>)** : Synchronous request/response
- **Dashed Arrow (- - ->)** : Asynchronous event/webhook
- **Activation Box (┌─┐)** : Active processing period
- **Note**: All interactions are numbered sequentially within each diagram

## Key Components

1. **Streamlit Dashboard** (`streamlit_app.py`): User interface for field engineers and administrators
2. **Flask API** (`app.py`): REST API server handling webhooks and API requests
3. **Database Service**: Manages Supabase PostgreSQL operations
4. **Neo4j Service**: Handles graph database relationships
5. **AI Agent Service**: OpenAI GPT-4 integration for validation and calculations
6. **Payment Service**: Stripe integration for payment processing
7. **Discord Service**: Discord webhook notifications
8. **WhatsApp Service**: WhatsApp Business API integration
9. **Auth Service**: Auth0 JWT token verification
10. **Scheduler Service**: APScheduler for automated jobs

## Workflow Summary

### Meter Reading & Bill Generation (13 Steps)
1. Field Engineer submits meter reading
2. Flask API receives webhook
3. Auth0 token verification
4. Get historical readings from database
5. AI validates reading (OpenAI)
6. AI calculates bill (OpenAI)
7. Store bill in database
8. Save to Neo4j graph
9. Create Stripe payment link
10. Update bill with payment info
11. Generate notification message (AI)
12. Send Discord notification
13. Log notification

### Payment Processing
1. Customer clicks payment link
2. Completes payment on Stripe
3. Stripe sends webhook to Flask API
4. API verifies signature
5. Updates bill status to "paid"
6. Logs payment event
7. Generates thank you message (AI)
8. Sends Discord confirmation
9. Logs notification

### Scheduled Jobs
- **Monthly Bills**: Generates bills for all active meters on 1st of month at 2:00 AM
- **Payment Reminders**: Sends reminders for bills due in 3 days (Daily @ 10:00 AM)
- **Overdue Marking**: Marks bills as overdue (Daily @ 11:00 AM)
- **Meter Collection**: Collects readings from smart meters (Sunday @ 8:00 AM)



