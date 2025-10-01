import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime

def parse_sms_body(body):
    """Extract transaction details from SMS body text"""
    data = {
        'amount': None,
        'recipient_name': None,
        'recipient_account': None,
        'tx_id': None,
        'new_balance': None,
        'fee': None,
        'transaction_type': None,
        'datetime': None,
        'sender_name': None,
        'sender_phone': None
    }
    
    amount_match = re.search(r'(\d+[\.,]?\d*)\s*RWF', body)
    if amount_match:
        data['amount'] = float(amount_match.group(1).replace(',', ''))
    
    txid_match = re.search(r'TxId[:\s]+(\d+)', body, re.IGNORECASE)
    if txid_match:
        data['tx_id'] = txid_match.group(1)
    
    financial_id_match = re.search(r'Financial Transaction Id[:\s]+(\d+)', body, re.IGNORECASE)
    if financial_id_match:
        data['tx_id'] = financial_id_match.group(1)
    
    balance_match = re.search(r'(?:new balance|NEW BALANCE)[:\s]+(\d+[\.,]?\d*)\s*RWF', body, re.IGNORECASE)
    if balance_match:
        data['new_balance'] = float(balance_match.group(1).replace(',', ''))
    
    fee_match = re.search(r'Fee was[:\s]+(\d+)\s*RWF', body, re.IGNORECASE)
    if fee_match:
        data['fee'] = float(fee_match.group(1))
    
    payment_match = re.search(r'payment of .+ to ([A-Za-z\s]+)\s+(\d+)', body, re.IGNORECASE)
    if payment_match:
        data['recipient_name'] = payment_match.group(1).strip()
        data['recipient_account'] = payment_match.group(2)
        data['transaction_type'] = 'payment'
    
    transfer_match = re.search(r'transferred to ([A-Za-z\s]+)\s+\((\d+)\)', body, re.IGNORECASE)
    if transfer_match:
        data['recipient_name'] = transfer_match.group(1).strip()
        data['sender_phone'] = transfer_match.group(2)
        data['transaction_type'] = 'transfer'
    
    received_match = re.search(r'received .+ from ([A-Za-z\s]+)\s+\(\*+(\d+)\)', body, re.IGNORECASE)
    if received_match:
        data['sender_name'] = received_match.group(1).strip()
        data['sender_phone'] = received_match.group(2)
        data['transaction_type'] = 'received'
    
    if 'deposit' in body.lower():
        data['transaction_type'] = 'deposit'
        data['recipient_name'] = 'Cash Deposit'
    
    if 'airtime' in body.lower():
        data['transaction_type'] = 'airtime'
        data['recipient_name'] = 'Airtime'
    
    datetime_match = re.search(r'at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', body)
    if datetime_match:
        data['datetime'] = datetime_match.group(1)
    
    return data

def determine_payment_transfer_types(transaction_type, body):
    """Determine payment_type and transfer_type based on transaction"""
    payment_type = None
    transfer_type = 'MOMO'
    
    if transaction_type == 'payment':
        payment_type = 'Sent'
    elif transaction_type == 'received':
        payment_type = 'Received'
    elif transaction_type == 'transfer':
        payment_type = 'Sent'
    elif transaction_type == 'deposit':
        payment_type = 'Received'
    elif transaction_type == 'airtime':
        payment_type = 'Sent'
    
    return payment_type, transfer_type

def parse_transactions(xml_file):
    """Parse XML file and convert to list of transaction dictionaries"""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    transactions = []
    trans_id = 1
    
    for sms in root.findall('.//sms'):
        protocol = sms.get('protocol')
        address = sms.get('address')
        date_timestamp = sms.get('date')
        readable_date = sms.get('readable_date')
        body = sms.get('body', '')
        
        parsed_data = parse_sms_body(body)
        
        date_obj = None
        timestamp_iso = None
        if date_timestamp:
            try:
                timestamp = int(date_timestamp) / 1000
                date_obj = datetime.fromtimestamp(timestamp)
                timestamp_iso = date_obj.isoformat() + 'Z'
            except (ValueError, OSError):
                pass
        
        payment_type, transfer_type = determine_payment_transfer_types(
            parsed_data['transaction_type'], 
            body
        )
        
        transaction = {
            'id': trans_id,
            'user_id': 1,
            'date': date_obj.strftime('%Y-%m-%d') if date_obj else None,
            'time_stamp': timestamp_iso,
            'body': body,
            'tx_id': parsed_data['tx_id'],
            'amount': parsed_data['amount'],
            'recipient_name': parsed_data['recipient_name'],
            'recipient_account': parsed_data['recipient_account'],
            'sender_name': parsed_data['sender_name'],
            'sender_phone': parsed_data['sender_phone'],
            'new_balance': parsed_data['new_balance'],
            'fee': parsed_data['fee'],
            'transaction_type': parsed_data['transaction_type'],
            'payment_type': payment_type,
            'transfer_type': transfer_type,
            'status': 'Completed',
            'protocol': protocol,
            'address': address,
            'readable_date': readable_date
        }
        
        transactions.append(transaction)
        trans_id += 1
    
    return transactions

def save_to_json(transactions, output_file='transactions.json'):
    """Save transactions to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transactions, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(transactions)} transactions to {output_file}")

if __name__ == '__main__':
    xml_file = 'modified_sms_v2.xml'
    transactions = parse_transactions(xml_file)
    save_to_json(transactions)
    print(f"Parsed {len(transactions)} transactions successfully")
