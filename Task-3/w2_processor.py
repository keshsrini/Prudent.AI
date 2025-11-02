"""
Simple W-2 processor module with single entrypoint function
"""
import os
import re
import json
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def process_w2(file_path):
    """
    Main entrypoint function to process W-2 file
    
    Args:
        file_path (str): Path to W-2 image or PDF file
        
    Returns:
        dict: {fields, insights, quality}
    """
    test_mode = os.getenv('TEST_MODE', 'true').lower() == 'true'
    
    if test_mode:
        return _mock_response()
    
    # Configure Gemini
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Read and process file
    with open(file_path, 'rb') as f:
        image_data = f.read()
    
    extraction_prompt = """
Analyze this W-2 tax form image and extract the data. Return your response as valid JSON only, with no additional text or explanation.

{
    "employee": {
        "name": "",
        "address": {"street": "", "city": "", "state": "", "zip": ""},
        "ssn_last4": ""
    },
    "employer": {
        "name": "",
        "address": {"street": "", "city": "", "state": "", "zip": ""},
        "ein": ""
    },
    "federal_boxes": {
        "box1_wages": 0,
        "box2_federal_tax": 0,
        "box3_ss_wages": 0,
        "box4_ss_tax": 0,
        "box5_medicare_wages": 0,
        "box6_medicare_tax": 0
    },
    "state_local": {
        "state_code": "",
        "state_wages": 0,
        "state_tax": 0
    }
}

Extract the exact values from the W-2 form. For SSN, only include last 4 digits. Convert amounts to numbers.
    """
    
    try:
        response = model.generate_content([extraction_prompt, {"mime_type": "image/jpeg", "data": image_data}])
        response_text = response.text.strip()
        
        # Try to extract JSON from response
        if '{' in response_text:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_text = response_text[json_start:json_end]
            fields = json.loads(json_text)
        else:
            fields = json.loads(response_text)
        
        # Mask any SSN/EIN in the response
        fields_str = json.dumps(fields)
        fields_str = re.sub(r'\b\d{3}-\d{2}-(\d{4})\b', r'XXX-XX-\1', fields_str)
        fields = json.loads(fields_str)
        
    except Exception as e:
        fields = {"error": f"Extraction failed: {str(e)}"}
    
    # Generate insights
    insights = _generate_insights(fields)
    
    return {
        "fields": fields,
        "insights": insights,
        "quality": {"confidence": "medium", "warnings": []}
    }

def _generate_insights(fields):
    """Generate tax insights from extracted fields"""
    insights = []
    
    if "federal_boxes" in fields and "error" not in fields:
        fb = fields["federal_boxes"]
        wages = fb.get("box1_wages", 0)
        fed_tax = fb.get("box2_federal_tax", 0)
        
        if wages > 0:
            rate = (fed_tax / wages) * 100
            insights.append(f"Federal withholding: {rate:.1f}% of wages")
            
            if rate < 12:
                insights.append("Low withholding - may owe taxes at filing")
            elif rate > 22:
                insights.append("High withholding - likely refund")
        
        # Social Security cap check (2023: $160,200)
        ss_wages = fb.get("box3_ss_wages", 0)
        if ss_wages >= 160000:
            insights.append("Near Social Security wage cap")
    
    if "state_local" in fields and fields["state_local"].get("state_code"):
        state = fields["state_local"]["state_code"]
        insights.append(f"State tax filing required: {state}")
    
    return insights

def _mock_response():
    """Mock data for test mode"""
    return {
        "fields": {
            "employee": {
                "name": "SAMPLE EMPLOYEE",
                "address": {"street": "123 TEST ST", "city": "TESTVILLE", "state": "TX", "zip": "12345"},
                "ssn_last4": "9999"
            },
            "employer": {
                "name": "TEST COMPANY LLC",
                "address": {"street": "456 CORP BLVD", "city": "BUSINESS CITY", "state": "TX", "zip": "54321"},
                "ein": "XX-XXXXXXX99"
            },
            "federal_boxes": {
                "box1_wages": 65000.00,
                "box2_federal_tax": 9750.00,
                "box3_ss_wages": 65000.00,
                "box4_ss_tax": 4030.00,
                "box5_medicare_wages": 65000.00,
                "box6_medicare_tax": 942.50
            },
            "state_local": {
                "state_code": "TX",
                "state_wages": 65000.00,
                "state_tax": 0.00
            }
        },
        "insights": [
            "Federal withholding: 15.0% of wages",
            "State tax filing required: TX"
        ],
        "quality": {"confidence": "test", "warnings": ["Mock data used"]}
    }

if __name__ == "__main__":
    # Simple CLI usage
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "896-1-1024x721.jpg"
    
    result = process_w2(file_path)
    print(json.dumps(result, indent=2))