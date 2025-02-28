from fastapi_mail import ConnectionConfig



conf = ConnectionConfig(MAIL_USERNAME='support@text.com',
                        MAIL_PASSWORD='11111',
                        MAIL_FROM='support@text.com',
                        MAIL_PORT=587,
                        MAIL_SERVER='smtp.text.com',
                        MAIL_STARTTLS=True,
                        MAIL_SSL_TLS=False,
                        USE_CREDENTIALS=True,
                        VALIDATE_CERTS=True,
                        TEMPLATE_FOLDER='templates', )

site_url = "text.com"