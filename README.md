# 🏋️ Gym Booking Service

**Gym Booking Service** is a web application for managing gyms, trainers, and training sessions.  
It allows users to search, book, and join training sessions, while trainers and administrators can manage schedules, gyms, and user accounts.

---

## 🚀 Features

- 👤 **Users**
  - Sign up, log in, and activate accounts via email
  - Browse available training sessions
  - Book and join trainings

- 🏋️ **Trainers**
  - Create and manage their own training sessions

- 🛠️ **Administrators**
  - Add gyms and training sessions
  - Create and manage trainers and other administrators

---

## 🛠️ Tech Stack

- [Django](https://www.djangoproject.com/) — backend framework
- [SQLite / PostgreSQL] — database (SQLite for local development, PostgreSQL for production)
- [Django Messages Framework](https://docs.djangoproject.com/en/5.2/ref/contrib/messages/) — user notifications
- Email-based account activation

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/gym-booking-service.git
cd gym-booking-service
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file or copy `.env.example` and set:
```ini
# DJANGO
SECRET_KEY=django-insecure-CHANGE_ME
DJANGO_SETTINGS_MODULE=config.settings.dev

# DB
POSTGRES_DB=neondb
POSTGRES_DB_PORT=5432
POSTGRES_USER=neondb_owner
POSTGRES_PASSWORD=CHANGE_ME
POSTGRES_HOST=localhost

# SMTP
EMAIL_HOST_USER=example@gmail.com
EMAIL_HOST_PASSWORD=CHANGE_ME
```

### 5. Apply migrations
```bash
python manage.py migrate
```

### 6. Create superuser
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---
## 🌍 Live Demo

Check out the deployed version here: [Gym Booking Service](https://gym-booking-service.onrender.com/)

___
## 🌐 Deployment

### Production Setup
- Use PostgreSQL instead of SQLite
- Set `DEBUG=False` and configure `ALLOWED_HOSTS`
- Configure real SMTP credentials for email activation

### Environment Variables

[.env.sample](.env.sample)
---

## 🔑 User Flow

1. **User registers** an account
2. **Receives activation email**
3. **Activates account**
4. **Browses and books** trainings
5. **Trainers manage** sessions
6. **Admins manage** gyms, sessions, and trainers



---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

**MIT License** — free to use and modify for learning or production projects 🚀
