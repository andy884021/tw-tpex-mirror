#!/usr/bin/env python3
"""Fetch TPEx 上櫃 daily close + 投信 for a date (outside Google, since TPEx returns 403 to Apps Script IPs).
Usage: tpex_relay.py 2026-10-29  -> writes tpex_YYYYMMDD.csv (code,name,close,volume,amount,vwap,trust_buy,trust_sell,trust_net)"""
import sys,json,csv,urllib.request,time
d=sys.argv[1]; ds=d.replace('-','/')
def get(u):
    for i in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=60)
            return json.load(r)
        except Exception as e: err=e; time.sleep(5)
    raise err
num=lambda s:float(str(s).replace(',','').strip()) if str(s).replace(',','').strip() not in('','--','---','----') else None
p=get(f'https://www.tpex.org.tw/www/zh-tw/afterTrading/otc?date={ds}&type=EW&response=json')
t=get(f'https://www.tpex.org.tw/www/zh-tw/insti/dailyTrade?type=Daily&sect=EW&date={ds}&response=json')
ymd=d.replace('-','')
pt=p['tables'][0]; tt=t['tables'][0]
if not pt.get('data') or not tt.get('data'):
    print(f'NODATA {d}', file=sys.stderr); sys.exit(3)
# raw JSON copies: the Apps Script wrapper serves these verbatim in place of the blocked URLs
json.dump(p,open(f'tpex_otc_{ymd}.json','w'),ensure_ascii=False)
json.dump(t,open(f'tpex_insti_{ymd}.json','w'),ensure_ascii=False)
f=[x.strip() for x in pt['fields']]
ic,iv,ia=f.index('收盤'),f.index('成交股數'),f.index('成交金額(元)') if '成交金額(元)' in f else [i for i,x in enumerate(f) if x.startswith('成交金額')][0]
# 投信 columns: fields 代號,名稱, then 外資(3 groups...), 投信 buy/sell/net. Locate by group header.
tf=tt['fields']; grp=[g['title'] for g in tt.get('groups',[])] if tt.get('groups') else None
# columns 11,12,13 = 投信 買進/賣出/買賣超 in current TPEx layout (verified 2026-10)
trust={r[0].strip():(num(r[11]),num(r[12]),num(r[13])) for r in tt['data']}
w=csv.writer(open(f'tpex_{d.replace("-","")}.csv','w',newline=''))
w.writerow(['date','code','name','close','volume','amount','vwap','trust_buy','trust_sell','trust_net'])
for r in pt['data']:
    c=r[0].strip(); cl,v,a=num(r[ic]),num(r[iv]),num(r[ia])
    tb=trust.get(c,(0,0,0))  # not listed in 三大法人 = no institutional trade -> 0
    w.writerow([d,c,r[1].strip(),cl,v,a,(a/v if v else None),*tb])
print(d,len(pt['data']),'price rows',len(trust),'trust rows')
