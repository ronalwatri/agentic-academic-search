"""
Agentic Academic Search - Streamlit Web App
Deploy-ready application for academic literature search
"""

import streamlit as st
import anthropic
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Agentic Academic Search",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .search-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .result-box {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-top: 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 5px;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SEARCHER CLASS
# ============================================================================

class AgenticAcademicSearcher:
    """Academic search system with web interface"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"
    
    def quick_search(self, query: str, progress_callback=None) -> str:
        """Quick search with progress updates"""
        if progress_callback:
            progress_callback("🔍 Searching...", 0.3)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system="You are an expert academic research assistant. Provide clear, well-cited answers.",
            messages=[{
                "role": "user",
                "content": f"Search for and summarize: {query}"
            }],
            tools=[{"type": "web_search_20250305", "name": "web_search"}]
        )
        
        if progress_callback:
            progress_callback("✅ Processing results...", 0.8)
        
        result = ""
        for block in response.content:
            if block.type == "text":
                result += block.text
        
        if progress_callback:
            progress_callback("✅ Complete!", 1.0)
        
        return result
    
    def comprehensive_search(
        self,
        research_question: str,
        focus_areas: Optional[List[str]] = None,
        time_frame: str = "last 3 years",
        max_iterations: int = 8,
        progress_callback=None
    ) -> Dict[str, Any]:
        """Comprehensive search with progress updates"""
        
        # Construct prompt
        user_prompt = f"""Research Question: {research_question}\n"""
        if focus_areas:
            user_prompt += f"Focus Areas: {', '.join(focus_areas)}\n"
        user_prompt += f"Time Frame: {time_frame}\n\n"
        user_prompt += """
Please conduct a comprehensive academic literature search:
1. Search Strategy: Plan multi-stage approach
2. Initial Searches: Broad landscape survey  
3. Targeted Searches: Deep dive into specifics
4. Synthesis: Comprehensive summary with themes, methods, findings

For each source provide:
- Full citation (APA format)
- Key contributions
- Methodology
- Relevant findings

Organize by themes.
"""
        
        messages = [{"role": "user", "content": user_prompt}]
        
        search_metadata = {
            "start_time": datetime.now().isoformat(),
            "research_question": research_question,
            "searches_performed": [],
            "tool_uses": 0
        }
        
        # Agentic loop
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            if progress_callback:
                progress = iteration / max_iterations
                progress_callback(f"🔄 Iteration {iteration}/{max_iterations}...", progress)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system="""You are an expert academic research assistant specializing in 
systematic literature review. Provide structured summaries with proper APA citations.""",
                messages=messages,
                tools=[{"type": "web_search_20250305", "name": "web_search"}]
            )
            
            if response.stop_reason == "end_turn":
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text
                
                search_metadata["end_time"] = datetime.now().isoformat()
                search_metadata["total_iterations"] = iteration
                
                if progress_callback:
                    progress_callback("✅ Search completed!", 1.0)
                
                return {
                    "findings": final_text,
                    "metadata": search_metadata
                }
            
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        search_metadata["tool_uses"] += 1
                        if block.name == "web_search":
                            query = block.input.get("query")
                            search_metadata["searches_performed"].append(query)
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Tool executed"
                        })
                
                messages.append({"role": "user", "content": tool_results})
        
        return {
            "findings": "Search incomplete - max iterations reached",
            "metadata": search_metadata
        }

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">🔬 Agentic Academic Search</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Literature Review & Research Assistant</div>', unsafe_allow_html=True)
    
    # Sidebar - API Key & Settings
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            help="Enter your Anthropic API key from console.anthropic.com"
        )
        
        if api_key:
            st.success("✅ API Key set!")
            # Store in session state
            st.session_state['api_key'] = api_key
        else:
            st.warning("⚠️ Please enter your API key to start")
            st.markdown("""
            **How to get API key:**
            1. Go to [console.anthropic.com](https://console.anthropic.com/)
            2. Sign up / Login
            3. Go to API Keys
            4. Create new key
            5. Copy & paste here
            """)
        
        st.divider()
        
        # Search Settings
        st.header("🔧 Search Settings")
        
        search_type = st.radio(
            "Search Type",
            ["Quick Search", "Comprehensive Search"],
            help="Quick: 30-60s, Comprehensive: 3-5 min"
        )
        
        if search_type == "Comprehensive Search":
            max_iterations = st.slider(
                "Search Depth",
                min_value=5,
                max_value=15,
                value=8,
                help="More iterations = more thorough (but slower)"
            )
            
            time_frame = st.selectbox(
                "Time Frame",
                ["last 3 years", "last 5 years", "2020-2024", "2018-2024"],
                help="Limit results to recent publications"
            )
        
        st.divider()
        
        # Info
        st.header("ℹ️ About")
        st.markdown("""
        **Agentic Academic Search** uses Claude AI to:
        - Search academic papers
        - Extract key findings
        - Generate literature reviews
        - Identify research gaps
        
        **Cost:** ~$0.30-2 per search
        """)
        
        # Usage stats
        if 'search_count' in st.session_state:
            st.metric("Searches Today", st.session_state['search_count'])
    
    # Main content
    if not api_key:
        st.info("👈 Please enter your API key in the sidebar to get started")
        
        # Demo/info section
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📚 Literature Review")
            st.write("Generate comprehensive reviews from 20-30 papers automatically")
        
        with col2:
            st.subheader("🔍 Smart Search")
            st.write("AI plans and executes multi-stage search strategies")
        
        with col3:
            st.subheader("📊 Research Gaps")
            st.write("Identify under-researched areas in your field")
        
        return
    
    # Initialize searcher
    if 'searcher' not in st.session_state or st.session_state.get('api_key') != api_key:
        try:
            st.session_state['searcher'] = AgenticAcademicSearcher(api_key)
            st.session_state['api_key'] = api_key
        except Exception as e:
            st.error(f"❌ Error initializing searcher: {e}")
            return
    
    searcher = st.session_state['searcher']
    
    # Search interface
    if search_type == "Quick Search":
        st.header("🔍 Quick Search")
        st.markdown("Get fast answers to specific questions (30-60 seconds)")
        
        query = st.text_input(
            "Enter your question:",
            placeholder="e.g., What is Aiken's V coefficient threshold?",
            help="Ask specific questions about academic concepts, standards, or references"
        )
        
        if st.button("🚀 Search", key="quick_search_btn"):
            if not query:
                st.warning("Please enter a question")
            else:
                # Progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(message, value):
                    status_text.text(message)
                    progress_bar.progress(value)
                
                try:
                    # Search
                    result = searcher.quick_search(query, update_progress)
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display results
                    st.success("✅ Search completed!")
                    
                    st.markdown("### 📄 Results:")
                    st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)
                    
                    # Download button
                    st.download_button(
                        "💾 Download Results",
                        data=result,
                        file_name=f"quick_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                    
                    # Update stats
                    st.session_state['search_count'] = st.session_state.get('search_count', 0) + 1
                    
                except Exception as e:
                    st.error(f"❌ Search failed: {e}")
    
    else:  # Comprehensive Search
        st.header("📚 Comprehensive Literature Search")
        st.markdown("Deep literature review with multiple papers (3-5 minutes)")
        
        # Research question
        research_question = st.text_area(
            "Research Question:",
            placeholder="e.g., Effectiveness of MOOC integration with project-based learning in vocational education",
            height=100,
            help="Your main research topic or question"
        )
        
        # Focus areas
        focus_areas_text = st.text_area(
            "Focus Areas (one per line):",
            placeholder="MOOC pedagogical design\nProject-based learning effectiveness\nVocational education\n21st century skills",
            height=100,
            help="Specific aspects to focus on"
        )
        
        focus_areas = [area.strip() for area in focus_areas_text.split('\n') if area.strip()]
        
        if st.button("🚀 Start Comprehensive Search", key="comp_search_btn"):
            if not research_question:
                st.warning("Please enter a research question")
            else:
                # Progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(message, value):
                    status_text.text(message)
                    progress_bar.progress(value)
                
                try:
                    # Estimate time
                    st.info(f"⏳ This will take approximately {max_iterations * 20} seconds...")
                    
                    # Search
                    results = searcher.comprehensive_search(
                        research_question=research_question,
                        focus_areas=focus_areas if focus_areas else None,
                        time_frame=time_frame,
                        max_iterations=max_iterations,
                        progress_callback=update_progress
                    )
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display results
                    st.success("✅ Literature review completed!")
                    
                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Searches Performed", len(results['metadata']['searches_performed']))
                    with col2:
                        st.metric("Tool Uses", results['metadata']['tool_uses'])
                    with col3:
                        st.metric("Iterations", results['metadata']['total_iterations'])
                    
                    # Main results
                    st.markdown("### 📄 Literature Review:")
                    st.markdown(f'<div class="result-box">{results["findings"]}</div>', unsafe_allow_html=True)
                    
                    # Search queries used
                    with st.expander("🔍 View Search Queries Used"):
                        for i, query in enumerate(results['metadata']['searches_performed'], 1):
                            st.write(f"{i}. {query}")
                    
                    # Download buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "💾 Download Literature Review",
                            data=results["findings"],
                            file_name=f"literature_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    with col2:
                        import json
                        metadata_json = json.dumps(results["metadata"], indent=2)
                        st.download_button(
                            "📊 Download Metadata (JSON)",
                            data=metadata_json,
                            file_name=f"search_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    # Update stats
                    st.session_state['search_count'] = st.session_state.get('search_count', 0) + 1
                    
                except Exception as e:
                    st.error(f"❌ Search failed: {e}")
                    st.exception(e)

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    # Initialize session state
    if 'search_count' not in st.session_state:
        st.session_state['search_count'] = 0
    
    main()
