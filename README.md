# 🧪TestClone
A web application for managing software testing projects, including test specifications, test suites, and test cases, inspired by the famous [TestLink](https://testlink.org/) with a spin on its looks and a few added funcitonalities.


<p align="center">
  <img src="readme_assets/testclone/1018.gif" alt="Testclone" width="800" />
</p>



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
    Create a `.env` file in the root directory and add the following variables:
    ```
    SECRET_KEY=your_super_secret_key
    DATABASE_KEY=mysql+pymysql://user:password@host/database_name
    ```

4.  **Initialize Database:**
    Run the script to create the necessary database tables.
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

