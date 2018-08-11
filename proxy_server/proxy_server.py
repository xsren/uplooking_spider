# coding:utf8
from flask import Flask, request, jsonify, Response
from functools import wraps

from config import DB_CONFIG

app = Flask(__name__)


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL, need token.\n', 403,
        {'WWW-Authenticate': 'Basic realm="token Required"'})


def get_db():
    if DB_CONFIG['DB_CONNECT_TYPE'] == 'pymongo':
        from db.MongoHelper import MongoHelper as SqlHelper
    elif DB_CONFIG['DB_CONNECT_TYPE'] == 'redis':
        from db.RedisHelper import RedisHelper as SqlHelper
    else:
        from db.SqlHelper import SqlHelper as SqlHelper
    sqlhelper = SqlHelper()
    sqlhelper.init_db()
    return sqlhelper


db = get_db()


def auth(fun):
    @wraps(fun)
    def wrapper_fun(*args, **kwargs):
        token = request.args.get("token", None)
        if db.find_token(token):
            return fun(*args, **kwargs)
        else:
            return authenticate()

    return wrapper_fun


@app.route('/delete')
@auth
def delete():
    ip = request.args.get('ip', None)
    if ip :
        data = db.delete(ip)
        return jsonify({'status': 0, 'info': 'ok', 'data': data})
    else:
        return jsonify({'status': 1, 'info': 'param not enough'})


@app.route('/select')
@auth
def select():
    count = int(request.args.get('count', 1))
    data = db.select(count)
    return jsonify({'status': 0, 'info': 'ok', 'data': data})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003, debug=False)
