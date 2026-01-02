# Electricity Billing System - Architecture Diagram

This document contains mermaid diagrams visualizing the complete architecture of the Electricity Billing Automation System.

> Current implementation note:
> - The Streamlit app (`streamlit_app.py`) is the primary UI and calls `DatabaseService` directly in **Supabase REST mode**.
> - The Flask API (`app.py`) is optional (primarily for webhooks / integrations).
> - In Supabase mode, readings live in the `readings` table (not `meter_readings`).

## System Architecture Overview

```mermaid
graph TB
    %% Client Layer
    subgraph Clients["👥 Client Layer"]
        FE[Field Engineer<br/>Mobile/Web]
        Admin[Administrator<br/>Web Dashboard]
        API_Client[API Clients<br/>External Systems]
    end

    %% Application Layer
    subgraph Apps["🚀 Application Layer"]
        Flask[Flask API Server<br/>app.py<br/>REST Endpoints]
        Streamlit[Streamlit Dashboard<br/>streamlit_app.py<br/>Admin/Field Engineer UI]
        React[React Dashboard<br/>billing-dashboard-react<br/>Modern Frontend]
    end

    %% Service Layer
    subgraph Services["⚙️ Service Layer"]
        DB_Service[DatabaseService<br/>Supabase Integration]
        AI_Service[AIAgentService<br/>OpenAI Integration]
        Payment_Service[PaymentService<br/>Stripe Integration]
        WhatsApp_Service[WhatsAppService<br/>WhatsApp Business API]
        Auth_Service[AuthService<br/>Auth0 JWT Verification]
        Scheduler_Service[SchedulerService<br/>APScheduler Jobs]
        Neo4j_Service[Neo4jService<br/>Graph Database]
        Tariff_Service[TariffRules<br/>Billing Calculations]
        Discord_Service[DiscordService<br/>Discord Notifications]
        Analytics_Service[AnalyticsService<br/>Analytics & Reports]
    end

    %% External Services
    subgraph External["🌐 External Services"]
        Supabase[(Supabase<br/>PostgreSQL Database)]
        Stripe[Stripe<br/>Payment Processing]
        OpenAI[OpenAI<br/>GPT-4 API]
        Auth0[Auth0<br/>Authentication]
        WhatsApp_API[WhatsApp Business<br/>Messaging API]
        Discord_API[Discord<br/>Webhook API]
        Neo4j[(Neo4j<br/>Graph Database<br/>Optional)]
    end

    %% Client to Application connections
    FE --> Streamlit
    Admin --> Streamlit
    Admin --> React
    API_Client --> Flask

    %% Application to Service connections
    Flask --> Auth_Service
    Flask --> DB_Service
    Flask --> AI_Service
    Flask --> Payment_Service
    Flask --> WhatsApp_Service
    Flask --> Scheduler_Service
    Flask --> Neo4j_Service
    Flask --> Discord_Service

    Streamlit --> Auth_Service
    Streamlit --> DB_Service
    Streamlit --> AI_Service
    Streamlit --> Payment_Service
    Streamlit --> Tariff_Service
    Streamlit --> Analytics_Service

    React --> Flask

    %% Service to External connections
    DB_Service --> Supabase
    AI_Service --> OpenAI
    Payment_Service --> Stripe
    WhatsApp_Service --> WhatsApp_API
    Auth_Service --> Auth0
    Neo4j_Service --> Neo4j
    Discord_Service --> Discord_API

    %% Internal service connections
    AI_Service --> Tariff_Service
    Payment_Service --> DB_Service
    Scheduler_Service --> DB_Service
    Scheduler_Service --> AI_Service
    Scheduler_Service --> Payment_Service
    Scheduler_Service --> WhatsApp_Service

    %% Webhook connections
    Stripe -.->|Webhook| Flask
    WhatsApp_API -.->|Webhook| Flask

    style Clients fill:#e1f5ff
    style Apps fill:#fff4e1
    style Services fill:#e8f5e9
    style External fill:#fce4ec
```

## Meter Reading to Bill Generation Workflow

```mermaid
sequenceDiagram
    participant FE as Field Engineer
    participant API as Flask API
    participant Auth as AuthService
    participant DB as DatabaseService
    participant AI as AIAgentService
    participant Tariff as TariffRules
    participant Payment as PaymentService
    participant WhatsApp as WhatsAppService
    participant Supabase as Supabase DB
    participant Stripe as Stripe API
    participant OpenAI as OpenAI API

    FE->>API: POST /webhook/meter-reading<br/>(with JWT token)
    API->>Auth: Verify JWT Token
    Auth->>Auth0: Validate Token
    Auth0-->>Auth: Token Valid
    Auth-->>API: Authentication Success

    API->>DB: Get Historical Readings
    DB->>Supabase: Query readings
    Supabase-->>DB: Last 10 readings
    DB-->>API: Historical Data

    API->>AI: Validate Meter Reading
    AI->>OpenAI: Analyze Reading Pattern
    OpenAI-->>AI: Validation Result
    AI-->>API: Valid/Invalid + Confidence

    alt Reading Valid
        API->>Tariff: Calculate Bill
        Tariff->>Tariff: Apply Tiered Rates
        Tariff-->>API: Bill Calculation

        API->>DB: Create Bill Record
        DB->>Supabase: Insert into bills table
        Supabase-->>DB: Bill Created
        DB-->>API: Bill ID

        API->>Payment: Create Payment Link
        Payment->>Stripe: Create Payment Link
        Stripe-->>Payment: Payment Link URL
        Payment-->>API: Payment Link

        API->>DB: Update Bill with Payment Link
        DB->>Supabase: Update bill record
        Supabase-->>DB: Updated

        API->>AI: Generate Notification Message
        AI->>OpenAI: Generate Personalized Message
        OpenAI-->>AI: Message Text
        AI-->>API: Notification Message

        API->>WhatsApp: Send Bill Notification
        WhatsApp->>WhatsApp_API: Send Message
        WhatsApp_API-->>WhatsApp: Message Sent
        WhatsApp-->>API: Success

        API->>DB: Log Notification
        DB->>Supabase: Insert into notifications
        Supabase-->>DB: Logged

        API-->>FE: Success Response<br/>(Bill ID, Payment Link, etc.)
    else Reading Invalid
        API-->>FE: Error: Invalid Reading<br/>(with reason)
    end
```

## Payment Processing Workflow

```mermaid
sequenceDiagram
    participant Customer as Customer
    participant Stripe as Stripe Checkout
    participant API as Flask API
    participant DB as DatabaseService
    participant AI as AIAgentService
    participant Discord as DiscordService
    participant Supabase as Supabase DB
    participant Discord_API as Discord Webhook

    Customer->>Stripe: Click Payment Link
    Customer->>Stripe: Complete Payment
    Stripe->>API: POST /webhook/stripe<br/>(checkout.session.completed)

    API->>API: Verify Webhook Signature
    API->>DB: Get Bill Details
    DB->>Supabase: Query bills table
    Supabase-->>DB: Bill Data
    DB-->>API: Bill Information

    API->>DB: Update Bill Status to 'paid'
    DB->>Supabase: Update bill status
    Supabase-->>DB: Updated

    API->>DB: Log Payment Event
    DB->>Supabase: Insert into payment_events
    Supabase-->>DB: Logged

    API->>AI: Generate Payment Confirmation Message
    AI->>OpenAI: Generate Thank You Message
    OpenAI-->>AI: Message Text
    AI-->>API: Confirmation Message

    API->>Discord: Send Payment Confirmation
    Discord->>Discord_API: Send Webhook
    Discord_API-->>Discord: Success
    Discord-->>API: Notification Sent

    API->>DB: Log Discord Notification
    DB->>Supabase: Insert into notifications
    Supabase-->>DB: Logged

    API-->>Stripe: 200 OK
```

## Scheduled Jobs Architecture

```mermaid
graph LR
    subgraph Scheduler["⏰ Scheduler Service"]
        Job1[Monthly Billing<br/>1st @ 2:00 AM]
        Job2[Payment Reminders<br/>Daily @ 10:00 AM]
        Job3[Overdue Marking<br/>Daily @ 11:00 AM]
        Job4[Meter Collection<br/>Sunday @ 8:00 AM]
    end

    subgraph Services["Services Used"]
        DB[DatabaseService]
        AI[AIAgentService]
        Payment[PaymentService]
        WhatsApp[WhatsAppService]
    end

    Job1 --> DB
    Job1 --> AI
    Job1 --> Payment
    Job1 --> WhatsApp

    Job2 --> DB
    Job2 --> WhatsApp

    Job3 --> DB

    Job4 --> DB
    Job4 --> AI

    style Scheduler fill:#e1f5ff
    style Services fill:#e8f5e9
```

## Database Schema Relationships

```mermaid
erDiagram
    READINGS ||--o{ BILLS : "basis_for"
    BILLS ||--o{ NOTIFICATIONS : "triggers"
    BILLS ||--o{ PAYMENT_EVENTS : "tracks"
    
    READINGS {
        int id PK
        int meter_id
        decimal reading_value
        date reading_date
        decimal consumption
        timestamp created_at
    }
    
    BILLS {
        int id PK
        int flat_id
        date billing_period_start
        date billing_period_end
        date due_date
        decimal flat_units
        decimal motor_units
        decimal total_units
        decimal total_amount
        string status
        timestamp created_at
        timestamp updated_at
    }
    
    NOTIFICATIONS {
        int id PK
        int bill_id FK
        string customer_id
        string channel
        text message
        string status
        string whatsapp_message_id
        timestamp sent_at
    }
    
    PAYMENT_EVENTS {
        int id PK
        int bill_id FK
        string event_type
        string payment_link_id
        string stripe_event_id
        jsonb event_data
        timestamp received_at
    }
```

## Component Interaction Map

```mermaid
graph TD
    subgraph Entry["Entry Points"]
        E1[Flask API<br/>Port 5000]
        E2[Streamlit<br/>Port 8501]
        E3[React App<br/>Vite Dev Server]
    end

    subgraph Core["Core Services"]
        C1[DatabaseService<br/>CRUD Operations]
        C2[AuthService<br/>JWT Verification]
        C3[SchedulerService<br/>Background Jobs]
    end

    subgraph Business["Business Logic"]
        B1[AIAgentService<br/>Validation & Messages]
        B2[TariffRules<br/>Bill Calculation]
        B3[AnalyticsService<br/>Reports & Stats]
    end

    subgraph Integration["External Integrations"]
        I1[PaymentService<br/>Stripe]
        I2[WhatsAppService<br/>Messaging]
        I3[DiscordService<br/>Notifications]
        I4[Neo4jService<br/>Graph Relations]
    end

    E1 --> C1
    E1 --> C2
    E1 --> B1
    E1 --> I1
    E1 --> I2
    E1 --> I3

    E2 --> C1
    E2 --> C2
    E2 --> B1
    E2 --> B2
    E2 --> B3

    E3 --> E1

    C3 --> C1
    C3 --> B1
    C3 --> I1
    C3 --> I2

    B1 --> B2
    I1 --> C1
    I2 --> C1
    I3 --> C1

    style Entry fill:#fff4e1
    style Core fill:#e8f5e9
    style Business fill:#e1f5ff
    style Integration fill:#fce4ec
```

## Technology Stack

```mermaid
graph TB
    subgraph Backend["Backend Stack"]
        Python[Python 3.10+]
        Flask[Flask<br/>REST API]
        Streamlit[Streamlit<br/>Dashboard]
        APScheduler[APScheduler<br/>Job Scheduling]
    end

    subgraph Frontend["Frontend Stack"]
        React[React<br/>UI Framework]
        Vite[Vite<br/>Build Tool]
        Tailwind[Tailwind CSS<br/>Styling]
    end

    subgraph Database["Database"]
        Supabase[(Supabase<br/>PostgreSQL)]
        Neo4j[(Neo4j<br/>Graph DB)]
    end

    subgraph External["External APIs"]
        Stripe_API[Stripe<br/>Payments]
        OpenAI_API[OpenAI<br/>GPT-4]
        Auth0_API[Auth0<br/>Auth]
        WhatsApp_API[WhatsApp<br/>Business]
        Discord_API[Discord<br/>Webhooks]
    end

    Python --> Flask
    Python --> Streamlit
    Python --> APScheduler
    Flask --> Supabase
    Flask --> Neo4j
    Streamlit --> Supabase
    React --> Flask
    Flask --> Stripe_API
    Flask --> OpenAI_API
    Flask --> Auth0_API
    Flask --> WhatsApp_API
    Flask --> Discord_API

    style Backend fill:#e8f5e9
    style Frontend fill:#fff4e1
    style Database fill:#e1f5ff
    style External fill:#fce4ec
```

## API Endpoints Overview

```mermaid
graph LR
    subgraph Webhooks["Webhook Endpoints"]
        W1[POST /webhook/meter-reading<br/>Process Meter Reading]
        W2[POST /webhook/stripe<br/>Payment Events]
    end

    subgraph Bills["Bill Endpoints"]
        B1[GET /api/bills/:id<br/>Get Bill Status]
        B2[GET /api/bills/customer/:id<br/>Get Customer Bills]
        B3[PUT /api/bills/:id/status<br/>Update Bill Status]
    end

    subgraph Scheduler["Scheduler Endpoints"]
        S1[GET /api/scheduler/status<br/>Get Job Status]
        S2[POST /api/scheduler/jobs/:id/run<br/>Run Job Manually]
    end

    subgraph Utility["Utility Endpoints"]
        U1[GET /health<br/>Health Check]
        U2[GET /webhook/meter-reading/test<br/>Test Endpoint]
    end

    style Webhooks fill:#e1f5ff
    style Bills fill:#e8f5e9
    style Scheduler fill:#fff4e1
    style Utility fill:#fce4ec
```

---

## Notes

- **Neo4j** is optional and used for relationship tracking
- **WhatsApp** can run in mock mode if not configured
- **Stripe webhook** signature verification can be disabled in test mode
- All services include retry logic and error handling
- Logging is handled via `utils/logger.py` with rotating file handlers
- Configuration is managed through `config.py` using environment variables



