"""Apply the Global Approval Inbox UI patch to the :5198 candidate main.py.

UI-only: HTML + CSS + front-end JS.  No API, audit, session, approval-semantics,
auth, DB or systemd change.  Every replacement is asserted (exactly one anchor).
Dry-run by default; pass --apply to write.
"""
import ast
import hashlib
import shutil
import sys

PATH = "/home/aika/gate2-ui-wt/local-console/main.py"

CSS_OLD = "/* === Aika-Box: unified ChatGPT-style scrollbars (CSS-only) === */"
CSS_NEW = r"""/* === Aika-Box: Global Approval Inbox (UI-only, 2026-09-14) === */
#p-qwenpaw .qp-side>.card.qp-audit-off{display:none!important}
#p-qwenpaw .qp-side>.card.qp-inboxcard{flex:1 1 auto}
#p-qwenpaw .qp-count{float:right;font-family:var(--mono);font-size:.68rem;color:var(--accent);font-weight:600}
#p-qwenpaw .qp-count.qp-zero{color:var(--txt2)}
#p-qwenpaw .qp-wgrp{font-family:var(--mono);font-size:.66rem;color:var(--txt2);margin:.15rem 0 .3rem;padding-bottom:.2rem;border-bottom:1px solid rgba(255,255,255,.07)}
#p-qwenpaw .qp-wgrp b{color:var(--txt)}
#p-qwenpaw .qp-ap{border:1px solid var(--border);border-left-width:3px;border-radius:8px;padding:.45rem .5rem;margin-bottom:.5rem;background:rgba(255,255,255,.012);cursor:pointer;transition:background .12s,box-shadow .12s}
#p-qwenpaw .qp-ap:hover{background:rgba(255,255,255,.045)}
#p-qwenpaw .qp-ap.sev-critical,#p-qwenpaw .qp-ap.sev-high{border-left-color:var(--warn)}
#p-qwenpaw .qp-ap.sev-medium{border-left-color:var(--accent)}
#p-qwenpaw .qp-ap.sev-low{border-left-color:var(--border);opacity:.85}
#p-qwenpaw .qp-ap.qp-hl{box-shadow:inset 0 0 0 1px var(--accent);background:rgba(90,170,255,.08)}
#p-qwenpaw .qp-ap.qp-done-approve{border-left-color:var(--success);opacity:.65}
#p-qwenpaw .qp-ap.qp-done-reject{border-left-color:var(--warn);opacity:.65}
#p-qwenpaw .qp-from{font-family:var(--mono);font-size:.65rem;color:var(--txt2);line-height:1.4;border-bottom:1px dashed rgba(255,255,255,.07);padding-bottom:.25rem;margin-bottom:.3rem}
#p-qwenpaw .qp-from span{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#p-qwenpaw .qp-from b{color:var(--txt);font-weight:600}
#p-qwenpaw .qp-apsev{font-family:var(--mono);font-size:.72rem;color:var(--warn)}
#p-qwenpaw .qp-apcmd{font-family:var(--mono);font-size:.74rem;margin:.2rem 0;word-break:break-all}
#p-qwenpaw .qp-apmeta{font-family:var(--mono);font-size:.64rem;color:var(--txt2);line-height:1.4}
#p-qwenpaw .qp-apbtn{margin:.4rem .4rem 0 0}
#p-qwenpaw .qp-apdone{font-family:var(--mono);font-size:.72rem;margin-top:.35rem}
/* === Aika-Box: unified ChatGPT-style scrollbars (CSS-only) === */"""

HTML_OLD = """      <div class="qp-side">
        <div class="card"><div class="h">&#9888; Approval（需人工點擊）</div>
          <div id="qp-approvals" class="note qp-scroll">目前無待決策。</div></div>
        <div class="card"><div class="h">&#9636; 最近決策（audit）</div>
          <div id="qp-audit" class="note qp-scroll">\u2014</div></div>
      </div>"""

HTML_NEW = """      <div class="qp-side">
        <div class="card qp-inboxcard"><div class="h">&#9888; APPROVAL &#183; 全局 Inbox（需人工點擊）<span id="qp-pending-count" class="qp-count qp-zero">Pending: 0</span></div>
          <div id="qp-inbox-sub" class="note" style="flex:none;margin:.1rem 0 .35rem">彙整所有已登記 Worker / Session 的待決策項（僅 PENDING 且可點擊）。</div>
          <div id="qp-approvals" class="note qp-scroll">目前無待決策。</div></div>
        <div class="card qp-audit-off" hidden><div class="h">&#9636; 最近決策（audit）</div>
          <div id="qp-audit" class="note qp-scroll">\u2014</div></div>
      </div>"""

JS_OLD_HEAD = "  // \u2500\u2500 approvals \u2500\u2500"
JS_OLD_TAIL = """  function pollApprovals(){
    if(!st.worker||!st.session) return;
    jget(API+'/approvals?worker_id='+encodeURIComponent(st.worker)+'&session_id='+encodeURIComponent(st.session))
      .then(function(d){ renderApprovals(d.approvals); })
      .catch(function(){});
  }
"""

JS_NEW = r"""  // ── approvals: GLOBAL INBOX (all workers, all sessions; UI-only) ──
  var SEV_RANK={CRITICAL:0,HIGH:1,MEDIUM:2,LOW:3};
  function sevClass(s){var t=String(s==null?'':s).toLowerCase();
    if(t==='critical')return 'sev-critical';
    if(t==='high')return 'sev-high';
    if(t==='medium')return 'sev-medium';
    return 'sev-low';}
  function remainingS(a){var ttl=Number(a.expires_in_s),age=Number(a.age_s);
    if(!isFinite(ttl))return null;
    if(!isFinite(age))return ttl;
    return Math.max(0,ttl-age);}
  function cmpInbox(a,b){
    var ra=(SEV_RANK[a.severity]==null?9:SEV_RANK[a.severity]);
    var rb=(SEV_RANK[b.severity]==null?9:SEV_RANK[b.severity]);
    if(ra!==rb)return ra-rb;
    var ta=remainingS(a),tb=remainingS(b);
    if(ta!=null&&tb!=null&&ta!==tb)return ta-tb;
    if(ta!=null&&tb==null)return -1;
    if(ta==null&&tb!=null)return 1;
    return (a.created_at||0)-(b.created_at||0);
  }
  function widOf(a){return a._worker||a.worker_id||'?';}
  function wlabel(wid){
    var w=(st.workers||[]).filter(function(x){return x.worker.worker_id===wid;})[0];
    return (w&&w.worker.display_name)?(w.worker.display_name+' \u00b7 '+wid):wid;}
  function sessionsOf(wid){
    var c=st.sessCache[wid];
    if(c&&(Date.now()-c.t)<10000)return Promise.resolve(c.ids);
    return jget(API+'/sessions?worker_id='+encodeURIComponent(wid)).then(function(d){
      var ids=(d.sessions||[]).map(function(s){return s.session_id;}).filter(function(x){return !!x;});
      st.sessCache[wid]={t:Date.now(),ids:ids};
      return ids;
    }).catch(function(){return c?c.ids:[];});
  }
  function workerPending(w){
    var wid=w.worker.worker_id;
    return sessionsOf(wid).then(function(ids){
      // ONE approvals call per worker regardless of session count (no N x M fan-out).
      var q=ids.map(function(s){return 'session_id='+encodeURIComponent(s);}).join('&');
      return jget(API+'/approvals?worker_id='+encodeURIComponent(wid)+(q?('&'+q):''));
    }).then(function(d){
      return (d.approvals||[]).map(function(a){a._worker=wid;return a;});
    }).catch(function(e){st.inboxErr=String((e&&e.message)||e);return [];});
  }
  function refreshInbox(){
    if(Date.now()<st.inboxHold)return Promise.resolve();
    var now=Date.now();
    Object.keys(st.decided).forEach(function(k){if(now-st.decided[k]>120000)delete st.decided[k];});
    var p=(st.workers&&st.workers.length)?Promise.resolve(st.workers)
      :jget(API+'/workers').then(function(d){st.workers=d.workers||[];return st.workers;});
    return p.then(function(ws){
      var cs=ws.filter(function(w){return w.status&&w.status.api_flavor==='console'&&w.worker.enabled!==false;});
      return Promise.all(cs.map(workerPending));
    }).then(function(lists){
      var items=[].concat.apply([],lists).filter(function(a){
        return a.state==='PENDING'&&a.clickable===true&&!st.decided[a.request_id];});
      st.inbox=items;renderInbox(items);
    }).catch(function(){});
  }
  function renderInbox(items){
    var box=el('qp-approvals'),cnt=el('qp-pending-count');
    if(cnt){cnt.textContent='Pending: '+items.length;cnt.className='qp-count'+(items.length?'':' qp-zero');}
    if(!box)return;
    if(!items.length){
      box.innerHTML=st.inboxErr?('目前無待決策。（部分 Worker 讀取失敗：'+esc(st.inboxErr)+'）'):'目前無待決策。';
      return;}
    st.inboxErr=null;
    var sorted=items.slice().sort(cmpInbox);
    box.innerHTML='';
    var lastW=null;
    sorted.forEach(function(a){
      var wid=widOf(a);
      if(wid!==lastW){
        lastW=wid;
        var n=sorted.filter(function(x){return widOf(x)===wid;}).length;
        var gh=document.createElement('div');gh.className='qp-wgrp';
        gh.innerHTML='<b>'+esc(wlabel(wid))+'</b> \u00b7 '+n+' pending';
        box.appendChild(gh);
      }
      box.appendChild(inboxCard(a));
    });
  }
  function inboxCard(a){
    var d=document.createElement('div');
    d.className='qp-ap '+sevClass(a.severity)+(st.hlRid===a.request_id?' qp-hl':'');
    d.setAttribute('data-rid',a.request_id);
    var from=document.createElement('div');from.className='qp-from';
    from.innerHTML='<span>From</span>'
      +'<span title="'+esc(widOf(a))+'">Worker: <b>'+esc(widOf(a))+'</b></span>'
      +'<span title="'+esc(a.session_id||'')+'">Session: <b>'+esc(a.session_id||'?')+'</b></span>';
    var sev=document.createElement('div');sev.className='qp-apsev';
    sev.textContent=(a.severity||'-')+' \u00b7 '+(a.tool||'-');
    var cmd=document.createElement('div');cmd.className='qp-apcmd';cmd.textContent=(a.requested_action||'-');
    var rem=remainingS(a);
    var meta=document.createElement('div');meta.className='qp-apmeta';
    meta.textContent='findings '+(a.findings_count==null?'-':a.findings_count)
      +' \u00b7 TTL '+(rem==null?'?':Math.round(rem)+'s left')
      +' \u00b7 created '+new Date((a.created_at||0)*1000).toLocaleTimeString()
      +' \u00b7 age '+Math.round(Number(a.age_s)||0)+'s';
    d.appendChild(from);d.appendChild(sev);d.appendChild(cmd);d.appendChild(meta);
    var holder=document.createElement('div');
    if(a.clickable){
      var b1=document.createElement('button');b1.className='btn-send qp-apbtn';b1.textContent='Approve';
      var b2=document.createElement('button');b2.className='btn-send qp-apbtn';b2.textContent='Reject';
      b1.onclick=function(e){if(e&&e.stopPropagation)e.stopPropagation();decide(a,'approve');};
      b2.onclick=function(e){if(e&&e.stopPropagation)e.stopPropagation();decide(a,'reject');};
      holder.appendChild(b1);holder.appendChild(b2);
    }else{
      var n2=document.createElement('div');n2.className='note';n2.textContent='（已失效，不可點擊）';
      holder.appendChild(n2);
    }
    var bar=document.createElement('button');bar.className='btn-send qp-apbtn';bar.textContent='Open';
    bar.onclick=function(e){if(e&&e.stopPropagation)e.stopPropagation();openSource(a);};
    d.appendChild(holder);d.appendChild(bar);
    d.onclick=function(){openSource(a);};
    return d;
  }
  function syncGroupCount(){
    var box=el('qp-approvals');if(!box)return;
    var heads=box.querySelectorAll('.qp-wgrp');
    for(var i=0;i<heads.length;i++){
      var h=heads[i],n=0,sib=h.nextElementSibling;
      while(sib&&!sib.classList.contains('qp-wgrp')){
        if(sib.classList.contains('qp-ap')&&!sib.classList.contains('qp-done-approve')
           &&!sib.classList.contains('qp-done-reject'))n++;
        sib=sib.nextElementSibling;}
      var b=h.querySelector('b');
      h.innerHTML='<b>'+(b?esc(b.textContent):'')+'</b> \u00b7 '+n+' pending';
    }
  }
  function flashCard(rid,kind,ok){
    var d=document.querySelector('.qp-ap[data-rid="'+rid+'"]');
    if(!d)return;
    var btns=d.querySelectorAll('button');
    for(var i=0;i<btns.length;i++){
      if(btns[i].textContent==='Approve'||btns[i].textContent==='Reject'){
        btns[i].disabled=true;btns[i].style.display='none';}}
    d.classList.remove('qp-hl');
    if(!ok){
      var f=document.createElement('div');f.className='qp-apdone';
      f.style.color='var(--warn)';f.textContent='\u2717 決定未成功（仍待決策）';
      d.appendChild(f);return;
    }
    d.classList.add('qp-done-'+kind);
    var z=document.createElement('div');z.className='qp-apdone';
    z.style.color=(kind==='approve'?'var(--success)':'var(--warn)');
    z.textContent=(kind==='approve'?'\u2713 Approved':'\u2717 Rejected');
    d.appendChild(z);
    var cnt=el('qp-pending-count');
    if(cnt){
      var n=parseInt(String(cnt.textContent).replace(/[^0-9]/g,''),10);
      if(!isFinite(n))n=1;
      n=Math.max(0,n-1);
      cnt.textContent='Pending: '+n;cnt.className='qp-count'+(n?'':' qp-zero');}
    st.inbox=(st.inbox||[]).filter(function(x){return x.request_id!==rid;});
    syncGroupCount();
    setTimeout(function(){
      if(d.parentNode){
        d.parentNode.removeChild(d);
        var box=el('qp-approvals');
        if(box&&!box.children.length)box.innerHTML='目前無待決策。';
      }
    },1500);
  }
  function decide(a,kind){
    var wid=widOf(a),sid=a.session_id||st.session;
    el('qp-runstatus').textContent=kind+' 送出中…';
    jpost(API+'/approvals/'+encodeURIComponent(a.request_id)+'/'+kind,
      {worker_id:wid,session_id:sid})
      .then(function(j){
        if(j&&j.ok){
          st.decided[a.request_id]=Date.now();
          st.inboxHold=Date.now()+1800;
          logLine('['+kind+'] '+(j.message||'ok'),true);
          flashCard(a.request_id,kind,true);
        }else{
          logLine('['+kind+'] 未成功: '+((j&&(j.message||j.error))||''),true);
          flashCard(a.request_id,kind,false);
        }
        loadAudit();
        setTimeout(pollApprovals,1900);
      })
      .catch(function(e){logLine('['+kind+'] 失敗: '+e.message,true);
        flashCard(a.request_id,kind,false);});
  }
  function openSource(a){
    var wid=widOf(a),sid=a.session_id;
    if(!wid||!sid)return;
    st.hlRid=a.request_id;
    if(st.hlTimer)clearTimeout(st.hlTimer);
    st.hlTimer=setTimeout(function(){st.hlRid=null;},4000);
    var wsel=el('qp-worker');if(wsel)wsel.value=wid;
    st.worker=wid;
    jget(API+'/workers?force=true').then(function(d){
      st.workers=d.workers||[];paintWorker(st.workers);}).catch(function(){});
    el('qp-hd').textContent='⌨ QwenPaw \u00b7 '+wid+' \u00b7 '+sid+'（開啟中…）';
    jget(API+'/sessions?worker_id='+encodeURIComponent(wid)).then(function(d){
      var list=d.sessions||[];
      var sel=el('qp-session');sel.innerHTML='';
      list.forEach(function(s){
        var o=document.createElement('option');o.value=s.session_id;
        o.textContent=s.session_id+' \u00b7 '+s.status+' \u00b7 '+s.messages+' msgs \u00b7 '+(s.source||'');
        sel.appendChild(o);});
      if(list.some(function(s){return s.session_id===sid;})){
        sel.value=sid;
      }else{
        var o2=document.createElement('option');o2.value=sid;
        o2.textContent=sid+' \u00b7 （不在清單，仍載入）';sel.appendChild(o2);sel.value=sid;}
      st.sessCache[wid]={t:Date.now(),ids:list.map(function(s){return s.session_id;})};
      st.session=sid;updateChatMeta();
      el('qp-hd').textContent='⌨ QwenPaw \u00b7 '+wid+' \u00b7 '+sid;
      return loadHistory();
    }).then(function(){
      scrollLogToBottom();
      renderInbox(st.inbox||[]);
      var d=document.querySelector('.qp-ap[data-rid="'+a.request_id+'"]');
      if(d)d.classList.add('qp-hl');
    }).catch(function(e){logLine('開啟來源失敗: '+e.message,true);});
  }
  function pollApprovals(){refreshInbox();}
  function startInbox(){if(!st.itimer)st.itimer=setInterval(function(){pollApprovals();},2000);pollApprovals();}
  function stopInbox(){if(st.itimer){clearInterval(st.itimer);st.itimer=null;}}
"""

EDITS = [
    # css + html + js blocks are applied as ordered steps in main() below
    ("finalize", "      renderApprovals(d.approvals);\n", "      pollApprovals();\n"),
    ("state", "var st={worker:null,session:null,run:null,es:null,timer:null,live:'',flavor:null};",
     "var st={worker:null,session:null,run:null,es:null,timer:null,live:'',flavor:null,"
     "workers:null,inbox:[],sessCache:{},decided:{},hlRid:null,hlTimer:null,inboxHold:0,"
     "inboxErr:null,itimer:null};"),
    ("loadworkers", "      var prefer='aika-core-01';",
     "      st.workers=d.workers||[];\n      var prefer='aika-core-01';"),
    ("nav", """  document.querySelectorAll('#nav a[data-p="qwenpaw"]').forEach(function(a){
    a.addEventListener('click',function(){ if(!el('qp-worker').options.length){loadWorkers();loadAudit();} });});""",
     """  document.querySelectorAll('#nav a[data-p="qwenpaw"]').forEach(function(a){
    a.addEventListener('click',function(){ if(!el('qp-worker').options.length){loadWorkers();}
      startInbox();loadAudit(); });});
  document.querySelectorAll('#nav a[data-p]').forEach(function(a){
    if(a.getAttribute('data-p')!=='qwenpaw')a.addEventListener('click',function(){ stopInbox(); });});"""),
    ("reload", "el('qp-reload').onclick=function(){loadWorkers();loadAudit();};",
     "el('qp-reload').onclick=function(){loadWorkers();loadAudit();pollApprovals();};"),
    ("init", "  updateChatMeta();\n  loadAudit();\n})();",
     """  updateChatMeta();
  loadAudit();
  if(el('p-qwenpaw')&&el('p-qwenpaw').classList.contains('show')) startInbox();
})();"""),
]


def main():
    src = open(PATH, encoding="utf-8").read()
    before = hashlib.sha256(src.encode()).hexdigest()[:16]
    out = src
    report = []

    # 1. CSS
    assert out.count(CSS_OLD) == 1, "css anchor"
    out = out.replace(CSS_OLD, CSS_NEW)
    report.append(("css", 1))

    # 2. HTML
    assert out.count(HTML_OLD) == 1, "html anchor"
    out = out.replace(HTML_OLD, HTML_NEW)
    report.append(("html", 1))

    # 3. JS approvals block head..tail
    i = out.find(JS_OLD_HEAD)
    j = out.find(JS_OLD_TAIL)
    assert i != -1 and j > i, "js block bounds"
    assert out.count(JS_OLD_HEAD) == 1, "js head unique"
    assert out.count(JS_OLD_TAIL) == 1, "js tail unique"
    out = out[:i] + JS_NEW + out[j + len(JS_OLD_TAIL):]
    report.append(("js", len(JS_NEW)))

    # 4. simple edits
    for name, old, new in EDITS:
        if name == "js":
            continue
        n = out.count(old)
        assert n == 1, f"{name}: anchor count {n}"
        out = out.replace(old, new)
        report.append((name, n))

    # sanity: old renderer gone, new symbols present
    for bad in ("function renderApprovals", "renderApprovals(d.approvals)"):
        assert bad not in out, f"leftover {bad}"
    for good in ("function renderInbox", "function refreshInbox", "function openSource",
                 "function startInbox", "qp-pending-count", "qp-audit-off"):
        assert good in out, f"missing {good}"

    ast.parse(out)  # python syntax still valid
    open("/tmp/gi-main.patched.py", "w", encoding="utf-8").write(out)
    after = hashlib.sha256(out.encode()).hexdigest()[:16]
    print("edits:", report)
    print(f"lines {src.count(chr(10))+1} -> {out.count(chr(10))+1}")
    print(f"bytes {len(src.encode())} -> {len(out.encode())}")
    print(f"sha16 {before} -> {after}")
    print("BOM:", out.startswith("\ufeff"))
    if "--apply" in sys.argv:
        shutil.copy2(PATH, PATH + ".pre-inbox")
        with open(PATH, "w", encoding="utf-8") as fh:
            fh.write(out)
        print("APPLIED to", PATH)
    else:
        print("dry-run only")


main()
