import xml.etree.ElementTree as ET
import re
from datetime import datetime

def extract_transaction_details(body_text):
    """
    Extract structured data from SMS body text
    """
    details = {}
    
    tx_id_match = re.search(r'TxId:\s*(\d+)', body_text)
    if tx_id_match:
        details['tx_id'] = tx_id_match.group(1)
    
    amount_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*RWF', body_text)
    if amount_match:
        amount_str = amount_match.group(1).replace(',', '')
        details['amount'] = int(amount_str)
    
    recipient_match = re.search(r'to\s+([^0-9]+?)\s+(\d+)', body_text)
    if recipient_match:
        details['recipient_name'] = recipient_match.group(1).strip()
        details['recipient_code'] = recipient_match.group(2)
    
    sender_match = re.search(r'from\s+([^(]+)\s*\(\*+(\d+)\)', body_text)
    if sender_match:
        details['sender_name'] = sender_match.group(1).strip()
        details['sender_phone'] = sender_match.group(2)
    
    balance_match = re.search(r'(?:new balance|NEW BALANCE)\s*:?\s*(\d{1,3}(?:,\d{3})*)\s*RWF', body_text, re.IGNORECASE)
    if balance_match:
        balance_str = balance_match.group(1).replace(',', '')
        details['new_balance'] = int(balance_str)
    
    fee_match = re.search(r'Fee was:?\s*(\d{1,3}(?:,\d{3})*)\s*RWF', body_text)
    if fee_match:
        fee_str = fee_match.group(1).replace(',', '')
        details['fee'] = int(fee_str)
    
    transferred_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*RWF transferred to', body_text)
    if transferred_match:
        amount_str = transferred_match.group(1).replace(',', '')
        details['amount'] = int(amount_str)
    
    received_match = re.search(r'received\s+(\d{1,3}(?:,\d{3})*)\s*RWF from', body_text)
    if received_match:
        amount_str = received_match.group(1).replace(',', '')
        details['amount'] = int(amount_str)
    
    deposit_match = re.search(r'deposit of\s+(\d{1,3}(?:,\d{3})*)\s*RWF', body_text)
    if deposit_match:
        amount_str = deposit_match.group(1).replace(',', '')
        details['amount'] = int(amount_str)
    
    payment_to_match = re.search(r'payment of\s+(\d{1,3}(?:,\d{3})*)\s*RWF to\s+([^0-9]+)', body_text)
    if payment_to_match:
        amount_str = payment_to_match.group(1).replace(',', '')
        details['amount'] = int(amount_str)
        details['recipient_name'] = payment_to_match.group(2).strip()
    
    return details

def determine_transaction_type(body_text):
    """
    Determine the type of transaction from SMS body
    """
    body_lower = body_text.lower()
    
    if 'received' in body_lower and 'from' in body_lower:
        return 'received'
    elif 'transferred to' in body_lower:
        return 'transfer'
    elif 'deposit' in body_lower and 'added' in body_lower:
        return 'deposit'
    elif 'payment of' in body_lower and 'to' in body_lower:
        return 'payment'
    elif 'airtime' in body_lower:
        return 'airtime'
    else:
        return 'other'

def parse_transactions(xml_file):
    """
    Parse XML file and convert to list of transaction dictionaries
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except FileNotFoundError:
        raise FileNotFoundError(f"XML file '{xml_file}' not found")
    except ET.ParseError as e:
        raise Exception(f"XML parsing error: {e}")
    
    transactions = []
    transaction_id = 1
    
    for sms in root.findall('sms'):
        transaction = {}
        
        transaction['id'] = transaction_id
        transaction_id += 1
        
        protocol = sms.get('protocol')
        if protocol:
            transaction['protocol'] = int(protocol)
        
        address = sms.get('address')
        if address:
            transaction['address'] = address
        
        date = sms.get('date')
        if date:
            try:
                timestamp = int(date) / 1000
                dt = datetime.fromtimestamp(timestamp)
                transaction['date'] = dt.strftime('%Y-%m-%d')
                transaction['timestamp'] = dt.isoformat()
            except (ValueError, OSError):
                transaction['date'] = None
                transaction['timestamp'] = None
        
        msg_type = sms.get('type')
        if msg_type:
            transaction['type'] = int(msg_type)
        
        body = sms.get('body')
        if body:
            transaction['body'] = body
            transaction['transaction_type'] = determine_transaction_type(body)
            details = extract_transaction_details(body)
            transaction.update(details)
        
        readable_date = sms.get('readable_date')
        if readable_date:
            transaction['readable_date'] = readable_date
        
        read = sms.get('read')
        if read:
            transaction['read'] = int(read)
        
        status = sms.get('status')
        if status:
            transaction['status'] = int(status)
        
        transactions.append(transaction)
    
    return transactions
