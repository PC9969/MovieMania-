# MovieMania 🎬 — Preference-Driven Movie Recommendation Platform

**MovieMania** is a full-stack Django web application designed for explicit, preference-driven movie discovery and recommendation.

Unlike traditional recommendation engines that require months of user ratings and opaque black-box machine learning algorithms, MovieMania helps viewers discover what to watch **right now** based on explicit mood, genre, language, minimum rating, era, and runtime preferences with transparent match explanations.

---

## 🌟 Key Highlights & Differentiator

> **"Find something worth watching based on your current preferences, without needing extensive historical watch data."**

- **Transparent Weighted Scoring**: Every recommendation provides a **Match Percentage (0–100%)** accompanied by exact justifications (e.g., *✓ Matches selected genre: Sci-Fi*, *✓ In preferred language: Hindi*, *✓ Rating 8.8 ≥ 8.0*).
- **Curated 70-Movie Real Dataset**: Pre-populated with real, iconic films spanning Hollywood classics, Bollywood masterpieces, and South Indian regional cinema across 18 genres.
- **Modern Dark Cinema UI/UX**: Designed with a bespoke, editorial obsidian palette, responsive cards, image fallback error handlers, and interactive filter controls.
- **Personalized Watchlist**: Authenticated users can bookmark films with instant AJAX toggling and real-time badge count updates.
- **College Viva & GitHub Ready**: Built cleanly with standard Django patterns, complete separation of concerns, and full unit test coverage.

---

## 🏗️ Architecture & How It Works

```
User Input (Mood, Genre, Language, Min Rating, Era, Runtime)
      │
      ▼
Django View (`movies:discover` / API)
      │
      ▼
Recommendation Engine (`movies/recommender.py`)
  ├── 1. Dynamic Weight Normalization (Genre: 35%, Lang: 25%, Rating: 20%, Era: 10%, Runtime: 5%, Mood: 5%)
  ├── 2. Candidate Filtering & DB Querying (Django ORM prefetch)
  ├── 3. Multi-Factor Match Scoring (0% - 100%)
  └── 4. Human-Readable Justification Compilation
      │
      ▼
Results Presentation (Dynamic Movie Cards with Match Badges & Reasons)
      │
      ▼
User Interaction (View Details / Content-Similar Shelf / Add to Watchlist)
```

### Recommendation Scoring Formula (Viva Explanation)
When all filters are active, the match score $S$ is calculated as:
$$S = W_{\text{genre}} \cdot M_{\text{genre}} + W_{\text{lang}} \cdot M_{\text{lang}} + W_{\text{rating}} \cdot M_{\text{rating}} + W_{\text{era}} \cdot M_{\text{era}} + W_{\text{runtime}} \cdot M_{\text{runtime}} + W_{\text{mood}} \cdot M_{\text{mood}}$$

- **Genre Match ($35\%$)**: Evaluates overlap between selected genres and movie genres ($80\%$ base for 1st match + bonus for multi-match).
- **Language Match ($25\%$)**: Exact match with user's selected language.
- **Rating Criteria ($20\%$)**: Full points if $R_{\text{movie}} \ge R_{\text{min}}$, with smooth fractional credit for close contenders.
- **Era Match ($10\%$)**: Verifies if release year falls within selected decade ($2020\text{s}$, $2010\text{s}$, $2000\text{s}$, $90\text{s}$, or Pre-$1990$ Classics).
- **Runtime & Mood ($5\% + 5\%$)**: Matches pacing and vibe tags (e.g., *Mind-Bending*, *Inspiring*, *Feel-Good*).
- *Dynamic Normalization*: If the user leaves criteria as "Any" (e.g. All Languages), active weights automatically re-scale to sum to $100\%$.

---

## 🗄️ Database Models

1. **`Genre`**:
   - `name` (unique CharField)
   - `slug` (SlugField)
2. **`Movie`**:
   - `title`, `slug` (unique)
   - `overview` (TextField)
   - `genres` (ManyToManyField to `Genre`)
   - `language` (CharField with choices: English, Hindi, Tamil, Telugu, Malayalam, Kannada, Korean, Japanese, etc.)
   - `release_year` (PositiveIntegerField)
   - `rating` (DecimalField, e.g., 8.8)
   - `runtime_minutes` (PositiveIntegerField)
   - `director` (CharField)
   - `cast` (TextField)
   - `poster_url`, `backdrop_url` (URLField)
   - `mood_tag` (CharField, e.g., "Mind-Bending")
   - `featured` (BooleanField)
3. **`Watchlist`**:
   - `user` (ForeignKey to `User`)
   - `movie` (ForeignKey to `Movie`)
   - `added_at` (DateTimeField)
   - UniqueConstraint on `(user, movie)`

---

## 📁 Project Structure

```
MovieMania-/
├── movie_project/
│   ├── settings.py           # Project settings & app registration
│   ├── urls.py               # Main URL router
│   ├── asgi.py
│   └── wsgi.py
├── movies/
│   ├── management/
│   │   └── commands/
│   │       └── load_movies.py# 70-movie database seeder command
│   ├── migrations/           # Database migrations
│   ├── admin.py              # Custom Django admin interface
│   ├── apps.py               # App configuration
│   ├── context_processors.py # Watchlist count context processor
│   ├── models.py             # Database models (Genre, Movie, Watchlist)
│   ├── recommender.py        # Recommendation algorithm & explanations
│   ├── tests.py              # Automated unit tests (12 tests)
│   ├── urls.py               # Movies app routes
│   └── views.py              # View controllers (Home, Discover, Detail, Watchlist, Auth, API)
├── static/
│   ├── css/
│   │   └── style.css         # Modern dark cinema CSS styling
│   └── js/
│       └── main.js           # AJAX watchlist toggle, filter sync, image fallbacks
├── templates/
│   ├── base.html             # Base layout template
│   └── movies/
│       ├── home.html         # Landing page with hero & shelves
│       ├── discover.html     # Recommendation engine page
│       ├── movie_detail.html # Detailed movie information & similar movies
│       ├── search.html       # Search results page
│       ├── watchlist.html    # User watchlist
│       ├── login.html        # Authentication login
│       └── register.html     # User registration
├── db.sqlite3                # SQLite database
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Installation Instructions

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Git

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone <repository-url>
cd MovieMania-

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Load Curated 70-Movie Dataset
Populate the database with real Hollywood, Bollywood, and South Indian movies:
```bash
python manage.py load_movies
```
*(Optional: Use `python manage.py load_movies --clear` to reset and reload the dataset).*

### 6. Create Superuser (Django Admin)
```bash
python manage.py createsuperuser
```
Follow the prompts to set your username and password.

### 7. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Running Automated Tests

Run the test suite:
```bash
python manage.py test movies
```
*Executes unit tests verifying model creation, recommendation scoring calculations, view rendering, AJAX watchlist toggles, and JSON API endpoints.*

---

## 🌐 API Endpoint

MovieMania provides a RESTful JSON endpoint for recommendations:
- **Endpoint**: `GET /api/recommend/`
- **Parameters**: `genres`, `language`, `min_rating`, `era`, `runtime`, `mood`
- **Example**:
  ```bash
  curl "http://127.0.0.1:8000/api/recommend/?language=English&genres=Sci-Fi&min_rating=8.0"
  ```
- **Response**: Returns matching movies, percentage scores, and justification points.

---

## 🔮 Future Improvements
- Collaborative filtering hybrid layer when user rating volume grows.
- User reviews and community star ratings.
- Personalized email digest of weekly recommended discoveries.
- Streaming availability provider integration (e.g. Netflix, Prime Video tags).

---

## 📚 Academic Reference & Attribution
This project was developed independently for academic and viva demonstration purposes, using the **GeeksforGeeks** tutorial *"Movie Recommendation System using Django"* ([Reference Article](https://www.geeksforgeeks.org/python/movie-recommendation-system-using-django/)) as an architectural and conceptual inspiration. The implementation has been completely rebuilt with modern cinema domain modeling, multi-factor weighted scoring, an expanded 70-movie authentic dataset, custom dark-mode design, AJAX watchlist functionality, and responsive UI components.

---
*Created for MovieMania — Academic Project Presentation.*
