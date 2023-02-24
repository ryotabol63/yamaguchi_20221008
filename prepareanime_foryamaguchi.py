#CSVの分配
import csv
import os
import sys
import numpy as np
from scipy import interpolate
import datetime
import drawanime


import kalman_for_tagdata

def before_linear_withtagID (csvname, columnno, tagid):

    with open (csvname, encoding = 'shift_jis')as ocsv:
        of = csv.reader(ocsv)
        header = next(of)  #ヘッダスキップ
        lognames = []   #拡張用（lognameを残しておく）
        for row in of:
            columnx = row[columnno]
            piid = row[7]
            if columnx != tagid:
                continue
            logname = 'preparefor_' + columnx + '_pi' + piid + '_From' + csvname
            if not(logname in lognames):
                lognames.append(logname)
                with open(logname,'w',encoding='shift_jis',newline='') as wf:      #前のデータが残っているといやなので上書き
                    csvout = csv.writer(wf)
                    header_for_write = [header[0], header[4], header[5], header[7], 'tagID:' + columnx]
                    csvout.writerow(header_for_write)
            with open(logname, 'a', encoding = 'shift-jis', newline = '')as wf:
                csvout = csv.writer(wf)
                write_row = [row[0], row[4], row[5], row[7]]
                csvout.writerow(write_row)
    return lognames


def dmcsv_new(targetfile):

    savename = (os.path.splitext(targetfile)[0]) + '_linear.csv'


    #とりあえず間に合わせ（csvreadとwrite）でヘッダの処理はします（今後更新したい）
    with open (targetfile, encoding = 'shift_jis')as ocsv:
        of = csv.reader(ocsv)
        header = next(of)  #ヘッダスキップ
        #print(header)
    with open(savename,'w', encoding= 'shift-jis',newline = '') as f:
        header_write = csv.writer(f)
        header_write.writerow(header)

    get_time = np.loadtxt(targetfile, delimiter= ',', dtype= 'str', skiprows = 1, usecols=[0])
    num_lq = np.loadtxt(targetfile, delimiter=',', skiprows = 1, usecols=[1,2])
    pino = np.loadtxt(targetfile, delimiter=',', skiprows = 1, usecols=[3])[0]
    #print(num_lq)
    #print(len(get_time))
    #print(get_time[0])
    #print(get_time)
    #data = np.genfromtxt(targetfile, skip_header = 1, delimiter = ',', names=True, dtype= None, encoding = 'shift_jis')
    #print(data)
    #print(data[:,1])    #送信番号がある想定
    #print(data[:,2])    #電波強度



    #ddm = data[~np.isnan(data).any(axis = 1)]
    #get_time = ddm[:,0]
    get_time_ep = []
    for gt in get_time: #エポック秒に変換
        #print(gt)
        gt_dt = datetime.datetime.strptime(gt,'%Y/%m/%d %H:%M:%S.%f')      
        gt_ep = gt_dt.timestamp()
        get_time_ep.append(gt_ep)
    #print(get_time_ep)
    #print(len(get_time_ep))
    #num = ddm[:,1]
    num = num_lq[:,0]
    #lq = ddm[:,2]
    lq = num_lq[:,1]
    #print(num[0])
    min = num[0] 
    minnum = 0
    #このファイルでは探索で決まるようにする（逆転が起こる前）ので，基本的には書き換えられる
    max = num[-1]
    for i in range(len(num)-1):    #i番目とi+1番目を比較するのでlen-1
        if num [-(i+1)] <= num[-(i+2)]:    #逆転が起こっている
            min = num[-(i+1)]
            minnum = len(num) -(i+1)
            break
    #データ全体を切り取った配列を用意するtime_new,lq_new,num_new
    num_new = num[minnum:len(num)]
    get_time_ep_new = get_time_ep[minnum:len(num)]
    lq_new = lq[minnum:len(num)]
    numfixed = np.arange(min, max)
    #print(len(get_time_ep_new))
    #print(len(numfixed))

    #print(len(num))
    linear_lq = interpolate.interp1d(num_new,lq_new)  #num_new,#lq_new
    linear_tm = interpolate.interp1d(num_new,get_time_ep_new)
    #print(numfixed)
    linear_lq3f = np.round(linear_lq(numfixed),decimals = 2)
    linear_tmep = linear_tm(numfixed)
    pino_forcopy = []
    for i in range(len(linear_lq3f)):     #配列の長さをそろえてくっつけられるように
        pino_forcopy.append(int(pino))       
    linear_tm_dt = []
    for ltm in linear_tmep:
        ltm_dt = datetime.datetime.fromtimestamp(ltm)
        linear_tm_dt.append(ltm_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
    #print(len(linear_lq3f))
    #print(len(pino_forcopy))
    out = np.stack([linear_tm_dt,numfixed,linear_lq3f,pino_forcopy], 1)
    #print(linear_lq3f)
    #print(numfixed.shape)
    #print(linear_lq3f.shape)
    #print(out)


    #print(type(ddm))

    #print(savename)
    with open(savename,'a',encoding= 'shift-jis') as f:
        fwrite = csv.writer(f, lineterminator='\n')
        fwrite.writerows(out)
    #np.savetxt(savename, out ,delimiter= ',', fmt=["%d","%.2f"])
    #print(type(out))
    return(savename)

def makeanimationlist(filelist,tagid):
    #とりあえず間に合わせ（csvreadとwrite）でヘッダの処理はします（今後更新したい）
    savename = 'beforeanime_' + tagid + '.csv'
    firstfile = filelist[0]
    with open (firstfile, encoding = 'shift-jis')as ocsv:
        of = csv.reader(ocsv)
        header = next(of)  #ヘッダスキップ
        #print(header)
    with open(savename,'w', encoding= 'shift-jis',newline = '') as f:
        header_write = csv.writer(f)
        header_write.writerow(header)
    def_num = np.loadtxt(firstfile, delimiter=',', skiprows = 1, usecols=[1])
    num_min = def_num[0]
    num_max = def_num[-1]

    num_of_files = len(filelist)
    pinos = []
    datalist = []
    lqs = [] 
    for file in filelist:
        intdata = np.loadtxt(file, delimiter=',', skiprows = 1, usecols=[1,2,3])
        strdata = np.loadtxt(file, delimiter= ',', dtype='str', skiprows = 1, usecols=[0])
        #print(intdata.shape)
        strdata = strdata.reshape(len(strdata),1)
        #print(strdata.shape)
        data = np.block([strdata, intdata])
        datalist.append(data)
        if intdata[:,0][0] < num_min:
            num_min = intdata[:,0][0]
        if intdata[:,0][-1] > num_max:
            num_max = intdata[:,0][-1]
    #print(datalist)
    out = []
    for i in range(int(num_min),int(num_max+1)):
        maxlq = 0
        for d in datalist:
            nums = []
            #print(d[:,1])
            for k in d[:,1]:
                #print(k)
                nums.append(int(float(k)))
            if i in nums:
                x = nums.index(i)
                #print(d[x][2])
                if float(d[x][2]) > maxlq:
                    maxlq = float(d[x][2])
                    data_for_out = d[x]
        if maxlq != 0:
            out.append(data_for_out)
    #print(out)
    with open(savename,'a',encoding= 'shift-jis') as f:
        fwrite = csv.writer(f, lineterminator='\n')
        fwrite.writerows(out)
    return(savename)

def prepareforanime_yamaguchi(tgtfile):
    timedata = np.loadtxt(tgtfile, delimiter= ',', dtype='str', skiprows = 1, usecols=[0])
    pidata = np.loadtxt(tgtfile, delimiter= ',', skiprows = 1, usecols=[3])
    timedata_dt = []
    for tm in timedata:
        #print(tm)
        #print(type(tm))
        try:
            tm_dt = datetime.datetime.strptime(tm,'%Y-%m-%d %H:%M:%S.%f')
            timedata_dt.append(tm_dt)
        except ValueError:
            pass
    #print(timedata_dt)
    #print(len(timedata_dt))
    #print(pidata)
    pidata_int = []
    for pi in pidata:
        pidata_int.append(int(pi))
    curdata = 0                 #今はどのデータまでチェックできたか
    timeslice = 0               #開始時から何秒経過したか
    datalen = len(timedata_dt)
    memo = '0'                        #初期値はこうすることとします（プロットを工夫して）
    curtimemin = timedata_dt[0]
    curtimemin.replace(microsecond= 0)
    curtimemax = curtimemin + datetime.timedelta(seconds = 1)
    timelist = []
    while curdata < datalen and curtimemax <= timedata_dt[-1]:
        if timedata_dt[curdata] < timedata_dt[0]:
            curdata = curdata + 1 #実験開始時刻までのデータはカット
            continue
        elif curtimemin <= timedata_dt[curdata] and timedata_dt[curdata] < curtimemax:
            memo = pidata[curdata]
            curdata = curdata + 1
            #print(curdata)
        timelist.append([timeslice,memo])
        curtimemin = curtimemax
        curtimemax = curtimemin + datetime.timedelta(seconds = 1)                          #やばかったらここを変えよう（2までは許容！）
        #変える場合はanimation の方の秒数も変える必要あり、変数化したい
        timeslice += 1
    #print(timelist)

    savename = 'timedatafrom_'+ tgtfile
    flist = [savename]
    with open(savename,'w', newline='') as f:
        writer = csv.writer(f)
        header =[file,'starttime:', \
            timedata_dt[0].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],'stoptime:', timedata_dt[-1].strftime('%Y-%m-%d %H:%M:%S')]
        writer.writerow(header)
        for data in timelist: 
            writer.writerow(data)
    return(flist,timedata_dt[0])
    



            

if __name__ == '__main__':
    a = input('filename:')
    tagid = '8201' + input('tagID(下4桁):')
    #b = int(input('columnno:'))
    #c = int(sys.argv[3])
    print('1st_process')
    lognames = before_linear_withtagID(a, 2, tagid)
    linear_file_names = []
    print('2nd_process(linear)')
    for file in lognames:
        linearname =  dmcsv_new(file)
        linear_file_names.append(linearname)
    kalman_file_names = []
    print('3rd_process(kalman)')
    for file in linear_file_names:
        kalman_file = kalman_for_tagdata.kalman_for_tagdata(file,2)
        kalman_file_names.append(kalman_file)
    print('4th_process(prepare_for_anime)')
    animename = makeanimationlist(kalman_file_names,tagid)
    print('final_process(animation)')
    args_foranime = prepareforanime_yamaguchi(animename)
    final_savename = drawanime.animetest(args_foranime[0], args_foranime[1])
    print('Finished. File name is "' + final_savename + '"')

    
        
    

