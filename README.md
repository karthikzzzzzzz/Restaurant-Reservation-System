# 🍽️ Restaurant Reservation System

This is an end-to-end AI-powered Restaurant Reservation System built using FastAPI and integrated with Ollama’s `llama3.2` model. The bot handles reservation requests, checks for available slots, and books tables intelligently based on user preferences.

---

## Demo Links
https://drive.google.com/file/d/1flBexYm6xTDtOInyI5AToe50oidGETTM/view?usp=sharing


## 🚀 Features

* Natural language reservation chatbot
* Handles multiple restaurants and locations
* Slot-based overlapping check logic
* Tool invocation for reservation actions
* Scalable and production-ready structure (v1)
* Powered by Ollama with `llama3` for LLM functionality

---

## 🛠️ Tech Stack

* **Backend**: FastAPI
* **LLM Engine**: Ollama (`llama3:8b`)
* **Model Serving**: Local with Ollama
* **Server**: `uvicorn`

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/karthikzzzzzzz/Restaurant-Reservation-System
cd Restaurant-Reservation-System
```

### 2. Set up a virtual environment (optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🤖 LLM Setup (Ollama)

### 1. Install Ollama

Download and install Ollama from: [https://ollama.com](https://ollama.com)

### 2. Pull the required model

```bash
ollama pull llama3.2
```

Make sure Ollama is running in the background.

---

## 🧪 Run the App

```bash
uvicorn main:app --reload
```

Once running, the API will be available at:
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — (Swagger UI for testing)

---

## 💻 Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be accessible at [http://localhost:3000](http://localhost:3000).

---

## 🔄 Bot Flow Summary

1. User sends a message (e.g., "Book a table at Indiranagar at 7 PM for 4 people").
2. The bot parses the message using the LLM.
3. Reservation tool checks for slot availability, avoids overlapping bookings.
4. If a slot is free, the bot confirms the reservation.
5. Responses are generated conversationally using the LLM.

---

## 📊 Database

Uses SQLAlchemy ORM for handling restaurant and reservation records. SQLite is used by default for local development.

---

## 🧠 Key Concepts

* **Slot Conflict Handling**: Ensures no overlapping reservations.
* **Tool Invocation**: LLM decides when to call reservation tool based on intent.
* **Stateful Design**: Ready to be scaled with memory and user tracking.

---

## 🔧 Future Scope

* Add support for multiple languages
* Integrate real-time availability UI
* Add user authentication
* Web frontend integration

---

## 🧹 Developer Notes

* Ensure Ollama is running and the model is pulled before hitting the API.
* Slots are currently 60 minutes long per booking by default.
* Reservation conflict logic uses time overlap checks.

