# QuizFlow – MultiAgent

AI-powered quiz platform with multi-agent generation system

---

## 🚀 Features

- Generate quizzes via AI (expect latency ~3–4 minutes)  
- 25 questions per quiz (supports MCQ, True/False, Short Answer)  
- Real-time progress tracking  
- Instant evaluation & feedback  
- Quiz history & analytics  
- Production-ready architecture (frontend + backend separation)  

---

## 📦 Tech Stack

| Component | Technology |
|-----------|-------------|
| Frontend | React / Next.js (or similar) |
| Backend | Node.js / Express (or similar) |
| AI / Integration | OpenAI API or equivalent |
| DB / Storage | (Whatever you are using — e.g. MongoDB, PostgreSQL) |
| Dev tooling | Scripts, environment variables, etc. |

---

## 🛠️ Initial Setup

Follow these steps to get the project running locally.

1. **Clone the repo**

```bash
git clone https://github.com/KHADIJA2008-KB/QUIZFLOW-MultiAgent.git
cd QUIZFLOW-MultiAgent
```
Install dependencies & setup

- From project root:
```
npm run setup
```

This script should (if implemented) install dependencies in both frontend & backend.

- Environment variables

- In backend/, create a .env with at least:

```
OPENAI_API_KEY=your_openai_key_here
```

- Add other required keys (database URI, secret keys, etc.) as needed.

- Run in development
```
npm run dev
```

This should start both frontend and backend (or use separate commands if configured).
```
# Production / Build

npm run build
npm start
```

After building, you can launch the production server via npm start.

🌐 Accessing the App

- Frontend UI: http://localhost:3000

- Backend API: http://localhost:8000

- API Docs / Swagger: http://localhost:8000/docs

(Adjust ports if your setup differs.)

🔧 How It Works (High Level)

- User starts a quiz request via frontend UI.

- Frontend sends request to backend API.

- Backend triggers one or more AI agents to generate questions and answers.

- Backend returns the generated quiz to frontend.

As user answers questions, progress & evaluation handled in real-time.

Results & analytics are stored and retrievable via history endpoints.

🧪 Testing & Validation

- Write unit tests for backend logic (question generation, validation, storage)

- Add component / integration tests for frontend UI

- Test edge cases: no answer, partial inputs, API failures, rate limiting

- Monitor latency: quiz generation may take time, so show loader UI feedback

📁 Project Structure (Suggested)
```
QUIZFLOW-MultiAgent/
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/
│   ├── controllers/
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── package.json
│   └── .env.example
├── setup.sh
├── start.sh
├── run.sh
└── README.md
```

You can adapt this according to your actual folder layout.

✅ Requirements

- Node.js (v16 or newer recommended)

- npm or yarn

- An active OpenAI API key (or equivalent AI service)

- A database (if persistence is needed)

- Internet connection for API calls

👥 Contributing

- Fork the repo

- Create a new branch: feature/some-feature

- Make changes & commit

- Push to your fork

- Open a Pull Request (PR)

- Describe the feature / bug fix, with before/after behavior

Please ensure code is linted, tested, and documented before proposing a merge.

📝 License & Attribution

Specify your license (MIT, Apache, etc.) here.
If using any external libraries, give credit or mention links.

🗒️ Future Ideas

- Support for different quiz types (e.g. essay, match)

- Timer & countdown per quiz

- Multi-language support

- Adaptive quizzes (question difficulty based on performance)

- Export results (PDF, CSV)

-  Webhooks / notifications integration
