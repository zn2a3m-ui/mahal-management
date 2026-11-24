from pathlib import Path

p = Path('android/app/src/main/assets/index.html')
html = p.read_text(encoding='utf-8')

old_debt = 'const id=Date.now(),dt=$("cdd").value||today();C().debts.push({id,name:n,amt:a,date:dt,paid:false});/* تسجيل الدين لا يخصم نقداً من الصندوق؛ التسديد فقط يضاف للصندوق */$("cdn").value="";$("cda").value="";save();rCash()};'
new_debt = 'const id=Date.now(),dt=$("cdd").value||today();C().debts.push({id,name:n,amt:a,date:dt,paid:false,paidAmt:0});C().tx.push({id:id+1,kind:"out",label:"دين",desc:"دين على الزبون: "+n,amt:a,date:dt,debtId:id});$("cdn").value="";$("cda").value="";save();rCash()};'
if old_debt in html:
    html = html.replace(old_debt, new_debt, 1)

old_cash = 'function rCash(){let tin=0,tout=0,mout=0,b=Number(C().openingBalance)||0;const m=$("cmonth").value;\n C().tx.forEach(t=>{b+=t.kind==="in"?t.amt:-t.amt;if(t.kind==="in")tin+=t.amt;else{tout+=t.amt;if(t.date.slice(0,7)===m)mout+=t.amt}});'
new_cash = old_cash + '\n /* خصم الديون القديمة التي لم تُسجل لها حركة إنشاء في الصندوق */\n C().debts.forEach(d=>{if(!C().tx.some(t=>t.debtId===d.id&&t.label==="دين"))b-=Number(d.amt)||0});'
if old_cash in html:
    html = html.replace(old_cash, new_cash, 1)

start = html.index('function groupForm(){')
end = html.index('function personalDebtForm(){', start)
group_code = Path('patches/group.js').read_text(encoding='utf-8')
html = html[:start] + group_code + html[end:]
p.write_text(html, encoding='utf-8')
