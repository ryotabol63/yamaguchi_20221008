#!/usr/bin/env python
# coding: UTF-8

#################################################################
# Copyright (C) 2017 Mono Wireless Inc. All Rights Reserved.    #
# Released under MW-SLA-*J,*E (MONO WIRELESS SOFTWARE LICENSE   #
# AGREEMENT).                                                   #
#################################################################

# ライブラリのインポート
import sys
import csv
import os
import random
#import copy
#import threading
import serial
import paramiko
import time
import datetime
from optparse import *
#from queue import Queue

from time import sleep
import paho.mqtt.client as mqtt

# WONO WIRELESSのシリアル電文パーサなどのAPIのインポート
sys.path.append('./MNLib/')
from apppal import AppPAL

# ここより下はグローバル変数の宣言
# コマンドラインオプションで使用する変数
options = None
args = None

# 各種フラグ
bEnableLog = False
bEnableErrMsg = False

# プログラムバージョン
Ver = "1.1.0"

# mqtt 接続----------------------------------------------------------
sys.stderr.write("*** 開始 ***\n")
host = '192.168.11.4'
port = 1883
pino = 6
topic = 'TWELITE/' + str(pino)

client = mqtt.Client(protocol=mqtt.MQTTv311)

client.connect(host, port=port, keepalive=60)
client.loop_start()  #別スレッドでループ（keepalive）の実装

header =['時間', '論理ID', 'タグID', '中継器ID', '送信番号', '電波強度', '電源電圧','piNo']

sheader = ",".join(header)
#client.publish(topic, sheader.encode('utf-8'))
# 今回は受信側でヘッダをつけます
# 日本語を送れるようにバイト列に変換（英数字の文字列のみならそのままstrで送れる）
#client.publish(topic, 'テスト'.encode('utf-8'))
#sleep(0.5)
#client.publish(topic, 'こんにちは')
#client.disconnect()
#sys.stderr.write("*** 終了 ***\n")
# ------------------------------------------------------------------


#CSVを開く

shortlog_name = str(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')) + '(' + str(random.randint(100,999)) + ').csv'

print(shortlog_name)

#終了時間

#end_time=60

#時間計測の始まり

#start=time.time()

#ヘッダは最初に移動

#データを取得するメイン部分。newline=''は改行をなくすためのオプション

def writeX(note):
    with open(shortlog_name,'a',encoding='shift_jis',newline='') as f:
        csvout = csv.writer(f)
        csvout.writerow(note)

#csvout.writerow(header)

def ParseArgs():
    global options, args

    parser = OptionParser()
    parser.add_option('-t', '--target', type='string', help='target for connection', dest='target', default=None)
    parser.add_option('-b', '--baud', dest='baud', type='int', help='baud rate for serial connection.', metavar='BAUD', default=19500)
    parser.add_option('-s', '--serialmode', dest='format', type='string', help='serial data format type. (Ascii or Binary)',  default='Ascii')
    parser.add_option('-l', '--log', dest='log', action='store_true', help='output log.', default=False)
    parser.add_option('-e', '--errormessage', dest='err', action='store_true', help='output error message.', default=False)
    (options, args) = parser.parse_args()

if __name__ == '__main__':
    print("*** MONOWIRELESS App_PAL_Viewer " + Ver + " ***")

    writeX(header)

    ParseArgs()

    bEnableLog = options.log
    bEnableErrMsg = options.err
    try:
        PAL = AppPAL(port=options.target, baud=options.baud, tout=0.05, sformat=options.format, err=bEnableErrMsg)
    except:
        print("Cannot open \"AppPAL\" class...")
        exit(1)

    while True:
        try:
            # データがあるかどうかの確認
            if PAL.ReadSensorData():
                # あったら辞書を取得する
                Data = PAL.GetDataDict()
                if Data['RouterSID'] == '80000000':
                    RSID = 'No Relay'
                else:
                    RSID = Data['RouterSID']
                print(Data)
                print(Data['ArriveTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], end = ",")
                print(Data['LogicalID'], end = ",")
                print(Data['EndDeviceSID'], end = ",")
                print(RSID, end = ",")
                print(Data['SequenceNumber'], end = ",")
                print(Data['LQI'], end = ",")
                print(Data['Power'], end = "\n")

                datas_TAG = [str(Data['ArriveTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]),\
                Data['LogicalID'],Data['EndDeviceSID'],RSID,Data['SequenceNumber'],Data['LQI'],Data['Power'], str(pino)]
                #最後はPIidなのでファイルによって異なる
                send_datas_TAG = [\
                        #str(Data['ArriveTime'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]),\
                Data['LogicalID'],Data['EndDeviceSID'],RSID,Data['SequenceNumber'],Data['LQI'],Data['Power'], str(pino)]

                writeX(datas_TAG)

                client.publish(topic + '/' + Data['EndDeviceSID'], ",".join(map(str, send_datas_TAG)))

                # なにか処理を記述する場合はこの下に書く
                #PAL.ShowSensorData()	# データを出力する
                # ここまでに処理を書く

                # ログを出力するオプションが有効だったらログを出力する。
                if bEnableLog == True:
                    PAL.OutputCSV()	# CSVでログをとる
            # Ctrl+C でこのスクリプトを抜ける
        except KeyboardInterrupt:
            break
    
    client.loop_stop(force= False)
    client.disconnect()
    del PAL


    print("*** Exit App_PAL Viewer ***")