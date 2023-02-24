# coding: UTF-8

# 書式パーサーの基底クラス
class FmtBase:
    def __init__(self):
        self.reinit()
        self.termchr = []

    # 初期化する。
    def reinit(self):
        self.state = 'e'
        self.len = 0
        self.len_read = 0
        self.payload = []
        self.checksum = 0
        self.b_complete = False
        
    # ステートが見つからなかった場合の実行メソッド。'e' empty 状態に戻す。
    def s_other(self, c):
        self.state = 'e'

    # 入力を処理する（入力はbyte, 
    def process(self, c): 
        prcone = False

        # 文字列型なら bytes 型へ変換しておく
        if type(c) == str:
            c = c.encode()

        if type(c) == int:
            # int 型は１バイト処理
            prcone = True
        elif type(c) == bytes or type(c) == list:
            # 要素数が１の場合は最初の要素を int 型に変換しておく
            if len(c) == 1:
                c = c[0]
                prcone = True
        else:
            # これ以外の型は処理できない
            return
        
        if prcone == True:
            # 入力が１バイトなので１バイト処理を行う
            self.key_dict.get(self.state, self.s_other)(c)
        else:
            # 初期化してから１バイト処理を行う
            self.reinit()
            for x in c:
                self.key_dict.get(self.state, self.s_other)(x)
                if self.b_complete == True:
                    break
            # 終端
            if self.b_complete == False:
                for x in self.termchr:
                    self.key_dict.get(self.state, self.s_other)(x)
                    if self.b_complete == True:
                        break
                
    # 入力を中断する。
    def terminate(self):
        self.reinit()

    # 完了状態かを確認する。
    def is_comp(self):
        return self.b_complete

    # ペイロードを得る（リスト型）
    def get_payload(self):
        return self.payload

    # ペイロードを得る（文字列変換、例外発生あり）
    def get_payload_in_str(self):
        #return "".join(map(chr, self.payload))
        return bytes(self.payload).decode('latin-1')

