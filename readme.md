# JobLane Backend

**JobLane** is a scalable, production-ready backend for a job hiring platform built using **Django REST Framework** (DRF).  
It powers secure authentication, role-based access, job management, applications, and admin analytics for the JobLane platform.  

This repository serves the **RESTful API** consumed by the React.js frontend.


## Key Highlights

- JWT authentication with refresh token rotation
- Email-based OTP verification (registration & password reset)
- Google OAuth2 login integration
- Role-based access control (Job Seeker, Recruiter, Admin)
- Resume uploads using Cloudinary
- Admin analytics dashboard with Django Jazzmin
- Rate-limited APIs using DRF throttling
- Production-ready deployment on Render

## Features

### Job Seekers
- User registration with email OTP verification
- Login using JWT or Google OAuth
- Browse and search job listings
- Apply for jobs with resume upload
- Save jobs for later
- Manage profile information

### Recruiters
- Recruiter-specific job management
- Create, update, and delete job postings
- View applicants for posted jobs
- Access control for recruiter-only actions

### Admin
- Custom Django admin using Jazzmin
- Admin analytics dashboard
- User, job, and application management
- Platform-level monitoring

### Authentication & Security
- JWT authentication using SimpleJWT
- Refresh token rotation & blacklisting
- Email-based OTP verification
- Google OAuth2 login
- Custom authentication backend (username/email)


## Tech Stack

- Python 3.x
- Django 5.x
- Django REST Framework
- PostgreSQL (NeonDB)
- dj-rest-auth
- SimpleJWT
- Cloudinary (media storage)
- Jazzmin (admin UI)
- Whitenoise (static file handling)

## Live Demo
Backend: [https://joblane-backend-0eqs.onrender.com/](https://joblane-backend-0eqs.onrender.com/)  
Frontend: [https://joblane-frontend.vercel.app/](https://joblane-frontend.vercel.app/)


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

## Docker Setup
Make sure Docker & Docker Compose are installed on your system.

### 1. Start the App
```
docker-compose up --build
```

### 2. Stop the App
```
docker-compose down
```

### 3. Run Django Commands Inside Docker
```
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
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

#Google Auth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=secret
GOOGLE_REDIRECT_URI=http://localhost:5173
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

### Authentication APIs
| Endpoint          | Method | Description                        |
| ----------------- | ------ | ---------------------------------- |
| `/auth/login/`    | POST   | Obtain JWT access & refresh tokens |
| `/auth/register/` | POST   | User registration                  |
| `/auth/google/`   | POST   | Google social login                |
| `/auth/profile/`  | GET    | Get authenticated user profile     |

### Jobseeker APIs
| Endpoint                | Method | Description                         |
| ----------------------- | ------ | ----------------------------------- |
| `/api/jobs/`            | GET    | List all job posts                  |
| `/api/jobs/{id}/`       | GET    | Retrieve single job details         |
| `/api/jobs/{id}/apply/` | POST   | Apply to a job                      |
| `/api/applied/`         | GET    | List jobs applied by logged-in user |
| `/api/jobs/{id}/save/`  | POST   | Save a job                          |
| `/api/saved/`           | GET    | List saved jobs                     |
| `/api/filters/`         | GET    | Get job filter options              |

### Recruiter APIs
| Endpoint                                   | Method    | Description                    |
| ------------------------------------------ | --------- | ------------------------------ |
| `/api/recruiter/jobs/`                     | GET       | List recruiter’s jobs          |
| `/api/recruiter/jobs/`                     | POST      | Create a new job               |
| `/api/recruiter/jobs/{id}/`                | PUT       | Update recruiter job           |
| `/api/recruiter/jobs/{id}/`                | DELETE    | Delete recruiter job           |
| `/api/recruiter/jobs/{job_id}/applicants/` | GET       | View applicants for a job      |
| `/api/recruiter/applicants/{id}/`          | GET       | View applicant details         |
| `/api/recruiter/applicants/{id}/status/`   | PATCH     | Update application status      |
| `/api/recruiter/company/`                  | GET / PUT | View or update company profile |
| `/api/recruiter/applicants/export/`        | GET       | Export applicants (Excel)  |


## Future Enhancements

- AI-based job recommendation engine
- Resume parsing & skill extraction
- Real-time notifications (WebSockets)
- Advanced analytics & reporting
- Audit logs for admin actions

## Contributing
Contributions, bug reports, and feature requests are welcome!

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request