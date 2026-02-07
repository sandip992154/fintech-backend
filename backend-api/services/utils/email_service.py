"""
Email Service for BANDARU PAY
============================

This module handles email notifications for resource management operations.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

# Configure logger
logger = logging.getLogger("bandaru_api")


class EmailService:
    """
    Service class for sending email notifications
    """
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "BANDARU PAY")
        
        # Initialize Jinja2 environment for templates
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "emails")
        if os.path.exists(template_dir):
            self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.jinja_env = None
            logger.warning("Email template directory not found")
    
    def _create_smtp_connection(self):
        """Create SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls(context=ssl.create_default_context())
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {str(e)}")
            raise
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None
    ) -> bool:
        """
        Send email notification
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            attachments: List of attachment dictionaries (optional)
            cc_emails: List of CC email addresses (optional)
            bcc_emails: List of BCC email addresses (optional)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email")
                return False
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = ", ".join(to_emails)
            
            if cc_emails:
                message["Cc"] = ", ".join(cc_emails)
            
            # Add text body
            text_part = MIMEText(body, "plain")
            message.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                message.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            # Prepare recipient list
            all_recipients = to_emails.copy()
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)
            
            # Send email
            with self._create_smtp_connection() as server:
                server.sendmail(self.from_email, all_recipients, message.as_string())
            
            logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        try:
            filename = attachment.get("filename", "attachment")
            content = attachment.get("content", b"")
            content_type = attachment.get("content_type", "application/octet-stream")
            
            part = MIMEBase(*content_type.split("/"))
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            message.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename', 'unknown')}: {str(e)}")
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> tuple:
        """
        Render email template
        
        Args:
            template_name: Template filename (without extension)
            context: Template context variables
        
        Returns:
            tuple: (text_body, html_body)
        """
        try:
            if not self.jinja_env:
                logger.warning("Template environment not initialized")
                return "", ""
            
            # Try to load text template
            text_body = ""
            try:
                text_template = self.jinja_env.get_template(f"{template_name}.txt")
                text_body = text_template.render(**context)
            except Exception as e:
                logger.warning(f"Text template not found for {template_name}: {str(e)}")
            
            # Try to load HTML template
            html_body = ""
            try:
                html_template = self.jinja_env.get_template(f"{template_name}.html")
                html_body = html_template.render(**context)
            except Exception as e:
                logger.warning(f"HTML template not found for {template_name}: {str(e)}")
            
            return text_body, html_body
            
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            return "", ""
    
    # ---------- Resource Management Email Methods ----------
    
    def send_resource_created_notification(
        self,
        recipient_emails: List[str],
        resource_name: str,
        resource_type: str,
        created_by: str,
        resource_url: str
    ) -> bool:
        """Send notification when a resource is created"""
        try:
            context = {
                "resource_name": resource_name,
                "resource_type": resource_type,
                "created_by": created_by,
                "resource_url": resource_url,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "platform_name": "BANDARU PAY"
            }
            
            # Try to render template
            text_body, html_body = self.render_template("resource_created", context)
            
            # Fallback to simple text if template not available
            if not text_body:
                text_body = f"""
Resource Created - {resource_name}

Hello,

A new {resource_type} resource has been created in BANDARU PAY.

Resource Details:
- Name: {resource_name}
- Type: {resource_type}
- Created by: {created_by}
- Created at: {context['timestamp']}

You can view the resource at: {resource_url}

Best regards,
BANDARU PAY Team
                """.strip()
            
            subject = f"New Resource Created: {resource_name}"
            
            return self.send_email(
                to_emails=recipient_emails,
                subject=subject,
                body=text_body,
                html_body=html_body if html_body else None
            )
            
        except Exception as e:
            logger.error(f"Failed to send resource created notification: {str(e)}")
            return False
    
    def send_resource_updated_notification(
        self,
        recipient_emails: List[str],
        resource_name: str,
        resource_type: str,
        updated_by: str,
        changes: List[str],
        resource_url: str
    ) -> bool:
        """Send notification when a resource is updated"""
        try:
            context = {
                "resource_name": resource_name,
                "resource_type": resource_type,
                "updated_by": updated_by,
                "changes": changes,
                "resource_url": resource_url,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "platform_name": "BANDARU PAY"
            }
            
            text_body, html_body = self.render_template("resource_updated", context)
            
            if not text_body:
                changes_text = "\n- ".join(changes) if changes else "Multiple fields updated"
                text_body = f"""
Resource Updated - {resource_name}

Hello,

A {resource_type} resource has been updated in BANDARU PAY.

Resource Details:
- Name: {resource_name}
- Type: {resource_type}
- Updated by: {updated_by}
- Updated at: {context['timestamp']}

Changes made:
- {changes_text}

You can view the resource at: {resource_url}

Best regards,
BANDARU PAY Team
                """.strip()
            
            subject = f"Resource Updated: {resource_name}"
            
            return self.send_email(
                to_emails=recipient_emails,
                subject=subject,
                body=text_body,
                html_body=html_body if html_body else None
            )
            
        except Exception as e:
            logger.error(f"Failed to send resource updated notification: {str(e)}")
            return False
    
    def send_resource_deleted_notification(
        self,
        recipient_emails: List[str],
        resource_name: str,
        resource_type: str,
        deleted_by: str,
        is_permanent: bool = False
    ) -> bool:
        """Send notification when a resource is deleted"""
        try:
            context = {
                "resource_name": resource_name,
                "resource_type": resource_type,
                "deleted_by": deleted_by,
                "is_permanent": is_permanent,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "platform_name": "BANDARU PAY"
            }
            
            text_body, html_body = self.render_template("resource_deleted", context)
            
            if not text_body:
                deletion_type = "permanently deleted" if is_permanent else "deleted"
                text_body = f"""
Resource {deletion_type.title()} - {resource_name}

Hello,

A {resource_type} resource has been {deletion_type} in BANDARU PAY.

Resource Details:
- Name: {resource_name}
- Type: {resource_type}
- {deletion_type.title()} by: {deleted_by}
- {deletion_type.title()} at: {context['timestamp']}

{"This action is permanent and cannot be undone." if is_permanent else "The resource can be restored if needed."}

Best regards,
BANDARU PAY Team
                """.strip()
            
            subject = f"Resource {'Permanently ' if is_permanent else ''}Deleted: {resource_name}"
            
            return self.send_email(
                to_emails=recipient_emails,
                subject=subject,
                body=text_body,
                html_body=html_body if html_body else None
            )
            
        except Exception as e:
            logger.error(f"Failed to send resource deleted notification: {str(e)}")
            return False
    
    def send_permission_changed_notification(
        self,
        recipient_emails: List[str],
        resource_name: str,
        permission_changes: str,
        changed_by: str,
        resource_url: str
    ) -> bool:
        """Send notification when resource permissions are changed"""
        try:
            context = {
                "resource_name": resource_name,
                "permission_changes": permission_changes,
                "changed_by": changed_by,
                "resource_url": resource_url,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "platform_name": "BANDARU PAY"
            }
            
            text_body, html_body = self.render_template("permission_changed", context)
            
            if not text_body:
                text_body = f"""
Resource Permissions Changed - {resource_name}

Hello,

The permissions for a resource have been changed in BANDARU PAY.

Resource: {resource_name}
Changes: {permission_changes}
Changed by: {changed_by}
Changed at: {context['timestamp']}

You can view the resource at: {resource_url}

Best regards,
BANDARU PAY Team
                """.strip()
            
            subject = f"Permissions Changed: {resource_name}"
            
            return self.send_email(
                to_emails=recipient_emails,
                subject=subject,
                body=text_body,
                html_body=html_body if html_body else None
            )
            
        except Exception as e:
            logger.error(f"Failed to send permission changed notification: {str(e)}")
            return False