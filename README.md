# ShoppingLists Flask Application Deployment Guide

This guide explains how to deploy, update, and troubleshoot the ShoppingLists Flask app on an AWS EC2 instance using Gunicorn, Nginx, and systemd.

---

## 1. Initial AWS EC2 Setup

- Launch an EC2 instance (Amazon Linux 2023 recommended).
- Configure security groups to allow SSH (port 22) and HTTP (port 80).
- SSH into the instance using your key pair.

## 2. Prepare the Server

```bash
# Update and install required packages
sudo yum update -y
sudo yum install -y git python3 python3-pip python3-devel gcc nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 3. Deploy the Application

```bash
# Clone your repository
sudo mkdir -p /var/www/shopping_list_app
sudo chown $USER:$USER /var/www/shopping_list_app
cd /var/www/shopping_list_app
git clone <YOUR_REPO_URL> .

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure Gunicorn with systemd

- Edit `/etc/systemd/system/shoppinglist.service`:

```ini
[Unit]
Description=Gunicorn instance to serve Shopping List app
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/var/www/shopping_list_app
Environment="PATH=/var/www/shopping_list_app/venv/bin"
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=<your-very-long-secret-key>"
ExecStart=/var/www/shopping_list_app/venv/bin/gunicorn --workers 1 --worker-class eventlet -b 0.0.0.0:5000 shopping_list_app.app:app
Restart=always
RestartSec=5s
StandardOutput=append:/var/log/shoppinglist/access.log
StandardError=append:/var/log/shoppinglist/error.log
SyslogIdentifier=shoppinglist

[Install]
WantedBy=multi-user.target
```

- Reload and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start shoppinglist.service
sudo systemctl enable shoppinglist.service
```

## 5. Configure Nginx

- Edit `/etc/nginx/conf.d/shoppinglist.conf`:

```nginx
server {
    listen 80 default_server;
    server_name _;

    location /static {
        alias /var/www/shopping_list_app/shopping_list_app/static;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

- Test and reload Nginx:

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## 6. Updating the Application (Typical Workflow)

1. **Commit and push changes to GitHub from your local machine.**
2. **On the EC2 instance:**
    ```bash
    cd /var/www/shopping_list_app
    git pull
    source venv/bin/activate
    pip install -r requirements.txt  # Important: Update dependencies
    sudo systemctl restart shoppinglist.service
    ```

   **Important:** Always update dependencies after pulling changes. If you've added new packages to your application, failing to update dependencies will cause 502 Bad Gateway errors.

## 7. Performance Optimizations

The application has been optimized for low-cost EC2 instances with the following features:

### Redis Session Management

Sessions are now stored in Redis instead of the filesystem, which reduces I/O load on the application server.

- **Setup Redis on EC2:**
  ```bash
  # Install Redis
  sudo yum install -y redis
  sudo systemctl start redis
  sudo systemctl enable redis
  ```

- **Required Environment Variables:**
  Add these to your systemd service file:
  ```
  Environment="SESSION_TYPE=redis" "REDIS_URL=redis://localhost:6379/0"
  ```

- **Local Development:**
  - On Linux/Mac: The app defaults to filesystem sessions if Redis is not available.
  - On Windows: The app automatically uses Flask's default session handling to avoid compatibility issues between eventlet and Flask-Session.

### Static File Serving

Static files (CSS, JS, images) are served directly by Nginx instead of Flask, which significantly reduces the load on your application server.

- This is configured in `.ebextensions/01_python.config` for Elastic Beanstalk.
- For manual EC2 deployment, ensure your Nginx configuration includes:
  ```
  location /static {
      alias /var/www/shopping_list_app/shopping_list_app/static;
  }
  ```

## 8. Troubleshooting

- **Check Gunicorn logs:**
    ```bash
    sudo journalctl -u shoppinglist.service -e -n 100 --no-pager
    sudo tail -n 50 /var/log/shoppinglist/error.log
    ```
- **Check Nginx logs:**
    ```bash
    sudo tail -n 50 /var/log/nginx/error.log
    sudo tail -n 50 /var/log/nginx/access.log
    ```
- **Check Redis logs:**
    ```bash
    sudo tail -n 50 /var/log/redis/redis.log
    ```
- **Common issues:**
    - **502 Bad Gateway after update:** Usually indicates missing dependencies. Run `pip install -r requirements.txt` in your virtual environment.
    - **Error in logs about missing modules:** Check if you've added new imports without installing the packages.
    - **Session issues after deployment:** Verify Redis is running and the REDIS_URL environment variable is correctly set.
    - **Internal Server Error after login:** Ensure `login_user` uses `duration=timedelta(...)`, not an integer.
    - **Nginx shows default page:** Confirm `shoppinglist.conf` uses `listen 80 default_server;` and `server_name _;`.
    - **Environment variables** in systemd file must be on a single line.

## 9. Security Notes
- Do not expose your `SECRET_KEY`, database credentials, or Redis URL publicly.
- For production, consider setting up HTTPS (Let's Encrypt) and a domain name.
- If using Redis for sessions in production with sensitive data, consider enabling Redis authentication.

---

**For more details, see the comments in the code and configuration files.**

## 9. Local Development

To run the ShoppingLists application locally for development:

1. **Use the provided development script:**
   ```
   run_dev.bat
   ```
   This script will:
   - Create a virtual environment if it doesn't exist
   - Install all required dependencies including development tools
   - Set up the Flask development environment
   - Start the Flask development server

2. **Access the application:**
   - Open your browser and navigate to `http://127.0.0.1:5000`
   - The development server provides automatic reloading when code changes are detected

3. **Development environment features:**
   - Debug mode enabled for detailed error messages
   - Interactive debugger for examining exceptions
   - Automatic reloading when code changes
