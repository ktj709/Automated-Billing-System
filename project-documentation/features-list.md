# Electricity Billing Automation System - Features List

> Status note: this is a product/UX backlog document and may describe features that are not implemented.
> For the current working system (Streamlit-first + Supabase REST), use the repo root `README.md` as the source of truth.

---

## Features List

### Meter Reading Operations

#### Submit Meter Reading

- [ ] **User Stories**
  * As a Field Engineer, I want to select a flat from a dropdown, so that I can quickly identify the correct meter without manual entry.
  * As a Field Engineer, I want to enter only the reading value and see auto-calculated consumption, so that I can verify accuracy before submission.
  * As an Administrator, I want submitted readings to be AI-validated, so that anomalies are flagged before bill generation.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Full-screen form with prominent reading input field
  * Auto-populated flat details (Unit ID, Client Name, Meter ID) on selection
  * Real-time consumption calculation displayed below reading input
  * Single "Submit" CTA with loading state during AI validation

- [ ] **Screen States**
  * **Empty State**: Flat dropdown focused, reading field disabled until flat selected
  * **Ready State**: Flat selected, reading field enabled, previous reading shown for reference
  * **Loading State**: Skeleton loader on validation, submit button disabled with spinner
  * **Success State**: Green checkmark animation, reading summary card appears
  * **Error State**: Red border on invalid field, inline error message, retry option

- [ ] **State Changes (Visual)**
  * Flat selection → smooth slide-in of flat details card (200ms ease-out)
  * Reading input → real-time consumption update with subtle number counter animation
  * Submit → button morphs to spinner → expands to success/error feedback

- [ ] **Animations & Visual Hierarchy**
  * Primary focus: Reading input field (largest, centered)
  * Secondary: Flat selection dropdown (top, full-width)
  * Tertiary: Consumption preview, previous reading reference (smaller, muted colors)
  * Micro-animation: Input field border glow on focus (blue pulse)
  * Success: Confetti burst for monthly reading milestones

- [ ] **Advanced Users & Edge Cases**
  * Keyboard shortcut: Tab through fields, Enter to submit
  * Offline mode: Queue readings locally with sync indicator
  * Duplicate reading: Warning modal with "Replace" or "Cancel" options
  * High consumption alert: Yellow warning before submission if >200% of average

---

#### View Reading History

- [ ] **User Stories**
  * As a Field Engineer, I want to view my submitted readings for this month, so that I can track my progress toward the target.
  * As an Administrator, I want to filter readings by date range and meter, so that I can audit specific periods.
  * As an Administrator, I want to download reading history as CSV, so that I can perform offline analysis.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Scrollable list with reading cards showing date, value, consumption, status
  * Progress bar at top showing monthly reading count vs target (200 readings/month)
  * Filter chips for quick date range selection (Today, This Week, This Month)
  * CSV export button with date range picker

- [ ] **Screen States**
  * **Loading State**: Skeleton cards with shimmer animation
  * **Empty State**: Illustration with "No readings yet" message and CTA to add first reading
  * **Data State**: Paginated list with infinite scroll
  * **Filtered State**: Active filter chips highlighted, clear-all option visible

- [ ] **State Changes (Visual)**
  * Filter chip tap → instant list update with fade transition (150ms)
  * Scroll → header collapses to compact mode, progress bar remains sticky
  * Pull-to-refresh → bounce animation with refresh indicator

- [ ] **Animations & Visual Hierarchy**
  * Primary: Reading value (large, bold)
  * Secondary: Date and consumption (medium, regular weight)
  * Tertiary: Meter ID, status badge (small, muted)
  * List entry animation: Cards slide up sequentially (50ms stagger)

- [ ] **Advanced Users & Edge Cases**
  * Export to CSV: Date range picker with download confirmation
  * Edit reading: Inline edit mode with save/cancel options
  * Delete reading: Confirmation dialog with reason field
  * No network: Cached data with "Last updated" timestamp

---

#### Update/Delete Meter Reading

- [ ] **User Stories**
  * As an Administrator, I want to update an incorrect reading, so that billing calculations remain accurate.
  * As an Administrator, I want to delete a duplicate reading, so that the meter history is clean.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Edit button on each reading card opens inline edit mode
  * Delete requires confirmation with audit trail entry
  * Changes logged with timestamp and user ID

- [ ] **Screen States**
  * **View Mode**: Reading displayed with Edit/Delete action buttons
  * **Edit Mode**: Inline form replaces card content, Save/Cancel buttons
  * **Confirm Delete**: Modal overlay with warning message and reason field
  * **Processing**: Skeleton overlay during API call

- [ ] **State Changes (Visual)**
  * Edit tap → card expands, fields become editable
  * Delete tap → modal slides up from bottom
  * Save → inline success indicator, card updates

- [ ] **Animations & Visual Hierarchy**
  * Edit mode: Blue border around card, fields animate in
  * Delete modal: Red accent color, prominent warning
  * Success: Green flash on saved row

- [ ] **Advanced Users & Edge Cases**
  * Undo delete: Available for 30 seconds post-deletion
  * Concurrent edit: Conflict detection with "Refresh" prompt
  * Audit log: All changes tracked in database

---

### Billing Operations

#### Generate Bill (Manual)

- [ ] **User Stories**
  * As an Administrator, I want to generate a bill from the latest reading, so that I can send the payment link to the customer.
  * As an Administrator, I want to see the tariff breakdown before confirming, so that I can explain charges if questioned.
  * As an Administrator, I want to adjust connected load before billing, so that fixed charges are calculated correctly.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Two-step wizard: Select Customer → Review & Generate
  * Tariff breakdown displayed as visual bar chart showing tier contributions
  * Editable connected load field with recalculate button
  * One-click payment link generation with copy-to-clipboard

- [ ] **Screen States**
  * **Step 1 - Select**: Customer search with autocomplete, recent customers shown
  * **Step 2 - Review**: Bill preview card with itemized charges, editable connected load
  * **Generating State**: Progress indicator with "Creating Stripe link..." message
  * **Complete State**: Bill summary with prominent "Copy Payment Link" button

- [ ] **State Changes (Visual)**
  * Step transition → horizontal slide with progress indicator dots
  * Tariff calculation → animated number counters for each tier amount
  * Link generated → button transforms green with checkmark

- [ ] **Animations & Visual Hierarchy**
  * Primary: Total Amount (extra large, accent color)
  * Secondary: Consumption, Period dates (medium)
  * Tertiary: Individual tier charges, fixed charges (small, table format)
  * Chart animation: Bars grow from zero on render (400ms ease-out)

- [ ] **Advanced Users & Edge Cases**
  * Keyboard: / to open customer search
  * Override mode: Admin can adjust consumption manually with audit log
  * Zero consumption: Warning with option to skip billing period
  * API failure: Retry button with error message, manual link input fallback

---

#### Tariff Calculator

- [ ] **User Stories**
  * As an Administrator, I want to preview bill calculations without creating a bill, so that I can answer customer inquiries.
  * As an Administrator, I want to compare residential vs commercial tariffs, so that I can verify correct tariff assignment.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Interactive calculator with consumption slider
  * Real-time tier breakdown display
  * Toggle between residential/commercial tariffs
  * Full bill preview with all charge categories

- [ ] **Screen States**
  * **Input State**: Clean form with consumption, load, tariff type inputs
  * **Calculated State**: Expandable sections showing energy charges, fixed charges, taxes
  * **Compare State**: Side-by-side residential vs commercial view

- [ ] **State Changes (Visual)**
  * Slider drag → instant recalculation with number animation
  * Tariff toggle → smooth crossfade between rate cards
  * Expand section → accordion animation with content reveal

- [ ] **Animations & Visual Hierarchy**
  * Primary: Amount Payable (largest, highlighted)
  * Secondary: Energy Charges, Fixed Charges subtotals
  * Tertiary: Individual tier breakdowns, per-unit rates

- [ ] **Advanced Users & Edge Cases**
  * Previous outstanding: Add to calculation with separate line item
  * Export calculation: PDF with full breakdown for customer reference

---

#### View All Bills

- [ ] **User Stories**
  * As an Administrator, I want to see all bills with their status, so that I can track collection progress.
  * As an Administrator, I want to filter bills by status (pending, paid, overdue), so that I can prioritize actions.
  * As an Administrator, I want to view bills by customer, so that I can handle customer inquiries.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Tabular view with sortable columns (Date, Customer, Amount, Status)
  * Status filter tabs: All, Pending, Paid, Overdue
  * Quick actions: View Details, Copy Payment Link, Send Reminder

- [ ] **Screen States**
  * **Loading State**: Table skeleton with column headers
  * **Data State**: Paginated table with status badges
  * **Filtered State**: Active filter highlighted, row count indicator
  * **Empty State**: "No bills match filter" with clear filter option

- [ ] **State Changes (Visual)**
  * Filter tab click → table rows fade and repopulate
  * Sort header click → column header arrow rotates, rows reorder
  * Row hover → action buttons reveal with fade-in

- [ ] **Animations & Visual Hierarchy**
  * Status badges: Color-coded (green=paid, yellow=pending, red=overdue)
  * Amount column: Right-aligned, monospace font
  * Row actions: Icon buttons with tooltips

- [ ] **Advanced Users & Edge Cases**
  * Bulk selection: Checkbox column for multi-select operations
  * Date range filter: Calendar picker with presets
  * Customer link: Click customer name to view all their bills

---

#### Track Payment Status

- [ ] **User Stories**
  * As an Administrator, I want to see all pending bills at a glance, so that I can prioritize follow-ups.
  * As an Administrator, I want to receive real-time updates when payments complete, so that I can confirm to customers immediately.
  * As an Administrator, I want to simulate payment webhooks for testing, so that I can verify the payment flow.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Dashboard with KPI cards: Total Outstanding, Paid This Month, Overdue Count
  * Filterable table with status badges (Pending, Paid, Overdue)
  * Quick actions: Send Reminder, View Details, Mark as Paid
  * Webhook simulator panel for testing

- [ ] **Screen States**
  * **Loading State**: KPI cards show skeleton, table rows shimmer
  * **Data State**: Cards populated, table sorted by due date (soonest first)
  * **Real-time Update**: Toast notification slides in when webhook received
  * **Empty State**: "All caught up!" message with celebration illustration

- [ ] **State Changes (Visual)**
  * Status update → row background briefly flashes green, badge animates to new state
  * Filter applied → table rows fade and reorder (200ms)
  * Webhook received → bell icon pulses, toast slides from top-right

- [ ] **Animations & Visual Hierarchy**
  * Primary: Outstanding amount KPI (largest card, red accent if overdue exist)
  * Secondary: Paid amount, collection rate (medium cards, green/blue)
  * Tertiary: Table data (standard row height, hover highlight)
  * Status badges: Color-coded with subtle pulse for overdue

- [ ] **Advanced Users & Edge Cases**
  * Bulk reminder: Select multiple → "Send Reminder to Selected" action
  * Manual status update: Override with confirmation modal
  * Webhook logs: Expandable section showing recent payment events
  * Simulate webhook: Test panel with bill ID input and event type selector

---

### Stripe Payment Integration

#### Create Payment Link

- [ ] **User Stories**
  * As the System, I want to automatically generate Stripe payment links for new bills, so that customers can pay instantly.
  * As an Administrator, I want payment links to include bill metadata, so that webhooks can update the correct bill.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Automatic generation during bill creation workflow
  * Payment link displayed with copy button
  * Link expiration indicator
  * QR code option for in-person payments

- [ ] **Screen States**
  * **Generating State**: Spinner with "Creating payment link..." text
  * **Generated State**: Link URL with copy button, QR code thumbnail
  * **Error State**: Retry button with error details
  * **Expired State**: Warning badge with regenerate option

- [ ] **State Changes (Visual)**
  * Generate → spinner transitions to link card
  * Copy click → button text changes to "Copied!" briefly
  * QR expand → modal with large scannable code

- [ ] **Animations & Visual Hierarchy**
  * Primary: Payment amount in Stripe checkout preview
  * Secondary: Copy to clipboard CTA
  * Tertiary: QR code, expiration info

- [ ] **Advanced Users & Edge Cases**
  * Stripe test mode: Banner indicating test environment
  * Currency: INR displayed with ₹ symbol
  * Link metadata: bill_id included for webhook matching

---

#### Process Payment Webhook

- [ ] **User Stories**
  * As the System, I want to automatically update bill status when Stripe confirms payment, so that records stay synchronized.
  * As an Administrator, I want payment events logged for audit purposes, so that I can investigate discrepancies.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Automatic webhook processing (no UI required)
  * Real-time dashboard update on successful payment
  * Payment event log in admin panel

- [ ] **Screen States**
  * **Webhook Received**: Toast notification with bill ID and amount
  * **Processing**: Brief loading state in event log
  * **Success**: Bill status updates, event logged with green checkmark
  * **Error**: Error logged with retry mechanism

- [ ] **State Changes (Visual)**
  * Payment received → toast slides in from top-right
  * Bill row → status badge animates to "Paid" with green flash
  * Event log → new row prepends with highlight

- [ ] **Animations & Visual Hierarchy**
  * Toast: Prominent but not blocking, auto-dismiss after 5s
  * Event log: Newest first, timestamp, event type, bill reference

- [ ] **Advanced Users & Edge Cases**
  * Signature verification: Validate Stripe webhook signature if secret configured
  * Duplicate events: Idempotent processing prevents double-updates
  * Failed updates: Queue for retry with exponential backoff

---

### Notifications

#### Send Bill Notification (WhatsApp)

- [ ] **User Stories**
  * As the System, I want to automatically send WhatsApp notifications when bills are generated, so that customers receive payment links without manual intervention.
  * As an Administrator, I want to preview the notification message before sending, so that I can ensure accuracy.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Automatic send after bill generation with opt-out toggle
  * Message preview showing WhatsApp bubble mockup
  * Delivery status indicator (Sent, Delivered, Read, Failed)

- [ ] **Screen States**
  * **Composing State**: Editable message template with variable placeholders highlighted
  * **Sending State**: Progress indicator with "Sending via WhatsApp..." text
  * **Sent State**: Green checkmark with timestamp
  * **Failed State**: Red X with retry button and error reason

- [ ] **State Changes (Visual)**
  * Send tap → button shrinks to spinner → expands to status
  * Delivery status → checkmarks animate in sequence (single → double → blue)
  * Retry → button shakes briefly before enabling

- [ ] **Animations & Visual Hierarchy**
  * Primary: Customer name and amount in message preview (bold)
  * Secondary: Payment link (blue, underlined)
  * Tertiary: Billing period, meter details (regular weight)
  * Mock device frame: Subtle shadow and border radius matching WhatsApp UI

- [ ] **Advanced Users & Edge Cases**
  * Mock mode: Banner indicating "WhatsApp not configured - messages logged only"
  * Invalid phone: Warn before sending, suggest customer data update
  * Rate limiting: Queue subsequent messages with countdown timer
  * Message template: AI-generated text with due date and account reference

---

#### Send Payment Confirmation (Discord)

- [ ] **User Stories**
  * As the System, I want to send Discord notifications when payments are received, so that administrators are informed in real-time.
  * As an Administrator, I want payment confirmations to include bill details, so that I can verify the transaction.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Automatic Discord webhook on payment completion
  * Rich embed with bill details, customer info, payment amount
  * Channel configuration in settings

- [ ] **Screen States**
  * **Queued State**: Notification pending in outgoing queue
  * **Sent State**: Green indicator with Discord message ID
  * **Failed State**: Red indicator with retry option

- [ ] **State Changes (Visual)**
  * Payment confirmed → Discord notification auto-triggers
  * Delivery success → log entry with checkmark

- [ ] **Animations & Visual Hierarchy**
  * Discord embed: Rich card with color accent, bold amount
  * Log entry: Timestamp, channel, message preview

- [ ] **Advanced Users & Edge Cases**
  * User mentions: Tag specific users for high-value payments
  * Fallback: Log to console if Discord not configured
  * Rate limiting: Batch multiple notifications if needed

---

#### Send Payment Reminders

- [ ] **User Stories**
  * As the System, I want to automatically send reminders for bills due within 3 days, so that customers pay on time.
  * As an Administrator, I want to manually trigger reminders for specific bills, so that I can follow up individually.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Automatic daily reminder job at 10:00 AM
  * Manual reminder button on each pending bill
  * Reminder history showing previous attempts

- [ ] **Screen States**
  * **Scheduled State**: Next reminder time displayed
  * **Sending State**: Progress indicator with count
  * **Complete State**: Summary of reminders sent
  * **Failed State**: List of failed deliveries with retry

- [ ] **State Changes (Visual)**
  * Job trigger → progress bar with bill count
  * Individual send → bill row shows "Reminder sent" badge

- [ ] **Animations & Visual Hierarchy**
  * Reminder badge: Orange color, timestamp
  * Bulk progress: Animated counter

- [ ] **Advanced Users & Edge Cases**
  * Do not disturb: Skip customers who paid after reminder was queued
  * Escalation: Second reminder before due date
  * Channel preference: WhatsApp first, Discord fallback

---

### Analytics & Reporting

#### Monthly Revenue Report

- [ ] **User Stories**
  * As an Administrator, I want to view monthly revenue totals, so that I can track financial performance.
  * As an Administrator, I want to see paid vs pending amounts, so that I can forecast cash flow.

##### UX/UI Considerations

- [ ] **Core Experience**
  * KPI cards: Total Revenue, Collected, Outstanding
  * Month picker for historical comparison
  * Breakdown by payment status

- [ ] **Screen States**
  * **Loading State**: Skeleton KPIs and chart placeholders
  * **Data State**: Populated cards with trend indicators
  * **Empty State**: "No data for selected period"

- [ ] **State Changes (Visual)**
  * Month change → cards fade and update
  * Trend arrows: Green up, red down

- [ ] **Animations & Visual Hierarchy**
  * Primary: Total Revenue (largest card)
  * Secondary: Collected, Outstanding (side-by-side)
  * Tertiary: Trend percentage

- [ ] **Advanced Users & Edge Cases**
  * Export: PDF/Excel report download
  * Year-over-year comparison

---

#### Consumption Analytics

- [ ] **User Stories**
  * As an Administrator, I want to see average consumption per customer, so that I can identify usage patterns.
  * As an Administrator, I want to flag high-consumption customers, so that I can offer efficiency advice.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Consumption distribution chart
  * Top consumers list
  * Customer-level drill-down

- [ ] **Screen States**
  * **Overview State**: Aggregate metrics and distribution
  * **Detail State**: Individual customer consumption history
  * **Comparison State**: Side-by-side customer comparison

- [ ] **State Changes (Visual)**
  * Chart interaction → tooltip with values
  * Customer click → expand to detail panel

- [ ] **Animations & Visual Hierarchy**
  * Chart bars: Animated on render
  * Top consumers: Ranked list with usage indicators

- [ ] **Advanced Users & Edge Cases**
  * Anomaly detection: AI-flagged unusual patterns
  * Export data: CSV download

---

#### Payment Success Rate

- [ ] **User Stories**
  * As an Administrator, I want to see collection rate over time, so that I can assess billing effectiveness.
  * As an Administrator, I want to identify late payers, so that I can adjust payment terms.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Success rate percentage prominently displayed
  * Trend chart over 30/60/90 days
  * Late payment list with days overdue

- [ ] **Screen States**
  * **Good State**: Green indicator if rate > 80%
  * **Warning State**: Yellow if rate 60-80%
  * **Alert State**: Red if rate < 60%

- [ ] **State Changes (Visual)**
  * Period toggle → chart updates with animation
  * Rate change → percentage counter animates

- [ ] **Animations & Visual Hierarchy**
  * Primary: Success rate percentage (large, color-coded)
  * Secondary: Trend chart
  * Tertiary: Individual late payer details

- [ ] **Advanced Users & Edge Cases**
  * Segmentation by customer type
  * Payment timing analysis

---

#### Customer Segmentation

- [ ] **User Stories**
  * As an Administrator, I want customers grouped by consumption and payment behavior, so that I can tailor communication.
  * As an Administrator, I want to identify VIP customers (high consumption, timely payment), so that I can prioritize their service.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Segment cards: High Consumers, Regular Payers, At-Risk
  * Customer list per segment
  * Segment transition alerts

- [ ] **Screen States**
  * **Overview State**: Segment summary cards
  * **Detail State**: Customer list for selected segment
  * **Comparison State**: Segment trends over time

- [ ] **State Changes (Visual)**
  * Segment click → expand to customer list
  * Segment badge → tooltip with criteria

- [ ] **Animations & Visual Hierarchy**
  * Segment cards: Color-coded (green=good, yellow=medium, red=at-risk)
  * Customer count: Badge on each segment

- [ ] **Advanced Users & Edge Cases**
  * Move customer: Manual segment override
  * Alert: Notify when customer moves to at-risk

---

### Scheduled Automation

#### Monthly Bill Generation

- [ ] **User Stories**
  * As the System, I want to automatically generate bills on the 1st of each month at 2:00 AM, so that billing is consistent.
  * As an Administrator, I want to see scheduled job status, so that I can verify automation is running.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Job card showing: Schedule, Next Run, Last Run, Status
  * Automatic execution on schedule
  * Manual trigger option for testing

- [ ] **Screen States**
  * **Idle State**: Next run countdown displayed
  * **Running State**: Progress bar with meter count
  * **Complete State**: Summary of bills generated
  * **Error State**: Error details with partial success count

- [ ] **State Changes (Visual)**
  * Midnight trigger → job card updates to "Running"
  * Completion → green checkmark, last run timestamp updates

- [ ] **Animations & Visual Hierarchy**
  * Countdown timer: Large, updating in real-time
  * Progress: Bar with percentage and meter name

- [ ] **Advanced Users & Edge Cases**
  * Skip month: Admin can disable upcoming run
  * Retry failed: Re-run for specific meters that failed

---

#### Payment Reminder Job

- [ ] **User Stories**
  * As the System, I want to send payment reminders daily at 10:00 AM for bills due within 3 days, so that customers are prompted to pay.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Daily scheduled execution
  * Filters pending bills with due date within 3 days
  * Sends WhatsApp reminders to each customer

- [ ] **Screen States**
  * **Scheduled State**: Next run time
  * **Running State**: Sending reminders count
  * **Complete State**: Reminders sent summary

- [ ] **State Changes (Visual)**
  * 10:00 AM → job activates automatically
  * Each reminder sent → counter increments

- [ ] **Animations & Visual Hierarchy**
  * Reminder count: Badge with running total
  * Success rate: Percentage of delivered messages

- [ ] **Advanced Users & Edge Cases**
  * Exception handling: Skip if WhatsApp service unavailable
  * Duplicate prevention: Don't remind same customer twice in 24 hours

---

#### Overdue Bill Marking

- [ ] **User Stories**
  * As the System, I want to mark bills as overdue daily at 11:00 AM if past due date and still pending, so that payment status is accurate.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Automatic status update for overdue bills
  * Discord notification for new overdue bills
  * Dashboard KPI update

- [ ] **Screen States**
  * **Running State**: Checking pending bills
  * **Complete State**: X bills marked overdue
  * **Alert State**: Discord notification sent

- [ ] **State Changes (Visual)**
  * Status change → bill row badge updates to red "Overdue"
  * KPI → overdue count increments

- [ ] **Animations & Visual Hierarchy**
  * Overdue badge: Red, prominent
  * Alert card: Orange warning

- [ ] **Advanced Users & Edge Cases**
  * Grace period: Configurable days before marking overdue
  * Re-evaluation: If paid after marked, status reverts

---

#### Smart Meter Reading Collection

- [ ] **User Stories**
  * As the System, I want to collect meter readings from smart meters every Sunday at 8:00 AM, so that billing data is up-to-date.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Weekly automated collection
  * AI validation on each collected reading
  * Error logging for failed collections

- [ ] **Screen States**
  * **Collecting State**: Progress through meter list
  * **Validating State**: AI verification of each reading
  * **Complete State**: Collection summary

- [ ] **State Changes (Visual)**
  * Sunday 8 AM → job starts automatically
  * Each meter → progress indicator advances

- [ ] **Animations & Visual Hierarchy**
  * Meter list: Checkmarks as each completes
  * Errors: Red X with meter ID

- [ ] **Advanced Users & Edge Cases**
  * Manual fallback: If smart meter fails, flag for manual reading
  * Simulation mode: For testing without real meters

---

#### Manage Scheduled Jobs

- [ ] **User Stories**
  * As an Administrator, I want to see all scheduled jobs and their next run times, so that I can ensure billing automation is active.
  * As an Administrator, I want to manually trigger a job, so that I can run billing cycles on-demand.
  * As an Administrator, I want to pause/resume scheduled jobs, so that I can control automation during maintenance.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Job cards showing: Name, Schedule (cron readable), Next Run, Last Run, Status
  * One-click "Run Now" button per job
  * Global toggle to pause/resume all scheduled jobs

- [ ] **Screen States**
  * **Active State**: Jobs running with green pulse indicator
  * **Paused State**: Muted colors, "Paused" badge, resume button prominent
  * **Running State**: Specific job card shows spinner, progress bar if available
  * **Error State**: Red badge with last error message, logs link

- [ ] **State Changes (Visual)**
  * Run Now tap → button becomes indeterminate progress bar
  * Job completes → success animation (checkmark burst), last run updates
  * Pause all → cards desaturate with slide-down "Paused" overlay

- [ ] **Animations & Visual Hierarchy**
  * Primary: Next Run time (countdown format: "in 2h 34m")
  * Secondary: Job name, schedule description ("1st of month @ 2:00 AM")
  * Tertiary: Last run time, status badge
  * Pulse animation: Subtle glow around active job cards

- [ ] **Advanced Users & Edge Cases**
  * Job history: Expandable section showing last 10 runs with timestamps
  * Force stop: Confirmation modal for running jobs
  * Schedule edit: Not in MVP, show tooltip "Contact admin to modify"
  * Concurrent runs: Warning if triggering while already executing

---

### Authentication & Authorization

#### Role-Based Access

- [ ] **User Stories**
  * As a Field Engineer, I want access only to meter reading features, so that I can focus on my responsibilities.
  * As an Administrator, I want full access to all system features, so that I can manage the entire billing process.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Role selection on app entry
  * Different navigation for each role
  * Admin requires Auth0 login, Engineer has simplified access

- [ ] **Screen States**
  * **Role Selection**: Two prominent role cards (Field Engineer, Administrator)
  * **Engineer View**: Limited tabs (Add Reading, History, Stats)
  * **Admin Login**: Auth0 credentials form
  * **Admin View**: Full 6-tab dashboard

- [ ] **State Changes (Visual)**
  * Role card tap → transition to corresponding dashboard
  * Logout → return to role selection

- [ ] **Animations & Visual Hierarchy**
  * Role cards: Large, prominent icons
  * Admin badge: Lock icon indicating secure area

- [ ] **Advanced Users & Edge Cases**
  * Session persistence: Remember role on refresh
  * Token expiry: Prompt re-authentication

---

#### Auth0 JWT Authentication

- [ ] **User Stories**
  * As an Administrator, I want to authenticate with Auth0, so that API access is secure.
  * As the System, I want to verify JWT tokens on each API request, so that unauthorized access is prevented.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Login form with User ID and JWT Token inputs
  * Token generation via get_token_simple.py script
  * Validation feedback with success/error messages

- [ ] **Screen States**
  * **Login State**: Form with user ID and token fields
  * **Validating State**: Spinner during token verification
  * **Success State**: Redirect to admin dashboard
  * **Error State**: Red message with "Invalid token" details

- [ ] **State Changes (Visual)**
  * Submit → button becomes spinner → expands to result
  * Success → balloons animation, transition to dashboard

- [ ] **Animations & Visual Hierarchy**
  * Login form: Centered, prominent
  * Help section: Expandable "How to get token" guide

- [ ] **Advanced Users & Edge Cases**
  * Token file: Auto-load from auth0_token.txt if exists
  * Fallback: Warning if Auth0 not configured, accept any auth0| prefix

---

### Data Management

#### Sample Data Generation

- [ ] **User Stories**
  * As a Developer, I want to generate sample meter readings, so that I can test the system without real data.
  * As an Administrator, I want to seed the database, so that demos have meaningful data.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Number input for readings to generate (1-12)
  * Generate button with confirmation
  * Summary of generated data

- [ ] **Screen States**
  * **Input State**: Form with count selector
  * **Generating State**: Progress indicator
  * **Complete State**: Success message with count

- [ ] **State Changes (Visual)**
  * Generate → progress bar → success flash

- [ ] **Animations & Visual Hierarchy**
  * Count selector: Prominent
  * Status: Success/error message below

- [ ] **Advanced Users & Edge Cases**
  * Realistic patterns: Generate readings with realistic progression
  * seed_database.py: CLI option for bulk seeding

---

#### Flat/Meter Registry

- [ ] **User Stories**
  * As a Field Engineer, I want to select flats from a registry, so that meter and customer data is pre-populated.
  * As an Administrator, I want the registry imported from Excel, so that setup is efficient.

##### UX/UI Considerations

- [ ] **Core Experience**
  * JSON registry loaded from data/meter_registry.json
  * Dropdown populated with flat details
  * Auto-fill of Unit ID, Client Name, Meter ID on selection

- [ ] **Screen States**
  * **Loading State**: Dropdown placeholder
  * **Ready State**: Flat options populated
  * **Selected State**: Details card displayed

- [ ] **State Changes (Visual)**
  * Selection → details slide in
  * Error → warning if registry missing

- [ ] **Animations & Visual Hierarchy**
  * Dropdown: Full-width, searchable
  * Details card: Compact, read-only fields

- [ ] **Advanced Users & Edge Cases**
  * Fallback: Empty list if file missing
  * Import utility: Excel to JSON converter

---

### AI-Powered Features

#### Meter Reading Validation

- [ ] **User Stories**
  * As the System, I want to analyze new readings against history using AI, so that anomalies are detected automatically.
  * As an Administrator, I want AI confidence scores, so that I can review low-confidence readings.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Automatic validation during submission
  * Confidence score display (0-100%)
  * Reason text explaining validation result

- [ ] **Screen States**
  * **Validating State**: AI processing indicator
  * **Valid State**: Green checkmark with confidence
  * **Invalid State**: Red warning with reason
  * **Low Confidence State**: Yellow warning for manual review

- [ ] **State Changes (Visual)**
  * Submit → AI spinner → result display
  * Confidence bar: Color gradient from red to green

- [ ] **Animations & Visual Hierarchy**
  * Confidence percentage: Large, color-coded
  * Reason text: Readable explanation below

- [ ] **Advanced Users & Edge Cases**
  * Fallback: Basic validation if OpenAI unavailable
  * Override: Admin can accept invalid readings

---

#### Notification Message Generation

- [ ] **User Stories**
  * As the System, I want AI to generate personalized bill notifications, so that messages are customer-friendly.
  * As the System, I want AI to generate payment confirmation messages, so that thank-you messages feel personal.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Automatic message generation with bill details
  * SMS-style format with account reference
  * Due date calculation (15 days from now)

- [ ] **Screen States**
  * **Generating State**: AI composing message
  * **Ready State**: Preview of message text
  * **Sent State**: Confirmation with delivery status

- [ ] **State Changes (Visual)**
  * Generation → text appears word-by-word (typewriter effect optional)

- [ ] **Animations & Visual Hierarchy**
  * Message preview: WhatsApp-style bubble
  * Key info: Amount and due date highlighted

- [ ] **Advanced Users & Edge Cases**
  * Fallback: Template message if AI unavailable
  * Customization: Edit message before sending (future feature)

---

### API Endpoints

#### REST API

- [ ] **User Stories**
  * As a Developer, I want REST endpoints for all billing operations, so that external systems can integrate.
  * As A Third-Party System, I want webhook endpoints for events, so that I can receive real-time updates.

##### UX/UI Considerations

- [ ] **Core Experience**
  * Flask API server on port 5000
  * JSON request/response format
  * Auth0 JWT authentication on protected endpoints

- [ ] **Endpoints Available**
  * `POST /webhook/meter-reading` - Process meter reading (protected)
  * `GET /api/bills/:id` - Get bill status
  * `GET /api/bills/customer/:id` - Get customer bills
  * `PUT /api/bills/:id/status` - Update bill status
  * `POST /webhook/stripe` - Stripe payment webhook
  * `GET /api/scheduler/status` - Get scheduler status
  * `POST /api/scheduler/jobs/:id/run` - Run job manually
  * `GET /health` - Health check
  * `GET /webhook/meter-reading/test` - Test endpoint

- [ ] **Response Formats**
  * Success: `{ "success": true, "data": {...} }`
  * Error: `{ "success": false, "error": "message" }`

- [ ] **Advanced Users & Edge Cases**
  * Rate limiting: Not implemented in MVP
  * Swagger docs: Future enhancement
  * Versioning: v1 assumed

---

## UX Design Principles Applied

- **Bold simplicity** with intuitive navigation creating frictionless experiences
- **Breathable whitespace** complemented by strategic color accents for visual hierarchy
- **Strategic negative space** calibrated for cognitive breathing room and content prioritization
- **Systematic color theory** applied through subtle gradients and purposeful accent placement
- **Typography hierarchy** utilizing weight variance and proportional scaling for information architecture
- **Visual density optimization** balancing information availability with cognitive load management
- **Motion choreography** implementing physics-based transitions for spatial continuity
- **Accessibility-driven contrast ratios** paired with intuitive navigation patterns ensuring usability
- **Feedback responsiveness** via state transitions communicating system status without latency
- **Content-first layouts** prioritizing user objectives over decorative elements for task completion
- **User goals and tasks** - Understanding what users need to accomplish and designing those primary tasks seamless and efficient
- **Information architecture** - Organizing content and features in a logical hierarchy that matches users' mental models
