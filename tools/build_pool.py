import json,re,sys,time,urllib.request,urllib.error,os
from concurrent.futures import ThreadPoolExecutor
UA={'User-Agent':'Mozilla/5.0','Accept-Language':'en','Cookie':'CONSENT=YES+1'}
BAD=re.compile(r'(sex|porn|nude|xxx|18\+|\bفضيحة|جنس|عاري|سكس|قتل|دماء|انتحار|مخدر|قمار|bet\b|casino|gambl)',re.I)
def get(u,method='GET',follow=True):
    class NR(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*a,**k): return None
    op=urllib.request.build_opener() if follow else urllib.request.build_opener(NR)
    r=urllib.request.Request(u,headers=UA,method=method)
    try:
        x=op.open(r,timeout=20); return x.status,x.read().decode('utf8','ignore')
    except urllib.error.HTTPError as e: return e.code,''
    except Exception: return 0,''
def cid(h,cache):
    if h in cache: return cache[h]
    s,b=get('https://www.youtube.com/@'+h)
    m=re.search(r'channel_id=(UC[\w-]{22})|"externalId":"(UC[\w-]{22})',b or '')
    if m: cache[h]=m.group(1) or m.group(2); return cache[h]
def rss(i):
    s,b=get('https://www.youtube.com/feeds/videos.xml?channel_id='+i)
    if s!=200: return []
    out=[]
    for e in re.findall(r'<entry>(.*?)</entry>',b,re.S):
        v=re.search(r'<yt:videoId>([\w-]+)',e); t=re.search(r'<title>(.*?)</title>',e,re.S)
        if v: out.append((v.group(1),(t.group(1) if t else '')))
    return out
def ok(v,title,seen):
    if v in seen or BAD.search(title): return None
    s,_=get('https://www.youtube.com/shorts/'+v,'GET',False)
    if s!=200: return None
    s,_=get('https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v='+v+'&format=json')
    if s!=200: return None
    return v
def main():
    cfg=json.load(open('tools/channels.json')); cache=cfg.get('ids',{})
    old=json.load(open('reels-pool.json')) if os.path.exists('reels-pool.json') else {'items':[]}
    items=[tuple(x) for x in old['items']]; seen={x[0] for x in items}
    stats={'channels':0,'unresolved':[],'checked':0,'added':0}
    def work(c):
        i=c.get('id') or cid(c['h'],cache)
        if not i: stats['unresolved'].append(c['h']); return []
        stats['channels']+=1
        res=[]
        for v,t in rss(i):
            if v in seen: continue
            stats['checked']+=1
            if ok(v,t,seen): res.append((v,c['cat']))
        return res
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(work,cfg['channels']):
            for it in r:
                if it[0] not in seen: seen.add(it[0]); items.append(it); stats['added']+=1
    cfg['ids']=cache; json.dump(cfg,open('tools/channels.json','w'),indent=1)
    items=items[-5000:]
    json.dump({'updated':time.strftime('%Y-%m-%d'),'items':[list(x) for x in items]},open('reels-pool.json','w'),separators=(',',':'))
    print(json.dumps(stats,ensure_ascii=False)); 
    from collections import Counter; print(len(items),Counter(x[1] for x in items))
main()
