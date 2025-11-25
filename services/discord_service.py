"""
Discord Notification Service
Sends billing notifications, reminders, and alerts via Discord webhooks
"""
from typing import Dict, Optional
import requests
from datetime import datetime
from config import Config
from utils.retry_decorator import retry
from utils.logger import setup_logger

logger = setup_logger('discord_service')


class DiscordService:
    """Discord webhook service for sending notifications"""
    
    def __init__(self):
        self.webhook_url = Config.DISCORD_WEBHOOK_URL
        self.enabled = bool(self.webhook_url and len(self.webhook_url) > 20)
        
        if self.enabled:
            logger.info("Discord service enabled")
        else:
            logger.warning("Discord service disabled - no webhook URL configured")
    
    def _send_to_user(self, user_id: str, message: str, title: str = None, color: int = 0x3498db) -> Dict:
        """
        Send a direct message to a Discord user via webhook mention
        
        Args:
            user_id: Discord user ID (numeric)
            message: Message content
            title: Optional embed title
            color: Embed color (hex)
        
        Returns:
            Dict with success status
        """
        if not self.enabled:
            logger.info(f"Discord disabled - Mock DM to user {user_id}")
            return {"success": True, "mock": True}
        
        try:
            # Mention the user and send via webhook
            embed = {
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if title:
                embed["title"] = title
            
            payload = {
                "content": f"<@{user_id}>",  # Mentions the user
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Discord DM sent to user {user_id}")
                return {"success": True, "mock": False}
            else:
                logger.error(f"Discord DM failed: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            logger.error(f"Discord DM error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
    def send_message(
        self,
        message: str,
        title: str = None,
        customer_id: str = None,
        discord_user_id: str = None,
        color: int = 0x3498db,  # Blue
        **kwargs
    ) -> Dict:
        """
        Send a message to Discord channel or user
        
        Args:
            message: Message content
            title: Optional embed title
            customer_id: Customer identifier
            discord_user_id: Optional Discord user ID for direct mentions
            color: Embed color (hex)
            **kwargs: Additional embed fields
        
        Returns:
            Dict with success status and message_id
        """
        # If user ID provided, send as mention
        if discord_user_id:
            return self._send_to_user(discord_user_id, message, title, color)
        
        if not self.enabled:
            logger.info(f"Discord disabled - Mock message: {message[:50]}...")
            print(f"\n💬 MOCK Discord Message")
            print(f"Title: {title}")
            print(f"Customer: {customer_id}")
            print(f"Message: {message}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return {
                "success": True,
                "message_id": f"mock_discord_{int(datetime.now().timestamp())}",
                "mock": True
            }
        
        try:
            # Build embed
            embed = {
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": f"Billing System • Customer: {customer_id or 'N/A'}"
                }
            }
            
            if title:
                embed["title"] = title
            
            # Add custom fields
            if kwargs:
                fields = []
                for key, value in kwargs.items():
                    fields.append({
                        "name": key.replace('_', ' ').title(),
                        "value": str(value),
                        "inline": True
                    })
                if fields:
                    embed["fields"] = fields
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Discord message sent successfully for customer {customer_id}")
                return {
                    "success": True,
                    "message_id": "discord_webhook_sent",
                    "status_code": response.status_code,
                    "mock": False
                }
            else:
                logger.error(f"Discord webhook failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "mock": False
                }
        
        except Exception as e:
            logger.error(f"Discord error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "mock": False
            }
    
    def send_notification(self, phone_number: str, message: str) -> Dict:
        """
        Send notification (compatible with WhatsApp interface)
        Note: phone_number is ignored for Discord
        """
        return self.send_message(
            message=message,
            title="Billing Notification",
            color=0x3498db
        )
    
    def send_bill_notification(
        self,
        customer_id: str,
        bill_id: str,
        amount: float,
        due_date: str,
        payment_link: str = None,
        discord_user_id: str = None
    ) -> Dict:
        """Send new bill notification"""
        message = f"New electricity bill generated!\n\n"
        message += f"**Bill ID:** {bill_id}\n"
        message += f"**Amount:** ₹{amount:,.2f}\n"
        message += f"**Due Date:** {due_date}\n"
        
        if payment_link:
            message += f"\n[Click here to pay]({payment_link})"
        
        return self.send_message(
            message=message,
            title="⚡ New Bill Generated",
            customer_id=customer_id,
            discord_user_id=discord_user_id,
            color=0x2ecc71  # Green
        )
    
    def send_payment_reminder(
        self,
        customer_id: str,
        bill_id: str,
        amount: float,
        due_date: str,
        days_until_due: int,
        payment_link: str = None,
        discord_user_id: str = None
    ) -> Dict:
        """Send payment reminder"""
        # Color based on urgency
        if days_until_due <= 0:
            color = 0xe74c3c  # Red - overdue
            urgency = "⚠️ OVERDUE"
        elif days_until_due <= 3:
            color = 0xe67e22  # Orange - urgent
            urgency = "🔴 URGENT"
        elif days_until_due <= 7:
            color = 0xf39c12  # Yellow - soon
            urgency = "⚠️ DUE SOON"
        else:
            color = 0x3498db  # Blue - normal
            urgency = "📋 REMINDER"
        
        message = f"Payment reminder for your electricity bill.\n\n"
        message += f"**Bill ID:** {bill_id}\n"
        message += f"**Amount:** ₹{amount:,.2f}\n"
        message += f"**Due Date:** {due_date}\n"
        message += f"**Days Until Due:** {days_until_due}\n"
        
        if payment_link:
            message += f"\n[Pay Now]({payment_link})"
        
        return self.send_message(
            message=message,
            title=f"{urgency} Payment Reminder",
            customer_id=customer_id,
            discord_user_id=discord_user_id,
            color=color
        )
    
    def send_overdue_notice(
        self,
        customer_id: str,
        bill_id: str,
        amount: float,
        days_overdue: int,
        late_fee: float = 0.0,
        discord_user_id: str = None
    ) -> Dict:
        """Send overdue bill notice"""
        message = f"Your electricity bill is overdue!\n\n"
        message += f"**Bill ID:** {bill_id}\n"
        message += f"**Amount:** ₹{amount:,.2f}\n"
        message += f"**Days Overdue:** {days_overdue}\n"
        
        if late_fee > 0:
            message += f"**Late Fee:** ₹{late_fee:,.2f}\n"
            message += f"**Total Due:** ₹{amount + late_fee:,.2f}\n"
        
        message += f"\nPlease pay immediately to avoid service disconnection."
        
        return self.send_message(
            message=message,
            title="🚨 OVERDUE NOTICE",
            customer_id=customer_id,
            discord_user_id=discord_user_id,
            color=0xe74c3c  # Red
        )
    
    def send_payment_confirmation(
        self,
        customer_id: str,
        bill_id: str,
        amount: float,
        payment_date: str,
        discord_user_id: str = None
    ) -> Dict:
        """Send payment confirmation"""
        message = f"Payment received successfully! Thank you.\n\n"
        message += f"**Bill ID:** {bill_id}\n"
        message += f"**Amount Paid:** ₹{amount:,.2f}\n"
        message += f"**Payment Date:** {payment_date}\n"
        message += f"\nYour account is now up to date."
        
        return self.send_message(
            message=message,
            title="✅ Payment Confirmed",
            customer_id=customer_id,
            discord_user_id=discord_user_id,
            color=0x2ecc71  # Green
        )
    
    def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info"
    ) -> Dict:
        """Send system alert"""
        colors = {
            "info": 0x3498db,      # Blue
            "warning": 0xf39c12,   # Yellow
            "error": 0xe74c3c,     # Red
            "critical": 0x9b59b6   # Purple
        }
        
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        color = colors.get(severity.lower(), 0x3498db)
        icon = icons.get(severity.lower(), "ℹ️")
        
        return self.send_message(
            message=message,
            title=f"{icon} System Alert: {alert_type}",
            color=color
        )
    
    def test_connection(self) -> Dict:
        """Test Discord webhook connection"""
        return self.send_message(
            message="Discord webhook is working correctly! 🎉",
            title="✅ Connection Test",
            color=0x9b59b6  # Purple
        )
