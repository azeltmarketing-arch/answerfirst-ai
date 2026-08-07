import json, smtplib, time, csv
from email.mime.text import MIMEText
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
SEQUENCES = json.loads((BASE / 'sequences.json').read_text())
PROSPECTS_PATH = BASE / 'prospects.json'
LOG_PATH = BASE / 'send_log.csv'
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
FROM_EMAIL = 'azelt5697@gmail.com'
FROM_NAME = 'Andrew — AnswerFirst AI'

def load_prospects():
    if PROSPECTS_PATH.exists():
        return json.loads(PROSPECTS_PATH.read_text())
    return []

def save_prospects(prospects):
    PROSPECTS_PATH.write_text(json.dumps(prospects, indent=2))

def log_send(prospect_id, email, subject, seq_id, status):
    with open(LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), prospect_id, email, subject, seq_id, status])

def send_email(to_email, subject, body, smtp_password):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To'] = to_email
    msg['Reply-To'] = FROM_EMAIL
    msg['List-Unsubscribe'] = '<mailto:unsubscribe@answerfirst-ai.vercel.app>'
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(FROM_EMAIL, smtp_password)
        server.send_message(msg)

def run_campaign(sequence_id, prospects, smtp_password, delay_seconds=120):
    seq = next((s for s in SEQUENCES if s['id'] == sequence_id), None)
    if not seq:
        print(f'Sequence {sequence_id} not found')
        return
    sent = 0
    for prospect in prospects:
        if prospect.get('status') != 'new':
            continue
        if sequence_id not in prospect.get('sequences_sent', []):
            subject = seq['subject']
            body = seq['body']
            for key, val in prospect.items():
                subject = subject.replace('{{' + key + '}}', str(val))
                body = body.replace('{{' + key + '}}', str(val))
            try:
                send_email(prospect['email'], subject, body, smtp_password)
                log_send(prospect['id'], prospect['email'], subject, sequence_id, 'sent')
                prospect.setdefault('sequences_sent', []).append(sequence_id)
                prospect['status'] = 'in_sequence'
                sent += 1
                print(f'Sent to {prospect["email"]}')
                if sent < len(prospects):
                    time.sleep(delay_seconds)
            except Exception as e:
                log_send(prospect['id'], prospect['email'], subject, sequence_id, f'error: {e}')
                print(f'Error sending to {prospect["email"]}: {e}')
    save_prospects(prospects)
    print(f'Campaign complete. Sent {sent} emails.')

if __name__ == '__main__':
    import sys
    seq_id = sys.argv[1] if len(sys.argv) > 1 else 'seq-cold-intro-1'
    password = sys.argv[2] if len(sys.argv) > 2 else input('Gmail app password: ')
    prospects = load_prospects()
    if not prospects:
        print('No prospects found in outreach/prospects.json')
    else:
        run_campaign(seq_id, prospects, password)
