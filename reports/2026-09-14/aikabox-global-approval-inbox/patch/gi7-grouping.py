"""Grouped rendering for the Global Approval Inbox (second pass, UI-only).

Replaces the flat "sort globally + header on worker change" renderer with
per-worker groups (group order by the group's most urgent card, card order by
severity -> shortest TTL -> oldest), so worker headers cannot interleave.
"""
import ast
import hashlib
import shutil
import sys

PATH = "/home/aika/gate2-ui-wt/local-console/main.py"

OLD = """    var sorted=items.slice().sort(cmpInbox);
    box.innerHTML='';
    var lastW=null;
    sorted.forEach(function(a){
      var wid=widOf(a);
      if(wid!==lastW){
        lastW=wid;
        var n=sorted.filter(function(x){return widOf(x)===wid;}).length;
        var gh=document.createElement('div');gh.className='qp-wgrp';
        gh.innerHTML='<b>'+esc(wlabel(wid))+'</b> \\u00b7 '+n+' pending';
        box.appendChild(gh);
      }
      box.appendChild(inboxCard(a));
    });
"""

NEW = """    var groups=inboxGroups(items);
    box.innerHTML='';
    groups.forEach(function(g){
      var gh=document.createElement('div');gh.className='qp-wgrp';
      gh.innerHTML='<b>'+esc(wlabel(g.wid))+'</b> \\u00b7 '+g.items.length+' pending';
      box.appendChild(gh);
      g.items.forEach(function(a){box.appendChild(inboxCard(a));});
    });
"""

GROUP_FN = """  function inboxGroups(items){
    var byW={},order=[];
    items.forEach(function(a){
      var w=widOf(a);
      if(!byW[w]){byW[w]=[];order.push(w);}
      byW[w].push(a);
    });
    var groups=order.map(function(w){var l=byW[w].slice().sort(cmpInbox);return {wid:w,items:l,top:l[0]};});
    groups.sort(function(A,B){return cmpInbox(A.top,B.top);});
    return groups;
  }
  function renderInbox(items){"""


def main():
    src = open(PATH, encoding="utf-8").read()
    before = hashlib.sha256(src.encode()).hexdigest()[:16]
    assert src.count(OLD) == 1, "render anchor"
    out = src.replace(OLD, NEW)
    assert out.count("  function renderInbox(items){") == 1
    out = out.replace("  function renderInbox(items){", GROUP_FN)
    ast.parse(out)
    after = hashlib.sha256(out.encode()).hexdigest()[:16]
    print(f"sha16 {before} -> {after}")
    print(f"lines {src.count(chr(10))+1} -> {out.count(chr(10))+1}  bytes {len(src.encode())} -> {len(out.encode())}")
    if "--apply" in sys.argv:
        shutil.copy2(PATH, "/tmp/gi-main.pre-grouping.py")
        open(PATH, "w", encoding="utf-8").write(out)
        print("APPLIED")
    else:
        print("dry-run")


main()
