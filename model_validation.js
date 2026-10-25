/* CIIP v1.6: independent issuer model audit & issue dashboard. */
let ciipValidation=null,ciipValidationError='';
async function refreshCiipValidation(){
 try{
  const r=await fetch('./audits/model_validation_latest.json?ts='+Date.now(),{cache:'no-store'});
  if(!r.ok)throw Error('HTTP '+r.status);
  const v=await r.json();
  if(v.schema!=='ciip-model-audit-v1')throw Error('Unexpected model audit schema');
  ciipValidation=v;ciipValidationError='';
 }catch(error){ciipValidation=null;ciipValidationError=String(error.message||error)}
 if(state.tab==='model_validation'||state.tab==='per_share')render();
}
function ciipValidationView(){
 const d=ciipValidation;
 if(!d)return '<section class="panel"><h2>Auditoría independiente de modelos</h2><div class="notice">El archivo de validación no está disponible: '+esc(ciipValidationError||'pendiente de generación')+'</div></section>';
 const issues=d.issue_log||[];
 const p0=issues.filter(x=>x.severity==='P0').length;
 const p1=issues.filter(x=>x.severity==='P1').length;
 const firms=Object.entries(d.issuers||{});
 const rows=firms.map(([ticker,item])=>
  '<tr><td><b>'+esc(ticker)+'</b><p class="muted tiny">'+esc(item.name)+'</p></td>'+
  '<td>'+esc(item.verdict)+'</td>'+
  '<td>'+item.P0+'</td><td>'+item.P1+'</td>'+
  '<td>'+ciipMoney(item.base_model_value_usd)+'</td>'+
  '<td><button class="btn secondary" data-ticker="'+esc(ticker)+'" onclick="ciipValAuditSelect(this.dataset.ticker)">Incidencias</button></td></tr>');
 const ticker=(d.issuers||{})[ciipAuditSelected]?ciipAuditSelected:firms[0]?.[0],c=d.issuers[ticker];
 const detailed=c?c.findings.map(x=>'<article class="ciip-result-card" style="padding:12px;margin-bottom:10px">'+
  '<div class="ciip-result-label"><b>'+esc(x.severity)+'</b> · '+esc(x.kind)+'</div>'+
  '<p>'+esc(x.detail)+'</p><p class="muted tiny">Impacto: '+esc(x.impact)+'</p>'+
  '<p class="muted tiny"><b>Corrección exigida:</b> '+esc(x.required_fix)+'</p>'+
  (x.source?'<a class="link tiny" rel="noopener noreferrer" target="_blank" href="'+esc(x.source)+'">Fuente oficial ↗</a>':'')+
  '</article>').join(''):'';
 const tests=c?c.checks.map(x=>'<li>'+ (x.pass?'✓':'✕')+' '+esc(x.name)+'</li>').join(''):'';
 return '<section class="panel"><h2>Auditoría de cinco valoraciones</h2><p><b>Dictamen global: no preparadas para decisiones de cartera.</b></p>'+
  '<p class="muted">Validación independiente de fórmulas, conciliación de CFO, CAPEX, adquisiciones, clases de acciones e hipótesis. Un cálculo correcto no valida el precio de compra.</p>'+
  '<div class="ciip-history-cards"><article class="panel"><span class="muted tiny">Compañías auditadas</span><h2>'+firms.length+'</h2></article>'+
  '<article class="panel"><span class="muted tiny">Incidencias críticas P0</span><h2>'+p0+'</h2></article>'+
  '<article class="panel"><span class="muted tiny">Incidencias mayores P1</span><h2>'+p1+'</h2></article></div>'+
  table(['Emisor','Dictamen','P0','P1','DCF base USD','Detalle'],rows)+
  '<p class="muted tiny">Última comprobación '+esc(d.as_of)+'. Los P0 bloquean el uso de los precios por acción como recomendaciones.</p></section>'+
  '<section class="panel"><h2>'+esc(ticker||'')+' · Incidencias y controles</h2>'+
  '<p class="muted">El modelo conserva los supuestos originales hasta superar las pruebas. Ninguna valoración está aprobada para comprar.</p>'+
  detailed+'<h3>Pruebas de cálculo y conciliación</h3><ul>'+tests+'</ul></section>';
}
function ciipValAuditSelect(ticker){ciipAuditSelected=ticker;render();}
function ciipAuditVerdict(ticker){
 const item=ciipValidation?.issuers?.[ticker];
 if(!item)return '<span class="muted tiny">Auditoría pendiente / no disponible</span>';
 return '<p class="muted tiny">Veredicto: <b>'+esc(item.verdict)+'</b> · '+item.P0+' bloqueos P0 · '+item.P1+' alertas P1. No apto para órdenes.</p>';
}
