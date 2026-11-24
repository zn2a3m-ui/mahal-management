function groupForm(){modal('إنشاء جمعية',`<form onsubmit="addGroup(event)"><div class="field"><label>اسم الجمعية</label><input id="gn" required></div><div class="formgrid"><div class="field"><label>المبلغ الشهري الثابت للجمعية د.أ</label><input id="ga" type="number" min=".01" step=".01" value="40" required></div><div class="field"><label>بداية الجمعية</label><input id="gs" type="date" value="${today()}" required></div></div><div class="field"><label>أسماء الأعضاء (اختياري، كل اسم بسطر)</label><textarea id="gm" rows="4" placeholder="أحمد&#10;محمد&#10;خالد"></textarea></div><button class="btn" style="width:100%">إنشاء الجمعية</button></form>`)}
function addGroup(e){e.preventDefault();let names=gm.value.split(String.fromCharCode(10)).map(x=>x.trim()).filter(Boolean);db.groups.push({id:uid(),name:gn.value.trim(),amount:+ga.value,start:gs.value,members:names.map((name,i)=>({id:uid(),name,order:i+1})),expenses:[],status:'active'});closeModal();save()}
function month(g,n){let d=new Date(g.start+'T12:00:00');d.setMonth(d.getMonth()+n);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')}
function groupMonthsDue(g){const s=new Date(g.start+'T12:00:00'),t=new Date();if(Number.isNaN(s.getTime())||t<s)return 0;let n=(t.getFullYear()-s.getFullYear())*12+t.getMonth()-s.getMonth();if(t.getDate()<s.getDate())n--;return Math.max(0,n+1)}
function groupExpensesTotal(g){return (g.expenses||[]).reduce((a,x)=>a+(Number(x.amount)||0),0)}
function groupBalance(g){return groupMonthsDue(g)*(Number(g.amount)||40)-groupExpensesTotal(g)}
function renderGroups(){groupList.innerHTML=db.groups.length?db.groups.map(g=>`<div class="item"><div class="row"><div><b>${esc(g.name)}</b><div class="meta">إضافة شهرية ثابتة ${m(g.amount)} د.أ · ${groupMonthsDue(g)} شهر محتسب</div></div><span class="pill ${g.status==='closed'?'':'warn'}">${g.status==='closed'?'منتهية':'نشطة'}</span></div><div class="member"><span>رصيد الجمعية الحالي</span><b class="green">${m(groupBalance(g))} د.أ</b></div><div class="row" style="margin-top:9px"><button class="btn sm" onclick="groupDetails('${g.id}')">إدارة الجمعية</button><button class="btn light sm" onclick="toggleGroup('${g.id}')">${g.status==='closed'?'إعادة فتح':'إنهاء'}</button><button class="btn danger sm" onclick="delGroup('${g.id}')">حذف</button></div></div>`).join(''):'<div class="empty">لا توجد جمعيات. أنشئ جمعية للبدء.</div>'}
function groupDetails(id){let g=db.groups.find(x=>x.id===id);g.expenses=g.expenses||[];let due=groupMonthsDue(g),h=`<div class="item"><div class="member"><span>الإضافة الشهرية الثابتة</span><b>${m(g.amount)} د.أ</b></div><div class="member"><span>عدد الأشهر المحتسبة</span><b>${due}</b></div><div class="member"><span>إجمالي المبالغ المضافة</span><b class="green">${m(due*g.amount)} د.أ</b></div><div class="member"><span>إجمالي المصاريف والمشتريات</span><b class="red">${m(groupExpensesTotal(g))} د.أ</b></div><div class="member"><span>رصيد الجمعية الحالي</span><b class="green">${m(groupBalance(g))} د.أ</b></div></div><div class="row" style="margin:12px 0"><button class="btn" onclick="groupExpenseForm('${g.id}')">＋ تسجيل مصروف / مشتريات</button></div><h4>الإضافات الشهرية المحتسبة</h4>`;for(let i=0;i<due;i++)h+=`<div class="member"><span>${month(g,i)}</span><b class="green">+${m(g.amount)} د.أ</b></div>`;h+='<h4>سجل المصاريف والمشتريات</h4>'+(g.expenses.length?g.expenses.slice().sort((a,b)=>b.date.localeCompare(a.date)).map(x=>`<div class="member"><span>${esc(x.date)} · ${esc(x.title)}</span><b class="red">−${m(x.amount)} د.أ</b></div>`).join(''):'<div class="empty">لا توجد مصاريف مسجلة.</div>');if(g.members?.length)h+='<h4>الأعضاء</h4>'+g.members.map(x=>`<div class="member"><span>${x.order}. ${esc(x.name)}</span></div>`).join('');modal('إدارة · '+g.name,h)}
function groupExpenseForm(id){modal('تسجيل مصروف / مشتريات للجمعية',`<form onsubmit="addGroupExpense(event,'${id}')"><div class="field"><label>البيان</label><input id="gexTitle" required maxlength="100" placeholder="مشتريات أو مصروف"></div><div class="formgrid"><div class="field"><label>المبلغ د.أ</label><input id="gexAmount" type="number" min=".01" step=".01" required></div><div class="field"><label>التاريخ</label><input id="gexDate" type="date" value="${today()}" required></div></div><button class="btn" style="width:100%">حفظ وخصم من الرصيد</button></form>`)}
function addGroupExpense(e,id){e.preventDefault();let g=db.groups.find(x=>x.id===id),v=+gexAmount.value;if(!g||v<=0)return alert('تحقق من المبلغ');g.expenses=g.expenses||[];g.expenses.push({id:uid(),title:gexTitle.value.trim(),amount:v,date:gexDate.value});closeModal();save();groupDetails(id)}
function toggleGroup(id){let g=db.groups.find(x=>x.id===id);g.status=g.status==='closed'?'active':'closed';save()}
function delGroup(id){if(confirm('حذف الجمعية وسجلاتها؟')){db.groups=db.groups.filter(x=>x.id!==id);save()}}

// Fix the legacy association "المتبقي المتاح" calculation: add the fixed monthly
// association amount from the selected start date, then deduct purchases/expenses
// and the unpaid portion of advances. Collections are shown separately and are
// not added again, preventing double counting.
function jmonths(){
 const q=J().start.split("-"),s=new Date(Number(q[0]),Number(q[1])-1,Number(q[2]||1),12),n=new Date();
 if(Number.isNaN(s.getTime())||n<s)return 0;
 let count=(n.getFullYear()-s.getFullYear())*12+n.getMonth()-s.getMonth();
 if(n.getDate()<s.getDate())count--;
 return Math.max(0,count+1);
}
function jcalc(){
 if(!Number(J().monthly))J().monthly=40;
 J().d.forEach(x=>{if(x.r===undefined)x.r=x.paid?x.a:0});
 J().collections=J().collections||[];
 const m=jmonths(),tot=m*(Number(J().monthly)||40),col=jsum(J().collections),
 sp=jsum(J().p),repaid=J().d.reduce((t,x)=>t+(x.r||0),0),
 du=J().d.reduce((t,x)=>t+x.a-(x.r||0),0),
 rem=(Number(J().openingBalance)||0)+tot-sp-du;
 return{m,tot,col,sp,du,repaid,rem};
}
