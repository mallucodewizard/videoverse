# videoverse

## Setup and Run the Django Project

### Prerequisites

- Python 3.x installed on your machine
- `pip` (Python package installer)

### Step 1: Clone the Repository

Clone the repository to your local machine using the following command:


git clone <repository_url>
cd videoverse/videoverse_project

### Step 3: Install Dependencies

Install the required packages using `requirements.txt`:

-   pip install -r requirements.txt

### Step 4: Apply Migrations
Apply the database migrations to set up your database schema:
- python manage.py migrate

### Step 5: Run the Development Server
Start the Django development server:

- python manage.py runserver
http://127.0.0.1:8000

Additional Commands
Running Tests

- python manage.py test


1. **Additional Commands**: python manage.py createsuperuser (for creating superuser in django).
2. **Troubleshooting**: [Django documentation](https://docs.djangoproject.com/en/stable/) for further assistance.

```sh