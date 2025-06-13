# ShoppingLists Project Overview

## Introduction

The ShoppingLists application is a Flask-based web application designed to allow users to create, manage, and share shopping lists. It supports user authentication and is designed for deployment on AWS Elastic Beanstalk, with considerations for cost optimization and scalability.

This set of guides aims to provide a comprehensive understanding of the project's architecture, features, setup, deployment, and maintenance for developers.

## Table of Contents

**New Developers: Start Here! --> [Quick Entry Guide for New Developers](./entry.md)**


This overview will be updated with links to detailed sub-guides covering various aspects of the project. Planned guides include:

*   **1. Setup and Installation:** [Instructions for setting up the development environment and running the application locally.](./01_setup_and_installation.md)
*   **2. Application Architecture:** [A deep dive into the project structure, main components, and how they interact.](./02_application_architecture.md)
*   **3. Core Features:** [Detailed explanation of key functionalities like list management, item handling, user accounts, and sharing.](./03_core_features.md)
*   **4. Database Guide:** [Information about the database schema, models, and migrations.](./04_database_guide.md)
*   **5. Frontend Development:** [Overview of templates, static assets (CSS, JS), and frontend logic.](./05_frontend_development.md)
*   **6. Deployment Guide:** [Steps and configurations for deploying the application to AWS Elastic Beanstalk.](./06_deployment_guide.md)
*   **7. AWS Cost Optimization:** [Strategies and implementations for reducing operational costs on AWS.](./07_aws_cost_optimization.md)
*   **8. Testing Strategy:** [How to run and write tests for the application.](./08_testing_strategy.md)
*   **9. Development Workflow:** [Guidelines for contributing to the project, including branching, PRs, and keeping documentation updated.](./09_development_workflow.md)



## Technology Stack

*   **Backend:** Python, Flask
*   **Frontend:** HTML, CSS, JavaScript, Jinja2 (Templating), Bootstrap
*   **Database:** SQLAlchemy (ORM), SQLite (default for development), (Potentially PostgreSQL for production)
*   **Session Management:** Flask-Session (with Redis for production, as per optimization goals)
*   **WSGI Server (Production):** Gunicorn, Eventlet
*   **Deployment:** AWS Elastic Beanstalk
*   **Testing:** Pytest
*   **Version Control:** Git
