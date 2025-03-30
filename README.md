# Mini Agentic Recruiter Bot

## Objective
This project implements a minimal viable AI agent that simulates an autonomous recruiter. It accepts a job description, conducts a basic voice-based screening interview, and integrates with Google Meet for scheduling.

## Architecture Overview
The agent is built using Python and leverages the LangGraph framework for managing the interview flow state machine. Key components include:
- **Agent Core (`agent.py`):** Defines the LangGraph state (`AgentState`) and nodes responsible for JD parsing, question generation, asking questions, processing answers (including evaluation and follow-up logic), and summarization. Uses LangChain and an OpenAI LLM (`gpt-3.5-turbo`).
- **Voice Interface (`voice_utils.py`):** Handles Speech-to-Text (OpenAI Whisper API) and Text-to-Speech (OpenAI TTS API) functionalities, along with microphone recording (`pyaudio`) and audio playback (`sounddevice`).
- **Meeting Integration (`meeting_utils.py`):** Schedules the interview session using the Google Calendar API and generates a Google Meet link. Handles OAuth2 authentication.
- **Configuration (`config.py`):** Manages API keys (via `.env`) and model settings.
- **Prompts (`prompts.py`):** Contains structured `PromptTemplate` definitions for interacting with the LLM for various tasks.
- **Utilities (`utils.py`):** Helper functions for reading files and basic validation.
- **Entry Point (`main.py`):** Orchestrates the process: schedules the meeting and then runs the agent interview loop.

## Key Decisions Made
- **Agent Framework:** LangGraph was chosen for its ability to explicitly define and manage complex conversational flows with cycles (like follow-up questions) and state transitions.
- **LLM:** OpenAI's `gpt-3.5-turbo` was selected for its balance of capability and cost for tasks like extraction, generation, and evaluation.
- **Voice Services:** OpenAI's Whisper API (STT) and TTS API were used for high-quality voice interaction and easy integration using the `openai` library.
- **Meeting Integration:** Google Meet scheduling via the Calendar API was chosen as a robust way to fulfill the integration requirement without the complexities of real-time bot joining.
- **Conversation Flow:** Implemented a follow-up mechanism based on LLM evaluation of the candidate's answer to make the interview more dynamic.

## Setup Instructions
1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd mannadamay12-mini-agentic-recruiter
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note:* `pyaudio` might require system-level dependencies (like `portaudio`) depending on your OS. Please refer to PyAudio installation guides if you encounter issues.
4.  **Set up API Keys:**
    - Create a `.env` file in the project root.
    - Add your OpenAI API key:
      ```dotenv
      OPENAI_API_KEY='your_openai_api_key_here'
      ```
5.  **Set up Google Calendar API Credentials:**
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create a new project or select an existing one.
    - Enable the "Google Calendar API".
    - Go to "Credentials", click "Create Credentials", and choose "OAuth client ID".
    - Select "Desktop app" as the application type.
    - Click "Create". Download the JSON file.
    - **Rename the downloaded JSON file to `credentials.json` and place it in the project root directory.**
    - The first time you run the script, it will open a browser window asking you to authorize access to your Google Calendar. After authorization, a `token.pickle` file will be created to store credentials for future runs.
6.  **Update Candidate Email:**
    - Open `main.py` and change the placeholder email `candidate@example.com` in the `schedule_google_meet` call to a valid email address you want to invite.

## How to Run
Ensure your microphone and speakers are working. Then run the main script:
```bash
python main.py