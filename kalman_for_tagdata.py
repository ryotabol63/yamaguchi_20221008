from dataclasses import dataclass
import pykalman
import scipy
import numpy as np
import csv

def kalman_for_tagdata(targetfile, rowname):
    rowname = int(rowname)
    savename = 'kalman_' + targetfile


    #とりあえず間に合わせ（csvreadとwrite）でヘッダの処理はします（今後更新したい）
    with open (targetfile, encoding = 'shift-jis')as ocsv:
        of = csv.reader(ocsv)
        header = next(of)  #ヘッダスキップ
        #print(header)
    with open(savename,'w', encoding= 'shift-jis',newline = '') as f:
        header_write = csv.writer(f)
        header_write.writerow(header)

    get_time = np.loadtxt(targetfile, delimiter= ',', dtype= 'str', skiprows = 1, usecols=[0])
    target = np.loadtxt(targetfile, delimiter=',', skiprows = 1, usecols=[1,2])
    pino = np.loadtxt(targetfile, delimiter=',', skiprows = 1, usecols=[3])
    #target = np.genfromtxt(targetfile, skip_header = 1, delimiter = ',', encoding = 'utf-8')
    data = target[:,(rowname-1)]
    #print(data)
    ukf = pykalman.UnscentedKalmanFilter(initial_state_mean= data[0], initial_state_covariance= data[0]/10,transition_covariance= 0.08)
    filtered = ukf.filter(data)[0]
    smoothed = ukf.smooth(data)[0]
    #必要なほうをつかって
    #np.savetxt(savename, filtered, delimiter= ',', fmt=['%.2f'])
    i = 0
    while i < len(target):
        target[i][rowname-1] = smoothed[i]
        i += 1
    #print(target)
    out = np.stack([get_time, target[:,0], target[:,1], pino],1)

    #print(out)

    with open(savename,'a',encoding= 'utf-8') as f:
        fwrite = csv.writer(f, lineterminator='\n')
        fwrite.writerows(out)
    return(savename)

if __name__ == '__main__':
    targetfile = input('データcsvを指定:')
    rowname = input('何行目か指定:')
    #data = np.genfromtxt(targetfile, skip_header = 0, delimiter = ',', encoding = 'utf-8')
    kalman_for_tagdata(targetfile,rowname)




