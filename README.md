# Groq Document Vision Chat

Document analysis assistant using Groq's LLama models for vision processing and interactive Q&A, built with Streamlit.

![App Screenshot](https://github.com/lesteroliver911/groq-doc-vision-chat/blob/main/lesteroliver-groq-vision.gif)
*Document Analysis Assistant Interface*

## Features

- PDF and image document analysis
- Interactive Q&A about uploaded documents
- Real-time response streaming
- Support for multiple file formats (PDF, PNG, JPG, JPEG)

## Why Groq & Model Choice

The application uses `llama-3.2-90b-vision-preview` instead of `llama-3.2-11b-vision-preview` due to superior performance and reduced hallucinations. The 90B parameter model provides significantly better analysis quality and more reliable results. Additionally, Groq's infrastructure offers exceptional inference speed compared to alternatives like OpenAI and Claude, making it an optimal choice for real-time document analysis.

## Requirements

- Python 3.8+
- Groq API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/lesteroliver911/groq-doc-vision-chat.git
cd groq-doc-vision-chat
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run src/main.py
```

2. Upload a document (PDF or image) using the sidebar
3. Click "Analyze Document" to process the file
4. Ask follow-up questions about the document using the chat interface

## Models Used

- Document Analysis: `llama-3.2-90b-vision-preview`
- Summarization & Q&A: `llama-3.3-70b-versatile`

## License

MIT
