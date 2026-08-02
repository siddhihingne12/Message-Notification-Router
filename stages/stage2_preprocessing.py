import re

OCR_MAP = {
    "img_001": "Water Tanker Notice: Supply at Gate 2 ends 11 AM",
    "img_002": "Ticket Refund Processing Portal - Enter Bank & OTP",
    "img_003": "Ladakh Travel Special Package 7 Nights Rs 17999",
    "img_004": "Deployment Release Review Notes & Incident Summary",
    "img_007": "Shopee Package Return Courier Pickup Code",
    "img_008": "Myntra Kurta Set Size M Sale Rs 850 Gate 2",
    "img_010": "Special Shopping Discount Offer Balance Ready",
    "img_011": "International School Circular Consent Form & Bus Timing",
    "img_012": "Faculty Advising Internship Form Deadline 5 PM Today",
    "img_023": "Society Fire Alarm Maintenance Elevators Paused 9 AM",
    "img_024": "Nvidia TSMC Semiconductor Research Report Earnings",
    "img_025": "Airport Plot Launch Rs 11000 Token Payment",
    "img_026": "Safety Advisory: Brand Never Asks For OTP Or Card Details"
}

WHISPER_MAP = {
    "vn_001": "Hey, let me know when you reach office.",
    "vn_002": "Please call me back immediately, it's urgent!",
    "vn_003": "Check out our exclusive instant loan offers.",
    "vn_004": "Did you check the school circular notes for tomorrow?",
    "vn_005": "Sync meeting notes are updated in the doc.",
    "vn_006": "Let's catch up on the client call status.",
    "vn_007": "Special promo audio discount on new launch.",
    "vn_008": "Hoop roll-on feedback survey reminder.",
    "vn_009": "Voice update regarding your upcoming booking.",
    "vn_012": "Kurta set pickup near Gate 2 reminder.",
    "vn_014": "Plot token booking launch offer audio details."
}

def process_ocr(media_id):
    """Returns OCR text for a given image media_id."""
    return OCR_MAP.get(media_id, "")

def process_whisper(media_id):
    """Returns transcribed text for a given voice note media_id."""
    return WHISPER_MAP.get(media_id, "")

def clean_text(text):
    """Strips and normalizes whitespace in the text."""
    if not text:
        return ""
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def preprocess_message(msg):
    """
    Simulates preprocessing a single message.
    Adds raw_text, ocr_text, whisper_text, and full_text to the message dict.
    """
    raw_text = msg.get('message_text', '') or msg.get('text', '') or ''
    media_id = msg.get('media_id', '')
    media_type = msg.get('media_type', '')
    
    ocr_text = process_ocr(media_id) if media_type == 'image' else ""
    whisper_text = process_whisper(media_id) if media_type == 'voice' else ""
    
    parts = []
    if raw_text:
        parts.append(raw_text)
    if ocr_text:
        parts.append(ocr_text)
    if whisper_text:
        parts.append(whisper_text)
        
    full_text = " ".join(parts)
    full_text = clean_text(full_text)
    
    msg['raw_text'] = raw_text
    msg['ocr_text'] = ocr_text
    msg['whisper_text'] = whisper_text
    msg['full_text'] = full_text
    
    return msg

def preprocess_all(messages):
    """Preprocess a list of message dicts."""
    print("="*70)
    print("  STAGE 2: PREPROCESSING")
    print("="*70)
    
    ocr_count = 0
    whisper_count = 0
    text_count = 0
    
    processed = []
    for msg in messages:
        p_msg = preprocess_message(msg.copy())
        if p_msg['ocr_text']:
            ocr_count += 1
        if p_msg['whisper_text']:
            whisper_count += 1
        if p_msg['raw_text']:
            text_count += 1
        processed.append(p_msg)
        
    print(f"  Processed {len(messages)} messages")
    print(f"  OCR extracted: {ocr_count}")
    print(f"  Whisper transcribed: {whisper_count}")
    print(f"  Text cleaned: {text_count}")
    print()
    return processed
