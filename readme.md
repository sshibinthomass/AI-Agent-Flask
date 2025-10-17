# End to End Project Agentic AI Chatbots

---

## 1. Clone or Download the Repository
Clone this repository or download it as a ZIP and extract it to your desired location.

```sh
git clone <your-repo-url>
cd <repo-directory>
```

---

## 2. Set Up Environment Variables

Create a `.env` file in your project root and add the following keys:

```ini
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# Tavily API Key
TAVILY_API_KEY=your_tavily_api_key_here

# Google Maps API Key
GOOGLE_MAP_API=your_google_map_api_key_here
```

### Purpose of Each API Key
- **OPENAI_API_KEY**: Enables access to OpenAI's language models (e.g. GPT-4.1-mini) for chatbot responses.
- **GROQ_API_KEY**: Enables access to Groq's LLMs for alternative or additional chatbot capabilities.
- **TAVILY_API_KEY**: Used for web search and retrieval features via the Tavily API.
- **GOOGLE_MAP_API**: Required for accessing Google Maps data, such as restaurant locations and reviews

### How to get these keys
- **OPENAI_API_KEY**: [Sign up for OpenAI](https://platform.openai.com/signup) and create an API key at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys).
- **GROQ_API_KEY**: [Sign up for Groq](https://console.groq.com/keys) and generate an API key.
- **TAVILY_API_KEY**: [Sign up for Tavily](https://app.tavily.com/) and get your API key from your account settings.
- **GOOGLE_MAP_API**: [Create a Google Cloud account](https://console.cloud.google.com/), enable the Maps API, and generate an API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).

After creating your `.env` file, the application will automatically load these variables at startup.

---

## 3. Install UV and Project Dependencies

### Install UV (if not already installed)
If you do not have UV installed, run:
```sh
pip install uv
```

### 3.1 Install [UV](https://github.com/astral-sh/uv) (if not already installed)
UV is a fast Python package manager. Install it by following the [official instructions](https://github.com/astral-sh/uv#installation).

### 3.2 Initialize UV in the project director (if not already initialized)
```sh
uv init
```

### 3.3 Create a virtual environment using UV
```sh
uv venv
```

### 3.4 Activate the virtual environment
- **Windows**:
  ```sh
  .venv\Scripts\activate
  ```
- **macOS/Linux**:
  ```sh
  source .venv/bin/activate
  ```

### 3.5 Install dependencies from `requirements.txt`
```sh
uv add -r requirements.txt
```
This will install all required packages listed in `requirements.txt` using UV.

---

## 4. Run the Streamlit App

To start the Streamlit application, run:

```sh
streamlit run app.py
```

This will launch the app in your default web browser. Make sure your virtual environment is activated before running this command.

---

## 5. UI Configuration: `uiconfigfile.ini`

The `uiconfigfile.ini` file controls the options available in the Streamlit UI, such as which LLMs, models, use cases, and chat history length are available for selection.

- **Location:** `src/langgraphagenticai/ui/uiconfigfile.ini`
- **Purpose:** Customize the dropdown options in the sidebar of the Streamlit app.
- **What you can configure:**
  - Available LLM providers (e.g., OpenAI, Groq)
  - Model options for each provider
  - Use case options
  - Chat history length (number of messages retained)

**Example `uiconfigfile.ini`:**
```ini
[DEFAULT]
PAGE_TITLE = Chatbot
LLM_OPTIONS = OpenAI, Groq
GROQ_MODEL_OPTIONS = qwen-qwq-32b, qwen/qwen3-32b, llama-3.1-8b-instant, llama-3.3-70b-versatile
OPENAI_MODEL_OPTIONS = gpt-4.1-mini
USECASE_OPTIONS = Sushi, Agentic AI, Basic Chatbot
CHAT_HISTORY_LENGTH = 20
```

**How to use:**
- Edit this file to add or remove LLMs, models, or use cases as needed.
- Adjust `CHAT_HISTORY_LENGTH` to control how much conversation context is retained.
- Changes will be reflected in the Streamlit UI the next time you start or refresh the app.

---