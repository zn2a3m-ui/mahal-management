from pathlib import Path

p = Path('android/app/src/main/assets/index.html')
html = p.read_text(encoding='utf-8')

# Shop cash: new credit sales reduce cash; initial/partial repayments increase it.
old_add = """function addDebt(e){e.preventDefault();let amount=+da.value,paid=+dpaid.value;if(amount<=0||paid<0||paid>amount)return alert('تحقق من المبالغ');db.shop.debts.push({id:uid(),name:dn.value.trim(),phone:dp.value,amount,paid,date:dd.value,note:dnote.value,payments:paid?[{amount:paid,date:dd.value,note:'دفعة أولية'}]:[]});closeModal();save()}"""
new_add = """function addDebt(e){e.preventDefault();let amount=+da.value,paid=+dpaid.value;if(amount<=0||paid<0||paid>amount)return alert('تحقق من المبالغ');const id=uid(),date=dd.value;db.shop.debts.push({id,name:dn.value.trim(),phone:dp.value,amount,paid,date,note:dnote.value,cashApplied:true,payments:paid?[{amount:paid,date,note:'دفعة أولية'}]:[]});db.shop.cash.push({id:uid(),type:'out',title:'دين على الزبون: '+dn.value.trim(),amount,date,category:'دين زبون',note:'تسجيل دين جديد',debtId:id,created:Date.now()});if(paid>0)db.shop.cash.push({id:uid(),type:'in',title:'دفعة أولية من: '+dn.value.trim(),amount:paid,date,category:'تحصيل ديون',note:'دفعة عند إنشاء الحساب',debtId:id,created:Date.now()});closeModal();save()}"""
assert old_add in html, 'Original addDebt implementation not found'
html = html.replace(old_add, new_add, 1)

# Existing debts from earlier versions were not posted to cash. Deduct only their
# outstanding amount; new debts are marked cashApplied and are not deducted twice.
old_bal = "function bal(){return sum('in')-sum('out')}"
new_bal = "function legacyDebtCashBase(d){if(d.cashApplied)return 0;if(d.legacyCashBase===undefined){const initial=(d.payments||[]).filter(p=>p.note==='دفعة أولية'||p.note==='مدفوع سابقاً').reduce((a,p)=>a+(Number(p.amount)||0),0);d.legacyCashBase=Math.max(0,(Number(d.amount)||0)-initial)}return Number(d.legacyCashBase)||0}\\nfunction bal(){return sum('in')-sum('out')-db.shop.debts.reduce((a,d)=>a+legacyDebtCashBase(d),0)}"
assert old_bal in html, 'Original shop balance function not found'
html = html.replace(old_bal, new_bal, 1)

old_pay_tx = "db.shop.cash.push({id:uid(),type:'in',title:'تحصيل دين: '+d.name,amount:v,date:pd.value,category:'تحصيل ديون',note:'دفعة من حساب العميل',created:Date.now()})"
new_pay_tx = "db.shop.cash.push({id:uid(),type:'in',title:'تحصيل دين: '+d.name,amount:v,date:pd.value,category:'تحصيل ديون',note:'دفعة من حساب العميل',debtId:id,created:Date.now()})"
assert old_pay_tx in html, 'Original debt repayment cash movement not found'
html = html.replace(old_pay_tx, new_pay_tx, 1)

old_del = "function delDebt(id){if(confirm('حذف حساب الدين؟')){db.shop.debts=db.shop.debts.filter(x=>x.id!==id);save()}}"
new_del = "function delDebt(id){const d=db.shop.debts.find(x=>x.id===id);if(confirm('حذف حساب الدين؟')){if(d?.cashApplied)db.shop.cash=db.shop.cash.filter(x=>x.debtId!==id);db.shop.debts=db.shop.debts.filter(x=>x.id!==id);save()}}"
assert old_del in html, 'Original debt deletion function not found'
html = html.replace(old_del, new_del, 1)

group_code = Path('patches/group.js').read_text(encoding='utf-8')
marker = '</script>'
pos = html.rfind(marker)
if pos < 0:
    raise SystemExit('Could not locate application script closing tag')
html = html[:pos] + '\n' + group_code + '\n' + html[pos:]
p.write_text(html, encoding='utf-8')
