# Welcome to the ShoppingLists Project!

This document provides a quick entry point for new developers joining the ShoppingLists project. Our goal is to help you get up to speed quickly and understand the project's structure, key features, and development practices.

## 1. Getting Started: Your First Steps

Before diving deep, please familiarize yourself with the initial setup and project overview:

*   **Project Overview:** Start with the [Project Overview](./project_overview.md). It provides a table of contents for all detailed developer guides.
*   **Setup and Installation:** Follow the [Setup and Installation Guide](./01_setup_installation.md) to get your local development environment running.

## 2. Understanding the Big Picture

Once you have the project running locally, these guides will help you understand its architecture and core components:

*   **Application Architecture:** [Application Architecture Guide](./02_application_architecture.md) - Understand how the Flask application is structured, including blueprints, the app factory pattern, configuration, and key extensions.
*   **Core Features:** [Core Features Guide](./03_core_features.md) - Learn about the main functionalities of the application from a user and technical perspective.
*   **Database:** [Database Guide](./04_database_guide.md) - Get familiar with the database schema, SQLAlchemy models, and how database migrations are handled.

## 3. Development Practices

As you start contributing, these guides are essential:

*   **Frontend Development:** [Frontend Development Guide](./05_frontend_development.md) - If you're working on the UI, this guide covers Jinja2 templates, static assets, and client-side JavaScript.
*   **Testing Strategy:** [Testing Strategy Guide](./08_testing_strategy.md) - Learn how to run and write tests for the application using Pytest.
*   **Development Workflow:** (To be created - this will cover branching, PRs, code style, etc.)

## 4. Deployment & Operations

For understanding how the application is deployed and managed in production:

*   **Deployment Guide:** [Deployment Guide (AWS Elastic Beanstalk)](./06_deployment_guide.md) - Details the deployment process to AWS.
*   **AWS Cost Optimization:** [AWS Cost Optimization Guide](./07_aws_cost_optimization.md) - Strategies for managing AWS costs effectively.

## 5. Key Technologies

*   **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-SocketIO, Flask-Session, Gunicorn.
*   **Frontend:** HTML, CSS, JavaScript, Jinja2, Bootstrap, Socket.IO Client.
*   **Database:** SQLite (development), PostgreSQL/MySQL (recommended for production), Redis (for sessions and SocketIO message queue).
*   **Testing:** Pytest, pytest-flask.
*   **Deployment:** AWS Elastic Beanstalk, Docker (implicitly via EB).

## 6. Where to Find Things

*   **Main Application Code:** `shopping_list_app/`
*   **Models:** `shopping_list_app/models.py`
*   **Routes/Views (Blueprints):** `shopping_list_app/auth/routes.py`, `shopping_list_app/main/routes.py`, `shopping_list_app/api/routes.py`
*   **Templates:** `shopping_list_app/templates/`
*   **Static Files:** `shopping_list_app/static/`
*   **Tests:** `tests/`
*   **Developer Guides:** `guides/` (you are here!)

We're excited to have you on the team! If you have any questions, don't hesitate to ask.
