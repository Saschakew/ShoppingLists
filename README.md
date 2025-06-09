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
ExecStart=/var/www/shopping_list_app/venv/bin/gunicorn --workers 1 --worker-class eventlet -b 0.0.0.0:5000 "shopping_list_app.app:create_app()"
Restart=always
RestartSec=5s
StandardOutput=append:/var/log/shoppinglist/access.log
StandardError=append:/var/log/shoppinglist/error.log
SyslogIdentifier=shoppinglist

[Install]
WantedBy=multi-user.target
```

> **IMPORTANT:** Note that the ExecStart line uses `"shopping_list_app.app:create_app()"` (with quotes) instead of `shopping_list_app.app:app`. This is because the application uses the factory pattern where the Flask app is created by a function rather than being a global variable.

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
    
    # Backup the database before pulling (optional but recommended)
    cp instance/shopping_list.db instance/shopping_list.db.backup
    
    # Pull changes
    git pull
    
    # Update dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Recreate database if needed (if database file was removed or schema changed)
    # This script handles eventlet monkey patching correctly
    cat > init_db.py << 'EOF'
    import eventlet
    eventlet.monkey_patch()
    
    from shopping_list_app.app import create_app
    from shopping_list_app.models import db
    
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    EOF
    
    # Run only if database issues are suspected
    python init_db.py
    
    # Restart the service
    sudo systemctl restart shoppinglist.service
    ```

   **Important Notes:**
   
   1. **Always update dependencies** after pulling changes. New packages or version changes can cause 502 Bad Gateway errors.
   
   2. **Database handling:**
      - If you see database errors after updating, run the `init_db.py` script to recreate tables
      - Consider backing up your database before major updates
      - Remember that the database file is now ignored by git (as it should be)
   
   3. **Application factory pattern:**
      - This application uses the factory pattern with `create_app()`
      - The systemd service must use `"shopping_list_app.app:create_app()"` (with quotes)
      - If you see "Failed to find attribute 'app'" errors, check this configuration

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

### Checking Logs

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

### Common Issues and Solutions

#### 502 Bad Gateway Errors

1. **Missing Dependencies**
   ```bash
   cd /var/www/shopping_list_app
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart shoppinglist.service
   ```

2. **Permission Issues** (status=4/NOPERMISSION in logs)
   ```bash
   # Fix ownership of application files
   sudo chown -R ec2-user:ec2-user /var/www/shopping_list_app
   
   # Ensure log directory exists with correct permissions
   sudo mkdir -p /var/log/shoppinglist
   sudo chown -R ec2-user:ec2-user /var/log/shoppinglist
   
   # Create instance directory if needed
   mkdir -p /var/www/shopping_list_app/instance
   chmod 755 /var/www/shopping_list_app/instance
   
   sudo systemctl restart shoppinglist.service
   ```

3. **Implementation Errors** (status=3/NOTIMPLEMENTED in logs)
   - Check if your app structure changed (e.g., module names, entry point)
   - Verify the ExecStart path in the systemd service file matches your current app structure
   - Check for syntax errors in your Python code

#### Other Common Issues

- **Error in logs about missing modules:** Check if you've added new imports without installing the packages.
- **Session issues after deployment:** Verify Redis is running and the REDIS_URL environment variable is correctly set.
- **Internal Server Error after login:** Ensure `login_user` uses `duration=timedelta(...)`, not an integer.
- **Nginx shows default page:** Confirm `shoppinglist.conf` uses `listen 80 default_server;` and `server_name _;`.
- **Environment variables** in systemd file must be on a single line.

## 9. Security Notes
- Do not expose your `SECRET_KEY`, database credentials, or Redis URL publicly.
- For production, consider setting up HTTPS (Let's Encrypt) and a domain name.
- If using Redis for sessions in production with sensitive data, consider enabling Redis authentication.

## 10. Subdomain Configuration

### AWS Route 53 Setup

1. **Create an A-record for your subdomain:**
   - In the Route 53 console, go to your hosted zone for `sascha-keweloh.com`
   - Create a new record with:
     - Name: `shoppinglists` (this creates `shoppinglists.sascha-keweloh.com`)
     - Type: A
     - Value: Your EC2 instance's Elastic IP address
     - TTL: 300 (or your preferred value)

2. **Verify DNS propagation:**
   ```bash
   nslookup shoppinglists.sascha-keweloh.com
   ```
   
### Nginx Configuration for Subdomain

- Edit `/etc/nginx/conf.d/shoppinglist.conf`:

```nginx
server {
    listen 80;
    server_name shoppinglists.sascha-keweloh.com;

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
    
    # WebSocket support for SocketIO
    location /socket.io {
        proxy_pass http://127.0.0.1:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Environment Variables for Subdomain

- Update your systemd service file (`/etc/systemd/system/shoppinglist.service`) to include the SERVER_NAME environment variable:

```ini
[Service]
# ... other settings ...
Environment="SERVER_NAME=shoppinglists.sascha-keweloh.com"
# ... other settings ...
```

- Restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart shoppinglist.service
```

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

## 10. Git Workflow and Database Files

The SQLite database file (`instance/shopping_list.db`) is ignored in `.gitignore` to prevent conflicts between different development environments. However, if you encounter the following error when pulling changes:

```
error: Your local changes to the following files would be overwritten by merge:
        instance/shopping_list.db
Please commit your changes or stash them before you merge.
Aborting
```

Use one of these solutions:

1. **Remove the database file from git tracking:**
   ```bash
   git rm --cached instance/shopping_list.db
   git commit -m "Stop tracking database file"
   git pull
   ```

   If you encounter a merge conflict after this step:
   ```bash
   # If you see: CONFLICT (modify/delete): instance/shopping_list.db deleted in HEAD and modified in [commit]...
   git rm instance/shopping_list.db
   git commit -m "Resolve merge conflict by removing database file"
   ```
   
   After removing the database file, you'll need to recreate it:
   ```bash
   # Initialize the database after removing it from git
   cd /var/www/shopping_list_app
   source venv/bin/activate
   
   # Create a script to initialize the database (handles eventlet monkey patching)
   cat > init_db.py << 'EOF'
   import eventlet
   eventlet.monkey_patch()  # This needs to happen first due to eventlet requirements
   
   from shopping_list_app.app import create_app
   from shopping_list_app.models import db
   
   app = create_app()
   with app.app_context():
       db.create_all()
       print("Database tables created successfully!")
   EOF
   
   # Run the script
   python init_db.py
   
   # Then restart the service
   sudo systemctl restart shoppinglist.service
   ```
   
   **Note:** If you're using Flask-Migrate, you should run migrations after creating the initial tables:
   ```bash
   export FLASK_APP=shopping_list_app.app:create_app
   flask db upgrade
   ```

2. **Stash your changes temporarily:**
   ```bash
   git stash
   git pull
   git stash pop  # Optional: only if you need your local DB changes
   ```

3. **For future reference:** Never commit database files to the repository. The application will create a new database file automatically if one doesn't exist.
