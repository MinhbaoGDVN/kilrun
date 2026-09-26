# Kilrun - AI Agent Terminal ⚡

**Kilrun** is a powerful AI Agent running directly on the terminal, designed to interact and automate programming tasks. The project automatically sets up the entire workspace, integrates various powerful AI models (such as Claude, Flux), and can operate flexibly via cookies without strictly requiring an API Key.

## 🌟 Key Features
* **Agent Mode:** Allows the AI to automatically create files, run shell commands, and execute Python code directly within a safe, isolated `workspace/`.
* **Multimodal Capabilities:** Supports natural language chat (defaulting to `claude-sonnet-5`), image generation (`flux-1.1-pro`), video generation (`video-ltx-2.5`), and Text-to-Speech (TTS).
* **Web Search Integration:** Enables the AI to proactively search the internet for real-time information using the `/search` command.
* **Intuitive Terminal UI:** Utilizes the `rich` library to display beautiful colors, markdown formatting, syntax highlighting, and an elegant workspace interface.

## 📂 Directory Structure
Upon installation, the system will automatically initialize the following standard structure:
* `core/`: The core engine handling API communication (Do not modify).
* `agent/`: Contains the main execution code of the AI Agent and system tools.
* `workspace/`: An isolated directory for the Agent to freely create, edit files, and work.
* `scripts/`: A dedicated folder for users to write their own custom interaction scripts.
* `logs/`: Where chat history and logs are automatically saved.

## 🚀 Installation & Usage

### 1. Automatic Installation
Simply run the installation script once in your terminal, pointing it to the directory where you want to install it:
```
python INSTALL.py
```

The system will automatically build the directory tree, create a Python virtual environment (.venv), and install necessary dependencies (httpx, rich). After installation, you can safely delete the INSTALL.py file.

2. Quick Start
Use the auto-generated startup scripts based on your operating system:

On Windows:

```
run.bat
```
To start directly in Agent mode, run: 
```
run.bat --agent
```

On Linux/macOS:
```
./run.sh
```
To start directly in Agent mode, run: 
```
./run.sh --agent
```

3. Basic Commands
Once inside the Kilrun interface, you can use the following commands:

- /mode agent : Switch to the mode that allows the AI to write code and execute commands automatically.
- /files : List current files in the workspace/.
- /image <prompt> : Request image generation.
- /help : Show the detailed help menu and all available commands.
