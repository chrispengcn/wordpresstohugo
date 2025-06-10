import os
import shutil
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify

app = Flask(__name__)

def load_config():
    """Load environment configuration"""
    load_dotenv()
    config = {
        'wordpress_content': os.getenv('WORDPRESS_CONTENT_PATH'),
        'hugo_content': os.getenv('HUGO_CONTENT_PATH'),
        'hugo_root': os.getenv('HUGO_ROOT'),
        'nginx_public': os.getenv('NGINX_PUBLIC'),
        'password': os.getenv('PUBLISH_PASSWORD'),
        'flask_port': os.getenv('FLASK_PORT', 5000)
    }
    
    # Validate configuration
    for key, value in config.items():
        if key != 'flask_port' and not value:
            raise ValueError(f"Config item {key.upper()} is not set")
    
    # Validate directories
    if not Path(config['wordpress_content']).exists():
        raise FileNotFoundError(f"WordPress content directory does not exist: {config['wordpress_content']}")
    if not Path(config['hugo_root']).exists():
        raise FileNotFoundError(f"Hugo root directory does not exist: {config['hugo_root']}")
    
    return config

def copy_markdown_files(src, dest):
    """Copy Markdown files from WordPress to Hugo"""
    src_path = Path(src)
    dest_path = Path(dest)
    
    # Ensure destination directory exists
    dest_path.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    for md_file in src_path.glob('**/*.md'):
        relative_path = md_file.relative_to(src_path)
        target_file = dest_path / relative_path
        
        # Ensure directory for target file exists
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(md_file, target_file)
        print(f"Copied: {md_file} -> {target_file}")
        copied += 1
    
    print(f"Copied {copied} Markdown files in total")
    return copied

def build_hugo_site(hugo_root):
    """Build Hugo site"""
    print("Starting Hugo site build...")
    try:
        result = subprocess.run(
            ['hugo', '--minify'],
            cwd=hugo_root,
            capture_output=True,
            text=True,
            check=True
        )
        print("Hugo build successful:")
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Hugo build failed: {e.stderr}")
        return False, e.stderr

def sync_to_nginx(hugo_public, nginx_public):
    """Sync to Nginx directory using rsync"""
    print("Starting sync to Nginx directory...")
    try:
        rsync_cmd = [
            'rsync', '-avz', '--delete',
            f"{hugo_public}/",
            f"root@{nginx_public}:/var/www/html/"
        ]
        
        result = subprocess.run(
            rsync_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print("Sync completed:")
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Sync failed: {e.stderr}")
        return False, e.stderr

def deploy_site():
    """Execute the full deployment process"""
    try:
        config = load_config()
        
        # Copy Markdown files
        copied_count = copy_markdown_files(
            config['wordpress_content'],
            config['hugo_content']
        )
        if copied_count == 0:
            return False, "No Markdown files found to copy"
        
        # Build Hugo site
        build_success, build_output = build_hugo_site(config['hugo_root'])
        if not build_success:
            return False, f"Hugo build failed: {build_output}"
        
        # Sync to Nginx
        sync_success, sync_output = sync_to_nginx(
            os.path.join(config['hugo_root'], 'public'),
            config['nginx_public']
        )
        if not sync_success:
            return False, f"Sync to Nginx failed: {sync_output}"
        
        return True, "Deployment completed successfully"
            
    except Exception as e:
        return False, f"Error during deployment: {str(e)}"

@app.route('/publish', methods=['POST'])
def publish():
    """API endpoint to trigger deployment"""
    password = request.args.get('password')
    
    config = load_config()
    if password != config['password']:
        return jsonify({
            'status': 'error',
            'message': 'Invalid password'
        }), 401
    
    success, message = deploy_site()
    if success:
        return jsonify({
            'status': 'success',
            'message': message
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': message
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """API endpoint to check service status"""
    return jsonify({
        'status': 'online',
        'message': 'Deployment service is running'
    }), 200

if __name__ == "__main__":
    config = load_config()
    app.run(host='0.0.0.0', port=config['flask_port'])    
