// Association ledger patch for the actual J() data model used by the Android build.
// Monthly addition is a fixed 40 JOD per association, not per member.
// Collections remain visible as a separate record and are not counted twice.
function jcalc(){
 const D=J();
 D.monthly=40;
 D.p=Array.isArray(D.p)?D.p:[];
 D.d=Array.isArray(D.d)?D.d:[];
 D.collections=Array.isArray(D.collections)?D.collections:[];
 D.d.forEach(x=>{if(x.r===undefined)x.r=x.paid?x.a:0});
 const m=jmonths(),tot=m*40,col=jsum(D.collections),sp=jsum(D.p),
 repaid=D.d.reduce((t,x)=>t+(Number(x.r)||0),0),
 du=D.d.reduce((t,x)=>t+Math.max(0,(Number(x.a)||0)-(Number(x.r)||0)),0),
 rem=(Number(D.openingBalance)||0)+tot-sp-du;
 return{m,tot,col,sp,du,repaid,rem};
}
J().monthly=40;
$("jmi").value="40";
$("jmi").readOnly=true;
$("jmi").oninput=function(){J().monthly=40;this.value="40";save();rJam()};
save();
rJam();
