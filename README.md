# Medical Bill Line Item Extraction API

A FastAPI-based solution for extracting line items from medical bills using Google's Gemini Vision API with a two-step OCR + structured extraction approach.

## Problem Statement

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
| ✅ Accepts document URL (as required) |
| ✅ Exact match with requirements |
| ✅ API key in .env file |
| ✅ Full token usage tracking |
| ✅ Gemini Vision (better accuracy) |
| ✅ All fields: page_no, page_type, etc. |
| ✅ FastAPI default: Port 8000 |

---

##  Installation & Setup

### Step 1: Install Dependencies

```bash
# Remove old packages
pip uninstall pytesseract pdf2image -y

# Install new requirements
pip install -r requirements.txt
```

### Step 2: Create .env File

**Create manually**
1. Create a file named `.env` (with the dot)
2. Add this line:
```
GEMINI_API_KEY=AIza...................
```
3. Save the file

### Step 3: Verify Setup

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ API Key loaded' if os.getenv('GEMINI_API_KEY') else '✗ Missing')"
```

Should output: `✓ API Key loaded`

---

##  Running the API

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

**You're all set start enter url and get result**

