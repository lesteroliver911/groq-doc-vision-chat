import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pathlib import Path
import time
import base64
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image

# Load environment variables
load_dotenv()

def initialize_session_state():
    """Initialize session state variables for the Streamlit app."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'is_streaming' not in st.session_state:
        st.session_state.is_streaming = False
    if 'file_content' not in st.session_state:
        st.session_state.file_content = None
    if 'analysis' not in st.session_state:
        st.session_state.analysis = None
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None

def get_groq_client():
    """Initialize Groq client with API key from environment variables."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    return Groq(api_key=api_key)

def encode_image_to_base64(image):
    """Convert PIL Image to base64 data URL."""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_str}"

def convert_pdf_to_images(pdf_bytes):
    """Convert PDF bytes to list of PIL Images."""
    try:
        images = convert_from_bytes(pdf_bytes)
        return images
    except Exception as e:
        st.error(f"Error converting PDF to images: {str(e)}")
        return None

def analyze_image(image_data_url):
    """Analyze single image using the vision model."""
    client = get_groq_client()
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please analyze this file and extract all relevant information in detail."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    }
                }
            ]
        }
    ]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=messages,
            temperature=0,
            max_tokens=3990,
            top_p=1,
            stream=False,
            stop=None
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        st.error(f"Error during image analysis: {str(e)}")
        return None

def analyze_file_content(uploaded_file):
    """Analyze file content based on file type."""
    file_type = uploaded_file.type.split('/')[-1].upper()
    
    # Create a container for the progress information
    progress_container = st.sidebar.container()
    
    if file_type == 'PDF':
        with progress_container:
            st.write("📄 Processing PDF...")
            pdf_images = convert_pdf_to_images(uploaded_file.getvalue())
            if not pdf_images:
                return None
            
            all_analyses = []
            progress_bar = st.progress(0)
            pages_info = st.empty()
            
            for i, image in enumerate(pdf_images):
                pages_info.write(f"📝 Analyzing page {i+1} of {len(pdf_images)}")
                image_data_url = encode_image_to_base64(image)
                page_analysis = analyze_image(image_data_url)
                if page_analysis:
                    all_analyses.append(f"Page {i+1}:\n{page_analysis}")
                progress_bar.progress((i + 1) / len(pdf_images))
            
            pages_info.write("✅ Analysis complete!")
            return "\n\n".join(all_analyses)
    
    else:  # Handle regular images
        with progress_container:
            st.write("🖼️ Processing image...")
            image_data_url = encode_image_to_base64(Image.open(uploaded_file))
            analysis = analyze_image(image_data_url)
            if analysis:
                st.write("✅ Analysis complete!")
            return analysis

def generate_summary(analysis):
    """Generate detailed summary using the versatile model."""
    client = get_groq_client()
    
    summary_system_prompt = """You are a highly skilled document summarizer. Create a clear, well-structured summary of the provided content analysis following these guidelines:

1. Start with a brief overview of the document's main topic or purpose
2. Organize the summary with clear headings and sections using markdown formatting
3. Include all key points and important details
4. Highlight any significant findings or conclusions
5. Use bullet points for lists of related items
6. Keep the language professional but accessible
7. Maintain a logical flow of information
8. Include any relevant numbers, dates, or data points
9. End with a brief conclusion if applicable

Format your response using markdown for better readability:
- Use ## for main sections
- Use ### for subsections
- Use bullet points (*) for lists
- Use bold (**) for emphasis on key terms
- Use proper spacing between sections

Aim to make the summary comprehensive yet concise and easily scannable."""

    messages = [
        {
            "role": "system",
            "content": summary_system_prompt
        },
        {
            "role": "user",
            "content": analysis
        }
    ]
    
    try:
        with st.spinner("🤖 Generating summary..."):
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=True
            )
            
            summary = ""
            summary_placeholder = st.empty()
            
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    summary += chunk.choices[0].delta.content
                    summary_placeholder.markdown(summary + "▌")
                    time.sleep(0.01)
            
            summary_placeholder.markdown(summary)
            return summary
            
    except Exception as e:
        st.error(f"Error during summary generation: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="Document Analysis Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("📑 Document Upload")
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "Upload PDF or Image",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Upload a document to analyze"
        )
        
        if uploaded_file and uploaded_file != st.session_state.current_file:
            st.session_state.current_file = uploaded_file
            st.session_state.messages = []
            st.session_state.analysis = None
        
        if uploaded_file:
            file_type = uploaded_file.type.split('/')[-1].upper()
            st.write(f"📎 File type: {file_type}")
            
            if st.button("🔍 Analyze Document", use_container_width=True):
                st.session_state.analysis = analyze_file_content(uploaded_file)
                if st.session_state.analysis:
                    summary = generate_summary(st.session_state.analysis)
                    if summary:
                        st.session_state.messages = []  # Clear previous messages
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": summary
                        })
        
        st.markdown("---")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.analysis = None
            st.session_state.current_file = None
            st.rerun()
    
    # Main content area
    st.title("🤖 Document Analysis Assistant")
    
    if not uploaded_file:
        st.info("👈 Please upload a document in the sidebar to begin analysis.")
        return

    # Get user input - moved outside container
    user_prompt = st.chat_input("Ask a follow-up question about the document...")
    
    # Display messages in container
    chat_container = st.container()
    with chat_container:
        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Process user input if provided and analysis exists
        if st.session_state.messages and user_prompt:
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                client = get_groq_client()
                messages = [
                    {
                        "role": "system",
                        "content": f"Previous analysis: {st.session_state.analysis}\n\nProvide a helpful, detailed response to the question."
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
                
                # Stream the response
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                    top_p=1,
                    stream=True
                )
                
                # Display streaming response
                response = ""
                placeholder = st.empty()
                
                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        response += chunk.choices[0].delta.content
                        placeholder.markdown(response + "▌")
                        time.sleep(0.01)
                
                # Final response display
                placeholder.markdown(response)
                
                # Add messages to chat history
                st.session_state.messages.append({"role": "user", "content": user_prompt})
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
