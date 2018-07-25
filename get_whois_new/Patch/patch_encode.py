#!/usr/bin/env python
# encoding:utf-8

'''
Renzo
2018.03.24
补丁-转任意编码为utf-8
'''

import chardet

class patch_code:

    @staticmethod
    def codeutf(str):
        coding = chardet.detect(str)['encoding']
        #print coding
        if coding == 'utf-8' or coding == 'ascii' or coding == None:
            strcoding = str
            #print "correct---utf/assic"
        elif coding == 'EUC-TW':
            #python无法识别‘EUC-TW’编码
            strcoding = str.decode('GB2312', 'ignore').encode('utf-8')
        else:
            strcoding = str.decode(coding,'ignore').encode('utf-8')
            #print "---coding to utf---============================"
            #print coding
        #print "-"*20
        return strcoding

    @staticmethod
    def dictcodeutf(dict):
        for key in dict:
            if isinstance(dict[key], str):
                temp = dict[key]
                dict[key] = patch_code.codeutf(temp)
        #print "-"*20
        return dict


if __name__ =="__main__":
    encoding = patch_code()
    str = str("take")
    encoding.codeutf(str)







