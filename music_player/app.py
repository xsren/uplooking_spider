import logging

from flask import Flask
from flask import render_template, jsonify
from mongo_handler import get_db
from run_parse_url_server import get_real_path

db = get_db()
app = Flask(__name__)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/')
def index_page():
    total = db['song_info'].count()
    song_cur = db['song_info'].find({}, {'mus_Name': 1, 'mus_Singer': 1, 'url': 1}).limit(10)
    songs = []
    for song in song_cur:
        new_song = {
            'singer': song['mus_Singer'][0]['name'],
            'mus_name': song['mus_Name'],
            'url': song['url'],
            'song_id': song['url'].split('/')[-1].split('.')[0],
        }
        songs.append(new_song)
    data = {
        'total': total,
        'songs': songs,
    }
    return render_template('index.html', data=data)


@app.route('/real_url/<song_id>')
def real_url(song_id):
    url = 'https://y.qq.com/n/yqq/song/{}.html'.format(song_id)

    logger.debug("begin to parse url:{}".format(url))
    status, data = get_real_path(url)
    if status == 0:
        logger.debug("finish to parse url:{},status:{}".format(url, status))
        return jsonify({'status': status, 'info': 'ok', 'data': data})
    else:
        logger.debug("finish to parse url:{},status:{},data:{}".format(url, status, data))
        return jsonify({'status': status, 'info': data})


@app.route('/admin')
def admin_page():
    album_task_count = db['album_task'].count()
    song_task_count = db['song_task'].count()
    song_count = db['song_info'].count()
    stats = {
        'album_task_count': album_task_count,
        'song_task_count': song_task_count,
        'song_count': song_count,
    }
    return render_template('admin.html', stats=stats)


if __name__ == '__main__':
    app.run()
