# Discord User Mentions Guide

## How to Get Your Discord User ID

To receive direct mentions in Discord notifications:

### Step 1: Enable Developer Mode
1. Open Discord
2. Go to **User Settings** (gear icon)
3. Navigate to **Advanced** (under App Settings)
4. Enable **Developer Mode**

### Step 2: Copy Your User ID
1. Right-click on your username anywhere in Discord
2. Select **Copy User ID**
3. You'll get a numeric ID like: `123456789012345678`

## Using Discord User ID in the Billing System

### In Streamlit Workflow Test
1. Go to the **🔄 Full Workflow Test** tab
2. Enter your Discord User ID in the **"Discord User ID"** field
3. Run the workflow
4. You'll be mentioned in the Discord channel when the notification is sent

### In Code
```python
from services.discord_service import DiscordService

discord = DiscordService()

# Send bill notification with user mention
discord.send_bill_notification(
    customer_id="CUST001",
    bill_id="BILL123",
    amount=2500.50,
    due_date="2025-12-15",
    payment_link="https://stripe.com/pay/123",
    discord_user_id="123456789012345678"  # Your Discord User ID
)
```

## Supported Notification Types with User Mentions

All notification methods support the `discord_user_id` parameter:

- ✅ `send_bill_notification()` - New bills
- ✅ `send_payment_reminder()` - Payment reminders
- ✅ `send_overdue_notice()` - Overdue notices
- ✅ `send_payment_confirmation()` - Payment confirmations
- ✅ `send_message()` - General messages

## How It Works

When you provide a Discord User ID:
- The message is sent to the channel via webhook
- You are mentioned at the top: `@YourUsername`
- You'll receive a Discord notification
- The message appears in the channel for everyone to see

## Privacy Note

- User mentions are visible to everyone in the channel
- Consider using a private/restricted channel for sensitive billing information
- Only users with access to the channel will see the notifications

## Testing

Run the test script with user ID prompt:
```bash
python test_discord.py
```

When prompted, enter your Discord User ID to test direct mentions.
