# LLM-Code-Assist - User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Features](#features)
6. [UI Guide](#ui-guide)
7. [Project Creation](#project-creation)
8. [Code Generation](#code-generation)
9. [Troubleshooting](#troubleshooting)
10. [Development Guide](#development-guide)

## Introduction
LLM-Code-Assist is a web-based IDE that helps developers create and manage Python projects using AI assistance. It combines modern UI design with powerful AI capabilities to streamline the development process.

## System Requirements
- Python 3.8 or higher
- Node.js 14+ (for development)
- 8GB RAM minimum (16GB recommended)
- Ollama installed and configured
- Chrome/Firefox/Safari (latest version)

## Installation

1. **Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd LLM-Code-Assist
   ```

2. **Set Up Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install Ollama**
   ```bash
   # Follow Ollama installation instructions for your OS
   # https://github.com/ollama/ollama
   # The ModelManager class in your application uses an environment variable to determine the base URL for connecting to the service. By default, it connects to http://localhost:11434. If you need to change the port, you can do so by setting the OLLAMA_BASE_URL environment variable.
   ```

4. **Download Required Model**
   ```bash
   ollama pull deepseek-coder-v2:16b
   ```

## Getting Started

1. **Start the Server**
   ```bash
   python app.py
   ```

2. **Access the Web Interface**
   - Open your browser
   - Navigate to `http://localhost:8001`
   - You should see the dark-themed landing page

## Features

### 1. Project Management
- Create new Python projects
- Choose from multiple frameworks:
  - Gradio
  - Python Scripts
  - (More frameworks coming soon)
- Manage project files and dependencies
- Execute projects directly from the IDE

### 2. AI Code Generation
- Smart code generation based on requirements
- Context-aware suggestions
- Code cleaning and optimization
- Error handling improvements

### 3. Real-time Features
- Live code execution
- Real-time error feedback
- Terminal output with color coding
- Automatic code saving

## UI Guide

### Theme System
- **Dark Theme**: Default theme with modern aesthetics
- **Glass-morphism**: Subtle blur and border effects
- **Color Scheme**:
  - Primary: #6200ea
  - Secondary: #03dac6
  - Success: Green variants
  - Error: Red variants

### Navigation
1. **Project Selection**
   - Click "Create New Project" on the landing page
   - Choose your framework from the grid layout
   - Enter project details

2. **Code Editor**
   - Left: File tree navigation
   - Center: Code editor with syntax highlighting
   - Right: Terminal output and controls

3. **Controls**
   - Top Bar: Project actions and settings
   - Bottom Bar: Execution controls and status

## Project Creation

1. **Start New Project**
   - Click "Create New Project"
   - Select framework (e.g., Gradio)
   - Enter project name
   - Describe project requirements

2. **Framework Selection**
   - Gradio: For web apps with UI
   - Python Script: For command-line tools

3. **Project Configuration**
   - Requirements will be analyzed
   - Dependencies automatically added
   - Project structure created

## Code Generation

### Using AI Assistance
1. **Requirement Analysis**
   - Enter project requirements in natural language
   - AI analyzes and structures requirements
   - Generates optimal project structure

2. **Code Generation**
   - AI generates clean, production-ready code
   - Follows best practices for chosen framework
   - Includes proper error handling
   - Adds documentation and type hints

3. **Code Customization**
   - Edit generated code in the IDE
   - Real-time syntax checking
   - Auto-completion support

## Troubleshooting

### Common Issues

1. **Ollama Connection**
   - Ensure Ollama is running
   - Check model is downloaded
   - Verify port 11434 is available

2. **Project Creation Fails**
   - Check project name is valid
   - Ensure requirements are clear
   - Verify framework selection

3. **Code Generation Issues**
   - Check internet connection
   - Ensure Ollama server is responsive
   - Try with simpler requirements first

### Error Messages
- "Model not found": Reinstall Ollama model
- "Server connection failed": Check Flask server
- "Invalid JSON response": Clear browser cache

## Development Guide

### Project Structure
```
LLM-Code-Assist-Testing/
├── agents/              # AI agents for different tasks
├── static/             # Frontend assets
│   ├── css/           # Styling
│   └── js/            # JavaScript code
├── templates/          # HTML templates
├── utils/             # Utility functions
└── projects/          # Generated projects
```

### Key Components
1. **Agents**
   - RequirementAnalyzer: Processes user requirements
   - ProjectCreator: Sets up project structure
   - CodeGenerator: Generates code
   - CodeCustomizer: Cleans and optimizes code

2. **RAG System**
   - Uses ChromaDB for vector storage
   - Retrieves relevant code examples
   - Enhances code generation quality

3. **Model Manager**
   - Handles Ollama integration
   - Manages model responses
   - Provides fallback responses

### Contributing
1. Fork the repository
2. Create feature branch
3. Follow code style guidelines
4. Submit pull request

## Support
For issues and support:
1. Check troubleshooting guide
2. Review existing GitHub issues
3. Create new issue with details
