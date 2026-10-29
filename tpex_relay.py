#!/usr/bin/env python3
"""Mirror TPEx JSON for the Apps Script relay. Usage: tpex_relay.py YYYY-MM-DD  (run inside data/)
Writes byte-identical source JSON:
  tpex_otc_YYYYMMDD.json, tpex_insti_YYYYMMDD.json      (daily, exit 3 if not published yet)
  tpex_bulletin_{exDailyQ,revivt,pvChgRslt}.json         (rolling range 2026/01/01..today; script filters by date)
  tpex_openapi_<name>.json                               (latest snapshot of selected OpenAPI datasets)
  tpex_YYYYMMDD.csv                                      (human-readable summary)"""
import sys,json,csv,urllib.request,time
d=sys.argv[1]; ds=d.replace('-','/'); ymd=d.replace('-','')
def get(u):
    err=None
    for i in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=90)
            return json.load(r)
        except Exception as e: err=e; time.sleep(5)
    raise err
B='https://www.tpex.org.tw/www/zh-tw/'
# rolling bulletins + openapi first (useful even on holidays)
for ep in ['exDailyQ','revivt','pvChgRslt']:
    try: json.dump(get(f'{B}bulletin/{ep}?startDate=2026/01/01&endDate={ds}&response=json'),open(f'tpex_bulletin_{ep}.json','w'),ensure_ascii=False)
    except Exception as e: print('bulletin fail',ep,e,file=sys.stderr)
for name in ['tpex_mainboard_daily_close_quotes','tpex_3insti_daily_trading','tpex_mainboard_quotes']:
    try: json.dump(get(f'https://www.tpex.org.tw/openapi/v1/{name}'),open(f'tpex_openapi_{name}.json','w'),ensure_ascii=False)
    except Exception as e: print('openapi fail',name,e,file=sys.stderr)
p=get(f'{B}afterTrading/otc?date={ds}&type=EW&response=json')
t=get(f'{B}insti/dailyTrade?type=Daily&sect=EW&date={ds}&response=json')
pt=p['tables'][0]; tt=t['tables'][0]
if not pt.get('data') or not tt.get('data'):
    print(f'NODATA {d}',file=sys.stderr); sys.exit(3)
json.dump(p,open(f'tpex_otc_{ymd}.json','w'),ensure_ascii=False)
json.dump(t,open(f'tpex_insti_{ymd}.json','w'),ensure_ascii=False)
num=lambda s:(lambda x:float(x) if x not in('','--','---','----') else None)(str(s).replace(',','').strip())
f=[x.strip() for x in pt['fields']]
ic,iv=f.index('收盤'),f.index('成交股數'); ia=[i for i,x in enumerate(f) if x.startswith('成交金額')][0]
trust={r[0].strip():(num(r[11]),num(r[12]),num(r[13])) for r in tt['data']}  # 投信 = cols 11-13
w=csv.writer(open(f'tpex_{ymd}.csv','w',newline=''))
w.writerow(['date','code','name','close','volume','amount','vwap','trust_buy','trust_sell','trust_net'])
for r in pt['data']:
    c=r[0].strip(); cl,v,a=num(r[ic]),num(r[iv]),num(r[ia])
    w.writerow([d,c,r[1].strip(),cl,v,a,(a/v if v else None),*trust.get(c,(0,0,0))])
print(d,len(pt['data']),'price rows',len(trust),'trust rows')
