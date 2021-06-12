#pip(3) install -r requirements.txt
#python(3) make4lib.py NOVEL_PATH
import sys

NOVEL_PATH = sys.argv[1]
DRY_RUN = False

import os
import codecs
import hashlib
import struct
import json
import brotli
import time

fileHashes = {}

txtBinPackCnt = 0
txtBinPack = b''
allBinPack = b''
totalPackLen = 0
booksCount = 0

books_title = []
books_packid = []
books_offset = []
books_len = []
books_tags = []
books_hash = []
packs = []
tags = []

currentPath = ''

TAGS = [
('文化科学','历史','科学','经济', '地理','军事'),
('经济管理','经济','法律','管理','财经','会计'),
('世界名著', '外国', '世界', '翻译', '名著'),
('中国古典','古典','文言','白话'),
('哲学宗教', '哲学', '宗教'),
('名人传记', '名人', '传记'),
('现代文学', '文学','校园','当代','散文','青春'),
('推理探案', '推理', '探案', '侦探'),
('恐怖悬疑', '恐怖', '灵异','悬疑'), 
('科幻小说', '科幻'),
('武侠魔幻', '武侠', '魔幻'),
('网络文学', '网络', '网文', '起点','玄幻','都市','宫廷','后宫'),
('心灵鸡汤', '励志','成功','成长','心灵'),
('其他书籍', '其他'),
]

for tg in TAGS:
    tags.append(tg[0])

failCnt = 0
def decodeFailHandler(ex):
    global failCnt
    #print(fullPath)
    #print(ex)
    failCnt += 1
    if failCnt > 500:
        raise ex
    return "?", ex.end

codecs.register_error('my', decodeFailHandler)

def autoDecodeFile(path):
    global currentPath
    currentPath = path
    with open(path, 'rb') as f:
        txtBin = f.read()
    return autoDecodeBin(txtBin)

def autoDecodeBin(txtBin):
    global failCnt
    try:
        if txtBin[:3] == codecs.BOM_UTF8:
            txtStr = txtBin[3:].decode('utf8')
        elif txtBin[:2] == codecs.BOM_UTF16_LE:
            txtStr = txtBin[2:].decode('utf_16_le')
        else:
            try:
                txtStr = txtBin.decode('utf8')
            except:
                failCnt = 0
                txtStr = txtBin.decode('gb18030', 'my')
        return txtStr
    except Exception as e:
        print(currentPath, e)
        log(['error', currentPath, str(e)])
        return ""

def saveToPkg(tags, title, txtStr):
    global failCnt, txtBinPack
    #print(title, len(txtStr))

    if len(txtStr) < 5000:
        log(['skip', title])
        print('Too small, sikpped.', title)
        return

    #txtStr = replaceWithDict(txtStr)
    encodedTxtBin = txtStr.encode('utf_16_le')
    h = hashlib.sha1(encodedTxtBin).digest()
    if h in fileHashes:
        log(['duplicated', title, fileHashes[h]])
        print('Duplicated file', title, fileHashes[h])
        return
    fileHashes[h] = title

    global booksCount
    booksCount += 1

    if DRY_RUN:
        return

    if len(txtBinPack) + len(encodedTxtBin) > 32 * 1024 * 1024:
        commitBinPack()
    books_title.append(title)
    books_packid.append(txtBinPackCnt)
    books_offset.append(len(txtBinPack))
    books_len.append(len(encodedTxtBin))
    books_tags.append(tags)
    (h32,) = struct.unpack('I', h[:4])
    books_hash.append(h32)
    txtBinPack += encodedTxtBin

def handleFile(path, title, txtStr):
    kw = path + txtStr[:1000]
    tags = 0
    for i in range(0, len(TAGS)):
        for k in TAGS[i]:
            if kw.find(k) != -1:
                tags += 1 << i
                break
    if tags == 0:
        tags += 1 << (len(TAGS) - 1)
    log(['file', path, title, tags])
    saveToPkg(tags, title, txtStr)

def myCompress(b):
    return brotli.compress(b, quality=11, lgwin=24)

def commitBinPack():
    global txtBinPack, totalPackLen, txtBinPackCnt, allBinPack
    if len(txtBinPack) == 0:
        return
    timeA = time.time()
    compressedPack = myCompress(txtBinPack)
    timeB = time.time()
    print('compress','%.2f' % (timeB-timeA), len(txtBinPack), len(compressedPack), '%.2f' % (len(compressedPack) / len(txtBinPack)))
    packs.extend([totalPackLen, len(compressedPack)])
    txtBinPack = b''
    totalPackLen += len(compressedPack)
    txtBinPackCnt += 1

    outFile.write(compressedPack)
    
    
def makeHeader(tocAddr, tocLen):
    return struct.pack('IIIIIIII', 0x44fb0001, tocAddr, 0, tocLen, 0, 0, 0, 0)

outFile = open('out.4lib', 'wb')
outFile.write(makeHeader(0, 0))

def checkMergeFile(dirpath, txtFileList):
    largeCnt = 0
    smallCnt = 0
    for fn in txtFileList:
        sz = os.path.getsize(dirpath + '/' + fn)
        if sz > 30000:
            largeCnt += 1
        else:
            smallCnt += 1
    return smallCnt > largeCnt

logFile = open ('make4lib.log', 'w', encoding='utf8')

def log(obj):
    logFile.write(json.dumps(obj,ensure_ascii=False))
    logFile.write('\n')

try:
    for dirpath, dirnames, filenames in os.walk(NOVEL_PATH):
        txtFileList = []
        for fn in filenames:
            fnLower = fn.lower()
            if (not fnLower.endswith('.txt')) or (fnLower.startswith('.')):
                #print('Skipping file: ' + fullPath)
                continue
            txtFileList.append(fn)
        if len(txtFileList) <= 0:
            continue
        txtFileList.sort()

        pathArr = dirpath[len(NOVEL_PATH):].replace('\\', '/').split('/')
        if (len(txtFileList) > 1) and (len(dirnames) == 0) and (checkMergeFile(dirpath, txtFileList)):
            title = pathArr[-1]
            if len(pathArr) >= 3:
                    title = pathArr[-2] + '/' + title
            print('merge file', txtFileList)
            log(['merge', title, txtFileList])
            mergedStr = ''
            for fn in txtFileList:
                mergedStr += '\n\n\n==========\n' + fn[:-4] + '\n==========\n\n\n'
                mergedStr += autoDecodeFile(dirpath + '/' + fn)
            handleFile(dirpath, title, mergedStr)
        else:
            for fn in txtFileList:
                title = fn[:-4]
                if len(pathArr) >= 2:
                    title = pathArr[-1] + '/' + title
                handleFile(dirpath, title, autoDecodeFile(dirpath + '/' + fn))
        
except KeyboardInterrupt:
    pass

commitBinPack()
print(totalPackLen)
toc = {
    'packs': packs,
    'books_title': books_title,
    'books_packid': books_packid,
    'books_offset':books_offset,
    'books_len':books_len,
    'books_tags':books_tags,
    'books_hash':books_hash,
    'tags': tags
}


tocData = myCompress(json.dumps(toc, ensure_ascii=False).encode('utf8'))
outFile.write(tocData)
outFile.seek(0, os.SEEK_SET)
outFile.write(makeHeader(totalPackLen, len(tocData)))
outFile.close()
logFile.close()

with open('toc.json', 'w', encoding='utf8') as f:
    json.dump(toc, f, ensure_ascii=False, indent=4)