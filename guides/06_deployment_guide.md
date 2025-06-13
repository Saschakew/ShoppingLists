# 6. Deployment Guide: AWS Elastic Beanstalk

This guide provides step-by-step instructions for deploying the ShoppingLists Flask application to AWS Elastic Beanstalk (EB). Elastic Beanstalk is a PaaS (Platform as a Service) that simplifies deploying and scaling web applications.

## Prerequisites

1.  **AWS Account:** You need an active AWS account.
2.  **AWS CLI & EB CLI:** Ensure you have the AWS Command Line Interface (CLI) and the Elastic Beanstalk CLI installed and configured on your local machine.
    *   [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
    *   [Install EB CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html)
3.  **Application Code:** Your ShoppingLists application code, including `requirements.txt`, `application.py`, and `Procfile`.
4.  **ZIP Archive:** Elastic Beanstalk deploys applications from a `.zip` file. You'll need to create this archive (excluding `venv`, `.git`, `__pycache__`, etc.). The EB CLI can help with this.

## Core Deployment Files

Ensure these files are correctly configured in the root of your project:

*   **`application.py`:** This is the entry point Elastic Beanstalk uses. It should instantiate your Flask app using the `create_app` factory.
    ```python
    # application.py
    from shopping_list_app.app import create_app

    # Elastic Beanstalk expects the WSGI callable to be named 'application'.
    application = create_app()

    # Optional: For running with Flask's dev server locally via `python application.py`
    # This part is NOT used by Gunicorn/EB directly but can be useful for local checks.
    # To run locally with SocketIO support for testing purposes:
    if __name__ == "__main__":
        from shopping_list_app.extensions import socketio # Assuming socketio is initialized in extensions
        # The debug flag should ideally be False or controlled by an env var for prod-like testing
        # For true development, you'd run via run_dev.bat or similar which sets FLASK_DEBUG.
        socketio.run(application, host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    ```

*   **`Procfile`:** Tells Elastic Beanstalk how to start your web application. For Gunicorn with Eventlet (for SocketIO):
    ```Procfile
    web: gunicorn --worker-class eventlet -b :5000 "application:application"
    ```
    *   `application:application` refers to the `application` callable within your `application.py` file.
    *   The port `:5000` is an internal port Gunicorn listens on; Elastic Beanstalk's Nginx will proxy requests from port 80 (HTTP) or 443 (HTTPS) to this port.

*   **`requirements.txt`:** Must list all dependencies, including `Flask`, `Flask-SocketIO`, `gunicorn`, and `eventlet`.

## Deployment Steps

### 1. Initialize Elastic Beanstalk Application

Navigate to your project's root directory in your terminal:

```bash
eb init -p python-3.8 <your-app-name>
```

*   Replace `python-3.8` with the desired Python version supported by EB (e.g., `python-3.9`, `python-3.11`). Check the latest EB Python platform versions.
*   Replace `<your-app-name>` with a unique name for your application (e.g., `shoppinglists`).
*   Follow the prompts to select a region and associate with your AWS credentials.
*   When asked about CodeCommit, choose 'N' unless you plan to use it.
*   It might ask to set up SSH. This is useful for debugging but not strictly necessary for basic deployment.

This command creates a `.elasticbeanstalk` directory in your project with configuration files.

### 2. Create an Environment

This step provisions the AWS resources (EC2 instances, load balancer, etc.) for your application:

```bash
eb create <your-environment-name>
```

*   Replace `<your-environment-name>` with a name for this specific deployment environment (e.g., `shoppinglists-dev` or `shoppinglists-prod`).
*   This process can take several minutes.
*   The EB CLI will automatically zip your application files (respecting `.ebignore` or `.gitignore` if configured) and upload it.

### 3. Configure Environment Variables

Your application requires environment variables like `SECRET_KEY`, `FLASK_ENV`, `SESSION_TYPE`, `REDIS_URL` (if using Redis), and `SOCKETIO_MESSAGE_QUEUE`.

Set these through the Elastic Beanstalk console:

1.  Go to the AWS Management Console -> Elastic Beanstalk.
2.  Select your application and then your environment.
3.  Go to **Configuration** -> **Software** -> **Edit**.
4.  Under **Environment properties**, add your key-value pairs:
    *   `FLASK_ENV`: `production`
    *   `SECRET_KEY`: *Your strong, unique secret key*
    *   `SESSION_TYPE`: `redis` (if using Redis for sessions)
    *   `REDIS_URL`: `redis://your-redis-endpoint:6379/0` (if using ElastiCache Redis or other Redis provider)
    *   `SOCKETIO_MESSAGE_QUEUE`: `redis://your-redis-endpoint:6379/1` (use a different Redis DB number or a separate Redis instance for SocketIO message queue if scaling beyond one instance)
    *   `FLASK_APP`: `application.py` (Though EB typically infers this, it can be good to set explicitly)
    *   `FLASK_DEBUG`: `0` (or remove, as `FLASK_ENV=production` implies this)
5.  Click **Apply**.
The environment will update, which might take a few minutes.

### 4. Static Files

By default, Elastic Beanstalk's Python platform uses Nginx, which can be configured to serve static files directly. You can configure this using `.ebextensions` for more control, or rely on default behaviors.

A common way to configure Nginx for static files via `.ebextensions` is to create a file like `.ebextensions/01_nginx_static.config`:

```yaml
# .ebextensions/01_nginx_static.config
option_settings:
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: shopping_list_app/static
```

This tells Nginx to serve files from the URL path `/static` directly from the `shopping_list_app/static` directory in your application bundle.

If you don't use `.ebextensions`, Nginx might still serve static files based on its default Python platform configuration, but using `option_settings` provides explicit control.

### 5. Database Setup (RDS)

For a production application, it's highly recommended to use Amazon RDS (Relational Database Service) instead of SQLite.

1.  **Create an RDS Instance:**
    *   Go to the AWS RDS console and create a new database (e.g., PostgreSQL or MySQL).
    *   Ensure it's in the same VPC as your Elastic Beanstalk environment or that security groups allow access from your EB EC2 instances.
2.  **Configure Security Groups:**
    *   The security group for your RDS instance must allow inbound connections on the database port (e.g., 5432 for PostgreSQL) from the security group of your Elastic Beanstalk EC2 instances.
3.  **Set Database URL:**
    *   Add the `DATABASE_URL` (or your app's specific SQLAlchemy connection string variable) to your Elastic Beanstalk environment variables (e.g., `postgresql://user:password@your-rds-endpoint.rds.amazonaws.com:5432/yourdbname`).

### 6. Running Database Migrations

After deploying and setting up RDS, you'll need to run your database migrations.

*   **Using `.ebextensions` (Recommended for automation):**
    You can create a configuration file in `.ebextensions` to run migrations during deployment. This command should only run on one instance (the leader).

    Example for Flask-Migrate (`.ebextensions/02_migrations.config`):
    ```yaml
    # .ebextensions/02_migrations.config
    container_commands:
      01_flask_db_upgrade:
        command: "source /var/app/venv/staging-LQM1lest/bin/activate && export FLASK_APP=application.py && flask db upgrade"
        leader_only: true
    ```
    *   **Note:** The path to `activate` (`/var/app/venv/staging-LQM1lest/bin/activate`) might vary slightly depending on the EB platform version. You might need to SSH into an instance to confirm the exact path or use a more dynamic way to source it.
    *   Ensure `FLASK_APP` is correctly set for the `flask` command to find your app and migrations.

*   **Manual Migration (Less ideal for automation):**
    1.  SSH into one of your EC2 instances managed by Elastic Beanstalk.
    2.  Navigate to `/var/app/current` (or `/var/app/staging` during deployment).
    3.  Activate the virtual environment (e.g., `source /var/app/venv/staging-LQM1lest/bin/activate`).
    4.  Set necessary environment variables if not already present (e.g., `export FLASK_APP=application.py`, `export DATABASE_URL=...`).
    5.  Run `flask db upgrade`.

### 7. SocketIO Configuration for Scalability

*   **Sticky Sessions:** If your environment scales to more than one EC2 instance, you need to enable sticky sessions (session affinity) on the Application Load Balancer (ALB) used by Elastic Beanstalk. This ensures a client consistently connects to the same server instance for the duration of their SocketIO session.
    *   Go to EC2 -> Load Balancers -> Select your ALB -> Listeners tab.
    *   For your HTTP/HTTPS listener, edit the rules.
    *   Forward to your target group. Edit the target group attributes and enable stickiness (e.g., AWSALB cookie, duration-based).
*   **Message Queue:** For robust multi-instance SocketIO, a message queue (like Redis) is essential. Ensure `SOCKETIO_MESSAGE_QUEUE` is set in your environment variables (e.g., `redis://your-redis-endpoint:6379/1`).

### 8. Accessing Your Application

Once the `eb create` or `eb deploy` command finishes successfully, the EB CLI will output the URL for your application. You can also find this URL in the Elastic Beanstalk console.

### 9. Deploying Updates

To deploy updates to your application:

1.  Commit your changes to Git.
2.  Run:
    ```bash
    eb deploy
    ```
    The EB CLI will package and upload the new version.

### 10. Logging and Monitoring

*   **EB Console:** Access logs directly from the Elastic Beanstalk environment page (Logs section).
*   **EB CLI:**
    ```bash
    eb logs
    eb health
    ```
*   **Instance Logs:** You can SSH into individual instances to view logs in `/var/log/` (e.g., `web.stdout.log` for Gunicorn output, Nginx logs).

## Troubleshooting Common Issues

*   **502 Bad Gateway:** Often indicates your application failed to start. Check `web.stdout.log` or `eb logs` for errors from Gunicorn or your Flask app.
*   **Permissions Errors:** Ensure your application files have appropriate permissions.
*   **Missing Dependencies:** Double-check `requirements.txt`.
*   **Environment Variables:** Verify all necessary environment variables are set correctly in the EB configuration.
*   **SocketIO Not Connecting:** Check Nginx configuration for WebSocket proxying (EB usually handles this with the Python platform, but custom Nginx configs might interfere), sticky sessions, and the message queue if using multiple instances.

This guide provides a comprehensive overview of deploying your ShoppingLists application to AWS Elastic Beanstalk. Always refer to the official AWS Elastic Beanstalk documentation for the most up-to-date information and advanced configurations.
