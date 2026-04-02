# ============================================================
# email_service.py
# Ce face: Trimite emailuri de alertă când un device iese offline
#
# Folosește SMTP — protocolul standard pentru trimitere email
# Outlook folosește smtp.office365.com pe portul 587
# ============================================================

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class EmailService:

    def __init__(self):
        self.sender   = os.getenv("EMAIL_SENDER", "")
        self.password = os.getenv("EMAIL_PASSWORD", "")
        self.receiver = os.getenv("EMAIL_RECEIVER", "")
        self.enabled  = os.getenv("EMAIL_ENABLED", "False").lower() == "true"

        # Outlook SMTP settings
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587

    def send_alert(self, device: dict, alert_type: str) -> bool:
        """
        Trimite un email de alertă pentru un device.

        Parametri:
            device:     dict cu info device (ip, hostname, type)
            alert_type: 'offline' sau 'back_online'

        Returnează:
            True dacă emailul a fost trimis cu succes
            False dacă a apărut o eroare
        """
        if not self.enabled:
            print("[EMAIL] Email alerts dezactivate în .env")
            return False

        if not self.sender or not self.password:
            print("[EMAIL] Credențiale lipsă în .env")
            return False

        try:
            # Construim subiectul și conținutul emailului
            if alert_type == "offline":
                subject = f"⚠️ ALERTĂ DIIP: {device.get('hostname', device['ip_address'])} este OFFLINE"
                color   = "#ef4444"
                icon    = "🔴"
                status_text = "OFFLINE"
                message_text = f"Device-ul nu răspunde la ping și a fost marcat ca offline."
            else:
                subject = f"✅ DIIP: {device.get('hostname', device['ip_address'])} a revenit ONLINE"
                color   = "#22c55e"
                icon    = "🟢"
                status_text = "ONLINE"
                message_text = "Device-ul răspunde din nou la ping."

            # Construim emailul HTML (arată profesional)
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body style="font-family: Arial, sans-serif; background: #f1f5f9; padding: 20px;">

                <div style="max-width: 600px; margin: 0 auto; background: white;
                            border-radius: 10px; overflow: hidden;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

                    <!-- Header -->
                    <div style="background: {color}; padding: 24px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 24px;">
                            {icon} {status_text}
                        </h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0;">
                            Digital Infrastructure Intelligence Platform
                        </p>
                    </div>

                    <!-- Conținut -->
                    <div style="padding: 32px;">
                        <h2 style="color: #1e293b; margin: 0 0 8px;">
                            {device.get('hostname', 'Device necunoscut')}
                        </h2>
                        <p style="color: #64748b; margin: 0 0 24px;">
                            {message_text}
                        </p>

                        <!-- Detalii device -->
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px 0; color: #64748b; font-size: 14px;">IP Address</td>
                                <td style="padding: 12px 0; font-family: monospace;
                                           color: #0891b2; font-weight: bold;">
                                    {device.get('ip_address', '—')}
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px 0; color: #64748b; font-size: 14px;">Tip Device</td>
                                <td style="padding: 12px 0; font-weight: 500;">
                                    {device.get('device_type', '—')}
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px 0; color: #64748b; font-size: 14px;">Sistem de Operare</td>
                                <td style="padding: 12px 0;">
                                    {device.get('os_name', '—')}
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px 0; color: #64748b; font-size: 14px;">Departament</td>
                                <td style="padding: 12px 0;">
                                    {device.get('department', '—')}
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e2e8f0;">
                                <td style="padding: 12px 0; color: #64748b; font-size: 14px;">Owner</td>
                                <td style="padding: 12px 0;">
                                    {device.get('owner', '—')}
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 12px 0; color: #64748b; font-size: 14px;">Detectat la</td>
                                <td style="padding: 12px 0; font-family: monospace; font-size: 13px;">
                                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                </td>
                            </tr>
                        </table>
                    </div>

                    <!-- Footer -->
                    <div style="background: #f8fafc; padding: 16px 32px;
                                border-top: 1px solid #e2e8f0; text-align: center;">
                        <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                            DIIP — Digital Infrastructure Intelligence Platform
                        </p>
                    </div>
                </div>

            </body>
            </html>
            """

            # Construim mesajul MIME
            # MIME = formatul standard pentru emailuri HTML
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = self.sender
            msg["To"]      = self.receiver

            # Adăugăm versiunea HTML
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # Trimitem prin SMTP
            # TLS = conexiune securizată (criptată)
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()  # activăm criptarea
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.receiver, msg.as_string())

            print(f"[EMAIL] ✓ Email trimis: {subject}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("[EMAIL] ✗ Eroare autentificare — verifică emailul și parola din .env")
            return False
        except smtplib.SMTPException as e:
            print(f"[EMAIL] ✗ Eroare SMTP: {e}")
            return False
        except Exception as e:
            print(f"[EMAIL] ✗ Eroare generală: {e}")
            return False

    def test_email(self) -> dict:
        """
        Trimite un email de test ca să verifici că configurația e corectă.
        Apelat din API: GET /api/email/test
        """
        test_device = {
            "ip_address":  "192.168.1.10",
            "hostname":    "WIN-SERVER01",
            "device_type": "Server",
            "os_name":     "Windows Server 2019",
            "department":  "IT",
            "owner":       "Ion Popescu"
        }

        success = self.send_alert(test_device, "offline")

        return {
            "success": success,
            "message": "Email de test trimis cu succes!" if success else "Eroare la trimitere. Verifică .env"
        }


# Instanță globală
email_service = EmailService()
