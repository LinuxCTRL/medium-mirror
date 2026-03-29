# Medium Mirror 🚀

A modern, distraction-free article reader and library manager for Medium content. Built with **FastAPI**, **Tailwind CSS**, and **SQLAlchemy**.

![Design Preview](https://img.shields.io/badge/Design-Stunning-indigo)
![Mode](https://img.shields.io/badge/Mode-Pure_Black_Dark-black)

## ✨ Features

- **Distraction-Free Reading:** Optimized typography and layout for focused reading.
- **Paywall Bypass:** Seamlessly mirrors Medium content via Freedium.
- **Pure Black Dark Mode:** High-contrast, easy-on-the-eyes experience.
- **Advanced Search:** Find articles by keywords with controllable search depth.
- **Bulk Fetch:** Import entire search result lists with a single click.
- **Admin Panel:** Manage your local library with bulk deletion tools.
- **Local Persistence:** All fetched articles are saved locally in a SQLite database.

## 🛠️ Tech Stack

- **Backend:** Python (FastAPI, SQLAlchemy, Uvicorn)
- **Frontend:** Jinja2 Templates, Tailwind CSS (CDN), Lucide Icons
- **Fonts:** Inter (Sans-serif), Lora (Serif)
- **Database:** SQLite (SQLAlchemy Async)

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Recommended) or `pip`

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/medium-mirror.git
   cd medium-mirror
   ```

2. Install dependencies:
   ```bash
   uv sync
   # or
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Open your browser at `http://localhost:8000`.

## 📂 Project Structure

- `app/api/`: FastAPI endpoints and routes.
- `app/core/`: Database configuration and project settings.
- `app/models/`: SQLAlchemy database models.
- `app/services/`: Content fetchers, parsers, and search logic.
- `app/templates/`: Jinja2 HTML templates with Tailwind CSS.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License. See `LICENSE` for more information.
