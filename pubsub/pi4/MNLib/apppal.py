#!/usr/bin/env python
# coding: UTF-8

import datetime
import os

from appbase import AppBase
from mwSerial import MWSerial

class AppPAL(AppBase):
	# コンストラクタ
	def __init__(self, port=None, baud=115200, tout=0.1 , sformat='Ascii', autolog=False, err=False ):
		super(AppPAL,self).__init__(port,baud,tout,App='AppPAL', smode=sformat, bErr=err)
		self.AutoLog = autolog
		self.InitDict()

	# デストラクタ
	def __del__(self):
		if self.file != None and self.b_openfile :
			self.FileClose()

	# シリアルデータを読み込んで解釈する
	def ReadSensorData(self):
		self.InitDict()
		self.ByteArr = self.SerialRead()
		if self.ByteArr != None:
			self.ReadDict['ArriveTime'] = datetime.datetime.today()
			self.ReadDict['LogicalID'] = self.ByteArr[11]
			self.ReadDict['EndDeviceSID'] = self.BinList2StrHex(self.ByteArr[7:11])
			self.ReadDict['RouterSID'] = self.BinList2StrHex(self.ByteArr[0:4])
			self.ReadDict['LQI'] = self.ByteArr[4]
			self.ReadDict['SequenceNumber'] = self.BinList2Int(self.ByteArr[5:7])
			self.ReadDict['Sensor'] = self.ByteArr[12]

			# App_PALだったら
			if self.ReadDict['Sensor'] == 0x80:
				self.ReadDict['PALID'] = self.ByteArr[13] & 0x1F
				self.ReadDict['PALVersion'] = (self.ByteArr[13] & 0xE0)>>5
				self.ReadDict['PALVersion'] = (self.ReadDict['PALVersion']&0x01)<<2 | (self.ReadDict['PALVersion']&0x02) | (self.ReadDict['PALVersion']&0x04)>>2	# ビットの入れ替え

				__SensorNum = self.ByteArr[14]
				__Addr = 15
				__i = 0
				while __i < __SensorNum:
					__ErrCode = 0
					__DataType = 0			# データのタイプを入れる
					__Type = None			# データの型を入れる
					__SensorID = 0			# センサのIDを入れる
					__bSigned = False		# データが符号付かどうかを入れる
					__bExByte = False		# 拡張バイトの有無を入れる
					__ExByte = 0			# 拡張バイトの内容を入れる
					__DataNum = 0			# データのバイト数を入れる

					# 4バイト読み込む
					__Param = self.BinList2Int(self.ByteArr[__Addr:__Addr+4])
					__Addr += 4
					__DataType = (__Param>>24)&0xFF
					if __DataType&0x80 != 0:
						__ErrCode = __DataType&0x7F
					else:
						__bExByte = True if (__DataType&0x10)!=0 else False
						__bSigned = True if (__DataType&0x04)!=0 else False
						if (__DataType&0x03)==0: __Type = 'Char'
						elif (__DataType&0x03)==1: __Type = 'Short'
						elif (__DataType&0x03)==2: __Type = 'Long'
						else: __Type = 'Variable'

					__SensorID = (__Param>>16)&0xFF
					__ExByte = (__Param>>8)&0xFF
					__DataNum = __Param&0xFF

					__StrSensorID = ''

					__Div = 1		# データの桁を合わせる

					if __SensorID == 0x00: __StrSensorID = 'HALLIC'
					elif __SensorID == 0x01:
						__StrSensorID = 'Temperature'
						__Div = 100.0
					elif __SensorID == 0x02:
						__StrSensorID = 'Humidity'
						__Div = 100.0
					elif __SensorID == 0x03: __StrSensorID = 'Illuminance'
					elif __SensorID == 0x04: __StrSensorID = 'Acceleration'
					elif __SensorID == 0x05: __StrSensorID = 'EventID'
					elif __SensorID == 0x30:
						if __ExByte == 0: __StrSensorID = 'ADC'
						if __ExByte == 8: __StrSensorID = 'Power'
						else: __StrSensorID = 'ADC%d' % (__ExByte)
					elif __SensorID == 0x31: __StrSensorID = 'DIO'
					elif __SensorID == 0x32: __StrSensorID = 'EEPROM'
					elif __SensorID == 0x34: __StrSensorID = 'WakeupFactor'
					else: __StrSensorID = 'Unknown'

					if __ErrCode == 0:
						if __StrSensorID == 'Acceleration':
							if ((__StrSensorID+'X') in self.ReadDict) == False:
								__freq = __ExByte>>5
								if __freq == 4:
									self.ReadDict['SamplingFrequency'] = 380
								elif __freq == 3:
									self.ReadDict['SamplingFrequency'] = 190
								elif __freq == 2:
									self.ReadDict['SamplingFrequency'] = 100
								elif __freq == 1:
									self.ReadDict['SamplingFrequency'] = 50
								else:
									self.ReadDict['SamplingFrequency'] = 25

								self.ReadDict[__StrSensorID+'X'] = list()
								self.ReadDict[__StrSensorID+'Y'] = list()
								self.ReadDict[__StrSensorID+'Z'] = list()

							self.ReadDict[__StrSensorID+'X'].append( self.Unsigned2Signed(self.BinList2Int(self.ByteArr[__Addr:__Addr+2]), 2)/1000.0 )
							self.ReadDict[__StrSensorID+'Y'].append( self.Unsigned2Signed(self.BinList2Int(self.ByteArr[__Addr+2:__Addr+4]), 2)/1000.0 )
							self.ReadDict[__StrSensorID+'Z'].append( self.Unsigned2Signed(self.BinList2Int(self.ByteArr[__Addr+4:__Addr+6]), 2)/1000.0 )
						elif __StrSensorID == 'EventID':
							self.ReadDict[__StrSensorID] = [ None, None, None ]
							self.ReadDict[__StrSensorID][0] = __ExByte
							self.ReadDict[__StrSensorID][1] = self.ByteArr[__Addr]
							self.ReadDict[__StrSensorID][2] = self.BinList2Int(self.ByteArr[__Addr+1:__Addr+4])
						elif __StrSensorID == 'WakeupFactor':
							self.ReadDict[__StrSensorID] = [ None, None, None ]
							self.ReadDict[__StrSensorID][0] = self.ByteArr[__Addr]
							self.ReadDict[__StrSensorID][1] = self.ByteArr[__Addr+1]
							self.ReadDict[__StrSensorID][2] = self.ByteArr[__Addr+2]
						else:
							if __Type == 'Variable':
								self.ReadDict[__StrSensorID] = self.ByteArr[__Addr:__Addr+__DataNum]
							else:
								self.ReadDict[__StrSensorID] = self.BinList2Int(self.ByteArr[__Addr:__Addr+__DataNum])
								if __bSigned:
									self.ReadDict[__StrSensorID] = self.Unsigned2Signed(self.ReadDict[__StrSensorID], __DataNum)

								if __Div != 1 and __Div != 0:
									self.ReadDict[__StrSensorID] /= __Div

						__Addr += __DataNum
					else:
						self.ReadDict[__StrSensorID] = 'Error(0x%02X)' % __ErrCode
						if __DataNum != 0:
							self.ReadDict[__StrSensorID] += ' ' + self.BinList2StrHex(self.ByteArr[__Addr:__Addr+__DataNum])
							__Addr += __DataNum

					__i += 1

			# App_Tag
			else:
				self.ReadDict['Power'] = (1950+self.ByteArr[13]*5) if (self.ByteArr[13] <= 170) else (2800+(self.ByteArr[13]-170)*10)
				self.ReadDict['ADC1'] = self.BinList2Int(self.ByteArr[14:16])
				self.ReadDict['ADC2'] = self.BinList2Int(self.ByteArr[16:18])

				# 各々のセンサの値を入れる
				if self.ReadDict['Sensor'] == 0x11:
					self.ReadDict['Temperature'] = (10.0 * self.ReadDict['ADC2'] - 6000.0 + self.BinList2Int(self.ByteArr[18:20]))/100.0

				elif self.ReadDict['Sensor'] == 0x31 or self.ReadDict['Sensor'] == 0x3A:
					self.ReadDict['Temperature'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[18:20]),2)/100.0
					self.ReadDict['Humidity'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[20:22]),2)/100.0

				elif self.ReadDict['Sensor'] == 0x32:
					self.ReadDict['Temperature'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[18:20]),2)/100.0

				elif self.ReadDict['Sensor'] == 0x33:
					self.ReadDict['Pressure'] = self.BinList2Int(self.ByteArr[18:20])

				elif self.ReadDict['Sensor'] == 0x34:
					self.ReadDict['AccelerationX'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[18:20]),2)/100.0
					self.ReadDict['AccelerationY'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[20:22]),2)/100.0
					self.ReadDict['AccelerationZ'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[22:24]),2)/100.0

				elif self.ReadDict['Sensor'] == 0x35:
					self.ReadDict['Mode'] = self.ByteArr[18]
					if self.ReadDict['Mode'] == 0xFA:		# Burst
						__AccelNum = self.ByteArr[19]
						self.ReadDict['AccelerationX'] = []
						self.ReadDict['AccelerationY'] = []
						self.ReadDict['AccelerationZ'] = []
						i = 0
						while i < __AccelNum:
							self.ReadDict['AccelerationX'].append(self.Unsigned2Signed(self.BinList2Int(self.ByteArr[i*6+20:i*6+22]),2)/1000.0)
							self.ReadDict['AccelerationY'].append(self.Unsigned2Signed(self.BinList2Int(self.ByteArr[i*6+22:i*6+24]),2)/1000.0)
							self.ReadDict['AccelerationZ'].append(self.Unsigned2Signed(self.BinList2Int(self.ByteArr[i*6+24:i*6+26]),2)/1000.0)
							i += 1

					elif self.ReadDict['Mode'] == 0xFB:		# Spin
						self.ReadDict['PWM'] = self.BinList2Int(self.ByteArr[19:21])
						self.ReadDict['Degree'] = self.BinList2Int(self.ByteArr[21:23])/10.0

					else:
						self.ReadDict['AccelerationX'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[19:21]),2)/100.0
						self.ReadDict['AccelerationY'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[21:23]),2)/100.0
						self.ReadDict['AccelerationZ'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[23:25]),2)/100.0

				elif self.ReadDict['Sensor'] == 0x36:
					self.ReadDict['Illuminance'] = self.BinList2Int(self.ByteArr[18:22])

				elif self.ReadDict['Sensor'] == 0x37:
					self.ReadDict['Roll'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[18:20]),2)
					self.ReadDict['Pitch'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[20:22]),2)
					self.ReadDict['Yaw'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[22:24]),2)

				elif self.ReadDict['Sensor'] == 0x38:
					self.ReadDict['Red'] = self.BinList2Int(self.ByteArr[18:20])
					self.ReadDict['Green'] = self.BinList2Int(self.ByteArr[20:22])
					self.ReadDict['Blue'] = self.BinList2Int(self.ByteArr[22:24])
					self.ReadDict['IR'] = self.BinList2Int(self.ByteArr[24:26])

				elif self.ReadDict['Sensor'] == 0x39:
					self.ReadDict['Temperature'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[18:20]),2)/100.0
					self.ReadDict['Humidity'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[20:22]),2)/100.0
					self.ReadDict['Pressure'] = self.BinList2Int(self.ByteArr[22:24])

				elif self.ReadDict['Sensor'] == 0x62:
					self.ReadDict['Mode'] = self.Unsigned2Signed(self.BinList2Int(self.ByteArr[18:20]),2)
					self.ReadDict['Interrupt'] = self.ByteArr[20]
					__AccelNum = self.ByteArr[21]
					self.ReadDict['SampleFrequency'] = self.ByteArr[22]
					self.ReadDict['AccelerationX'] = []
					self.ReadDict['AccelerationY'] = []
					self.ReadDict['AccelerationZ'] = []
					i = 0
					while i < __AccelNum:
						self.ReadDict['AccelerationX'].append(self.Unsigned2Signed(self.BinList2Int(self.ByteArr[i*6+23:i*6+25]),2)/1000.0)
						self.ReadDict['AccelerationY'].append(self.Unsigned2Signed(self.BinList2Int(self.ByteArr[i*6+25:i*6+27]),2)/1000.0)
						self.ReadDict['AccelerationZ'].append(self.Unsigned2Signed(self.BinList2Int(self.ByteArr[i*6+27:i*6+29]),2)/1000.0)
						i += 1
	
				elif self.ReadDict['Sensor'] == 0xD1:
					__SensorNum = self.ByteArr[18]
					i = 0
					__SnsData = self.ByteArr[19:]
					self.ReadDict['SensorBitmap'] = 0

					while i < __SensorNum:
						__nextSns = __SnsData[0]

						if __nextSns == 0x31:
							self.ReadDict['SensorBitmap'] |= 0x0001
							self.ReadDict['Temperature'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[1:3]),2)/100.0
							self.ReadDict['Humidity'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[3:5]),2)/100.0
							__Increment = 5

						elif __nextSns == 0x32:
							self.ReadDict['SensorBitmap'] |= 0x0002
							self.ReadDict['Temperature'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[1:3]),2)/100.0
							__Increment = 3

						elif __nextSns == 0x33:
							self.ReadDict['SensorBitmap'] |= 0x0004
							self.ReadDict['Pressure'] = self.BinList2Int(__SnsData[1:3])
							__Increment = 3

						elif __nextSns == 0x34:
							self.ReadDict['SensorBitmap'] |= 0x0008
							self.ReadDict['AccelerationX'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[1:3]),2)/100.0
							self.ReadDict['AccelerationY'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[3:5]),2)/100.0
							self.ReadDict['AccelerationZ'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[5:7]),2)/100.0
							__Increment = 7

						elif __nextSns == 0x35:
							self.ReadDict['SensorBitmap'] |= 0x0010
							self.ReadDict['ADXL34xMode'] = __SnsData[1]
							self.ReadDict['AccelerationX'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[2:4]),2)/100.0
							self.ReadDict['AccelerationY'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[4:6]),2)/100.0
							self.ReadDict['AccelerationZ'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[6:8]),2)/100.0
							__Increment = 8

						elif __nextSns == 0x36:
							self.ReadDict['SensorBitmap'] |= 0x0020
							self.ReadDict['Illuminance'] = self.BinList2Int(__SnsData[1:5])
							__Increment = 5

						elif __nextSns == 0x37:
							self.ReadDict['SensorBitmap'] |= 0x0040
							self.ReadDict['Roll'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[1:3]),2)
							self.ReadDict['Pitch'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[3:5]),2)
							self.ReadDict['Yaw'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[5:7]),2)
							__Increment = 7

						elif __nextSns == 0x38:
							self.ReadDict['SensorBitmap'] |= 0x0080
							self.ReadDict['Red'] = self.BinList2Int(__SnsData[1:3])
							self.ReadDict['Green'] = self.BinList2Int(__SnsData[3:5])
							self.ReadDict['Blue'] = self.BinList2Int(__SnsData[5:7])
							self.ReadDict['IR'] = self.BinList2Int(__SnsData[7:9])
							__Increment = 9

						elif __nextSns == 0x39:
							self.ReadDict['SensorBitmap'] |= 0x0100
							self.ReadDict['Temperature'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[1:3]),2)/100.0
							self.ReadDict['Humidity'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[3:5]),2)/100.0
							self.ReadDict['Pressure'] = self.BinList2Int(__SnsData[5:7])
							__Increment = 7

						elif __nextSns == 0x3A:
							self.ReadDict['SensorBitmap'] |= 0x0200
							self.ReadDict['Temperature'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[1:3]),2)/100.0
							self.ReadDict['Humidity'] = self.Unsigned2Signed(self.BinList2Int(__SnsData[3:5]),2)/100.0
							__Increment = 5


						__SnsData = __SnsData[__Increment:]
						i+=1

				elif self.ReadDict['Sensor'] == 0xFE:
					self.ReadDict['Mode'] = self.ByteArr[18]
					self.ReadDict['EndDeviceDI'] = self.ByteArr[19]
					self.ReadDict['ParentDO'] = self.ByteArr[20]
				elif self.ReadDict['Sensor'] != 0x10:
					return False

			if self.AutoLog:
				self.OutputData()

			return True
		else:
			return False

	def GetSensorName(self):
		__PrintStr = 'None'
		__Element = self.ReadDict['Sensor']
		if __Element == 0x10: __PrintStr = 'Analog'
		elif __Element == 0x11: __PrintStr = 'LM61'
		elif __Element == 0x31: __PrintStr = 'SHT21'
		elif __Element == 0x32: __PrintStr = 'ADT7410'
		elif __Element == 0x33: __PrintStr = 'MPL115A2'
		elif __Element == 0x34: __PrintStr = 'LIS3DH'
		elif __Element == 0x35: __PrintStr = 'ADXL34x'
		elif __Element == 0x36: __PrintStr = 'TSL2561'
		elif __Element == 0x37: __PrintStr = 'L3GD20'
		elif __Element == 0x38: __PrintStr = 'S11059-02DT'
		elif __Element == 0x39: __PrintStr = 'BME280'
		elif __Element == 0x3A: __PrintStr = 'SHT31'
		elif __Element == 0x3B: __PrintStr = 'SHTC3'
		elif __Element == 0x62: __PrintStr = 'ADXL362'
		elif __Element == 0x80: __PrintStr = 'PAL'
		elif __Element == 0xD1: __PrintStr = 'MultiSensor'
		elif __Element == 0xFE: __PrintStr = 'Button'

		return __PrintStr

	def GetModeName(self, sensor, mode):
		__ReturnVal = ''
		# ADXL34xの場合
		if sensor == 0x35:
			if mode == 0x00: __ReturnVal = 'Normal'
			elif mode == 0xFF: __ReturnVal = 'Nekotter'
			elif mode == 0xFE: __ReturnVal = 'Low Energy'
			elif mode == 0xFD: __ReturnVal = 'Dice'
			elif mode == 0xFC: __ReturnVal = 'Shake'
			elif mode == 0xFB: __ReturnVal = 'Spin'
			elif mode == 0xFA: __ReturnVal = 'Burst'
			elif mode <= 0x1F:
				if mode&0x01: __ReturnVal += 'Tap '
				if mode&0x02: __ReturnVal += 'DoubleTap '
				if mode&0x04: __ReturnVal += 'FreeFall '
				if mode&0x08: __ReturnVal += 'Active '
				if mode&0x10: __ReturnVal += 'Inactive'
		elif sensor == 0x62:
			__ReturnVal = 'Normal'
		# 押しボタンの場合
		elif sensor == 0xFE:
			if mode == 0x00: __ReturnVal = 'Falling Edge'
			elif mode == 0x01: __ReturnVal = 'Rising Edge'
			elif mode == 0x02: __ReturnVal = 'Falling/Rising Edge'
			elif mode == 0x04: __ReturnVal = 'TWELITE SWING'
			

		return __ReturnVal
	
	def GetPALName(self, pal):
		__ReturnVal = ''
		if pal == 0x01: __ReturnVal = 'OPENCLOSE-SENSE-PAL'
		elif pal == 0x02: __ReturnVal = 'AMIENT-SENSE-PAL'
		elif pal == 0x03: __ReturnVal = 'MOTION-SENSE-PAL'
		elif pal == 0x04: __ReturnVal = 'NOTICE-PAL'
		elif pal == 0x05: __ReturnVal = 'TWELITE-CUE'

		return __ReturnVal

	def GetEventName(self, event):
		__eventname = ['Unknown', 'Unknown']
		if not isinstance(event, list):
			return __eventname

		if event[0]&0x7F == 0:
			__eventname[0] = 'Magnet'
			if event[1]&0x7F == 0:
				__eventname[1] == 'Open'
			elif event[1]&0x7F == 1:
				__eventname[1] = 'Close(N)'
			elif event[1]&0x7F == 2:
				__eventname[1] = 'Close(S)'
		elif event[0]&0x7F == 1:
			__eventname[0] = 'Temperature'
		elif event[0]&0x7F == 2:
			__eventname[0] = 'Humidity'
		elif event[0]&0x7F == 3:
			__eventname[0] = 'Illuminance'
		elif event[0]&0x7F == 4:
			__eventname[0] = 'Acceleration'
			if event[1] == 1:
				__eventname[1] = 'Dice1'
			elif event[1] == 2:
				__eventname[1] = 'Dice2'
			elif event[1] == 3:
				__eventname[1] = 'Dice3'
			elif event[1] == 4:
				__eventname[1] = 'Dice4'
			elif event[1] == 5:
				__eventname[1] = 'Dice5'
			elif event[1] == 6:
				__eventname[1] = 'Dice6'
			elif event[1] == 8:
				__eventname[1] = 'Shake'
			elif event[1] == 16:
				__eventname[1] = 'Move'

		return __eventname

	def GetWakeupFactorName(self, factor):
		__factorname = [ 'Unknown', 'Unknown', 'Unknown' ]
		if not isinstance( factor, list ):
			return __factorname

		if isinstance(factor[0], int):
			__factorname[0] = 'PacketID_%d' % factor[0]

		if isinstance(factor[1], int):
			if factor[1] == 0x00:
				__factorname[1] = 'Magnet'
			elif factor[1] == 0x01:
				__factorname[1] = 'Temperature'
			elif factor[1] == 0x02:
				__factorname[1] = 'Humidity'
			elif factor[1] == 0x03:
				__factorname[1] = 'Illuminance'
			elif factor[1] == 0x04:
				__factorname[1] = 'Acceleration'
			elif factor[1] == 0x31:
				__factorname[1] = 'DIO'
			elif factor[1] == 0x35:
				__factorname[1] = 'Timer'

		if isinstance(factor[2], int):
			if factor[2] == 0:
				__factorname[2] = 'Occurred_Event'
			elif factor[2] == 1:
				__factorname[2] = 'Changed_Value'
			elif factor[2] == 2:
				__factorname[2] = 'Upper_then_Threshold'
			elif factor[2] == 3:
				__factorname[2] = 'Lower_Then_Threshold'
			elif factor[2] == 4:
				__factorname[2] = 'Within_Threshold'

		return __factorname

	# 自動ログ機能を有効にする
	def EnableAutoLog(self):
		self.AutoLog = True

	# 自動ログ機能を無効にする
	def DisableAutoLog(self):
		self.AutoLog = False

	# ログを書き込むファイルを開く
	def FileOpen(self):
		self.b_openfile = True
		__Appname = self.AppName
		__date = datetime.datetime.today()
		__ModuleSID = self.ReadDict['EndDeviceSID'][1:len(self.ReadDict['EndDeviceSID'])]
		__SensorName = self.GetSensorName()
		if __SensorName == 'ADXL34x':
			if self.ReadDict['Mode'] == 0xFB:
				__SensorName += '-Spin'
		elif __SensorName == 'PAL':
			__SensorName = self.GetPALName(self.ReadDict['PALID'])

			if self.ReadDict['PALID'] == 0x05:
				__Appname = 'AppCUE'

		__FileName = __Appname + '_'+ __ModuleSID + '_' + __SensorName + '_%04d%02d%02d' % (__date.year, __date.month, __date.day)
		__ext = '.csv'
		__FileName += __ext

		#print(__FileName)

		try:
			if os.path.exists(__FileName):
				self.file = open(__FileName,'a')
			else:
				self.file = open(__FileName,'w')
				self.OutputList( self.ReadDict.keys() )
		except:
			if self.ShowError:
				import traceback
				traceback.print_exc()
			else:
				print("Cannot Open File(" + __FileName + ")...")

	def OutputCSV(self):
		self.FileOpen()
		self.OutputList(self.CreateOutputList())
		if ( 'AccelerationX' in self.ReadDict.keys() ):
			if isinstance(self.ReadDict['AccelerationX'], list):
				i = 1
				while i < len(self.ReadDict['AccelerationX']):
					__AccelList = ['']*len(self.ReadDict)
					j = 0
					for k in self.ReadDict.keys():
						if k.find('Acceleration') >= 0:
							__AccelList[j] = self.ReadDict[k][i]

						j += 1

					self.OutputList(__AccelList)
					i += 1

		self.FileClose()

	def CreateOutputList(self):
		Outlist = list()

		# 辞書のキーを取得する
		__KeyList = self.ReadDict.keys()

		# キーごとに出力を変える
		for keys in __KeyList:
			# 出力する文字列を入れる変数の初期化
			__OutStr = ''
			# 要素を入れる
			__Element = self.ReadDict[keys]

			# 到来時間
			if keys == 'ArriveTime':
				__OutStr = '\t%04d/%02d/%02d %02d:%02d:%02d.%03d' % ( __Element.year,
																	  __Element.month,
																	  __Element.day,
																	  __Element.hour,
																	  __Element.minute,
																	  __Element.second,
																	  __Element.microsecond/1000)

			# SID
			elif keys.find('SID') >= 0:
				# 要素の中身が0x80000000の場合、中継していないのでその旨を出力する
				if __Element == '80000000':
					__OutStr = '\tNo Relay'
				# 最上位ビットが不要なため消す
				else:
					__OutStr = '\t' + __Element[1:len(self.ReadDict[keys])]

			# センサー
			elif keys == 'Sensor':
				__OutStr = '\t' + self.GetSensorName()

			elif keys == 'SensorBitmap':
				__OutStr = '\t%04X' % __Element

			elif keys == 'Interrupt':
				__OutStr = '\t0x%02X' % __Element

			# センサごとのモード
			elif keys == 'Mode':
				__OutStr = self.GetModeName(self.ReadDict['Sensor'], __Element )

			elif keys == 'HALLIC':
				if __Element&0x7F == 0:
					__OutStr = '\tOpen'
				elif __Element&0x7F == 1:
					__OutStr = '\tClose(N)'
				elif __Element&0x7F == 2:
					__OutStr = '\tClose(S)'
				else:
					__OutStr = '\tUnknown'

			# 加速度
			elif keys.find('Acceleration') >= 0:
				if isinstance( __Element, list ):
					__OutStr = __Element[0]
				else:
					__OutStr = __Element

			elif keys == 'EventID' :
				if isinstance( __Element, list ):
					__tmp = self.GetEventName(__Element)
					__OutStr = "\t%s:%s" % (__tmp[0], __tmp[1])
				else:
					__OutStr = __Element

			elif keys == 'WakeupFactor' :
				if isinstance( __Element, list ):
					__tmp = self.GetWakeupFactorName(__Element)
					__OutStr = "\t%s:%s:%s" % (__tmp[0], __tmp[1], __tmp[2])
				else:
					__OutStr = __Element

			else:
				__OutStr = __Element

			Outlist.append(__OutStr)

#		print(Outlist)
		return Outlist

	# 辞書の中のデータを標準出力する
	def ShowSensorData(self):
		# 辞書のキーを取得する
		__KeyList = self.ReadDict.keys()

		# コンソールをクリアする
		#print( '%c[2J%c[H' % (27, 27), end='' )
		if os.name == 'nt':
			os.system('cls')
		elif os.name == 'posix':
			os.system('clear')

		# キーごとに出力を変える
		for keys in __KeyList:
			# 出力する文字列を入れる変数の初期化
			__PrintStr = ''
			# 要素を入れる
			__Element = self.ReadDict[keys]

			# 到来時間
			if keys == 'ArriveTime':
				__PrintStr = '%04d/%02d/%02d %02d:%02d:%02d.%03d' % ( __Element.year,
																	  __Element.month,
																	  __Element.day,
																	  __Element.hour,
																	  __Element.minute,
																	  __Element.second,
																	  __Element.microsecond/1000)

			# SID
			elif keys.find('SID') >= 0:
				# 要素の中身が0x80000000の場合、中継していないのでその旨を出力する
				if __Element == '80000000':
					__PrintStr = 'No Relay'
				# 最上位ビットが不要なため消す
				else:
					__PrintStr = __Element[1:len(self.ReadDict[keys])]

			# PAL ID
			elif keys == 'PALID':
				if __Element == 0x01: __PrintStr = 'OPEN-CLOSE PAL'
				elif __Element == 0x02: __PrintStr = 'AMBIENT PAL'
				elif __Element == 0x03: __PrintStr = 'MOTION PAL'
				elif __Element == 0x04: __PrintStr = 'NOTICE PAL'
				elif __Element == 0x05: __PrintStr = 'TWELITE CUE'

			# LQI
			elif keys == 'LQI':
				__dbm = (7.0 * __Element - 1970.0) / 20.0
				__PrintStr = str(__Element) + ' (%.02f [dBm])' % __dbm

			# センサー
			elif keys == 'Sensor':
				__PrintStr = self.GetSensorName()

			# センサー
			elif keys == 'SensorBitmap':
				__PrintStr = '0x%04X' % __Element

			elif keys == 'Interrupt':
				__PrintStr = '0x%04X' % __Element

			# 電源電圧 or ADC
			elif keys == 'Power' or keys.find('ADC') >= 0:
				__PrintStr = str(__Element) + ' [mV]'

			# 温度
			elif keys == 'Temperature':
				__PrintStr = '%.02f' % __Element + ' [°C]'

			# 湿度
			elif keys == 'Humidity':
				__PrintStr = '%.02f' % __Element + ' [%]'

			# 気圧
			elif keys == 'Pressure':
				__PrintStr = str(__Element) + ' [hPa]'

			# 加速度
			elif keys.find('Acceleration') >= 0:
				if isinstance( __Element, list ):
					for data in __Element:
						__PrintStr += '%.03f\t' % data
				else:
					__PrintStr = '%.03f' % __Element + ' [g]'

			elif keys == 'EventID':
				if isinstance( __Element, list ):
					__tmp = self.GetEventName(__Element)
					__PrintStr = "%s, %s" % (__tmp[0], __tmp[1])
				else:
					__PrintStr = str(__Element)

			elif keys == 'WakeupFactor':
				if isinstance( __Element, list ):
					__tmp = self.GetWakeupFactorName(__Element)
					__PrintStr = "%s, %s, %s" % (__tmp[0], __tmp[1],__tmp[2])
				else:
					__PrintStr = str(__Element)

			# サンプリング周波数
			elif keys.find('SamplingFrequency') >= 0:
				__PrintStr = str(__Element) + ' [Hz]'

			# 角度
			elif keys == 'Degree':
				__PrintStr = str(__Element) + ' [°]'

			# ジャイロの角速度
			elif keys == 'Roll' or keys == 'Pitch' or keys == 'Yaw':
				__PrintStr = str(__Element) + ' [dps]'

			# 照度
			elif keys == 'Illuminance':
				__PrintStr = str(__Element) + ' [lux]'

			# センサごとのモード
			elif keys == 'Mode':
				__PrintStr = self.GetModeName(self.ReadDict['Sensor'], __Element )

			elif keys == 'HALLIC':
				if (__Element&0x7F) == 0:
					__PrintStr = 'Open'
				elif __Element&0x7F == 1:
					__PrintStr = 'Close(N)'
				elif __Element&0x7F == 2:
					__PrintStr = 'Close(S)'
				else:
					__PrintStr = 'Unknown'

			# 出力用の文字列に中身が入っている場合はそちらを出力する
			if __PrintStr != '':
				print( keys + ' : ' + __PrintStr )
			# 出力用の文字列に何も入っていない場合はそのまま出力する
			else:
				print( keys + ' : ' + str(__Element) )

# 実装実験用Main関数
if __name__ == '__main__':
	PAL = AppPAL(port='COM4', sformat='Ascii', autolog=True)

	try:
		while True:
			if PAL.ReadSensorData():
				PAL.ShowSensorData()

	except KeyboardInterrupt:
		del PAL
