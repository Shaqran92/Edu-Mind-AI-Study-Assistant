<div align="center">
  <h1>🎓 EduMind AI Study Assistant</h1>
  <p><i>Your intelligent, gamified, and offline-resilient study companion.</i></p>
</div>

---

**EduMind AI Study Assistant** is a powerful desktop application designed to supercharge your learning process. By combining cutting-edge Large Language Models (Gemini & OpenAI) with robust offline Natural Language Processing (NLP) fallbacks, EduMind ensures you can study uninterrupted—generating summaries, quizzes, flashcards, and concept maps from your notes or YouTube videos in seconds.

## ✨ Key Features

*   **📚 Smart Material Import**: Extract text seamlessly from PDFs, DOCX files, Markdown, TXT, or simply paste a YouTube URL to instantly import video transcripts.
*   **🤖 Multi-Provider AI Engine**: Effortlessly swap between **Google Gemini** (1.5 Flash) and **OpenAI**. The app manages API rate limits with exponential backoff.
*   **🔌 Fault-Tolerant Offline Mode**: No internet? Hit an API rate limit? No problem. EduMind automatically falls back to a custom, local NLP engine (using TF-IDF and heuristic analysis) to generate summaries and study materials offline.
*   **🧠 Comprehensive Study Packages**: With a single click, generate:
    *   **Concise or Detailed Summaries**
    *   **Key Takeaways & Bullet Points**
    *   **Interactive Flashcards** (with Anki CSV export)
    *   **Gradable Multiple-Choice Quizzes**
*   **🕸️ Dynamic Concept Mapping**: Uses `NetworkX` to visualize the hidden relationships between concepts in your notes.
*   **🎮 Gamification & Productivity**: Stay motivated with daily streaks, XP points, and a built-in **Pomodoro Timer**.
*   **📊 Interactive Analytics**: Visualize your study time, quiz scores, and activity trends using beautiful, interactive `Plotly` charts.
*   **⚡ Buttery Smooth UI**: Built with `PyQt6` and heavy multithreading (`QThread`/`AIWorker`), ensuring the interface never freezes during intensive AI generation tasks.

---

## 🛠️ Technology Stack

*   **Frontend GUI:** Python, PyQt6, QtWebEngine
*   **AI Integration:** `google-generativeai`, `openai`
*   **Offline NLP:** Standard library heuristics, Regex, Data Parsing
*   **Database:** SQLite3
*   **Data Visualization:** Plotly, Matplotlib, NetworkX
*   **Security:** `keyring` (for secure API key storage)

---

## 🚀 Getting Started

### Prerequisites
Make sure you have **Python 3.9+** installed on your system. 

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/EduMind-AI.git
   cd EduMind-AI
   ```

2. **Create a virtual environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Application:**
   ```bash
   python app_init.py
   # Or directly via main:
   # python ui/main.py
   ```

---

## ⚙️ Configuration & API Keys

EduMind uses secure system keyrings to manage your API keys, rather than relying on plain-text environment variables. 

Upon launching the app for the first time, you can navigate to the **Settings** menu to securely input your **Gemini** and/or **OpenAI** API keys. If you prefer not to use an API key, simply select **Offline Mode** to utilize the local NLP engine.

---

## 📸 Screenshots

*(Add screenshots of your Dashboard, Study Assistant Tab, Concept Map, and Analytics here)*

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
Feel free to check the [issues page](https://github.com/yourusername/EduMind-AI/issues).

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
