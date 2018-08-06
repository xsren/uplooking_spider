from flask import Flask, request, jsonify
from mongo_handler import get_db

db = get_db()

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/insert_data', methods=['POST'])
def insert_data():
    rj = request.get_json()
    print(rj)
    coll_name = rj['coll_name']
    data = rj['data']
    if not db[coll_name].find_one({'url': data['url']}):
        db[coll_name].insert_one(data)

    return 'OK'


@app.route('/insert_task', methods=['POST'])
def insert_task():
    rj = request.get_json()
    print(rj)
    coll_name = rj['coll_name']
    task = rj['data']
    if not db[coll_name].find_one({'url': task['url']}):
        db[coll_name].insert_one(task)

    return 'OK'


@app.route('/get_task')
def get_task():
    coll_name = request.args.get('coll_name', None)
    task = db[coll_name].find_and_modify({'status': 0}, {'$set': {'status': 1}})

    if not task:
        task = {}
    task.pop('_id', None)
    return jsonify(task)


@app.route('/update_task', methods=['POST'])
def update_task():
    rj = request.get_json()
    coll_name = rj['coll_name']
    task = rj['data']
    status = rj['status']
    db[coll_name].update_one({'url': task['url']}, {'$set': {'status': status}})
    return 'OK'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
