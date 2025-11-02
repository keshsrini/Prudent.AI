import os
import re
import json
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class W2Analyzer:
    def __init__(self):
        self.test_mode = os.getenv('TEST_MODE', 'true').lower() == 'true'
        if not self.test_mode:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    def mask_ssn(self, text):
        """Mask SSN to show only last 4 digits"""
        return re.sub(r'\b\d{3}-\d{2}-(\d{4})\b', r'XXX-XX-\1', text)

    def process_w2(self, file_path):
        """Main function to process W-2 file"""
        if self.test_mode:
            return self._mock_response()
        
        # Read image and send to Gemini
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        # Extraction prompt
        extraction_prompt = """
        Extract all W-2 tax form data from this image and return ONLY valid JSON with this structure:
        {
            "employee": {
                "name": "",
                "address": {"street": "", "city": "", "state": "", "zip": ""},
                "ssn_last4": "",
                "ein_last4": ""
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
        """
        
        try:
            response = self.model.generate_content([extraction_prompt, {"mime_type": "image/jpeg", "data": image_data}])
            fields = json.loads(response.text.strip())
        except:
            fields = {"error": "Failed to extract data"}
        
        # Generate insights
        insights = self._generate_insights(fields)
        
        return {
            "fields": fields,
            "insights": insights,
            "quality": {"confidence": "medium", "warnings": []}
        }

    def _generate_insights(self, fields):
        """Generate basic insights from extracted data"""
        insights = []
        
        if "federal_boxes" in fields:
            fb = fields["federal_boxes"]
            if fb.get("box1_wages", 0) > 0:
                withholding_rate = (fb.get("box2_federal_tax", 0) / fb["box1_wages"]) * 100
                insights.append(f"Federal withholding rate: {withholding_rate:.1f}%")
                
                if withholding_rate < 10:
                    insights.append("Low federal withholding - may owe taxes")
                elif withholding_rate > 25:
                    insights.append("High federal withholding - likely refund")
        
        if "state_local" in fields and fields["state_local"].get("state_code"):
            insights.append(f"State filing required: {fields['state_local']['state_code']}")
        
        return insights

    def _mock_response(self):
        """Mock response for test mode"""
        return {
            "fields": {
                "employee": {
                    "name": "JOHN DOE",
                    "address": {"street": "123 MAIN ST", "city": "ANYTOWN", "state": "CA", "zip": "12345"},
                    "ssn_last4": "1234",
                    "ein_last4": "5678"
                },
                "employer": {
                    "name": "SAMPLE COMPANY INC",
                    "address": {"street": "456 BUSINESS AVE", "city": "CORPORATE", "state": "CA", "zip": "54321"},
                    "ein": "XX-XXXXXXX78"
                },
                "federal_boxes": {
                    "box1_wages": 50000.00,
                    "box2_federal_tax": 7500.00,
                    "box3_ss_wages": 50000.00,
                    "box4_ss_tax": 3100.00,
                    "box5_medicare_wages": 50000.00,
                    "box6_medicare_tax": 725.00
                },
                "state_local": {
                    "state_code": "CA",
                    "state_wages": 50000.00,
                    "state_tax": 2500.00
                }
            },
            "insights": [
                "Federal withholding rate: 15.0%",
                "State filing required: CA",
                "Standard withholding rates detected"
            ],
            "quality": {"confidence": "high", "warnings": ["Test mode - mock data"]}
        }

def main():
    analyzer = W2Analyzer()
    
    # Process the sample W-2
    w2_file = Path("896-1-1024x721.jpg")
    
    if not w2_file.exists():
        print("W-2 file not found!")
        return
    
    print("Processing W-2...")
    result = analyzer.process_w2(w2_file)
    
    print("\n" + "="*50)
    print("W-2 ANALYSIS RESULTS")
    print("="*50)
    
    # Display results
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()