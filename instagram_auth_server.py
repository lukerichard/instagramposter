from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import urllib.parse

app = Flask(__name__)

INSTAGRAM_CLIENT_ID = os.environ.get('INSTAGRAM_CLIENT_ID', '703358962095350')
INSTAGRAM_CLIENT_SECRET = os.environ.get('INSTAGRAM_CLIENT_SECRET', 'def5602ef37d452d2626a2cebdf2105f')
INSTAGRAM_REDIRECT_URI = os.environ.get('INSTAGRAM_REDIRECT_URI', 'https://minuet.ca/instagram-callback')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://minuet.app.n8n.cloud/webhook-test/aa2e73fc-8ed5-46eb-9e8b-8c06e71f71b0')

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Welcome to Instagram Poster</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f9f9f9; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
            .container { text-align: center; }
            .btn { padding: 1em 2em; font-size: 1.2em; background: #007bff; color: #fff; border: none; border-radius: 5px; cursor: pointer; margin-top: 2em; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to Instagram Poster</h1>
            <p>Click below to login with Instagram and start posting!</p>
            <form action="/start-instagram-login" method="get">
                <button class="btn" type="submit">Login with Instagram</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/start-instagram-login')
def start_instagram_login():
    client_id = os.environ.get('INSTAGRAM_CLIENT_ID', '703358962095350')
    redirect_uri = os.environ.get('INSTAGRAM_REDIRECT_URI', 'http://localhost:5000/instagram-callback')
    auth_url = (
        'https://api.instagram.com/oauth/authorize'
        f'?client_id={client_id}'
        f'&redirect_uri={urllib.parse.quote(redirect_uri)}'
        '&scope=user_profile,user_media'
        '&response_type=code'
    )
    return '', 302, {'Location': auth_url}

@app.route('/exchange_token', methods=['POST'])
def exchange_token():
    code = request.json.get('code')
    if not code:
        return jsonify({'error': 'Missing code'}), 400

    # Exchange code for access token
    token_url = 'https://api.instagram.com/oauth/access_token'
    data = {
        'client_id': INSTAGRAM_CLIENT_ID,
        'client_secret': INSTAGRAM_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': INSTAGRAM_REDIRECT_URI,
        'code': code
    }
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        return jsonify({'error': 'Failed to get access token', 'details': resp.text}), 400

    access_token = resp.json().get('access_token')
    user_id = resp.json().get('user_id')

    # Send access token to webhook
    webhook_resp = requests.post(WEBHOOK_URL, json={'access_token': access_token, 'user_id': user_id})
    if webhook_resp.status_code != 200:
        return jsonify({'error': 'Failed to send to webhook', 'details': webhook_resp.text}), 400

    return jsonify({'success': True, 'access_token': access_token, 'user_id': user_id})

@app.route('/instagram-callback')
def instagram_callback():
    return send_from_directory('.', 'webhook.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 