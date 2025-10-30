"""
Email Notification Module for HSCRC Survey System
Sends emails on submission and approval
"""

import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def get_email_config():
    """Get email configuration from Streamlit secrets"""
    try:
        return {
            'smtp_server': st.secrets.get("email", {}).get("smtp_server", "smtp.gmail.com"),
            'smtp_port': st.secrets.get("email", {}).get("smtp_port", 587),
            'sender_email': st.secrets["email"]["sender_email"],
            'sender_password': st.secrets["email"]["sender_password"],
            'sender_name': st.secrets.get("email", {}).get("sender_name", "HSCRC Survey System")
        }
    except Exception as e:
        st.error(f"❌ Email configuration not found in secrets: {str(e)}")
        return None

def send_submission_email(recipient_email, hospital_name, contact_name, submission_data):
    """
    Send email notification when hospital submits survey
    
    Args:
        recipient_email: Hospital's email address
        hospital_name: Name of the hospital
        contact_name: Name of contact person
        submission_data: Dictionary with submission details
    """
    config = get_email_config()
    if not config:
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"HSCRC Survey Submitted - {hospital_name}"
        msg['From'] = f"{config['sender_name']} <{config['sender_email']}>"
        msg['To'] = recipient_email
        
        # Email body
        bp1 = submission_data.get('bp1', 'N/A')
        bp1_tier = submission_data.get('bp1_tier', 'N/A')
        bp2 = submission_data.get('bp2', 'N/A')
        bp2_tier = submission_data.get('bp2_tier', 'N/A')
        timestamp = submission_data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #0066cc; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info-box {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0066cc; margin: 15px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .button {{ background-color: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏥 Survey Submitted Successfully</h1>
            </div>
            
            <div class="content">
                <p>Dear {contact_name},</p>
                
                <p>Thank you for submitting your HSCRC Best Practices Survey for <strong>{hospital_name}</strong>.</p>
                
                <div class="info-box">
                    <h3>📋 Submission Summary</h3>
                    <p><strong>Submitted:</strong> {timestamp}</p>
                    <p><strong>Hospital:</strong> {hospital_name}</p>
                    <p><strong>Contact:</strong> {contact_name}</p>
                </div>
                
                <div class="info-box">
                    <h3>🎯 Best Practices Selected</h3>
                    <p><strong>First Best Practice:</strong> {bp1} (Tier {bp1_tier})</p>
                    <p><strong>Second Best Practice:</strong> {bp2} (Tier {bp2_tier})</p>
                </div>
                
                <p><strong>Status:</strong> 📝 DRAFT - Your submission is currently under review by HSCRC staff.</p>
                
                <p>You can log back into the portal at any time to:</p>
                <ul>
                    <li>View your submission</li>
                    <li>Edit your responses (before approval)</li>
                    <li>Download a PDF report</li>
                </ul>
                
                <p>You will receive another email once your submission has been approved by HSCRC staff.</p>
            </div>
            
            <div class="footer">
                <p>Maryland Health Services Cost Review Commission</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to send submission email: {str(e)}")
        return False

def send_approval_email(recipient_email, hospital_name, contact_name, approved_by, approved_at):
    """
    Send email notification when submission is approved
    
    Args:
        recipient_email: Hospital's email address
        hospital_name: Name of the hospital
        contact_name: Name of contact person
        approved_by: Name of person who approved
        approved_at: Timestamp of approval
    """
    config = get_email_config()
    if not config:
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"✅ HSCRC Survey APPROVED - {hospital_name}"
        msg['From'] = f"{config['sender_name']} <{config['sender_email']}>"
        msg['To'] = recipient_email
        
        # Email body
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info-box {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .checkmark {{ font-size: 48px; color: #28a745; text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ Your Survey Has Been Approved!</h1>
            </div>
            
            <div class="content">
                <div class="checkmark">✓</div>
                
                <p>Dear {contact_name},</p>
                
                <p>Great news! Your HSCRC Best Practices Survey for <strong>{hospital_name}</strong> has been officially approved.</p>
                
                <div class="info-box">
                    <h3>✅ Approval Details</h3>
                    <p><strong>Hospital:</strong> {hospital_name}</p>
                    <p><strong>Approved By:</strong> {approved_by}</p>
                    <p><strong>Approved On:</strong> {approved_at}</p>
                </div>
                
                <p><strong>What this means:</strong></p>
                <ul>
                    <li>✅ Your submission is now finalized and official</li>
                    <li>✅ Your responses are locked and cannot be edited</li>
                    <li>✅ You can download an official PDF report from the portal</li>
                </ul>
                
                <p>Thank you for your participation in the HSCRC Best Practices initiative!</p>
                
                <p>If you need to make any changes to your approved submission, please contact HSCRC staff directly.</p>
            </div>
            
            <div class="footer">
                <p>Maryland Health Services Cost Review Commission</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to send approval email: {str(e)}")
        return False

def test_email_config():
    """Test email configuration - useful for setup"""
    config = get_email_config()
    if not config:
        return False
    
    try:
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
        return True
    except Exception as e:
        st.error(f"❌ Email configuration test failed: {str(e)}")
        return False
