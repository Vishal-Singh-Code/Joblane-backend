# JobLane Backend

**JobLane** is India’s #1 Hiring Platform built using **Django** and **Django REST Framework (DRF)**. This repository contains the backend API for the JobLane application, providing robust and secure services for job seekers and recruiters.

The backend handles authentication, job postings, applications, user roles, and API endpoints, serving the React.js frontend of the platform.

---

## Features

- JWT Authentication with **dj-rest-auth**
- Google OAuth2 Login Integration
- Role-based access for **Job Seekers** and **Recruiters**
- Job posting, updating, and deletion for recruiters
- Applying to jobs for job seekers
- View applicants for each job post
- RESTful API with Django REST Framework

---

## Tech Stack

- Python 3.x
- Django 5.x
- Django REST Framework
- PostgreSQL (NeonDB)
- dj-rest-auth & SimpleJWT

---

## Live Demo

Backend: [https://joblane-backend-0eqs.onrender.com/](https://joblane-backend-0eqs.onrender.com/)  
Frontend: [https://joblane-frontend.vercel.app/](https://joblane-frontend.vercel.app/)

---

## Setup Instructions

### 1️⃣ Clone the repository:
```bash
git clone https://github.com/vishal-singh-code/joblane-backend.git
cd joblane-backend
```
### 2️⃣ Create Virtual Environment and Install Dependencies:
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
### 3️⃣ Database Setup:
```
python manage.py makemigrations
python manage.py migrate
```
### 4️⃣ Run the Development Server:
```
python manage.py runserver
```

## Environment Variables
```
# Django Secret Key
SECRET_KEY=your-django-secret-key

# Debug mode (Set to False for production)
DEBUG=True   # Change to False when deploying

# Allowed Hosts (Comma-separated)
ALLOWED_HOSTS=your-backend-url.onrender.com,localhost,127.0.0.1

# CORS Origins (Comma-separated)
CORS_ALLOWED_ORIGINS=https://joblane-frontend.vercel.app

# Database (Neon or any Postgres DB)
DATABASE_URL=your-database-url

# Cloudinary (For image uploads)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## Project Structure
```
joblane-backend/
├── accounts/       # Custom user & profile management
├── jobs/           # Job posting & applications
├── joblane/        # Core settings & URLs
├── .env
├── requirements.txt
└── manage.py
```
## API Endpoints Overview
| Endpoint                 | Method | Description                           |
| ------------------------ | ------ | ------------------------------------- |
| `/api/login/`            | POST   | Obtain JWT access & refresh tokens    |
| `/api/register/`         | POST   | User registration                     |
| `/api/google/login/`     | POST   | Google social login                   |
| `/api/profile/`          | GET    | Get user profile                      |
| `/api/jobs/`             | GET    | List all job posts                    |
| `/api/jobs/{id}/`        | GET    | Retrieve single job details           |
| `/api/jobs/create/`      | POST   | Create new job post (Recruiter only)  |
| `/api/jobs/update/{id}/` | PUT    | Update job post (Recruiter only)      |
| `/api/jobs/delete/{id}/` | DELETE | Delete job post (Recruiter only)      |
| `/api/apply/`            | POST   | Apply to job (Jobseeker only)         |
| `/api/applicants/{id}/`  | GET    | View applicants for a job (Recruiter) |


## Contributing
Contributions, bug reports, and feature requests are welcome!
Feel free to open an issue or submit a pull request.