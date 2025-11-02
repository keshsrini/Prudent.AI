# W-2 Parser & Insight Generator

Simple Python application that extracts W-2 tax form data using Google's Gemini AI.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API key in `.env`:
```
GEMINI_API_KEY=your_actual_api_key
TEST_MODE=false
```

## Usage

### As a module:
```python
from w2_processor import process_w2
result = process_w2("896-1-1024x721.jpg")
print(result["insights"])
```

### Command line:
```bash
python w2_processor.py
# or
python main.py
```

## Features

- **Single entrypoint**: `process_w2(file_path)` function
- **Privacy-focused**: SSN/EIN masking, no data persistence
- **Gemini AI integration**: Uses vision API for extraction
- **Tax insights**: Withholding analysis, filing requirements
- **Test mode**: Mock responses when `TEST_MODE=true`

## Output Structure

```json
{
  "fields": {
    "employee": {"name": "", "address": {}, "ssn_last4": ""},
    "employer": {"name": "", "address": {}, "ein": ""},
    "federal_boxes": {"box1_wages": 0, "box2_federal_tax": 0, ...},
    "state_local": {"state_code": "", "state_wages": 0, "state_tax": 0}
  },
  "insights": ["Federal withholding: 13.0% of wages", ...],
  "quality": {"confidence": "medium", "warnings": []}
}
```

## Files

- `w2_processor.py` - Main module with `process_w2()` function
- `main.py` - CLI wrapper
- `extraction_prompt.txt` - Gemini extraction prompt template
- `insights_prompt.txt` - Insights generation prompt template
- `896-1-1024x721.jpg` - Sample W-2 image