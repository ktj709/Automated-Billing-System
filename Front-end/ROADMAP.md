# Roadmap — Blessings Electric Billing AI

> Status note: this roadmap is for the optional React frontend.
> The current repo runs Streamlit-first; Clerk items here are not used by the Python app (Auth0 is the optional auth integration).

## Current MVP (In Progress)

- [x] UI components (Directory, Billing, Reports)
- [x] Billing calculation logic
- [ ] Supabase database integration
- [ ] Clerk authentication
- [ ] Data migration from JSONL
- [ ] Real data persistence

---

## Post-MVP Features

### Priority 1: Core Enhancements

#### Multi-User Tracking
- Track which admin entered each reading
- Audit log for bill generation and status changes
- User activity history

#### PDF Export
- Generate PDF invoices for individual bills
- Batch PDF generation for entire block
- Customizable invoice template with logo

#### Bill Status Management
- Mark bills as paid with payment date
- Automatic overdue status after X days
- Bulk status updates

---

### Priority 2: Communication & Notifications

#### WhatsApp Integration
- Send bill notifications via WhatsApp
- Payment reminders for pending bills
- Integrate with WhatsApp Business API

#### SMS Notifications
- Bill generation alerts
- Payment due reminders
- Overdue notices

#### Email Integration
- Send PDF invoices via email
- Monthly statements
- Payment confirmation emails

---

### Priority 3: Advanced Features

#### Payment Gateway Integration
- Online payment option for residents
- Payment tracking and reconciliation
- Multiple payment method support (UPI, cards, etc.)

#### Mobile App
- React Native or Flutter app for field engineers
- Offline meter reading entry
- Sync when back online

#### Field Engineer Portal
- Dedicated interface for meter readings
- GPS location tracking
- Photo capture of meter readings

---

### Priority 4: Analytics & Reporting

#### Advanced Analytics Dashboard
- Consumption trends over time
- Block-wise comparison
- Seasonal patterns

#### Defaulter Management
- Automated reminder scheduling
- Escalation workflow
- Payment plan tracking

#### Export & Integration
- Excel/CSV bulk export
- Integration with accounting software (Tally, etc.)
- API for third-party integrations

---

### Priority 5: System Improvements

#### Role-Based Access Control
- Admin role (full access)
- Accountant role (view + payment updates)
- Field engineer role (reading entry only)
- Resident portal (view own bills)

#### Data Backup & Recovery
- Automated daily backups
- Point-in-time recovery
- Data export for compliance

#### Performance & Scale
- Caching for frequently accessed data
- Pagination for large datasets
- Database optimization

---

## Technical Debt & Improvements

- [ ] Add comprehensive error handling
- [ ] Implement loading skeletons
- [ ] Add unit tests for billing calculations
- [ ] Add E2E tests for critical flows
- [ ] Set up CI/CD pipeline
- [ ] Add logging and monitoring
- [ ] Implement rate limiting

---

## Notes

- Features should be prioritized based on user feedback
- Each feature should be scoped and estimated before implementation
- Consider regulatory requirements for data retention and privacy
