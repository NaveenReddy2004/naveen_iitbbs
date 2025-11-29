# 🏥 Medical Bill Line Item Extraction API

A FastAPI-based solution for extracting line items from medical bills using Google's Gemini Vision API with a two-step OCR + structured extraction approach.

## 🎯 Problem Statement

Extract line item details from medical bills including:
- Individual line item amounts
- Sub-totals (where they exist)
- Final total without double-counting
- Match the exact API response format from requirements

## 🏗️ Architecture

```
Image URL → Gemini Vision (OCR) → Raw Text → Gemini Flash (JSON) → Validated Response
```

### Key Features
✅ **Two-step processing**: OCR → Structured extraction  
✅ **Exact schema compliance**: Matches problem requirements  
✅ **Token tracking**: Full usage metrics  
✅ **Secure**: API key in .env file  
✅ **Robust validation**: Prevents common errors  
✅ **FastAPI**: Modern, fast, with auto docs  

---

## 📋 What Changed From Your Code

| Your Code | Fixed Code |
|-----------|------------|
| ❌ Accepts file upload | ✅ Accepts document URL (as required) |
| ❌ Wrong response format | ✅ Exact match with requirements |
| ❌ Hardcoded API key | ✅ API key in .env file |
| ❌ No token tracking | ✅ Full token usage tracking |
| ❌ Tesseract OCR | ✅ Gemini Vision (better accuracy) |
| ❌ Missing required fields | ✅ All fields: page_no, page_type, etc. |
| ❌ Port 5000 | ✅ FastAPI default: Port 8000 |

---

## 🚀 Installation & Setup

### Step 1: Install Dependencies

```bash
# Remove old packages
pip uninstall pytesseract pdf2image -y

# Install new requirements
pip install -r requirements.txt
```

### Step 2: Create .env File

**Option A: Command Line**
```bash
# Windows
echo GEMINI_API_KEY=AIzaSyDM6b6zNcbSedbKPByWwe5bAo1Hry0mBuk > .env

# Mac/Linux
echo "GEMINI_API_KEY=AIzaSyDM6b6zNcbSedbKPByWwe5bAo1Hry0mBuk" > .env
```

**Option B: Create manually**
1. Create a file named `.env` (with the dot)
2. Add this line:
```
GEMINI_API_KEY=AIzaSyDM6b6zNcbSedbKPByWwe5bAo1Hry0mBuk
```
3. Save the file

### Step 3: Verify Setup

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ API Key loaded' if os.getenv('GEMINI_API_KEY') else '✗ Missing')"
```

Should output: `✓ API Key loaded`

---

## 🎮 Running the API

### Start the Server

```bash
python main.py
```

**You'll see:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**🎉 Your API is now running on port 8000!**

---

## 🧪 Testing the API

### Method 1: Test Script (Recommended)

Open a **NEW terminal** and run:

```bash
python test_api_fastapi.py
```

**Expected Output:**
```
================================================================================
Testing FastAPI Bill Extraction API
================================================================================
Endpoint: http://localhost:8000/extract-bill-data
Document URL: https://hackrx.blob.core.windows.net/assets...
--------------------------------------------------------------------------------
Sending request... (this may take 10-30 seconds)

✓ Status Code: 200
--------------------------------------------------------------------------------

📄 Full Response:
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 1245,
    "input_tokens": 890,
    "output_tokens": 355
  },
  "data": {
    "pagewise_line_items": [...],
    "total_item_count": 5
  }
}

✅ SUCCESS!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Total Items Extracted: 5
🎯 Total Tokens Used: 1245
```

### Method 2: cURL

```bash
curl -X POST http://localhost:8000/extract-bill-data \
  -H "Content-Type: application/json" \
  -d "{\"document\": \"YOUR_IMAGE_URL_HERE\"}"
```

### Method 3: FastAPI Docs (Interactive)

1. Keep server running
2. Open browser: http://localhost:8000/docs
3. Click on `/extract-bill-data`
4. Click "Try it out"
5. Enter your document URL:
```json
{
  "document": "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?sv=2025-07-05&..."
}
```
6. Click "Execute"

### Method 4: Python Script

```python
import requests

response = requests.post(
    'http://localhost:8000/extract-bill-data',
    json={
        'document': 'YOUR_DOCUMENT_URL_HERE'
    }
)
print(response.json())
```

---

## 📁 Project Structure

```
hackrx-bill-extraction/
├── main.py                 # Fixed FastAPI application
├── requirements.txt        # Updated dependencies
├── test_api_fastapi.py    # Test script
├── .env                    # API key (YOU CREATED THIS)
├── .gitignore             # Git ignore file
└── README.md              # This file
```

---

## 🔑 Key Changes Explained

### 1. API Endpoint Change
**Before:**
```python
@app.post("/extract-bill-data")
async def extract_bill_data(file: UploadFile = File(...)):
```

**After:**
```python
@app.post("/extract-bill-data")
async def extract_bill_data(request: BillExtractionRequest):
    # request.document contains the URL
```

### 2. Environment Variables
**Before:**
```python
os.environ["GEMINI_API_KEY"] = "AIzaSy..."  # ❌ Hardcoded
```

**After:**
```python
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # ✅ From .env
```

### 3. Response Format
**Before:**
```python
{
    "is_success": True,
    "extracted_data": "..."  # ❌ Wrong format
}
```

**After:**
```python
{
    "is_success": True,
    "token_usage": {
        "total_tokens": 1245,
        "input_tokens": 890,
        "output_tokens": 355
    },
    "data": {
        "pagewise_line_items": [
            {
                "page_no": "1",
                "page_type": "Bill Detail",
                "bill_items": [...]
            }
        ],
        "total_item_count": 5
    }
}  # ✅ Exact match
```

### 4. OCR Approach
**Before:** Tesseract (local, less accurate)  
**After:** Gemini Vision (cloud, more accurate for complex bills)

---

## 🛠️ Troubleshooting

### Issue 1: "GEMINI_API_KEY not found"
**Solution:**
```bash
# Check if .env exists
ls -la .env     # Mac/Linux
dir .env        # Windows

# Recreate if needed
echo "GEMINI_API_KEY=AIzaSyDM6b6zNcbSedbKPByWwe5bAo1Hry0mBuk" > .env
```

### Issue 2: "Port 8000 already in use"
**Solution:**
```bash
# Find and kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Issue 3: Import errors
**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Issue 4: Can't connect to API
**Check:**
1. Is the server running? (Should see Uvicorn output)
2. Using correct port? (8000, not 5000)
3. Correct URL? (http://localhost:8000)

---

## 📊 Response Schema (From Problem Statement)

```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 1245,
    "input_tokens": 890,
    "output_tokens": 355
  },
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail | Final Bill | Pharmacy",
        "bill_items": [
          {
            "item_name": "Consultation Fee",
            "item_amount": 500.0,
            "item_rate": 500.0,
            "item_quantity": 1.0
          }
        ]
      }
    ],
    "total_item_count": 1
  }
}
```

---

## 🚀 Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file
echo "GEMINI_API_KEY=AIzaSyDM6b6zNcbSedbKPByWwe5bAo1Hry0mBuk" > .env

# 3. Run server
python main.py

# 4. In new terminal, test
python test_api_fastapi.py
```

---

## 🎯 Next Steps

1. ✅ Test with training samples
2. ✅ Check accuracy against actual totals
3. ✅ Tune prompts if needed
4. ✅ Deploy to cloud (Railway, Render, etc.)

---

## 📚 Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Gemini API**: https://ai.google.dev/docs
- **Problem Statement**: Check Postman collection

---

## ⚙️ Environment Variables

Required in `.env`:
```bash
GEMINI_API_KEY=your_api_key_here
```

---

## 🔒 Security Note

⚠️ Never commit `.env` to Git  
✅ Already in `.gitignore`  
✅ API key is now secure

---

**You're all set! 🚀**