import json

from flask import Flask, request

from mongo_handler import get_db

db = get_db()


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/insert_data')
def insert_data():
    data = request.args.get('data', None)
    print(data)
    return 'OK'


@app.route('/insert_task')
def insert_task():
    album_task = request.args.get('data', None)
    album_task_dict = json.loads(album_task)
    print(album_task_dict)
    if not db['album_task'].find_one({'url': album_task_dict['url']}):
        db['album_task'].insert_one(album_task_dict)

    return 'OK'


@app.route('/get_task')
def get_task():
    data = request.args.get('data', None)
    print(data)
    return 'OK'


@app.route('/update_task')
def update_task():
    data = request.args.get('data', None)
    print(data)
    return 'OK'


if __name__ == '__main__':
    app.run()
