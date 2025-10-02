import xml.etree.ElementTree as ET
import json
from datetime import datetime

def parse_sms_xml(xml_file_path):
    """
    Parse XML SMS data and convert to JSON format
    Returns list of transaction dictionaries
    """
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    
    transactions = []
    transaction_id = 1
    
    for sms in root.findall('sms'):
        # Extract attributes from XML
        body = sms.get('body', '')
        sms_date = sms.get('date', '')
        readable_date = sms.get('readable_date', '')
        address = sms.get('address', '')
        
        # Parse transaction details from body
        transaction = {
            'id': transaction_id,
            'sms_date': int(sms_date) if sms_date else None,
            'readable_date': readable_date,
            'address': address,
            'body': body,
            'amount': extract_amount(body),
            'transaction_type': categorize_transaction(body),
            'recipient': extract_recipient(body),
            'balance': extract_balance(body),
            'txid': extract_txid(body),
            'fee': extract_fee(body)
        }
        
        transactions.append(transaction)
        transaction_id += 1
    
    return transactions

def extract_amount(body):
    """Extract transaction amount from SMS body"""
    import re
    
    # Pattern for amounts like "2000 RWF" or "2,000 RWF"
    pattern = r'(\d{1,3}(?:,\d{3})*|\d+)\s*RWF'
    matches = re.findall(pattern, body)
    
    if matches:
        # Return first amount found, remove commas
        return float(matches[0].replace(',', ''))
    return None

def extract_balance(body):
    """Extract new balance from SMS body"""
    import re
    
    # Pattern for balance like "new balance: 2000 RWF" or "NEW BALANCE :2000 RWF"
    pattern = r'(?:new balance|NEW BALANCE)\s*:?\s*(\d{1,3}(?:,\d{3})*|\d+)\s*RWF'
    match = re.search(pattern, body, re.IGNORECASE)
    
    if match:
        return float(match.group(1).replace(',', ''))
    return None

def extract_txid(body):
    """Extract transaction ID from SMS body"""
    import re
    
    # Pattern for TxId or Transaction Id
    pattern = r'(?:TxId|Transaction Id)\s*:?\s*(\d+)'
    match = re.search(pattern, body, re.IGNORECASE)
    
    if match:
        return match.group(1)
    return None

def extract_fee(body):
    """Extract transaction fee from SMS body"""
    import re
    
    # Pattern for fee like "Fee was 0 RWF" or "Fee was: 100 RWF"
    pattern = r'Fee was:?\s*(\d{1,3}(?:,\d{3})*|\d+)\s*RWF'
    match = re.search(pattern, body, re.IGNORECASE)
    
    if match:
        return float(match.group(1).replace(',', ''))
    return 0.0

def extract_recipient(body):
    """Extract recipient name from SMS body"""
    import re
    
    # Pattern for recipient like "to Jane Smith" or "from Jane Smith"
    pattern = r'(?:to|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    match = re.search(pattern, body)
    
    if match:
        return match.group(1)
    return None

def categorize_transaction(body):
    """Categorize transaction based on SMS body content"""
    body_lower = body.lower()
    
    if 'received' in body_lower:
        return 'received'
    elif 'payment of' in body_lower:
        return 'payment'
    elif 'transferred to' in body_lower:
        return 'transfer'
    elif 'bank deposit' in body_lower or 'cash deposit' in body_lower:
        return 'deposit'
    elif 'airtime' in body_lower:
        return 'airtime'
    else:
        return 'other'

def save_to_json(transactions, output_file):
    """Save transactions list to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transactions, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(transactions)} transactions to {output_file}")

if __name__ == '__main__':
    # Parse XML and save to JSON
    xml_path = 'data/raw/modified_sms_v2.xml'
    output_path = 'data/processed/transactions.json'
    
    transactions = parse_sms_xml(xml_path)
    save_to_json(transactions, output_path)
    
    print(f"Parsed {len(transactions)} transactions")
    print(f"Sample transaction: {json.dumps(transactions[0], indent=2)}")
