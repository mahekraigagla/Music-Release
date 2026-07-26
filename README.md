# 🎵 NextDrop AI – Release Strategist & Music Analytics

An AI-powered music release strategist platform that analyzes song files (MP3/WAV), extracts acoustic features with Librosa, predicts 7-day streaming velocity with XGBoost, and generates optimal drop windows and strategy checklists.

---

## 🚀 Quick Setup Instructions

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 15+ (Running on `localhost:5433` or `5432`)

### 2. Clone the Repository
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/music-release-strategist.git
cd music-release-strategist
```

### 3. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r backend/requirements.txt
```

### 4. Setup Environment Variables
Create a `backend/.env` file:
```env
DATABASE_URL=postgresql+asyncpg://postgres:Mahek@localhost:5433/nextdrop_db
ACTIVE_MODEL_PATH=data/models/release_model.pkl
```

### 5. Run Database Migrations & Seed Lookups
```bash
cd backend
alembic upgrade head
python -m scripts.seed_lookups
```

### 6. Start the Web Dashboard
```bash
uvicorn app.main:app --port 8000
```
Open **http://127.0.0.1:8000/dashboard** in your browser!
