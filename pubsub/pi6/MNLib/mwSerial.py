#!/usr/bin/python
# coding: UTF-8

try:
	import serial
	import serial.tools.list_ports
except ImportError:
	print( "Cannot inport pyserial..." )
	print( "Please install pyserial. " )
	quit()

from parseFmt_Ascii import FmtAscii
from parseFmt_Binary import FmtBinary

# シリアル読み込みを行うクラス

class MWSerial:
	def __init__( self, port=None, baud=115200, timeout=0.1, parity=serial.PARITY_NONE, stop=1, byte=8, rtscts=0, dsrdtr=0, mode='Ascii' ):
		self.reinit(port, baud, timeout, parity, stop, byte, rtscts, dsrdtr, mode)

	def __del__(self):
		self.SerialClose()

	def reinit(self, port=None, baud=115200, timeout=0.1, parity=serial.PARITY_NONE, stop=1, byte=8, rtscts=0, dsrdtr=0, mode='Ascii' ):
		self.port = port
		self.baud = baud
		self.timeout = timeout
		self.parity = parity
		self.stopbits = stop
		self.bytesize = byte
		self.rtscts = rtscts
		self.dsrdtr = dsrdtr

		self.ser = None
		self.mode = mode
		self.bDataArrived = False

		if self.port == None:
			self.SerialSelect()
			if self.port == None:
				print( "Not found device..." )
				exit(1)

		__bOk = self.SerialOpen()
		if not __bOk:
			__ErrStr = "Cannot open " + self.port + "..."
			print( __ErrStr )
			print( "Please close the software using " + self.port + "." )
			exit(1)

		self.Fmt = None
		if self.mode == 'Ascii':
			self.Fmt = FmtAscii()
		elif self.mode == 'Binary':
			self.Fmt = FmtBinary()
		else:
			return

	# シリアルポートを検索する。
	def SerialSelect(self, portname=None):

		if not portname == None:
			self.port = portname
			return

		__port = serial.tools.list_ports.comports()

		__portnum = len(__port)
		if __portnum == 0:
			return
		elif __portnum == 1:
			self.port = __port[0].device
			return
		else:
			while True:
				i = 0
				for name in __port:
					print('%2d : %s' % (i, name.device))
					i += 1

				try:
					c = input( 'Select port number(0-%d) > ' % (__portnum-1) )
				except KeyboardInterrupt:
					exit(1)

				num = 0
				try:
					num = int(c)
				except ValueError:
					print("No number. Please input again.")
					continue

				if num >= __portnum:
					print("The number entered is out of range. Please input again.")
					continue

				self.port = __port[num].device
				return

	# シリアルポートを開く
	def SerialOpen(self):
		if self.port != None:
			try:
				self.ser = serial.Serial(
							self.port,
							self.baud,
							timeout = self.timeout,
							parity = self.parity,
							stopbits = self.stopbits,
							bytesize = self.bytesize,
							rtscts = self.rtscts,
							dsrdtr = self.dsrdtr
						)
				print("  *** Open %s ***" % self.port)
				return True
			except KeyboardInterrupt:
				print("\r\nInput interrupt key.")
				return False
			except:
				print("\r\nCannnot Open Serial Port...")
				import traceback
				traceback.print_exc()
				return False
		else:
			return False

	# シリアルポートを閉じる
	def SerialClose(self):
		if self.ser != None:
			self.ser.close()

	def SerialWrite(self, Cmd):
		__writedata = self.Fmt.S_output(Cmd)
		self.ser.write(__writedata)

	def GetPayload(self):
		if self.ser != None and self.Fmt != None :
			return self.Fmt.get_payload()
		else:
			return None

	def ReadSerialLine(self):
		self.bDataArrived = False
		if self.mode == 'Ascii':
			self.msg = self.ser.read(1)
			if(len(self.msg) > 0):
				self.Fmt.process(self.msg)
				if self.Fmt.is_comp():
					self.bDataArrived = True
			else:
				self.bDataArrived = False

		elif self.mode == 'Binary':
			if self.ser.inWaiting() > 0:
				while True:
					self.c = ord(self.ser.read(1))
					self.Fmt.process(self.c)
					if self.Fmt.is_comp():
						break
				if self.Fmt.is_comp():
					self.bDataArrived = True
				else:
					self.bDataArrived = False
					self.Fmt.terminate()
			else:
				self.bDataArrived = False
		else:
			return 0

		return 1

	def IsDataArrived(self):
		return self.bDataArrived

	def GetMode(self):
		return self.mode

	def GetCheckSum(self):
		return self.Fmt.get_checksum()

# テスト用コード
if __name__=='__main__':
	ser = serial.Serial( "COM7", 115200, timeout=0.1  )
	fmt = MWSerial( ser, 'Ascii' )

	i = 0
	try:
		while True:
			fmt.ReadSerialLine()
			if fmt.IsDataArrived():
				msg = fmt.GetPayload()
				print(msg)
	except KeyboardInterrupt:
		ser.close()
