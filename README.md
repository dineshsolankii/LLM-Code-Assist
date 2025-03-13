# LLM-Code-Assist

A web-based IDE for generating and executing Python projects with AI assistance. Built with Flask and vanilla JavaScript.

## Features

- **AI-Powered Code Generation**: Uses Ollama with deepseek-coder-v2:16b model
- **Modern UI**: Dark theme with glass-morphism effects and smooth transitions
- **Real-time Communication**: Flask backend with SocketIO
- **Code Editing**: CodeMirror integration with custom theme
- **Multiple Framework Support**: Django, Flask, Streamlit, Gradio, Python
- **RAG System**: Uses ChromaDB for retrieving relevant code examples
- **Project Management**: Create, edit, and execute Python projects

## Components

1. **Frontend**
   - HTML/CSS/JS with CodeMirror
   - Dark theme with modern styling
   - Responsive design with glass-morphism effects
   - Enhanced terminal output with color coding

2. **Backend**
   - Flask server
   - SocketIO for real-time updates
   - ChromaDB for vector storage
   - Ollama integration for AI models

3. **AI Agents**
   - RequirementAnalyzer
   - ProjectCreator
   - CodeGenerator
   - ProjectExecutor
   - CodeCustomizer

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python app.py
   ```

## Development

The project uses a modern tech stack:
- **Frontend**: Vanilla JavaScript with modern ES6+ features
- **Backend**: Python 3.8+ with Flask
- **Database**: ChromaDB for vector storage
- **AI**: Ollama with deepseek-coder-v2:16b model

## Theme System

- Dark theme by default
- Glass-morphism effects with blur and subtle borders
- Gradient text for headings
- Floating animations for icons
- Color scheme:
  - Primary: #6200ea
  - Secondary: #03dac6
  - Surface colors for layering
  - Success/Error states
