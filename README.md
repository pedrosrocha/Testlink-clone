# 🧪TestClone

<p align="center">
  <img src="readme_assets/testclone/1018.gif" alt="Testclone" width="800" />
</p>

A web application for managing software testing projects, including test specifications, test suites, and test cases, inspired by the famous [TestLink](https://testlink.org/) with a spin on its looks and a few added funcitonalities.

[Live demo](https://tesclone.onrender.com/): \
username: **editor user** \
password: **editor**

The database deploy was made using [aiven](https://aiven.io/) and the flask deploy was made on [render](https://render.com/). Both free tier, so it may take a few seconds to fully load the apllication. 


for admin privilegies send me an email at **pedro.vic13133@gmail.com** or reach me on [linkedin](https://linkedin.com/in/pedrovicrocha)




## ⚙️Core Technologies Used

| Layer | Technologies |
|--------|---------------|
| **Backend** | Python  · Flask · SQLAlchemy Core |
| **Frontend** | JavaScript (Fetch API) · jQuery · Bootstrap 5 · Jinja2 · SortableJS · jsTree |
| **Database** | MySQL  |
| **Testing** | Pytest · unittest.mock |
| **Environment** | Pipenv  |
<p align="left"> 
  <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExZHZmNnRndnBnNXM0d2hlZmFobHR1NDVqczF3MndodGRhYXYyb3EwNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/SvFocn0wNMx0iv2rYz/giphy.gif" alt="js" width="75"/> 
  <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmI5OTB1b2I2bGY3dWtleTdyNHptNDVyNmdiYmFneTd6NDU3NHp3biZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/KAq5w47R9rmTuvWOWa/giphy.gif" alt="py" width="75"/>
</p>

## 🌟Key Features
*    🔐**User Authentication & Security:**
        Session-based authentication to manage user access.

*    🧩**Project & Test Management:**
        * Create and manage multiple testing projects.
        * Organize tests in a hierarchical structure using Test Suites.
        * Create, edit, and delete Test Cases with detailed steps (actions and expected results).
        * Drag-and-drop functionality to reorder test steps.
        * Version control for test cases to track changes over time.

*    👥**Role-Based Access Control (RBAC):**
        * Admin: Full control over users, projects, and system settings.
        * Editor: Can create, edit, and manage test suites and test cases.
        * Viewer: Read-only access to test specifications.

*    💻**Intuitive User Interface:**
        * A clean, responsive UI built with Bootstrap 5.
        * A dynamic, tree-based navigation for test suites and cases (jstree).
        * Rich text editing for test steps provided by TinyMCE.
        * 

## 🧠 Key Architectural Concepts

*   **Separation of Concerns:** The application is structured with a clear separation between the web views (Flask), business logic (service layer in `Parameters`), and data access (database connectors).
*   **Role-Based Access Control:** User actions are restricted based on roles (Admin, Editor, Viewer) using custom decorators.
*   **RESTful API Design:** The frontend communicates with the backend for dynamic actions (e.g., creating, renaming, deleting test items) via a RESTful API.
*   **Comprehensive Unit Testing:** The project includes a robust test suite to ensure code quality and reliability.
*   **Performance:** Caching is implemented for database queries to improve application performance.

## 🧩Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Testlink-clone
    ```

2.  **Install dependencies:**
    This project uses Pipenv for dependency management.
    ```bash
    pipenv install
    ```

3.  **Configure Environment:**
    Create a `.env` file in the root directory and add the following variables. Update them with your local database configuration:
    ```env
    SECRET_KEY=your_super_secret_key
    DATABASE_HOST=localhost
    DATABASE_USER=your_db_user
    DATABASE_PASSWORD=your_db_password
    DATABASE_NAME=testclone
    DATABASE_PORT=3306
    DATABASE_KEY=mysql+pymysql://
    ```

4.  **Initialize Database:**
    Run the script to create the database and tables. This script will also populate the database with initial data, including a default administrator account:
    *   **Username:** `admin user`
    *   **Password:** `admin`

    ```bash
    pipenv run python -m webapp.Parameters.Database.create_tables
    ```

## 🚀Running the Application

To start the Flask development server, run:
```bash
pipenv run flask run
```

## 🧪Running Tests

To execute the test suite, run:
```bash
pipenv run pytest
```

