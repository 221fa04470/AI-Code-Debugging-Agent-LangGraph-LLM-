# 🤖 AI Code Debugging Agent (LangGraph + LLM)

![Python](https://img.shields.io/badge/Python-3.10-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-AI-green)
![LLM](https://img.shields.io/badge/LLM-Groq%20%7C%20Gemini-orange)
![Status](https://img.shields.io/badge/Status-Active-success)

🚀 **A next-generation AI-powered debugging assistant that intelligently detects, fixes, and explains code errors in real-time using LangGraph and Large Language Models.**

---

## ✨ Overview

Debugging code can be time-consuming and frustrating.
This project introduces an **AI-driven debugging agent** that automates the process of identifying issues, fixing them, and explaining the solution — all through an intuitive chat-based interface.

---

## 🚀 Key Features

* 🔍 **Automated Bug Detection & Fixing**
* 💬 **Interactive Chat-Based Debugging Interface**
* 🌐 **Multi-language Code Support**
* ⚡ **Fast, Context-Aware AI Analysis**
* 🧠 **Detailed Explanations for Learning**
* 🔐 **Secure Authentication (JWT-based)**

---

## 🖥️ Demo

### 🔐 Login Interface

![Login](https://github.com/user-attachments/assets/c9632bad-d1bb-4190-8eeb-b41adbbf724e)

### 💻 Debugging Dashboard

![Dashboard](https://github.com/user-attachments/assets/55276ae3-b7a7-4109-a5d9-c08837d85625)

### ⚡ Code Analysis Output

![Output](https://github.com/user-attachments/assets/71733b16-c59c-4403-bc5e-7c0993975207)

---

## 🛠️ Tech Stack

| Category        | Technology                  |
| --------------- | --------------------------- |
| 🐍 Backend      | Python                      |
| 🧠 AI Framework | LangGraph, LangChain        |
| 🤖 LLMs         | Groq (LLaMA), Google Gemini |
| 🌐 Frontend     | HTML, CSS, JavaScript       |
| 🗄️ Database    | MongoDB                     |
| 🔐 Auth         | JWT                         |

---

## 🏗️ Project Architecture

```text
User Input → LangGraph Workflow → LLM Processing → Bug Detection → Auto Fix → Explanation Output
```

---

## 📂 Project Structure

```
AI-Code-Debugging-Agent/
│
├── routes/
├── agent.py
├── server.py
├── database.py
├── auth.py
├── index.html
├── session_routes.py
├── .gitignore
├── README.md
└── requirements.txt
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/221fa04470/ai-code-debugging-agent.git
cd ai-code-debugging-agent
```

---

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key
MONGO_URL=mongodb://localhost:27017
DB_NAME=ai_debug_agent
JWT_SECRET=your_secret_key
```

⚠️ **Important:** Never upload `.env` to GitHub.

---

### 4️⃣ Run the Application

```bash
python server.py
```

---

## ⚡ How It Works

1. 📥 User inputs buggy code
2. 🧠 LangGraph orchestrates the workflow
3. 🤖 LLM analyzes and detects errors
4. 🔧 AI generates corrected code
5. 💡 Provides explanation for learning

---

## 🎯 Use Cases

* 👨‍🎓 Students learning programming
* 👨‍💻 Developers improving productivity
* 🎯 Technical interview preparation
* 🧪 Code validation and testing

---

## 🔮 Future Enhancements

* 🌍 Cloud deployment (SaaS model)
* 🔊 Voice-based debugging assistant
* 📊 Code quality scoring system
* 🔌 IDE integrations (VS Code extension)

---

## 🔐 Security Practices

* API keys managed using `.env`
* Sensitive data excluded via `.gitignore`
* No secrets stored in version control

---

## 👨‍💻 Author

**Harsha Reddy**
🎓 B.Tech CSE | AI Developer
💡 Passionate about AI, Backend Systems & Scalable Applications

---

## ⭐ Support

If you found this project helpful, consider giving it a ⭐ on GitHub!

---

## 📜 License

This project is licensed under the MIT License.
