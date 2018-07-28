# music_spider
kk点歌——音乐爬虫



# 创建环境

```
virtualenv -p /usr/local/bin/python3 env
source env/bin/activate
```

# 安装依赖

```
pip install -r requirements.txt
```

# run server

```
cd main
python run_server.py
```

# run spider

```
cd main
python run_crawler.py -s qq -t crawl_hot_songs --log-level debug
```