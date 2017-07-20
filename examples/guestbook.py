"""Remote profiling example with Flask.

First of all launch vprof in remote mode:

    vprof -r

and launch this script:

    python guestbook.py

Then you can profile '/' and '/add' handlers:

    curl http://127.0.0.1:5000/profile/main

and

    curl --data "name=foo&message=bar" http://127.0.0.1:5000/profile/add

Check profiler_handler source code below for details.
"""

import contextlib
import jinja2
import flask
import sqlite3

from vprof import runner

DB = '/tmp/guestbook.db'
DB_SCHEMA = """
DROP TABLE IF EXISTS entry;
CREATE TABLE entry (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	message TEXT NOT NULL
);
"""
LAYOUT = """
<html>
  <title>Guestbook</title>
  <body>
    <form method=post action=/add>
      Name: <input type=text name=name><br>
      Message: <textarea name=message></textarea><br>
      <input type=submit value=Post><br>
    </form>
    <ul>
    {% for entry in entries %}
      <li><h2>{{ entry.name }}</h2>
        {{ entry.message | safe }}
      </li>
    {% endfor %}
    </ul>
  </body>
</html>
"""


def connect_to_db():
    """Establishes connection to SQLite."""
    return sqlite3.connect(DB)


def init_db():
    """Initializes DB."""
    with contextlib.closing(connect_to_db()) as db:
        db.cursor().executescript(DB_SCHEMA)
        db.commit()


app = flask.Flask('guestbook')


@app.before_request
def before_request():
    """Establishes SQLite connection before request."""
    flask.g.db = connect_to_db()


@app.teardown_request
def teardown_request(exception):
    """Closes SQLite connection after request is processed."""
    db = getattr(flask.g, 'db', None)
    if db is not None:
        db.close()


@app.route('/')
def show_guestbook():
    """Returns all existing guestbook records."""
    cursor = flask.g.db.execute(
        'SELECT name, message FROM entry ORDER BY id DESC;')
    entries = [{'name': row[0], 'message': row[1]} for row in cursor.fetchall()]
    return jinja2.Template(LAYOUT).render(entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    """Adds single guestbook record."""
    name, msg = flask.request.form['name'], flask.request.form['message']
    flask.g.db.execute(
        'INSERT INTO entry (name, message) VALUES (?, ?)', (name, msg))
    flask.g.db.commit()
    return flask.redirect('/')


@app.route('/profile/<uri>', methods=['GET', 'POST'])
def profiler_handler(uri):
    """Profiler handler."""
    # HTTP method should be GET.
    if uri == 'main':
        runner.run(show_guestbook, 'cmhp')
    # In this case HTTP method should be POST singe add_entry uses POST
    elif uri == 'add':
        runner.run(add_entry, 'cmhp')
    return flask.redirect('/')


if __name__ == '__main__':
    init_db()
    app.run()
