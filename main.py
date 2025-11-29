import os
import json
import re
import requests
from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found! Create .env file with your API key")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize models
vision_model = genai.GenerativeModel('gemini-2.5-flash')
text_model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI(
    title="Medical Bill Extraction API",
    version="1.0.0",
    description="Extract line items from medical bills - Accepts URLs only"
)


# Request model - ONLY accepts URL
class BillExtractionRequest(BaseModel):
    document: str  # Must be a valid URL (http/https)


class TokenTracker:
    """Track token usage across API calls"""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
    
    def add_usage(self, response):
        """Add token usage from a Gemini response"""
        if hasattr(response, 'usage_metadata'):
            self.input_tokens += response.usage_metadata.prompt_token_count
            self.output_tokens += response.usage_metadata.candidates_token_count
            self.total_tokens += response.usage_metadata.total_token_count


def download_image_from_url(url: str) -> Image.Image:
    """
    Download image from URL ONLY
    No base64 support - URLs only as per requirement
    """
    # Validate it's a proper URL
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must start with http:// or https://"
        )
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download image from URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process image: {str(e)}"
        )


def extract_text_with_vision(image: Image.Image, tracker: TokenTracker) -> str:
    """
    Step 1: Extract text from image using Gemini Vision (OCR)
    """
    ocr_prompt = """
    You are an expert OCR system. Extract ALL text from this medical bill image.
    
    Instructions:
    1. Extract EVERY piece of text you see, maintaining the original layout
    2. Include headers, line items, amounts, dates, and any other text
    3. Preserve the structure and relationships between items
    4. Pay special attention to:
       - Item names/descriptions
       - Quantities
       - Rates/unit prices
       - Amounts/totals
       - Any subtotals or grand totals
    5. If there are tables, maintain the tabular structure
    
    Return ONLY the extracted text, nothing else.
    """
    
    try:
        response = vision_model.generate_content([ocr_prompt, image])
        tracker.add_usage(response)
        return response.text
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR extraction failed: {str(e)}"
        )


def parse_to_json(ocr_text: str, tracker: TokenTracker) -> dict:
    """
    Step 2: Parse OCR text into structured JSON format
    """
    extraction_prompt = f"""
    You are a medical bill data extraction expert. Extract line item details from this bill text.
    
    BILL TEXT:
    {ocr_text}
    
    CRITICAL INSTRUCTIONS:
    1. ONLY extract MONETARY line items (products/services with amounts)
    2. DO NOT extract dates, invoice numbers, or non-monetary fields as amounts
    3. Each line item MUST have:
       - item_name: The product/service description (string) - EXACTLY as in bill
       - item_amount: The NET amount AFTER discounts (float, currency value)
       - item_rate: The unit price (float, currency value)
       - item_quantity: The quantity purchased (float, can be 1 if not specified)
    
    4. Determine page_type from content:
       - "Bill Detail": Detailed itemized charges
       - "Final Bill": Summary/total page
       - "Pharmacy": Pharmacy/medication items
    
    5. VALIDATION RULES:
       - item_amount should equal item_rate × item_quantity (or close to it)
       - Only include items with valid currency amounts
       - Skip header rows, totals rows, and non-item entries
       - DO NOT include subtotals or grand totals as line items
    
    6. COMMON MISTAKES TO AVOID:
       - DO NOT put invoice date/time in item_amount
       - DO NOT put invoice number in item_amount
       - DO NOT include tax rows as line items
       - DO NOT include "Total", "Subtotal", "Grand Total" as line items
    
    Return ONLY valid JSON in this exact format:
    {{
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
            {{
                "item_name": "Item description",
                "item_amount": 100.50,
                "item_rate": 50.25,
                "item_quantity": 2.0
            }}
        ]
    }}
    
    Return ONLY the JSON, no markdown backticks, no explanations.
    """
    
    try:
        response = text_model.generate_content(extraction_prompt)
        tracker.add_usage(response)
        
        # Clean and parse JSON
        json_text = response.text.strip()
        # Remove markdown code blocks if present
        json_text = re.sub(r'^```json\s*', '', json_text)
        json_text = re.sub(r'^```\s*', '', json_text)
        json_text = re.sub(r'\s*```$', '', json_text)
        
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


def validate_and_clean(data: dict) -> dict:
    """Validate and clean extracted data"""
    if 'bill_items' not in data:
        data['bill_items'] = []
    
    cleaned_items = []
    for item in data['bill_items']:
        # Ensure all required fields exist
        if not all(k in item for k in ['item_name', 'item_amount', 'item_rate', 'item_quantity']):
            continue
        
        # Convert to proper types
        try:
            item['item_amount'] = float(item['item_amount'])
            item['item_rate'] = float(item['item_rate'])
            item['item_quantity'] = float(item['item_quantity'])
        except (ValueError, TypeError):
            continue
        
        # Skip items with invalid amounts
        if item['item_amount'] <= 0:
            continue
        
        # Skip if amount looks like a date/ID (very large numbers)
        if item['item_amount'] > 1000000:
            continue
        
        cleaned_items.append(item)
    
    data['bill_items'] = cleaned_items
    return data


@app.post("/extract-bill-data")
async def extract_bill_data(request: BillExtractionRequest):
    """
    Main API endpoint - Extracts line items from medical bill
    
    Accepts ONLY URLs:
    {
        "document": "https://example.com/bill.png"
    }
    
    Returns EXACT format as per requirement:
    {
        "is_success": true,
        "data": {
            "pagewise_line_items": [...],
            "token_usage": {...},
            "total_item_count": 12
        }
    }
    """
    tracker = TokenTracker()
    
    try:
        # Step 1: Download image from URL
        image = download_image_from_url(request.document)
        
        # Step 2: Extract text using Gemini Vision (OCR)
        ocr_text = extract_text_with_vision(image, tracker)
        
        # Step 3: Parse to structured JSON
        structured_data = parse_to_json(ocr_text, tracker)
        
        # Step 4: Validate and clean
        validated_data = validate_and_clean(structured_data)
        
        # Step 5: Build response in EXACT format
        response = {
            "is_success": True,
            "data": {
                "pagewise_line_items": [validated_data],
                "token_usage": {
                    "total_tokens": tracker.total_tokens,
                    "input_tokens": tracker.input_tokens,
                    "output_tokens": tracker.output_tokens
                },
                "total_item_count": len(validated_data['bill_items'])
            }
        }
        
        return JSONResponse(content=response, status_code=200)
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Handle unexpected errors
        return JSONResponse(
            content={
                "is_success": False,
                "error": str(e),
                "data": {
                    "pagewise_line_items": [],
                    "token_usage": {
                        "total_tokens": tracker.total_tokens,
                        "input_tokens": tracker.input_tokens,
                        "output_tokens": tracker.output_tokens
                    },
                    "total_item_count": 0
                }
            },
            status_code=500
        )


@app.get("/")
def home():
    """Root endpoint with API info"""
    return {
        "service": "Medical Bill Line Item Extraction API",
        "version": "1.0.0",
        "status": "running",
        "accepts": "URLs only (http/https)",
        "endpoints": {
            "/extract-bill-data": "POST - Extract line items from bill image URL",
            "/health": "GET - Health check",
            "/docs": "GET - Interactive API documentation"
        },
        "example_request": {
            "document": "https://example.com/medical-bill.png"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Bill Extraction API",
        "gemini_configured": GEMINI_API_KEY is not None
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 80)
    print("Starting Bill Extraction API")
    print("=" * 80)
    print(f"✓ Gemini API Key: {'Configured' if GEMINI_API_KEY else '❌ MISSING'}")
    print(f"✓ Server: http://localhost:8000")
    print(f"✓ Docs: http://localhost:8000/docs")
    print(f"✓ Health: http://localhost:8000/health")
    print("=" * 80)
    print("\n API accepts ONLY URLs")
    print("   Request: {'document': 'https://example.com/bill.png'}\n")
    

    uvicorn.run(app, host="0.0.0.0", port=8000)
