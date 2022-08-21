import base64
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google.cloud import secretmanager

RECIPIENT = "me@seanhofer.com"
PROJECT_ID = "coherent-coder-193013"

CLIENT = secretmanager.SecretManagerServiceClient()

def contact(request):
  """Handles Contact Form requests.

  Args:
    request (flask.Request): HTTP request object.
  Returns:
    The response text.
  """
  USER = get_secret("seanbot-user")
  PASS = get_secret("seanbot-pass")
  ALLOWED_DOMAINS = get_secret("contact-form-allowed-domains")
  SMTP_DOMAIN = get_secret("smtp-domain")
  SMTP_PORT = get_secret("smtp-port")

  headers = {}
  if request.headers['origin'] in ALLOWED_DOMAINS:
    headers = {
      'Access-Control-Allow-Origin': request.headers['origin']
    }

  fields = {}
  data = request.form.to_dict()
  for field in data:
    fields[field] = data[field]

  if not has_required_fields(fields):
    return (f'Missing required fields. Include name email and message.', 400, headers)

  try:
    msg = MIMEMultipart()
    msg['Subject'] = f'Message from {fields["name"]} via seanhofer.com!'
    msg['From'] = f'"{fields["name"]}" {fields["email"]}'
    msg['To'] = RECIPIENT
    msg.add_header('reply-to', fields["email"])
    msg.attach(MIMEText(fields["message"], 'plain'))
  except Exception as e:
    print("Error constructing message fields: {0}".format(str(e)))
    return ("Error constructing message fields: {0}".format(str(e)), 500, headers)

  if "attachments" in fields:
    try:
      b64_files = fields["attachments"].split(',')
      file_names = fields["attachment_names"].split(',')
      for index, b64_file in enumerate(b64_files):
        bytes_file = base64.b64decode(b64_file)
        part = MIMEApplication(bytes_file, Name=file_names[index])
        part['Content-Disposition'] = f'attachment; filename="{file_names[index]}"'
        msg.attach(part)
    except:
      print("Error attaching attachments. names: {0} attachments: {1}".format(
        file_names, b64_files))
      return ("Error attaching attachments. names: {0} attachments: {1}".format(file_names, b64_files), 500, headers)

  try:
    context = ssl.create_default_context()
    print(SMTP_DOMAIN)
    print(SMTP_PORT)
    with smtplib.SMTP_SSL(SMTP_DOMAIN, SMTP_PORT, context=context) as server:
      server.login(USER, PASS)
      print("logged in successfully")
      server.sendmail(fields["email"], RECIPIENT, msg.as_string())
  except Exception as e:
    print("Error sending email: {0}".format(str(e)))
    return ('%s:%s'.format(SMTP_DOMAIN, SMTP_PORT), 500, headers)

  return (f'success: "{msg.as_string()}"', 200, headers)


def has_required_fields(fields):
  return 'name' in fields and 'email' in fields and 'message' in fields

def get_secret_path(secret_id):
  return f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"

def get_secret(secret_id):
  encoded = CLIENT.access_secret_version(request={"name": get_secret_path(secret_id)})
  return encoded.payload.data.decode("UTF-8")
