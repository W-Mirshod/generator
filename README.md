Django Project Deployment

This repository contains a Django project deployed using Nginx and uWSGI. It serves as a web application configured for production-grade performance.
Project Structure


**Setup and Installation:**
Ensure you have nginx, pip, git, virtualenv installed:
```
sudo apt install nginx python3 python3-venv python3-pip git build-essential python3-dev -y
```

Step 1: Clone the Repository
```
cd /var/www
git clone https://github.com/mega-devs/generator.git
cd generator
```

Step 2: Create and Activate a Virtual Environment
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Step 3: Install Dependencies & uswgi dependencies 
```
pip install -r requirements.txt
sudo apt update
sudo apt install build-essential python3-dev
```

Step 4: Configure Django
```
python manage.py migrate
python manage.py collectstatic
```

Step 5: Configure uWSGI
The uwsgi.ini file is already configured. Just verify its content:
```
[uwsgi]
chdir = /var/www/generator
module = myproject.wsgi:application
master = true
processes = 4

socket = /tmp/uwsgi.sock
chmod-socket = 666
vacuum = true
die-on-term = true

logto = /var/log/uwsgi/uwsgi.log
```

Give permissions:
```
sudo chmod 755 /var/www/generator
sudo mkdir -p /run/uwsgi
sudo chown www-data:www-data /run/uwsgi
sudo chmod 775 /run/uwsgi
```

Step 6: Configure Nginx

Use the following configuration (or refer to nginx_configuration.txt):

```
server {
    listen 80;
    server_name 91.240.118.210;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:///tmp/uwsgi.sock;
    }

    location /static/ {
        alias /var/www/generator/staticfiles/;
    }

    error_log /var/www/generator/logs/nginx-error.log;
    access_log /var/www/generator/logs/nginx-access.log;
}
```

Enable & Reload:
```
sudo ln -s /etc/nginx/sites-available/generator /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

sudo systemctl reload nginx
sudo systemctl daemon-reload
```

Step 7: Start Services
```
sudo systemctl start uwsgi
sudo systemctl enable uwsgi

sudo systemctl start nginx
sudo systemctl enable nginx
```

Check uWSGI status:
```
sudo systemctl status uwsgi
```
Check Nginx status:
```
sudo systemctl status nginx
```
