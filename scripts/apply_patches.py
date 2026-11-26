from pathlib import Path

p = Path('android/app/src/main/assets/index.html')
html = p.read_text(encoding='utf-8')

# Shop debts: registering a customer debt reduces the shop cash immediately.
old_debt = 'const id=Date.now(),dt=$("cdd").value||today();C().debts.push({id,name:n,amt:a,date:dt,paid:false});/* تسجيل الدين لا يخصم نقداً من الصندوق؛ التسديد فقط يضاف للصندوق */$("cdn").value="";$("cda").value="";save();rCash()};'
new_debt = 'const id=Date.now(),dt=$("cdd").value||today();C().debts.push({id,name:n,amt:a,date:dt,paid:false,paidAmt:0,cashApplied:true});C().tx.push({id:id+1,kind:"out",label:"دين",desc:"دين على الزبون: "+n,amt:a,date:dt,debtId:id});$("cdn").value="";$("cda").value="";save();rCash()};'
assert old_debt in html, 'Customer debt creation code not found in restored app source'
html = html.replace(old_debt, new_debt, 1)

# Old customer debts have no creation transaction. Deduct their original amount once;
# repayments already exist as cash-in transactions and therefore remain counted once.
old_tx_loop = 'C().tx.forEach(t=>{b+=t.kind==="in"?t.amt:-t.amt;if(t.kind==="in")tin+=t.amt;else{tout+=t.amt;if(t.date.slice(0,7)===m)mout+=t.amt}});'
new_tx_loop = old_tx_loop + '\n C().debts.forEach(d=>{if(!d.cashApplied)b-=Number(d.amt)||0});'
assert old_tx_loop in html, 'Shop cash transaction calculation not found'
html = html.replace(old_tx_loop, new_tx_loop, 1)

# Replace the association formula used by the actual J() ledger.
old_monthly_handler = '$("jmi").oninput=function(){J().monthly=parseFloat(this.value)||0;save();rJam()};'
new_monthly_handler = '$("jmi").value="40";$("jmi").readOnly=true;$("jmi").oninput=function(){J().monthly=40;this.value="40";save();rJam()};'
assert old_monthly_handler in html, 'Association monthly amount control not found'
html = html.replace(old_monthly_handler, new_monthly_handler, 1)

html = html.replace('المساهمة الشهرية', 'الإضافة الشهرية للجمعية (40 د.أ إجمالاً)')

# Remove the member-subscription collection card and all related UI hooks.
html = html.replace('<div>الاشتراكات المحصّلة فعلياً<b id="jcollected"></b></div>', '')
html = html.replace('$("jcb").onclick=()=>jadd("collections","jcn","jca");', '')
html = html.replace('else if(t.dataset.col!==undefined){J().collections.splice(+t.dataset.col,1);save();rJam()}', '')
html = html.replace(' $("jdp").textContent=fmt(c.repaid);$("jcollected").textContent=fmt(c.col);$("jrem").textContent=fmt(c.rem);', ' $("jdp").textContent=fmt(c.repaid);$("jrem").textContent=fmt(c.rem);')
html = html.replace(' $("jcl").innerHTML=D.collections.length?D.collections.map((x,i)=>\`<div class="it"><span class="d">\${esc(x.n)}<span>\${fd(x.t)}</span></span><b class="amt in">\${fmt(x.a)}</b><button class="sm" data-col="\${i}">✕</button></div>\`).join(""):\'<div class="e">لا توجد تحصيلات مسجلة</div>\';', '')
html = html.replace('+"\\nالاشتراكات المحصّلة فعلياً: "+fmt(c.col)', '')


# Keep internal automatic cloud backup, but remove all manual backup/copy UI and the
# association member-subscription collection card from the rendered app.
html = html.replace('أنشئ نسخة احتياطية لحماية بياناتك', 'تُحفظ بياناتك تلقائياً')
group_code = Path('patches/group.js').read_text(encoding='utf-8')
marker = '</script>'
pos = html.rfind(marker)
if pos < 0:
    raise SystemExit('Could not locate application script closing tag')
html = html[:pos] + '\n' + group_code + r'''
(function(){
 const buttonTerms=/نسخة احتياطية|نسخ احتياطي|إنشاء نسخة|استعادة نسخة|تصدير البيانات|استيراد البيانات|نسخ البيانات|نسخ الملخص|backup|restore backup|export data|import data/i;
 const cardTerms=/تحصيل اشتراكات الأعضاء|أخذ نسخة احتياطية|استرجاع\s*\/\s*استيراد نسخة|نسخة احتياطية للجمعية/i;
 function clean(){
  document.querySelectorAll('button,a,[role="button"]').forEach(el=>{
   const label=((el.innerText||'')+' '+(el.getAttribute('aria-label')||'')+' '+(el.getAttribute('title')||'')).trim();
   if(label && buttonTerms.test(label)) el.remove();
  });
  document.querySelectorAll('.card,details').forEach(el=>{
   const heading=el.querySelector(':scope > b,:scope > summary');
   const label=heading ? (heading.innerText||heading.textContent||'').trim() : '';
   if(label && cardTerms.test(label)) el.remove();
  });
 }
 clean();
 new MutationObserver(clean).observe(document.documentElement,{childList:true,subtree:true});
})();
''' + '\n' + html[pos:]

# Association ledger: confirm deletions and make payment actions resilient.
association_fix = r"""
(function(){
 const section=$("m_jam");
 section.onclick=function(e){
  const t=e.target.closest("button"); if(!t||!t.dataset)return;
  const d=t.dataset;
  if(d.p!==undefined){if(!confirm("حذف سجل المشتريات هذا؟"))return;J().p.splice(+d.p,1);save();rJam();return}
  if(d.d!==undefined){const x=J().d[+d.d];if(!x)return;if(!confirm("تأكيد حذف سلفة "+x.n+"؟ لا يمكن التراجع عن الحذف."))return;J().d.splice(+d.d,1);save();rJam();return}
  if(d.r!==undefined){payI=+d.r;rJam();const q=$("jpv");if(q)q.focus();return}
  if(d.no!==undefined){payI=-1;rJam();return}
  if(d.ok!==undefined){
   const x=J().d[+d.ok];if(!x)return;
   const left=Math.max(0,(Number(x.a)||0)-(Number(x.r)||0));
   const field=$("jpv");let v=field?Number(field.value):NaN;
   if(!Number.isFinite(v)||v===0){msg("أدخل مبلغًا صحيحًا للسداد");return}
   if(v>0&&v>left)v=left;
   if(v<0)v=Math.max(v,-(Number(x.r)||0));
   if(v===0){payI=-1;rJam();return}
   x.r=(Number(x.r)||0)+v;x.paid=x.r>=(Number(x.a)||0)-0.0001;
   x.h=Array.isArray(x.h)?x.h:[];x.h.push({v,t:today()});
   payI=-1;save();rJam();
  }
 };
})();
"""
marker = '</script>'
pos = html.rfind(marker)
if pos < 0: raise SystemExit('Could not locate script closing tag for association fix')
html = html[:pos] + association_fix + '\\n' + html[pos:]

p.write_text(html, encoding='utf-8')
