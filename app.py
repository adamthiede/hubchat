from flask import Flask, redirect, url_for, session, request, render_template
from flask_oauthlib.client import OAuth
import sqlite3, os, time

secret_key=os.environ.get('SECRET_KEY')
client_id=os.environ.get('GITHUB_CLIENT_ID')
client_secret=os.environ.get('GITHUB_CLIENT_SECRET')
MESSAGE_LIMIT=int(os.environ.get('MESSAGE_LIMIT', 100))

app = Flask(__name__)
app.secret_key = secret_key
app.config['GITHUB_CLIENT_ID'] = client_id
app.config['GITHUB_CLIENT_SECRET'] = client_secret
oauth = OAuth(app)
github = oauth.remote_app(
    'github',
    consumer_key=app.config['GITHUB_CLIENT_ID'],
    consumer_secret=app.config['GITHUB_CLIENT_SECRET'],
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
)

conn = sqlite3.connect('messages.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS messages
             (id INTEGER PRIMARY KEY, sender TEXT, receiver TEXT, message TEXT, timestamp INTEGER)''')
conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    if request.headers.get('X-Forwarded-Proto', None)=='https':
        return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))
    return github.authorize(callback=url_for('authorized', _external=True))


@app.route('/logout')
def logout():
    session.pop('github_token')
    return redirect(url_for('index'))

@app.route('/login/authorized')
def authorized():
    response = github.authorized_response()
    if response is None or response.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error'], request.args['error_description']
        )
    session['github_token'] = (response['access_token'], '')
    user = github.get('user')
    return redirect(url_for('messages'))

@app.route('/messages')
def messages():
    if 'github_token' not in session:
        return redirect(url_for('index'))
    user = github.get('user')
    c.execute('SELECT * FROM messages WHERE receiver=? OR sender=?', (user.data['login'], user.data['login']))
    messages = c.fetchall()
    return render_template('messages.html', user=user.data, messages=messages)

def prune_messages(sender, receiver):
    c.execute('SELECT id FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp DESC', (sender, receiver, receiver, sender))
    messages = c.fetchall()
    if len(messages) > MESSAGE_LIMIT:
        for message_id in messages[MESSAGE_LIMIT:]:
            c.execute('DELETE FROM messages WHERE id=?', (message_id[0],))
        conn.commit()

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'github_token' not in session:
        return redirect(url_for('index'))
    user = github.get('user')
    receiver = request.form['receiver']
    message = request.form['message']
    timestamp = int(time.time())
    c.execute('INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)', (user.data['login'], receiver, message, timestamp))
    conn.commit()
    prune_messages(user.data['login'], receiver)
    return redirect(url_for('messages'))

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run(debug=True)
