import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from app.core.config import settings

async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = None
) -> bool:
    """Send an email using configured SMTP server."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email

    # Add text/plain and text/html parts
    if text_content:
        message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(html_content, "html"))

    try:
        async with aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=settings.SMTP_TLS
        ) as smtp:
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            await smtp.send_message(message)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

async def send_lead_notification(lead) -> bool:
    """Send notification to agents about new lead."""
    subject = f"New Lead: {lead.name} - {lead.source}"
    
    html_content = f"""
    <h2>New Lead Details</h2>
    <p><strong>Name:</strong> {lead.name}</p>
    <p><strong>Email:</strong> {lead.email}</p>
    <p><strong>Phone:</strong> {lead.phone}</p>
    <p><strong>Source:</strong> {lead.source}</p>
    <p><strong>Budget Range:</strong> ${lead.min_budget:,} - ${lead.max_budget:,}</p>
    <p><strong>Timeline:</strong> {lead.purchase_timeline}</p>
    
    <h3>Property Preferences</h3>
    <pre>{lead.property_preferences}</pre>
    
    <p>Please follow up with this lead as soon as possible.</p>
    """
    
    text_content = f"""
    New Lead Details
    ----------------
    Name: {lead.name}
    Email: {lead.email}
    Phone: {lead.phone}
    Source: {lead.source}
    Budget: ${lead.min_budget:,} - ${lead.max_budget:,}
    Timeline: {lead.purchase_timeline}
    
    Please follow up with this lead as soon as possible.
    """
    
    return await send_email(
        to_email=settings.AGENT_NOTIFICATION_EMAIL,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

async def send_property_recommendation(
    lead,
    properties: List[dict]
) -> bool:
    """Send property recommendations to lead."""
    subject = "Personalized Property Recommendations"
    
    properties_html = "".join([
        f"""
        <div style="margin-bottom: 20px;">
            <img src="{p['image_url']}" style="max-width: 300px;" />
            <h3>{p['title']}</h3>
            <p><strong>Price:</strong> ${p['price']:,}</p>
            <p><strong>Location:</strong> {p['address']}</p>
            <p>{p['description'][:200]}...</p>
            <a href="{p['url']}">View Details</a>
        </div>
        """
        for p in properties
    ])
    
    html_content = f"""
    <h2>Your Personalized Property Recommendations</h2>
    <p>Based on your preferences, we think you'll love these properties:</p>
    {properties_html}
    <p>Contact us to schedule a viewing or learn more about any of these properties.</p>
    """
    
    return await send_email(
        to_email=lead.email,
        subject=subject,
        html_content=html_content
    )
