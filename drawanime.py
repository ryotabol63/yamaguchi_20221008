#山口ようにいじってるので元のを上書きしないように
import matplotlib.pyplot as plt
#import pandas
import numpy as np
from matplotlib.animation import ArtistAnimation
import os
import random
import math
import datetime
import matplotlib.patches as patches

def determine_coordinate():
    coordinate = []   #座標
    pi1 = (2,2)         #pi1(x,y)
    pi2 = (6,2)         #pi2(x,y)
    pi3 = (9,1)         #pi3(x,y)
    pi4 = (12,8)         #pi4(x,y)    
    pi5 = (15,6)         #pi5(x,y)
    pi6 = (6,9)         #pi6(x,y)
    coordinate.extend([pi1,pi2,pi3,pi4,pi5,pi6])
    #print(coordinate)
    return(coordinate)





def coordinate(pn,coordinatexy):     #ここで座標を入力
    if pn >= 1 and pn <= 6:
        x = coordinatexy[(int(pn)-1)][0]
        y = coordinatexy[(int(pn)-1)][1]
    else:
        x = 0
        y = 0
    return (x,y)



def animetest(targetfile,basedatetime):

    fig = plt.figure()
    #print(type(targetfile))
    
    anim = [] #アニメーション用に描くパラパラ図のデータを格納するためのリスト
    data = []
    for target in targetfile: #データ取り込み部
        data.append(np.genfromtxt(target, skip_header = 1, delimiter = ',', encoding = 'utf-8'))#ヘッダ一行
    t = data[0][:,0].tolist()
    tt = [int(k) for k in t]
    
    ylist = []
    xrand = []
    yrand = []
    #print(data)
    count = 0
    for list in data:
        count += 1
        #print(data[:,0])
        #print(tt)
        theta = 2.0 * math.pi * random.random()
        radius = math.sqrt(random.random())
        xrand.append(0.2 * radius * math.cos(theta))
        yrand.append(0.2 * radius * math.sin(theta))
        ylist.append(list[:,1].tolist())
    #print(xrand)
    #print(yrand)
    #print(count)

    #print (type(y))
    phistory = [0, 0, 0, 0, 0, 0]     #各pi を踏んだ回数
    coordinatexy = determine_coordinate()   #xy座標の定義

    tryno = 0
    for j in tt:
        curdatetime = basedatetime + datetime.timedelta(seconds= j)
        curtime = curdatetime.strftime('%H:%M:%S')
        im = plt.plot()
        #print(type(im))
        counter = 0
        #print(ylist)
        jind = tt.index(j)
        for pllist in ylist:
            #print(pllist)
            try:
                cpl = pllist[jind]
                phistory[(int(cpl)- 1)] += 1 
                co = coordinate(cpl,coordinatexy)
                x = co[0] + xrand[counter]
                #print(x)
                y = co[1] + yrand[counter]
                im = im + plt.plot(x,y,'s', color='red',markersize=5, aa=True)
            except IndexError:
                pass
            counter += 1
        tryno += 1
        #sum_phis = sum(phistory)
        p_rate = [0,0,0,0,0,0]
        if tryno != 0:
            for i in range(6):
                p_rate[i] = phistory[i] / tryno
        #print(p_rate)
        his_text = 'P1:' + str(phistory[0]) + 'times, ' + str(round(p_rate[0] * 100)) + '%\n' + \
                   'P2:' + str(phistory[1]) + 'times, ' + str(round(p_rate[1] * 100)) + '%\n' + \
                   'P3:' + str(phistory[2]) + 'times, ' + str(round(p_rate[2] * 100)) + '%\n' + \
                   'P4:' + str(phistory[3]) + 'times, ' + str(round(p_rate[3] * 100)) + '%\n' + \
                   'P5:' + str(phistory[4]) + 'times, ' + str(round(p_rate[4] * 100)) + '%\n' + \
                   'P6:' + str(phistory[5]) + 'times, ' + str(round(p_rate[5] * 100)) + '%\n'
        #print(his_text)
        tx = plt.text(12,10,curtime + '\n' + his_text)       #時間のprintはここ
        anim.append(im + [tx])
    
    anim = ArtistAnimation(fig, anim) # アニメーション作成
    
    #円とラベルの描画
    N = 200 #曲線のなめらかさ
    pi_2 = 2.0 * math.pi
    t = np.linspace(0,pi_2,N)#媒介変数
    #centerlistx = (13,1,5,3,8)#円の中心リスト（各Piの位置に相当）
    #centerlisty = (5,8,8,2,1)
    for num in range(0,6):
        cirx = coordinatexy[num][0] + 0.5 * np.cos(t)
        ciry = coordinatexy[num][1] + 0.5 * np.sin(t)
        plt.plot(cirx,ciry,'-', color='blue')
        piname = 'P' + str(num + 1)
        plt.text(coordinatexy[num][0]-1.2, coordinatexy[num][1]+0.4, piname)
    r1x = np.linspace(0,10,N)
    #r2x = np.linspace(10,16,N)
    ry = np.linspace(1,9,100)
    for xn in (12,15):
        rrx = np.linspace(xn,xn,100)
        plt.plot(rrx,ry,color= 'black')
    for yn in (2,-100):
        rry = np.linspace(yn,yn,N)
        plt.plot(r1x,rry,color= 'black')
        #plt.plot(r2x,rry,color = 'black')
    plt.text(3,3,'Zipline')
    plt.text(12,5,'Slacklines')
    plt.text(4,6,'Athletics')
    #plt.xlabel('X',fontsize=18)
    #plt.ylabel('Y',fontsize=18)
    plt.xlim(0,18)              #描画領域(x)
    plt.ylim(0,16)              #描画領域(y)

    fig.show() 
    savename = 'animetest.gif'
    anim.save(savename, writer='pillow')   #アニメーションをt.gifという名前で保存し，gifアニメーションファイルを作成する。
    return(savename)

if __name__ == "__main__":

    tgtfiles = []    
    print("csvファイル名を入力(終了:0):")
    while True:
        tgtfile = input()
        if tgtfile == '0':
            break
        else:
            tgtfiles.append(tgtfile)#ファイル名を入力
    #print(tgtfiles)
    while True:
        print('開始時間を入力(%Y-%m-%d %H:%M:%S)')
        basetime = input()
        try:
            basedatetime = datetime.datetime.strptime(basetime,'%Y-%m-%d %H:%M:%S')
            break
        except:
            print('formaterror')
            continue
    animetest(tgtfiles,basedatetime)
