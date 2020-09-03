# coding=utf-8

import datetime
import json
import logging
import logging.handlers
import pathlib
import requests
import time
import sqlite3

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json; charset=UTF-8',
    'User-Agent': 'nrjscrape.py'
}

api_url_base = 'https://api.p4.no/10/musikk/sok/'

logs_dir = 'logs/'
logs_file = 'nrjscrape.log'

# create logs directory
base_dir = pathlib.Path(__file__).resolve().parent
logs_dir = base_dir.joinpath(logs_dir)
logs_file = logs_dir.joinpath(logs_file)
pathlib.Path(logs_dir).mkdir(parents=True, exist_ok=True)

# create logger
logger = logging.getLogger('NRJSCRAPE')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)10s[%(process)d] %(levelname)7s: %(message)s')

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)

# file logger
fh = logging.handlers.TimedRotatingFileHandler(logs_file, when="d", interval=1, backupCount=60)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# start app
logger.info(f'==> LOGS DIR: {logs_dir}')
logger.info(f'==> LOGS FILE: {logs_file}')
logger.info(f'==> API BASE: {api_url_base}')


# database stuff
db = 'nrjscrape.sqlite3'
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cursor = con.cursor()

# Generate timestamps
logger.info('Generating timestamps...')
dt = datetime.datetime(2020, 7, 1)
end = datetime.datetime(2020, 8, 10, 23, 59, 59)
step = datetime.timedelta(minutes=15)

result = []
while dt < end:
    # edit in some static data to get correct format. bruh1..
    cr = dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    # save if day is friday, saturday or sunday
    weekenddays = [5, 6, 7]
    if dt.isoweekday() in weekenddays:
        result.append(cr)
    dt += step

logger.info(f'timestamps to scrape: {len(result)}')
for r in result:
    api_url_endpoint = f'{api_url_base}{r}'
    logger.info(f'requesting {api_url_endpoint}')

    try:
        a = requests.get(api_url_endpoint, headers=headers,  timeout=10)
        
        if a.status_code == 200:
            data = a.json()
            
            for entry in data:    
                musicId = entry['musicId']
                artist = entry['artist']
                title = entry['title']
                startTime = entry['startTime']

                sql_query = 'INSERT INTO songs (musicId, artist, title, startTime) VALUES (?, ?, ?, ?)'

                # MusicId will be identical for same artist and titles and can be used as unique key to avoid dupli
                # using quick and dirty try except here instead of querying the database for each entry.. bruh2..
                try:
                    cursor.execute(sql_query, (musicId, artist, title, startTime))
                    con.commit()
                    logger.info(f"[{startTime}] [{musicId}] {artist} - {title}")

                except:
                    logger.warning(f"Already in DB - SKIP! [{musicId}] {artist} - {title}")
        else:
            logger.warning(a.status_code)
            logger.debug(a.content)
    # bruh3..
    except Exception as e:
        logger.critical(f'something went wrong while requesting {api_url_endpoint} :: {repr(e)} - {str(e)}')
    
    time.sleep(10) # rate limiter.. bruh4..
