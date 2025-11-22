from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
import sys
import time
import io
import zipfile

sys.path.append(str(Path(__file__).parent))

from backend.ingest import DocumentIngestion
from backend.rag import RAGEngine
from backend.script_generation import SeleniumScriptGenerator


st.set_page_config(
    page_title="QuantumQA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #507192;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #3498db;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'kb_built' not in st.session_state:
    st.session_state.kb_built = False
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = []
if 'selected_test_cases' not in st.session_state:  # Changed to plural
    st.session_state.selected_test_cases = []
if 'generated_scripts' not in st.session_state:  # Changed to plural
    st.session_state.generated_scripts = {}
if 'uploaded_files_data' not in st.session_state:
    st.session_state.uploaded_files_data = []


def main():
    st.markdown('<div class="main-header">🤖 QuantumQA - Autonomous QA Agent</div>', unsafe_allow_html=True)
    st.markdown("**Documentation-Grounded Test Case & Selenium Script Generation**")
    
    with st.sidebar:
        st.markdown("### 📋 Navigation")
        st.markdown("---")
        
        phase = st.radio(
            "Select Phase:",
            ["📥 Phase 1: Knowledge Base", "🧪 Phase 2: Test Case Generation", "⚙️ Phase 3: Script Generation"],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        
        if st.session_state.kb_built:
            st.success("✅ Knowledge Base: Built")
        else:
            st.warning("⚠️ Knowledge Base: Not Built")
        
        st.info(f"📝 Test Cases: {len(st.session_state.test_cases)}")
        
        # Updated to show multiple selections
        if st.session_state.selected_test_cases:
            st.info(f"🎯 Selected: {len(st.session_state.selected_test_cases)} test case(s)")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        This autonomous QA agent:
        - Builds a testing brain from documentation
        - Generates grounded test cases
        - Creates executable Selenium scripts
        """)
    
    if "Phase 1" in phase:
        render_phase_1()
    elif "Phase 2" in phase:
        render_phase_2()
    elif "Phase 3" in phase:
        render_phase_3()


def render_phase_1():
    st.markdown('<div class="section-header">Phase 1: Knowledge Base Builder</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Upload your project documentation and HTML file to build the knowledge base. The system will:
    - Parse documents (PDF, MD, TXT, JSON, HTML)
    - Extract text and HTML selectors
    - Generate embeddings using SentenceTransformers
    - Store chunks in ChromaDB with metadata
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📄 Upload Support Documents")
        st.markdown("Upload 3-5 documentation files (PDF, MD, TXT, JSON)")
        
        support_docs = st.file_uploader(
            "Support Documents",
            type=['pdf', 'md', 'txt', 'json'],
            accept_multiple_files=True,
            key="support_docs",
            label_visibility="collapsed"
        )
        
        st.markdown("#### 🌐 Upload HTML File")
        st.markdown("Upload the checkout.html or your target web page")
        
        html_file = st.file_uploader(
            "HTML File",
            type=['html', 'htm'],
            accept_multiple_files=False,
            key="html_file",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("#### 📝 Quick Test with Sample Files")
        if st.button("🚀 Load Sample Files"):
            st.session_state.use_sample_files = True
            st.success("Sample files will be used when building KB")
        
        st.markdown("---")
        
        st.markdown("#### 💡 Tips")
        st.info("""
        **Recommended documents:**
        - Product specifications
        - UI/UX guidelines
        - API endpoints
        - Feature descriptions
        """)
    
    st.markdown("---")
    
    col_build, col_reset = st.columns([3, 1])
    
    with col_build:
        build_button = st.button("🔨 Build Knowledge Base", key="build_kb", use_container_width=True)
    
    with col_reset:
        reset_button = st.button("🗑️ Reset KB", key="reset_kb", use_container_width=True)
    
    if reset_button:
        try:
            from chromadb import PersistentClient
            client = PersistentClient(path="./db")
            try:
                client.delete_collection("qa_knowledge_base")
                st.session_state.kb_built = False
                st.session_state.test_cases = []
                st.session_state.selected_test_cases = []  # Reset multi-select
                st.session_state.generated_scripts = {}  # Reset scripts
                st.success("✅ Knowledge Base reset successfully!")
            except:
                st.warning("⚠️ Knowledge Base was already empty")
        except Exception as e:
            st.error(f"❌ Error resetting KB: {str(e)}")
    
    if build_button:
        files_to_process = []
        
        if st.session_state.get('use_sample_files', False):
            sample_dir = Path("assets")
            if sample_dir.exists():
                for file_path in sample_dir.glob("*"):
                    if file_path.is_file():
                        with open(file_path, 'rb') as f:
                            files_to_process.append((str(file_path), f.read(), file_path.name))
        else:
            if support_docs:
                for doc in support_docs:
                    files_to_process.append((doc.name, doc.read(), doc.name))
            
            if html_file:
                files_to_process.append((html_file.name, html_file.read(), html_file.name))
        
        if not files_to_process:
            st.error("❌ Please upload at least one file or use sample files")
            return
        
        st.session_state.uploaded_files_data = files_to_process
        
        with st.spinner("🔄 Building Knowledge Base..."):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Initializing ingestion engine...")
                progress_bar.progress(10)
                
                ingestion = DocumentIngestion(persist_directory="./db", reset=True)
                
                status_text.text(f"Processing {len(files_to_process)} files...")
                progress_bar.progress(30)
                
                stats = ingestion.ingest_documents(files_to_process)
                
                status_text.text("Generating embeddings and storing in ChromaDB...")
                progress_bar.progress(80)
                
                st.session_state.kb_built = True
                
                progress_bar.progress(100)
                status_text.text("✅ Knowledge Base built successfully!")
                
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown("### ✅ Knowledge Base Built Successfully!")
                st.markdown(f"**Total Files Processed:** {stats['total_files']}")
                st.markdown(f"**Total Chunks Created:** {stats['total_chunks']}")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("#### 📊 Processing Details")
                
                df = pd.DataFrame(stats['files_processed'])
                st.dataframe(df, use_container_width=True)
                
                doc_types = stats.get('doc_types', {})
                if doc_types:
                    st.markdown("#### 📚 Document Types")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    type_cols = [col1, col2, col3, col4]
                    for idx, (doc_type, count) in enumerate(doc_types.items()):
                        with type_cols[idx % 4]:
                            st.metric(doc_type.upper(), count)
                
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error building knowledge base: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


def render_phase_2():
    st.markdown('<div class="section-header">Phase 2: Test Case Generation</div>', unsafe_allow_html=True)
    
    if not os.environ.get("GEMINI_API_KEY"):
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("### ⚠️ Gemini API Key Not Found")
        st.markdown("Please set the GEMINI_API_KEY environment variable to use AI-powered test case generation.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    if not st.session_state.kb_built:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("### ⚠️ Knowledge Base Not Built")
        st.markdown("Please build the knowledge base in Phase 1 before generating test cases.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    st.markdown("""
    Enter your testing requirements below. The RAG engine will:
    - Embed your query
    - Retrieve relevant documentation chunks
    - Generate test cases grounded in the docs
    - Provide source attribution for traceability
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_query = st.text_area(
            "Testing Requirements",
            placeholder="Example: Generate positive and negative test cases for the discount code feature",
            height=100,
            help="Describe what you want to test. Be specific about features, scenarios, or user flows."
        )
    
    with col2:
        st.markdown("#### 💡 Example Prompts")
        st.info("""
        **Good prompts:**
        - Test discount codes
        - Validate checkout form
        - Test shipping options
        - Cart functionality
        """)
    
    if st.button("🧪 Generate Test Cases", key="generate_tests", use_container_width=True):
        if not user_query.strip():
            st.error("❌ Please enter a testing requirement")
            return
        
        with st.spinner("🔄 Generating test cases..."):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Initializing RAG engine...")
                progress_bar.progress(20)
                
                rag_engine = RAGEngine(persist_directory="./db")
                
                status_text.text("Retrieving relevant documentation...")
                progress_bar.progress(40)
                
                retrieved_chunks = rag_engine.retrieve_context(user_query, top_k=6)
                
                status_text.text(f"Retrieved {len(retrieved_chunks)} relevant chunks. Generating test cases...")
                progress_bar.progress(60)
                
                test_cases = rag_engine.generate_test_cases(user_query, retrieved_chunks)
                
                st.session_state.test_cases = test_cases
                
                progress_bar.progress(100)
                status_text.text("✅ Test cases generated successfully!")
                
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown(f"### ✅ Generated {len(test_cases)} Test Cases")
                st.markdown("</div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error generating test cases: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    if st.session_state.test_cases:
        st.markdown("---")
        
        # Add Select All / Deselect All buttons
        col_sel1, col_sel2, col_sel3 = st.columns([1, 1, 4])
        with col_sel1:
            if st.button("✅ Select All", use_container_width=True):
                st.session_state.selected_test_cases = st.session_state.test_cases.copy()
                st.rerun()
        with col_sel2:
            if st.button("❌ Deselect All", use_container_width=True):
                st.session_state.selected_test_cases = []
                st.rerun()
        
        st.markdown("### 📋 Generated Test Cases")
        
        for idx, tc in enumerate(st.session_state.test_cases):
            tc_id = tc.get('Test_ID', f'tc_{idx}')
            is_selected = any(t.get('Test_ID') == tc_id for t in st.session_state.selected_test_cases)
            
            with st.expander(f"**{tc_id}** - {tc.get('Feature', 'Unknown Feature')}", expanded=(idx==0)):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Test Scenario:** {tc.get('Test_Scenario', 'N/A')}")
                    
                    st.markdown("**Steps:**")
                    steps = tc.get('Steps', [])
                    if isinstance(steps, list):
                        for step_idx, step in enumerate(steps, 1):
                            st.markdown(f"{step_idx}. {step}")
                    else:
                        st.markdown(str(steps))
                    
                    st.markdown(f"**Expected Result:** {tc.get('Expected_Result', 'N/A')}")
                    
                    grounded_in = tc.get('Grounded_In', [])
                    if grounded_in:
                        st.markdown("**📚 Grounded In:**")
                        st.markdown(", ".join(grounded_in))
                
                with col2:
                    # Checkbox for selection
                    checkbox_label = "✅ Selected" if is_selected else "Select"
                    if st.checkbox(checkbox_label, value=is_selected, key=f"select_{idx}"):
                        if not is_selected:
                            st.session_state.selected_test_cases.append(tc)
                            st.rerun()
                    else:
                        if is_selected:
                            st.session_state.selected_test_cases = [
                                t for t in st.session_state.selected_test_cases 
                                if t.get('Test_ID') != tc_id
                            ]
                            st.rerun()
        
        # Show selection summary
        if st.session_state.selected_test_cases:
            st.markdown("---")
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown(f"### ✅ {len(st.session_state.selected_test_cases)} Test Case(s) Selected for Script Generation")
            selected_ids = [tc.get('Test_ID', 'N/A') for tc in st.session_state.selected_test_cases]
            st.markdown("**Selected:** " + ", ".join(selected_ids))
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📊 Test Cases Table")
        
        df_data = []
        for tc in st.session_state.test_cases:
            tc_id = tc.get('Test_ID', 'N/A')
            is_selected = any(t.get('Test_ID') == tc_id for t in st.session_state.selected_test_cases)
            steps_str = ", ".join(tc.get('Steps', [])) if isinstance(tc.get('Steps'), list) else str(tc.get('Steps', ''))
            df_data.append({
                'Selected': '✅' if is_selected else '⬜',
                'Test_ID': tc_id,
                'Feature': tc.get('Feature', 'N/A'),
                'Scenario': tc.get('Test_Scenario', 'N/A'),
                'Expected_Result': tc.get('Expected_Result', 'N/A'),
                'Grounded_In': ', '.join(tc.get('Grounded_In', []))
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        st.download_button(
            label="📥 Download Test Cases (JSON)",
            data=json.dumps(st.session_state.test_cases, indent=2),
            file_name="test_cases.json",
            mime="application/json"
        )


def render_phase_3():
    st.markdown('<div class="section-header">Phase 3: Selenium Script Generation</div>', unsafe_allow_html=True)
    
    if not os.environ.get("GEMINI_API_KEY"):
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("### ⚠️ Gemini API Key Not Found")
        st.markdown("Please set the GEMINI_API_KEY environment variable to use AI-powered script generation.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    if not st.session_state.selected_test_cases:  # Changed condition
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("### ⚠️ No Test Cases Selected")
        st.markdown("Please select test cases from Phase 2 before generating scripts.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Show selected test cases summary
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown(f"### 🎯 Selected Test Cases: {len(st.session_state.selected_test_cases)}")
    for tc in st.session_state.selected_test_cases:
        st.markdown(f"- **{tc.get('Test_ID', 'N/A')}**: {tc.get('Test_Scenario', 'N/A')}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Estimate API usage
    total_cases = len(st.session_state.selected_test_cases)
    estimated_time = total_cases * 4  # 4 seconds per request
    st.info(f"⏱️ Estimated generation time: ~{estimated_time} seconds ({total_cases} test case(s) × 4 sec/case)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("⚙️ Generate Selenium Scripts", key="generate_script", use_container_width=True):
            with st.spinner("🔄 Generating Selenium scripts..."):
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Initializing script generator...")
                    progress_bar.progress(5)
                    
                    script_gen = SeleniumScriptGenerator(persist_directory="./db")
                    generated_scripts = {}
                    
                    total_cases = len(st.session_state.selected_test_cases)
                    
                    for idx, tc in enumerate(st.session_state.selected_test_cases):
                        tc_id = tc.get('Test_ID', f'test_{idx}')
                        
                        status_text.text(f"Generating script {idx + 1}/{total_cases}: {tc_id}...")
                        
                        try:
                            script = script_gen.generate_script(tc)
                            generated_scripts[tc_id] = script
                            
                            progress = int(((idx + 1) / total_cases) * 95)
                            progress_bar.progress(progress)
                            
                            # Rate limiting: wait 4 seconds between requests (15 RPM = 1 request per 4 seconds)
                            if idx < total_cases - 1:
                                status_text.text(f"Rate limiting... waiting 4 seconds before next request...")
                                time.sleep(4)
                        
                        except Exception as e:
                            st.warning(f"⚠️ Failed to generate script for {tc_id}: {str(e)}")
                            generated_scripts[tc_id] = f"# Error generating script for {tc_id}\n# {str(e)}"
                    
                    st.session_state.generated_scripts = generated_scripts
                    
                    progress_bar.progress(100)
                    status_text.text(f"✅ Generated {len(generated_scripts)} script(s) successfully!")
                    
                    st.success(f"✅ {len(generated_scripts)} Selenium script(s) generated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error generating scripts: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    with col2:
        if st.session_state.generated_scripts:
            if st.button("🔄 Regenerate All Scripts", key="regenerate_script", use_container_width=True):
                st.session_state.generated_scripts = {}
                st.rerun()
    
    # Display generated scripts
    if st.session_state.generated_scripts:
        st.markdown("---")
        st.markdown("### 📜 Generated Selenium Scripts")
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("#### ✅ Scripts Ready for Download")
        st.markdown(f"Generated **{len(st.session_state.generated_scripts)}** production-ready script(s) with:")
        st.markdown("- ✓ Correct selectors from HTML analysis")
        st.markdown("- ✓ WebDriverWait for stable execution")
        st.markdown("- ✓ Comments linking to source documentation")
        st.markdown("- ✓ Proper error handling")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Individual script expanders
        for tc_id, script in st.session_state.generated_scripts.items():
            with st.expander(f"📄 Script for {tc_id}", expanded=False):
                st.code(script, language="python", line_numbers=True)
                
                st.download_button(
                    label=f"📥 Download {tc_id}.py",
                    data=script,
                    file_name=f"{tc_id}_selenium.py",
                    mime="text/x-python",
                    key=f"download_{tc_id}",
                    use_container_width=True
                )
        
        # Download all as ZIP
        st.markdown("---")
        st.markdown("### 📦 Bulk Download")
        
        col_zip1, col_zip2 = st.columns([1, 2])
        
        with col_zip1:
            # Create ZIP file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for tc_id, script in st.session_state.generated_scripts.items():
                    zip_file.writestr(f"{tc_id}_selenium.py", script)
            
            st.download_button(
                label="📦 Download All Scripts as ZIP",
                data=zip_buffer.getvalue(),
                file_name="selenium_scripts.zip",
                mime="application/zip",
                use_container_width=True
            )
        
        with col_zip2:
            st.info(f"💡 ZIP file contains {len(st.session_state.generated_scripts)} script(s)")


if __name__ == "__main__":
    main()