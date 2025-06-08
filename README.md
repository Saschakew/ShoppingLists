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
    sudo systemctl restart shoppinglist.service
    ```

## 7. Troubleshooting

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
- **Common issues:**
    - Internal Server Error after login: Ensure `login_user` uses `duration=timedelta(...)`, not an integer.
    - Nginx shows default page: Confirm `shoppinglist.conf` uses `listen 80 default_server;` and `server_name _;`.
    - Environment variables in systemd file must be on a single line.

## 8. Security Notes
- Do not expose your `SECRET_KEY` or database credentials publicly.
- For production, consider setting up HTTPS (Let's Encrypt) and a domain name.

---

**For more details, see the comments in the code and configuration files.**
