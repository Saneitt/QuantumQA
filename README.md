# 🤖 Autonomous QA Agent

**Documentation-Grounded Test Case & Selenium Script Generation**

An intelligent autonomous QA agent that builds a "testing brain" from project documentation and generates executable Selenium test scripts with complete traceability to source documents.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Demo Video Script](#demo-video-script)
- [Support Documents](#support-documents)
- [Future Enhancements](#future-enhancements)

---

## 🎯 Overview

This autonomous QA agent solves the critical problem of maintaining test automation in sync with product documentation. It uses Retrieval-Augmented Generation (RAG) to ensure all generated test cases and Selenium scripts are **grounded strictly in provided documentation**, eliminating hallucinations and ensuring traceability.

### The Challenge

Traditional test automation tools often:
- ❌ Generate tests that drift from requirements
- ❌ Break frequently due to incorrect selectors
- ❌ Lack explainability and traceability
- ❌ Require repetitive manual scripting

### Our Solution

✅ **Documentation-Grounded** - Every test case cites its source  
✅ **Intelligent Selector Extraction** - Analyzes HTML DOM automatically  
✅ **Production-Ready Scripts** - WebDriverWait, error handling, clean code  
✅ **RAG-Powered** - Uses vector similarity to retrieve relevant context  
✅ **Traceable** - Clear provenance from docs to test cases to scripts  

---

## ⭐ Key Features

### Phase 1: Knowledge Base Construction
- 📄 **Multi-format Support**: PDF, Markdown, TXT, JSON, HTML
- 🧩 **Intelligent Chunking**: 500-600 char chunks with 120 char overlap
- 🧠 **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- 🗄️ **Vector Storage**: ChromaDB with persistent storage
- 🔍 **HTML Analysis**: Automatic selector extraction (id, name, class, data-test)

### Phase 2: Test Case Generation
- 🎯 **RAG Engine**: Retrieves top-K relevant documentation chunks
- 📝 **Structured Output**: JSON test cases with Test_ID, Feature, Steps, Expected_Result
- 📚 **Source Attribution**: Every test case references "Grounded_In" documents
- ✅ **Validation**: Ensures no hallucinated features
- 🔄 **Natural Language Queries**: Simple prompts like "Test discount codes"

### Phase 3: Selenium Script Generation
- ⚙️ **Production-Ready**: Selenium Python scripts with best practices
- ⏱️ **WebDriverWait**: Explicit waits for stable execution
- 🎯 **Correct Selectors**: Uses extracted selectors from HTML analysis
- 📖 **Documented**: Comments linking to source documentation
- 💾 **Downloadable**: One-click download as .py file

---

## 🏗️ Architecture

```
┌────────────────────────────┐
│      Streamlit UI          │  ← User Interface (3 Phases)
└───────────┬────────────────┘
            │
    ┌───────┴──────────────────────┐
    │   Document Ingestion Layer    │  ← backend/ingest.py
    │  (Parse, Chunk, Embed, Store) │
    └───────┬──────────────────────┘
            │
    ┌───────▼──────────────────────┐
    │     Vector Database (Chroma)  │  ← ./db/ (persistent)
    └───────┬──────────────────────┘
            │   Retrieval (RAG)
    ┌───────▼──────────────────────┐
    │      RAG Engine               │  ← backend/rag.py
    │  (Query → Retrieve → Generate)│
    └───────┬──────────────────────┘
            │
    ┌───────▼──────────────────────┐
    │  Test Case Generation Agent   │  ← GeminiAPI
    └───────┬──────────────────────┘
            │
    ┌───────▼──────────────────────┐
    │ Selenium Script Generator     │  ← backend/script_generation.py
    └──────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Rapid UI with file uploads & live outputs |
| **LLM** | OpenAI GPT-4 | Test case & script generation |
| **Embeddings** | SentenceTransformers | all-MiniLM-L6-v2 (local, lightweight) |
| **Vector DB** | ChromaDB | Persistent vector storage |
| **Chunking** | LangChain | RecursiveCharacterTextSplitter |
| **PDF Parsing** | PyMuPDF (fitz) | Extract text from PDFs |
| **HTML Parsing** | BeautifulSoup | DOM analysis & selector extraction |
| **Markdown** | python-markdown | Markdown to text conversion |
| **Automation** | Selenium Python | Output script format |
| **Data Validation** | Pydantic | Schema validation |

---

## 📦 Installation

### Prerequisites

- **Python**: 3.11+ (3.12 not supported)
- **Gemini API Key**: Required for test case generation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd autonomous-qa-agent
```

### Step 2: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using uv (recommended for faster installation)
uv sync
```

### Step 3: Set Environment Variables

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Or create a `.env` file:

```
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 4: Run the Application

```bash
streamlit run app.py --server.port 5000
```

The app will be available at `http://localhost:5000`

---

## 🚀 Usage

### Quick Start with Sample Files

1. **Launch the app**: `streamlit run app.py --server.port 5000`

2. **Phase 1 - Build Knowledge Base**:
   - Click "🚀 Load Sample Files" button
   - Click "🔨 Build Knowledge Base"
   - Wait for processing (~10-15 seconds)
   - ✅ Knowledge Base built!

3. **Phase 2 - Generate Test Cases**:
   - Enter prompt: "Generate test cases for discount code feature"
   - Click "🧪 Generate Test Cases"
   - Review generated cases in expandable cards
   - Click "✅ Select for Script" on desired test case

4. **Phase 3 - Generate Selenium Script**:
   - Click "⚙️ Generate Selenium Script"
   - Wait for script generation
   - Click "📥 Download Python Script"
   - Run the script locally!

### Advanced Usage

#### Upload Custom Documents

**Phase 1:**
1. Upload 3-5 support documents (PDF, MD, TXT, JSON)
2. Upload your target HTML file
3. Click "Build Knowledge Base"

**Supported file types:**
- `.pdf` - Product specs, requirements
- `.md` - Markdown documentation
- `.txt` - Plain text guides
- `.json` - API endpoints, configurations
- `.html` - Target web page

#### Example Prompts for Phase 2

```
✅ Good Prompts:
- "Generate positive and negative test cases for the discount code feature"
- "Create test cases to validate the checkout form"
- "Test all shipping method scenarios"
- "Generate edge cases for cart quantity management"

❌ Avoid:
- "Test everything" (too vague)
- "Make tests" (not specific)
```

---

## 📁 Project Structure

```
autonomous-qa-agent/
│
├── app.py                    # Main Streamlit application
│
├── backend/
│   ├── __init__.py
│   ├── ingest.py             # Document parsing & embedding
│   ├── rag.py                # RAG engine with OpenAI
│   ├── selectors.py          # HTML selector extraction
│   └── script_generation.py  # Selenium script generator
│
├── assets/                   # Sample documents
│   ├── checkout.html         # E-Shop checkout page
│   ├── product_specs.md      # Product specifications
│   ├── ui_ux_guide.txt       # UI/UX guidelines
│   └── api_endpoints.json    # API documentation
│
├── db/                       # ChromaDB persistent storage
│
├── pyproject.toml            # Project dependencies
├── README.md                 # This file
└── .streamlit/
    └── config.toml           # Streamlit configuration
```

---

## 🔬 How It Works

### 1. Document Ingestion Pipeline

```python
File Upload → Parser Selection → Text Extraction → Chunking → Embedding → Vector Storage
```

**Details:**
- **PDF**: PyMuPDF extracts text from all pages
- **Markdown**: Converted to plain text via python-markdown
- **JSON**: Flattened into readable pseudo-document format
- **HTML**: BeautifulSoup extracts text + DOM selectors
- **Chunking**: 500-600 char chunks, 120 char overlap
- **Metadata**: source_document, doc_type, chunk_id, selectors

### 2. RAG-Powered Test Case Generation

```python
User Query → Embed Query → Retrieve Top-K Chunks → Compile Context → LLM Generation → Validate → Return Test Cases
```

**Strict Grounding Rules:**
- ✅ Only use features from retrieved documentation
- ✅ Every test case must include "Grounded_In" field
- ✅ Reference exact filenames
- ❌ No hallucinated features
- ❌ No assumptions beyond documentation

### 3. Selenium Script Generation

```python
Test Case → Retrieve HTML Selectors → Retrieve Docs → Build Prompt → LLM Generation → Format Script → Return Python Code
```

**Script Features:**
- Chrome WebDriver initialization
- WebDriverWait with 10-20 second timeouts
- Correct selectors from HTML analysis
- Comments referencing source documents
- Error handling and logging
- Modular function structure

---

## 🎬 Demo Video Script

### 0:00 - 0:30 | Introduction
- Welcome and project overview
- Problem statement: keeping tests in sync with docs
- Solution preview: autonomous QA agent

### 0:30 - 1:30 | Phase 1: Upload & Build KB
- Show Streamlit UI
- Click "Load Sample Files"
- Click "Build Knowledge Base"
- Show progress indicators
- Highlight processing stats (files, chunks, types)

### 1:30 - 2:30 | Phase 2: Generate Test Cases
- Navigate to Phase 2
- Enter prompt: "Generate test cases for discount code"
- Click "Generate Test Cases"
- Show JSON table output
- Expand test case to show steps and "Grounded_In" field
- Highlight source attribution

### 2:30 - 4:00 | Phase 3: Generate Selenium Script
- Select a test case
- Navigate to Phase 3
- Show selected test case details
- Click "Generate Selenium Script"
- Show progress
- Highlight generated code:
  - WebDriverWait usage
  - Correct selectors
  - Comments with source references

### 4:00 - 5:00 | Download & Execute (Optional)
- Download the script
- Show file in VS Code
- Run script locally (optional)
- Show successful test execution

### 5:00 - 5:30 | Summary & Benefits
- Recap 3 phases
- Emphasize documentation grounding
- Highlight traceability
- Call to action

---

## 📚 Support Documents

### Included Sample Assets

#### checkout.html
- Single-page e-commerce checkout flow
- 3 products with "Add to Cart" functionality
- Cart with quantity management
- Discount code input (SAVE15, SAVE20)
- Customer details form (Name, Email, Address)
- Shipping options (Standard/Express)
- Payment methods (Credit Card/PayPal)
- Form validation with inline errors

#### product_specs.md
- Product catalog with prices
- Shopping cart functionality rules
- Discount code specifications (SAVE15 = 15%, SAVE20 = 20%)
- Shipping cost rules (Standard = Free, Express = $10)
- Payment methods
- Form validation rules (regex patterns, required fields)
- Business logic

#### ui_ux_guide.txt
- Color palette specifications
- Typography guidelines
- Button specifications (Pay Now button = green!)
- Form validation error display (red text)
- Input field styling
- Layout spacing rules
- Accessibility requirements

#### api_endpoints.json
- Product catalog endpoints
- Cart management APIs
- Discount code validation endpoint
- Shipping calculation API
- Order submission endpoint
- Payment processing specifications

---

## 🚀 Future Enhancements

### Planned Features

1. **Playwright Support**
   - Alternative to Selenium for faster execution
   - Better reliability for modern web apps

2. **Test Execution in UI**
   - Run scripts directly from Streamlit
   - Capture screenshots and logs
   - Display pass/fail results

3. **Multi-Page HTML Support**
   - Handle complex multi-page applications
   - Automatic page object model generation

4. **Assertion Auto-Generation**
   - DOM validation for expected results
   - Smart assertion recommendations

5. **Test Coverage Dashboard**
   - Visual map of tested vs untested features
   - Document utilization analytics
   - Gap analysis

6. **Cost Estimation**
   - Token usage tracking
   - OpenAI API cost projection
   - Budget alerts

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is provided as-is for educational and assessment purposes.

---

## 🙏 Acknowledgments

- **Assignment by**: OceanAI
- **Technologies**: OpenAI, ChromaDB, SentenceTransformers, Streamlit, Selenium
- **Inspiration**: The need for traceable, documentation-grounded QA automation

---

## 📞 Support

For questions or issues:
- Check the demo video for usage guidance
- Review the sample assets in `assets/` folder
- Ensure OpenAI API key is set correctly
- Verify Python version is 3.11

---

**Built with ❤️ for autonomous, intelligent QA testing**
