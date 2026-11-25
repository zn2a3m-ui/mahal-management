// Association ledger patch for the actual J() data model used by the Android build.
// Monthly addition is a fixed 40 JOD per association, not per member.
// Collections remain visible as a separate record and are not counted twice.
function jcalc(){
 const D=J();
 D.monthly=40;
 D.p=Array.isArray(D.p)?D.p:[];
 D.d=Array.isArray(D.d)?D.d:[];
 D.collections=Array.isArray(D.collections)?D.collections:[];
 // Preserve legacy records: an old fully-paid advance may only have paid=true.
 // Normalize every repayment to the range 0..original advance amount.
 D.d.forEach(x=>{
  const principal=Math.max(0,Number(x.a)||0);
  const recorded=x.r===undefined?(x.paid?principal:0):(Number(x.r)||0);
  x.r=Math.min(principal,Math.max(0,recorded));
 });
 const m=jmonths(),tot=m*40,col=jsum(D.collections),sp=jsum(D.p),
 totalAdvances=D.d.reduce((t,x)=>t+(Number(x.a)||0),0),
 repaid=D.d.reduce((t,x)=>t+(Number(x.r)||0),0),
 du=Math.max(0,totalAdvances-repaid),
 // Each repayment restores exactly that amount to the association's available balance.
 // Equivalent to subtracting outstanding advances; keeps old records intact.
 rem=(Number(D.openingBalance)||0)+tot-sp-totalAdvances+repaid;
 return{m,tot,col,sp,du,repaid,rem};
}
J().monthly=40;
$("jmi").value="40";
$("jmi").readOnly=true;
$("jmi").oninput=function(){J().monthly=40;this.value="40";save();rJam()};
save();
rJam();
