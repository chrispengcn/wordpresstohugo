# WordPress to Hugo Deployment Script

This script automates the process of transferring Markdown content from WordPress to Hugo, building the Hugo site, and syncing it to an Nginx server. It includes a Flask API for triggering deployments via HTTP requests.

## Features

- Copies Markdown files from WordPress content directory to Hugo
- Builds Hugo site with minification
- Syncs generated site to Nginx server using rsync
- Secure password protection for deployment
- REST API endpoint for triggering deployments
- Status check endpoint

## Prerequisites

1. Python 3.7+
2. Hugo installed and available in PATH
3. rsync installed
4. SSH key configured for passwordless access to Nginx server
5. Required Python packages:
   - flask
   - python-dotenv

## Configuration

Create a `.env` file in the project root with the following variables:
# WordPress content directory (containing Markdown files)
WORDPRESS_CONTENT_PATH=/path/to/wordpress-content

# Hugo content directory
HUGO_CONTENT_PATH=/path/to/hugo/content

# Hugo root directory
HUGO_ROOT=/path/to/hugo

# Nginx server address
NGINX_PUBLIC=your-server-ip-or-domain

# Deployment password
PUBLISH_PASSWORD=your-secure-password

# Flask server port (optional, default: 5000)
FLASK_PORT=5000
## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/wordpress-to-hugo-deploy.git
   cd wordpress-to-hugo-deploy
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install flask python-dotenv
   ```

## Usage

### Running the Flask Server
python deploy.py
The server will start on the port specified in `.env` (default: 5000).

### Triggering a Deployment

Send a POST request to the `/publish` endpoint with the correct password:
curl -X POST "http://localhost:5000/publish?password=your_password_here"
### Checking Server Status
curl "http://localhost:5000/status"
## Deployment in Production

For production environments, it is recommended to use a proper WSGI server like Gunicorn:

1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Run the application:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 deploy:app
   ```

3. Consider using a process manager like systemd to ensure the application starts on boot and restarts automatically.

## Security Considerations

1. Always use HTTPS in production to protect the password during transmission
2. Store passwords and sensitive information in environment variables
3. Restrict access to the API endpoint using firewall rules
4. Regularly update dependencies and the operating system
5. Use strong, unique passwords    
