# coding: UTF-8

from parseFmt import FmtBase

# 特別な書式ではないが、1行を読み取る
class FmtLine(FmtBase):
    def __init__(self):
        self.reinit()
        
        # 状態と呼び出すべき関数のテーブル
        self.key_dict = {
            'e' : self.s_empty,
            'p' : self.s_payload,
        }

        # 終端は改行文字
        FmtBase.termchr = [ 0x0d, 0x0a ]

    def s_empty(self, c):
        if not(c == 0x0d or c == 0x0a):
            self.reinit()
            self.state = 'p'
            self.b_complete = False
            self.payload.append(c)
    
    def s_payload(self, c):
        if c == 0x0d or c == 0x0a:
            self.b_complete = True
            self.len = len(self.payload)
            self.state = 'e'
        else:
            self.payload.append(c)
