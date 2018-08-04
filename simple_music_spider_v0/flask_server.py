from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/insert_data')
def insert_data():
    data = request.args.get('data', None)
    print(data)
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