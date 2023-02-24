# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
#import influxdb
import datetime
import random
import json
import csv

#import partcsv

#for MQTT broker
MQTT_HOST = '127.0.0.1'    #local
MQTT_PORT = 1883
KEEP_ALIVE = 60
TOPIC = 'TWELITE/5/#'

#for InfluxDB
#DB_HOST = '127.0.0.1'
#DB_PORT = 8086
#DB_NAME = 'influx_iot01'
#DB_MEASUREMENT = 'table1'

#db = influxdb.InfluxDBClient(
    #host='localhost',
    #port=8086,
    #database='influx_iot01'
#)

"""
接続を試みたときに実行
def on_connect(client, userdata, flags, respons_code):

* client
Clientクラスのインスタンス

* userdata
任意のタイプのデータで新たなClientクラスののインスタンスを作成するときに>設定することができる

* flags
応答フラグが含まれる辞書
クリーンセッションを0に設定しているユーザに有効。
セッションがまだ存在しているかどうかを判定する。
クリーンセッションが0のときは以前に接続したユーザに再接続する。

0 : セッションが存在していない
1 : セッションが存在している

* respons_code
レスポンスコードは接続が成功しているかどうかを示す。
0: 接続成功
1: 接続失敗 - incorrect protocol version
2: 接続失敗 - invalid client identifier
3: 接続失敗 - server unavailable
4: 接続失敗 - bad username or password
5: 接続失敗 - not authorised
"""

def on_connect(client, userdata, flags, respons_code):
    print('status {0}'.format(respons_code))
    client.subscribe(client.topic)

"""
def on_message(client, userdata, message):
topicを受信したときに実行する
"""
def on_message(client, userdata, message):
    nakami = message.payload
    message_json = nakami.decode('utf-8')                #受信データはバイト列なのでそれを文字列に変換する
    print (message_json)
    print (type(message_json))
    #print(message.topic + ' ' + str(message.payload))
    #message_json=str(message.payload)
    #message_json=my_removeprefix(message_json, "b'")
    #message_json=my_removesuffix(message_json, "'")
    #print(message_json.decode('utf-8'))


    with open(mqttlog_name, 'a', encoding='shift-jis',newline='') as f:
        if message_json.startswith('時間'):
            wdata = message_json
        else:
            wdata = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]) + ',' + message_json
            f.write(wdata + '\n')                        #すでにコンマ区切りされたデータなので単にwriteするだけ+改行
    #message_dict=json.loads(message_json)
    #print(message_dict)
    #write_to_influxdb(message_dict)

def my_removeprefix(s, prefix):
    if s.startswith(prefix):
        return s[len(prefix):]
    else:
        return s

def my_removesuffix(s, suffix):
    return s[:-len(suffix)] if s.endswith(suffix) else s


if __name__ == '__main__':
    #tagname = input('tagIDを入力:')
    random_int =  '(' + str(random.randint(100, 999)) + ')'
    #mqttlog_name = 'mqtt' + str(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')) + tagname + random_int  + '.csv'
    mqttlog_name = 'data_' + str(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')) + '_pi5'+  '.csv'

    with open(mqttlog_name, 'a', encoding='shift-jis',newline='') as f:
        header =','.join(['時間', '論理ID', 'タグID', '中継器ID', '送信番号', '電波強度', '電源電圧','piNo'])
        f.write(header + '\n')                        #すでにコンマ区切りされたデータなので単にwriteするだけ+改行

    while 1:
        try:

            client = mqtt.Client(protocol=mqtt.MQTTv311)
            client.topic = TOPIC# + '/' + tagname

            client.on_connect = on_connect
            client.on_message = on_message

            client.connect(MQTT_HOST, port=MQTT_PORT, keepalive=KEEP_ALIVE)

            # ループ
            client.loop_forever()       
        except KeyboardInterrupt:
            print('end')
            break           

print("終了処理中です。")

#partcsv.partcsv(mqttlog_name, 2, 1)             