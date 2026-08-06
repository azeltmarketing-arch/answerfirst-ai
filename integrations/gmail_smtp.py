"""
Gmail SMTP Sender for AnswerFirst AI
Zero-cost email sending via Gmail SMTP + optional app password.
No paid APIs required.
"""

import smtplib
import ssl
import json
import time
import os
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Tuple


class GmailSMTP:
    """
    Free Gmail SMTP email sender.
    Supports standard Gmail SMTP with app password.
    """
    
    def __init__(self, sender_email: str = "azelt.marketing@gmail.com",
                 sender_password: str = "",
                 smtp_server: str = "smtp.gmail.com",
                 smtp_port: int = 587):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_email(self, to_email: str, subject: str, body: str,
                   is_html: bool = False, attachments: Optional[List[str]] = None) -> Dict:
        """
        Send a single email via Gmail SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body text or HTML
            is_html: Whether body is HTML
            attachments: List of file paths to attach
        
        Returns:
            Send result with status and message ID
        """
        if not self.sender_password:
            return {
                "status": "error",
                "error": "Gmail app password required. Set sender_password or use setup_gmail_app_password() to configure.",
                "to": to_email,
                "subject": subject
            }
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type))
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{os.path.basename(filepath)}"'
                            )
                            msg.attach(part)
            
            # Send via SMTP
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            return {
                "status": "sent",
                "to": to_email,
                "subject": subject,
                "from": self.sender_email,
                "sent_at": datetime.now().isoformat(),
                "message_id": f"<{datetime.now().timestamp()}@{self.smtp_server}>"
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                "status": "error",
                "error": "Authentication failed. Check app password or enable less-secure apps.",
                "to": to_email,
                "subject": subject
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "to": to_email,
                "subject": subject
            }
    
    def send_batch(self, recipients: List[Dict], subject_template: str,
                   body_template: str, is_html: bool = False,
                   delay_seconds: int = 2) -> List[Dict]:
        """
        Send personalized emails to multiple recipients.
        
        Args:
            recipients: List of {email, first_name, last_name, company} dicts
            subject_template: Subject with {first_name}, {company} placeholders
            body_template: Body with personalization placeholders
            is_html: Whether body is HTML
            delay_seconds: Delay between sends to avoid rate limits
        
        Returns:
            List of send results
        """
        results = []
        for i, recipient in enumerate(recipients):
            # Personalize
            email = recipient.get("email", "")
            if not email:
                continue
            
            first_name = recipient.get("first_name", recipient.get("owner_first_name", ""))
            last_name = recipient.get("last_name", recipient.get("owner_last_name", ""))
            company = recipient.get("company", recipient.get("business_name", ""))
            
            subject = subject_template
            body = body_template
            
            subject = subject.replace("{first_name}", first_name).replace("{company}", company).replace("{last_name}", last_name)
            body = body.replace("{first_name}", first_name).replace("{company}", company).replace("{last_name}", last_name)
            
            # Send
            result = self.send_email(email, subject, body, is_html)
            result["recipient"] = email
            results.append(result)
            
            # Rate limiting
            if i < len(recipients) - 1:
                time.sleep(delay_seconds)
        
        return results
    
    def send_sequence(self, recipients: List[Dict], sequence: List[Dict],
                      delay_days: bool = True) -> List[Dict]:
        """
        Send a sequence of emails to multiple recipients.
        
        Args:
            recipients: List of recipient dicts
            sequence: List of {day, subject, body, delay_days} dicts
            delay_days: Whether to space out by day count
        
        Returns:
            List of send results grouped by sequence step
        """
        all_results = []
        for step in sequence:
            day = step.get("day", 1)
            subject = step.get("subject", "")
            body = step.get("body", "")
            step_delay = step.get("delay_days", delay_days)
            
            print(f"[*] Sending sequence day {day}: {subject}")
            
            results = self.send_batch(
                recipients=recipients,
                subject_template=subject,
                body_template=body,
                delay_seconds=2 if step_delay else 0
            )
            
            all_results.append({
                "day": day,
                "subject": subject,
                "results": results,
                "sent_count": sum(1 for r in results if r.get("status") == "sent"),
                "error_count": sum(1 for r in results if r.get("status") == "error")
            })
            
            # Wait if this isn't the last step
            if step_delay and day < sequence[-1].get("day", day):
                print(f"[*] Waiting 24h before next sequence step...")
                time.sleep(5)  # Demo: 5s instead of 24h
        
        return all_results


def load_config(config_path: str = "C:/Users/azelt/answerfirst-ai/integrations/config.json") -> Dict:
    """Load integration config."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def validate_email(email: str) -> bool:
    """Basic email validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# ==================== FREE OUTREACH SEQUENCES ====================

FREE_SEQUENCES = {
    "hvac_roofing_cold_email": [
        {
            "day": 1,
            "subject": "Quick question about {company}",
            "body": """
Hi {first_name},

I was looking at {company} and noticed you're doing great work in the {city} area.

I help HVAC and roofing contractors fill their calendars with qualified appointments without lifting a finger. Think of it as a dedicated appointment-setter who works 24/7.

Would you be open to a 15-minute chat this week to see if this could work for {company}?

Best,
Andrew Zelt
AnswerFirst AI
""",
        },
        {
            "day": 3,
            "subject": "Re: Quick question about {company}",
            "body": """
Hi {first_name},

Just wanted to follow up on my last email. I know you're busy running {company}, so I'll be brief.

I recently helped a similar contractor in Phoenix add 15+ qualified appointments per month with zero extra work on their end.

If that sounds useful, let me know. No pitch - just a quick conversation.

Andrew
""",
        },
        {
            "day": 7,
            "subject": "Last check-in - {company}",
            "body": """
Hi {first_name},

I don't want to clutter your inbox, so this is my last note.

If adding qualified appointments to {company}'s calendar is a priority right now, I'm here. If not, no worries at all.

Either way, best of luck with the business.

Andrew
AnswerFirst AI
""",
        },
    ]
}


# ==================== TESTING ====================

if __name__ == "__main__":
    # Example: send a test email
    client = GmailSMTP()
    
    result = client.send_email(
        to_email="test@example.com",
        subject="Test from AnswerFirst AI",
        body="This is a test email sent via Gmail SMTP. No API keys needed!"
    )
    print(result)
