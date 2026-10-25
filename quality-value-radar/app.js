(() => {
'use strict';
const seed = window.QVR_SEED;
const baseQuotes = window.QVR_FALLBACK_QUOTES.quotes;
const STORAGE_KEY = 'quality-value-radar:v1';
const TODAY = () => { const p=Object.fromEntries(new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Madrid',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date()).filter(x=>x.type!=='literal').map(x=>[x.type,x.value])); return `${p.year}-${p.month}-${p.day}`; };
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtN = (v, digits=2) => Number(v).toLocaleString('es-ES',{minimumFractionDigits:digits,maximumFractionDigits:digits});
const money = (n,curr) => n==null || !Number.isFinite(+n) ? '—' : `${fmtN(n,Math.abs(n)>=1000?0:2)} ${curr||''}`;
const pct = v => v==null||!Number.isFinite(v) ? '—' : (v>=0?'+':'')+fmtN(v,1)+' %';
const selectOptions = (arr,current) => arr.map(o=>`<option value="${esc(o.value)}" ${o.value===current?'selected':''}>${esc(o.label)}</option>`).join('');
const L = (n)=>seed.investors.find(x=>x.id===n);
const issuer = s => companies().find(c=>c.s===s);
const initial = {watch:['CPRT','AMZN','CSU.TO'],page:'overview',settings:{hurdle:20},valuation:{},quoteOverrides:{},notes:{},custom:[],filters:{term:'',sector:'all',manager:'all',overlap:'all',sort:'matches'},selected:'CPRT'};
let state = load();
let remoteQuotes = {};
let autoAnalysis = {companies:{},unavailable:{},exclusions:{}};
let internationalResearch = {companies:{}};
let reliabilityV5 = {companies:{},counters:{},status:'pending_first_execution'};
let opportunityV6 = {models:{},researchRank:[],status:'pending_first_run'};
let backtestV6 = {tickers:{},status:'pending_first_run'};
let alertsV6 = {alerts:[]};
let sensitivityV7 = {models:{}};
let auditV8 = {companies:{}};
let economicV9 = {models:{}};
let auditV10 = {models:{}};
let reconciliationV11 = {models:{}};
let closeoutV12 = {models:{}};
let evidenceV13 = {models:{}};
let production = {state:'initializing',companies:{},coverage:{}};
let analysisStatus = 'Análisis fundamental todavía no cargado';
let quotationsNotice = 'Referencias fechadas; no son cotizaciones en directo';
let activeModal = null;
function load(){try{const z=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null'); if(z && typeof z==='object' && !Array.isArray(z)) return {...initial,...z,filters:{...initial.filters,...(z.filters||{})},settings:{...initial.settings,...(z.settings||{})}};}catch(e){}return structuredClone(initial);}
function persist(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));}catch(e){toast('No se pudo guardar: revisa espacio o privacidad de tu navegador.');}}
const companies = () => [...seed.companies,...state.custom];
const companyCount = id => companies().filter(c=>c.links.some(l=>l[0]===id)).length;
const links = c => c.links.map(([id,status])=>({investor:L(id),status})).filter(l=>l.investor);
const fullLinksCount = c => new Set(c.links.filter(l=>l[1]!=='historica').map(l=>l[0])).size;
const allLinksCount = c => new Set(c.links.map(l=>l[0])).size;
const overlap = c => fullLinksCount(c)>=2;
const quote = ticker => state.quoteOverrides[ticker] || remoteQuotes[ticker] || baseQuotes[ticker] || null;
const daysOld = date => {if(!date)return Infinity;const x=Date.parse(`${date}T00:00:00Z`);return Number.isFinite(x)?Math.max(0,Math.floor((Date.now()-x)/86400000)):Infinity;};
const quoteFresh = q => q&&Number(q.price)>0 && daysOld(q.date)<=7;
const valuation = c => {
  const d=state.valuation[c.s]||{};
  let fair=null,source='sin valorar';
  if(d.fair!=null && Number(d.fair)>0){fair=+d.fair;source='estimación introducida';}
  else if(d.eps>0&&d.exitPe>0&&d.years>0){ fair = (+d.eps*Math.pow(1+(+d.growth||0)/100,+d.years)*+d.exitPe)/Math.pow(1+(+d.discount||0)/100,+d.years);source='escenario PER'; }
  const q=quote(c.s);const difference=(fair>0 && q?.price>0) ? (1-q.price/fair)*100 : null;
  return {fair,source,difference,q,stale:!quoteFresh(q),hasModel:!!(d.eps>0&&d.exitPe>0&&d.years>0)};
};
function chipStatus(c,short=false){ const v=valuation(c);if(v.fair==null)return `<span class="pill neutral">Sin valorar</span>`;if(!v.q)return `<span class="pill amber">Falta precio</span>`;if(v.stale)return `<span class="pill amber">Precio caducado</span>`;if(v.difference>=+state.settings.hurdle)return `<span class="pill">${short?'Descuento':'Posible descuento'} ${fmtN(v.difference,0)} %</span>`;if(v.difference<0)return `<span class="pill red">Sobre valor propio ${fmtN(-v.difference,0)} %</span>`;return `<span class="pill blue">Descuento ${fmtN(v.difference,0)} %</span>`;}
function labelQuote(q){ if(!q)return 'Sin precio cargado';return `${q.kind==='cierre'?'Cierre':'Precio'} ${q.date} · ${q.source||'Fuente no especificada'}`; }
function watchButton(s){return `<button class="btn btn-quiet btn-sm" data-watch="${esc(s)}" title="Añadir o quitar de seguimiento" aria-label="${state.watch.includes(s)?'Quitar de':'Añadir a'} seguimiento">${state.watch.includes(s)?'★ Siguiendo':'☆ Seguir'}</button>`;}
function linkPills(c){return `<div class="badge-list">${links(c).map(({investor,status})=>`<span class="mini-badge ${status==='historica'?'historical':''}" title="${esc(investor.name)} · ${status}">${esc(investor.initials)} · ${status==='historica'?'hist.':status==='cobertura'?'cubierta':status==='fondo'?'fondo':'citada'}</span>`).join('')}</div>`;}
function topHeading(kicker,title,sub,right=''){return `<div class="page-intro"><div><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${sub}</p></div>${right}</div>`;}
function statCard(label,value,extra,cl=''){return `<article class="stat-card"><div class="stat-label">${label}</div><div class="stat-number ${cl}">${value}</div><div class="stat-detail">${extra}</div></article>`;}
function shortCandidate(c){let v=valuation(c);return `<div class="candidate-row"><div class="ticker-symbol">${esc(c.s.split('.')[0].slice(0,5))}</div><div><div class="candidate-name">${esc(c.n)}</div><div class="candidate-sub">${esc(c.sector)} · ${fullLinksCount(c)} fuentes no históricas${allLinksCount(c)>fullLinksCount(c)?' + histórica':''}</div></div><div class="candidate-right"><strong>${v.q?money(v.q.price,v.q.currency):'S/D'}</strong><small>${v.q?esc(v.q.date):'Sin cotización'}</small></div><button class="btn btn-quiet btn-sm" data-open="${esc(c.s)}">Ver</button></div>`;}

function reliabilityPanel(){
 const v=reliabilityV5;
 const c=v.counters||{};
 const examples=['CPRT','ADBE','INTU','ASML'];
 return '<section class="panel" style="margin:16px 0"><div class="panel-head"><div><h3>Auditoría de evidencias · v5</h3><p>Comprobación de adquisiciones, CAPEX y perspectivas de caja; no confundir hipótesis con datos auditados</p></div></div>'+
 '<div class="stat-grid">'+statCard('Empresas revisadas',c.companies??'—','US + cobertura internacional')+statCard('Guía financiera oficial',c.withGuidance??'—','Orientación de ingresos, no consenso')+statCard('ROI adquisiciones verificado',c.verifiedAcquisitionReturns??'—','Sin retorno inventado')+statCard('CAPEX desglosado acreditado',c.verifiedCapexSplits??'—','El no divulgado queda pendiente')+'</div>'+
 '<div class="table-wrap"><table class="data-table"><thead><tr><th>Empresa</th><th>Previsión</th><th>Adquisiciones</th><th>CAPEX</th></tr></thead><tbody>'+
 examples.map(t=>{const d=v.companies?.[t],m=d?.guidance,acq=d?.acquisitionCohorts||[];return '<tr><td><b>'+esc(t)+'</b></td><td>'+(m?'Ingresos '+fmtN(m.revenueLow,0)+'–'+fmtN(m.revenueHigh,0)+' M '+esc(m.unit)+' ('+m.fiscalYear+')':'Sin guía primaria validada')+'</td><td>'+(acq.length?'ROI realizado pendiente ('+acq.length+' eventos)':'Sin cohortes evaluables')+'</td><td>Sin desglose certificado</td></tr>'}).join('')+
 '</tbody></table></div><p class="tiny muted">Cualquier estimación basada en ingresos × margen histórico se etiqueta «modelo derivado»; no equivale a consenso de analistas. El radar no emite señales de compra hasta verificar retornos e inversión de mantenimiento.</p></section>';
}
async function refreshReliability(){
 try{const r=await fetch('data/reliability_v5.json',{cache:'no-store'});if(r.ok){const v=await r.json();if(v.schema==='qvr-v5-evidence')reliabilityV5=v;}}catch(e){}render();
}

function productionPanel(){
 const p=production||{},c=p.coverage||{},items=(p.focus||[]);
 const age=x=>x==null?'Sin datos':x===0?'Hoy':x+' días';
 const status=p.state==='operational'?'Operativo':p.state==='degraded'?'Datos parciales':'Inicializando';
 return '<section class="panel" style="margin-bottom:20px"><div class="panel-head"><div><h3>Estado operativo del radar</h3><p>Última sincronización '+esc(p.generatedAt||'pendiente')+' · '+esc(status)+'</p></div><span class="pill '+(p.state==='operational'?'':'amber')+'">'+esc(status)+'</span></div>'+
 '<div class="stat-grid">'+statCard('Cotizaciones recientes',c.quotesCurrent7d??'—','De '+(c.universe??'—')+' símbolos')+
 statCard('Modelos SEC',c.USSECModelAttempted??'—','Cobertura de investigación')+
 statCard('Modelos económicos',c.economicModels??'—','Escenarios sectoriales')+
 statCard('Precios certificados',c.investmentGradePriceCount??0,'Ninguna señal de compra automática')+'</div>'+
 '<div class="table-wrap"><table class="data-table"><thead><tr><th>Empresa</th><th>Último precio</th><th>Escenarios de estudio</th><th>Estado</th></tr></thead><tbody>'+
 items.map(t=>{const x=p.companies?.[t];if(!x)return '';
 const v=x.scenariosIllustrative||{};
 return '<tr><td><b>'+esc(t)+'</b><small> '+esc(x.name||'')+'</small></td>'+
 '<td>'+money(x.price,x.currency)+'<small> '+esc(x.priceDate||'—')+' · '+age(x.quoteAgeDays)+'</small></td>'+
 '<td>'+money(v.bear,x.currency)+' / '+money(v.base,x.currency)+' / '+money(v.bull,x.currency)+'</td>'+
 '<td><span class="pill amber">Revisión pendiente</span><small>'+esc(x.openEvidenceCount)+' incidencias documentales</small></td></tr>'
 }).join('')+'</tbody></table></div>'+
 '<p class="tiny muted">Los precios son cierres con fecha, no cotizaciones en tiempo real. Los escenarios no son valores de compra aprobados. La app no realiza operaciones ni envía avisos externos.</p></section>';
}
async function refreshProduction(){
 try{const r=await fetch('data/production_status.json',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);
 const d=await r.json();if(d.schema!=='qvr-production-v1')throw Error('Formato no válido');production=d;
 }catch(e){production={state:'degraded',companies:{},coverage:{},generatedAt:null};}render();
}

function evidenceV13Panel(){
 const d=evidenceV13.models||{}, names=['ADBE','INTU','CPRT','CSU.TO','ASML','DNP.WA'];
 return '<section class="panel" style="margin:18px 0"><div class="panel-head"><div><h3>Auditoría de evidencia v13</h3><p>Estado documental y correcciones contables; las valoraciones no constituyen recomendaciones de compra</p></div></div>'+
 '<div class="cards-3">'+names.filter(t=>d[t]).map(t=>{const x=d[t];return '<article class="stock-card"><div class="eyebrow">'+esc(t)+'</div><h3>Investigación pendiente</h3>'+
 (t==='DNP.WA'?'<p class="small">Flujo corregido por depreciación: '+money(x.baseModelAfterDepreciationFix,'PLN')+' (escenario, no precio aprobado)</p>':'')+
 '<div class="mini-note">'+esc((x.missingSourceItems||[]).slice(0,2).join('; '))+'</div></article>'}).join('')+'</div></section>';
}
async function refreshEvidenceV13(){
 try{const r=await fetch('data/evidence_audit_v13.json',{cache:'no-store'});if(r.ok){const d=await r.json();if(d.schema==='qvr-evidence-audit-v13')evidenceV13=d;}}catch(e){}render();
}

function closeoutV12Panel(){
 const m=closeoutV12.models||{};
 return '<section class="panel" style="margin:18px 0"><div class="panel-head"><div><h3>Cierre documental v12</h3><p>Partidas verificadas, balance de la fecha y discrepancias que impiden certificar el precio</p></div></div><div class="cards-3">'+['ADBE','INTU','CPRT','CSU.TO','ASML','DNP.WA'].filter(t=>m[t]).map(t=>{
 const x=m[t],status=x.status==='documentary_closed_conditional'?'Conciliación parcial':'Faltan datos materiales';
 return '<article class="stock-card"><div class="eyebrow">'+esc(t)+'</div><h3>'+status+'</h3><p class="small">Balance: '+esc(x.balanceDate||'—')+'</p>'+
 '<div class="mini-note">'+esc((x.remaining||[]).slice(0,3).join('; '))+'</div><p class="tiny muted">Precio aprobado: ninguno</p></article>';}).join('')+'</div>'+
 '<p class="tiny muted">No equivale a una valoración validada: nunca se combina deuda actual parcial con flujos antiguos sin conciliación, ni se suman saldos restringidos como caja del accionista.</p></section>';
}
async function refreshCloseoutV12(){
 try{const r=await fetch('data/closeout_v12.json',{cache:'no-store'});if(r.ok){const j=await r.json();if(j.schema==='qvr-closeout-v12')closeoutV12=j}}catch(e){}render();
}

function reconciliationV11Panel(){
 const m=reconciliationV11.models||{};
 return '<section class="panel" style="margin:18px 0"><div class="panel-head"><div><h3>Conciliaciones v11</h3><p>Correcciones matemáticas verificables y cuestiones documentales pendientes</p></div></div><div class="cards-3">'+['ADBE','INTU','CPRT','CSU.TO','ASML','DNP.WA'].filter(t=>m[t]).map(t=>{
 const x=m[t];return '<article class="stock-card"><div class="eyebrow">'+esc(t)+'</div><h3>'+esc(x.status||'pendiente')+'</h3><p class="small">Escenario base no aprobado: '+money(x.illustrativeBase,t==='CSU.TO'?'CAD':t==='DNP.WA'?'PLN':'USD')+'</p><div class="mini-note">'+esc((x.outstanding||[]).join('; '))+'</div></article>';}).join('')+'</div><p class="tiny muted">Un cambio de metodología no acredita el retorno realizado de inversiones ni reemplaza un estado proforma. No hay objetivos de compra autorizados.</p></section>';
}
async function refreshReconciliationV11(){
 try{const r=await fetch('data/reconciliation_v11.json',{cache:'no-store'});if(r.ok){const j=await r.json();if(j.schema==='qvr-reconciliation-v11')reconciliationV11=j}}catch(e){}render()
}

function financialAuditV10Panel(){
 const models=auditV10.models||{};
 const tickers=['ADBE','INTU','CPRT','CSU.TO','ASML','DNP.WA'];
 const arr=tickers.filter(t=>models[t]);
 return '<section class="panel" style="margin:18px 0"><div class="panel-head"><div><h3>Auditoría financiera v10</h3><p>Flujos FCFE frente a FCFF, deuda, caja y reinversión</p></div></div><div class="cards-3">'+arr.map(t=>{
  const d=models[t],b=d.balanceBridge||{};
  const bridge=(t==='ASML')?'<p class="small">Ajuste sin leases: '+fmtN(b.equityAdjustmentExcludingLeasesEURMillions,1)+' M EUR; con leases: '+fmtN(b.equityAdjustmentIncludingLeasesEURMillions,1)+' M EUR</p>':
   (t==='DNP.WA'?'<p class="small">Deuda neta con arrendamientos; ajuste final pendiente de coherencia FCFF.</p>':'<p class="small">Flujo del accionista aproximado: evitar volver a descontar deuda.</p>');
  return '<article class="stock-card"><div class="eyebrow">'+esc(t)+' · '+esc(d.basis||'')+'</div><h3>Sin objetivo aprobado</h3>'+bridge+
  '<p class="tiny muted">Balance '+esc(d.balanceAsOf||'—')+'</p><div class="mini-note">'+esc((d.unresolvedItems||[]).slice(0,2).join('; '))+'</div></article>';
 }).join('')+'</div><p class="tiny muted">Los puentes mostrados utilizan cortes financieros históricos que pueden no coincidir con el inicio del DCF. La falta de conciliación bloquea cualquier precio objetivo definitivo.</p></section>';
}
async function refreshFinancialAuditV10(){
 try{const r=await fetch('data/financial_audit_v10.json',{cache:'no-store'});if(r.ok){const x=await r.json();if(x.schema==='qvr-financial-bridge-v10')auditV10=x;}}catch(e){}render();
}

function economicV9Panel(){
 const m=economicV9.models||{},ticks=['ADBE','INTU','CPRT','CSU.TO','ASML','DNP.WA'];
 return '<section class="panel" style="margin:18px 0"><div class="panel-head"><div><h3>Economía del negocio · modelos sectoriales v9</h3><p>Escenarios derivados de indicadores operativos y de reinversión, no precios objetivo auditados</p></div></div><div class="cards-3">'+ticks.filter(t=>m[t]).map(t=>{
 const x=m[t],v=x.scenarios||{},old=x.legacyModelBaseValue;
 const cur=t==='CSU.TO'?'CAD':t==='DNP.WA'?'PLN':t==='ASML'?'USD':'USD';
 return '<article class="stock-card"><div class="eyebrow">'+esc(t)+' · '+esc(x.archetype)+'</div>'+
 '<div class="card-prices"><div><small>Modelo anterior</small><b>'+money(old,cur)+'</b></div><div><small>Escenario central v9</small><b>'+money(v.base?.valuePerShare,cur)+'</b></div></div>'+
 '<p class="small">Prudente '+money(v.bear?.valuePerShare,cur)+' · optimista '+money(v.bull?.valuePerShare,cur)+'</p>'+
 '<p class="tiny muted">Precio fechado '+esc(x.currentQuoteDate||'—')+': '+money(x.currentQuote,cur)+'</p>'+
 '<div class="mini-note">No aprobado para inversión: '+esc((x.missingEvidence||[]).slice(0,2).join('; '))+'</div></article>';
 }).join('')+'</div><p class="tiny muted">Hipótesis configuradas por negocio: ingresos y margen de caja de software; flujo incremental ACV; cohortes de adquisiciones CSU; margen operativo y reinversión de ASML; aperturas, productividad, CAPEX y circulante de Dino. Falta conciliar la estructura financiera y los retornos realizados.</p></section>';
}
async function refreshEconomicV9(){
 try{const r=await fetch('data/economic_v9.json',{cache:'no-store'});if(r.ok){const d=await r.json();if(d.schema==='qvr-economic-model-v9')economicV9=d;}}catch(e){}render();
}

function auditV8Panel(){
 const m=auditV8.companies||{};
 const tickers=['ADBE','INTU','CPRT'];
 return '<section class="panel" style="margin:18px 0"><div class="panel-head"><div><h3>Conciliación documental v8</h3><p>Acciones diluidas, recompras y adquisición ACV, sin recomendación de compra</p></div></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Empresa</th><th>Media diluida (M)</th><th>Acciones puntuales (M)</th><th>Conciliación</th></tr></thead><tbody>'+tickers.map(t=>{const x=m[t];return '<tr><td>'+esc(t)+'</td><td>'+fmtN(x?.annualWeightedDilutedSharesMillions,2)+'</td><td>'+fmtN(x?.outstandingSharesSnapshotMillions,2)+'</td><td>'+esc(x?.ledgerTieOut||'Pendiente')+'</td></tr>'}).join('')+'</tbody></table></div>'+
 '<p class="tiny muted">Las acciones puntuales y la media anual diluida no miden lo mismo. Las recompras consumen caja; las emisiones y la SBC requieren conciliación para evitar doble cómputo.</p>'+
 '<div class="mini-note">Copart / ACV: pago agregado de control según fuente aportada '+(m.CPRT?.acquisition?fmtN(m.CPRT.acquisition.closingAggregateUSDMillions,2)+' MUSD':'pendiente')+'. Umbral teórico de caja al 12%: '+(m.CPRT?.acquisition?fmtN(m.CPRT.acquisition.annualCashHurdle12PctUSDMillions,2)+' MUSD/año':'pendiente')+'. Retorno realizado no validado.</div></section>';
}
async function refreshAuditV8(){
 try{const r=await fetch('data/audit_v8.json',{cache:'no-store'});if(r.ok){const x=await r.json();if(x.schema==='qvr-v8-audit')auditV8=x}}catch(e){}render();
}

function sensitivityV7Panel(){
 const m=sensitivityV7.models||{};
 const items=['ADBE','INTU','CPRT','CSU.TO','ASML','DNP.WA'];
 const cards=items.filter(t=>m[t]).map(t=>{
  const x=m[t],units=x.currency||'';
  const cap=x.capex||{},dil=x.netShares||{},acq=x.acquisitions||{};
  const impact=(cap.reportedCapexStress||[]).map(y=>'<span>'+fmtN(y.changeInTotalCapexPct,0)+'% CAPEX: '+money(y.valuePerShare,units)+'</span>').join(' · ');
  const dilution=(dil.cases||[]).map(y=>'<span>'+fmtN(y.annualNetDilutedShareChangePct,1)+'%/año: '+money(y.valuePerShare,units)+'</span>').join(' · ');
  return '<article class="stock-card"><div class="eyebrow">'+esc(t)+' · sensibilidad</div><h3>Base '+money(x.baselineIndicativeValue,units)+'</h3>'+
  '<p class="small"><b>CAPEX (estrés, no desglose real):</b> '+(impact||esc(cap.reason||'No conciliado'))+'</p>'+
  '<p class="small"><b>Acciones netas:</b> '+(dilution||'Sin base armonizada')+'</p>'+
  '<p class="tiny muted"><b>Adquisiciones:</b> '+esc(acq.status||'Sin comprobación')+'</p>'+
  '<div class="mini-note">Sin precio de compra validado. Los escenarios son contrafactuales, no datos de la empresa.</div></article>';
 }).join('');
 return '<section class="panel" style="margin:18px 0"><div class="panel-head"><div><h3>Sensibilidad de valoración v7</h3><p>Inversiones, dilución y retorno sobre capital adquirido</p></div><span class="pill neutral">Sin señal automática</span></div>'+
 '<div class="cards-3">'+(cards||'<p>Resultados pendientes de primera ejecución</p>')+'</div>'+
 '<p class="tiny muted">Al reducir CAPEX sin modificar crecimiento, los flujos se exageran; el análisis también calcula un escenario que reduce el crecimiento junto a la inversión. Las emisiones de acciones y la compensación en acciones pueden solaparse: no sumar todos los impactos.</p></section>';
}
async function refreshSensitivityV7(){
 try{const r=await fetch('data/sensitivity_v7.json',{cache:'no-store'});if(r.ok){const d=await r.json();if(d.schema==='qvr-sensitivity-v7')sensitivityV7=d;}}catch(e){}render();
}

function opportunitiesV6Panel(){
 const v=opportunityV6||{},m=v.models||{},rank=v.researchRank||[];
 const cards=rank.map(t=>{
 const x=m[t]||{},confidence=x.confidence||{},price=x.price,entry=x.entryPrice,base=x.baseValue;
 const level=confidence.tier==='high'?'Alta':confidence.tier==='medium'?'Estimada':'Insuficiente';
 return '<article class="stock-card"><div class="eyebrow">'+esc(t)+' · '+esc(x.sector||'')+'</div><h3>'+esc(x.name||t)+'</h3>'+
 '<p class="tiny muted">Calidad: '+(x.qualityScore==null?'Sin puntuación':fmtN(x.qualityScore,0)+'/100')+' · Confianza: '+esc(level)+' ('+fmtN(confidence.score||0,0)+'/100)</p>'+
 '<div class="card-prices"><div><small>Precio '+esc(x.quoteDate||'no fechado')+'</small><b>'+money(price,x.currency)+'</b></div><div><small>Entrada ilustrativa</small><b>'+money(entry,x.currency)+'</b></div></div>'+
 '<p class="small">DCF base: '+money(base,x.currency)+' · margen vs base: '+pct(x.marginVsBasePct)+'</p>'+
 '<p class="small">IRR hipotética 5 años: '+pct(x.projectedIrrPct?.fiveYear)+' · 10 años: '+pct(x.projectedIrrPct?.tenYear)+'</p>'+
 '<p class="tiny muted">Escenarios: '+money(x.scenarios?.bear?.value,x.currency)+' / '+money(x.scenarios?.base?.value,x.currency)+' / '+money(x.scenarios?.bull?.value,x.currency)+'</p>'+
 '<div class="mini-note">'+esc((x.blockers||[]).slice(0,3).join('; ')||'Requiere revisión humana')+'</div></article>';
 }).join('');
 const tested=Object.values(backtestV6.tickers||{});
 return '<section class="panel" style="margin-bottom:18px"><div class="panel-head"><div><h3>Radar de oportunidades v6</h3><p>Escenarios, precios de entrada y ranking de investigación; no son recomendaciones de compra</p></div><span class="pill neutral">'+rank.length+' empresas prioritarias</span></div>'+
 '<div class="cards-3">'+(cards||'<p class="muted">Primera valoración en proceso</p>')+'</div>'+
 '<p class="tiny muted">Backtest histórico: '+tested.filter(x=>x.status==='measured').length+' de '+tested.length+' compañías con evidencia temporal suficiente. '+esc((backtestV6.limitations||[]).slice(0,2).join('; '))+'</p>'+
 '<p class="tiny muted">Alertas de estudio fechadas: '+(alertsV6.alerts||[]).length+'. Se registran dentro del radar; no se envían notificaciones externas.</p></section>';
}
async function refreshOpportunityV6(){
 try{
  const names=['opportunity_v6.json','backtest_v6.json','opportunity_alerts_v6.json'];
  const data=await Promise.all(names.map(async n=>{const r=await fetch('data/'+n,{cache:'no-store'});return r.ok?await r.json():null}));
  if(data[0]?.schema==='qvr-v6')opportunityV6=data[0];
  if(data[1]?.schema==='qvr-pit-backtest-v6')backtestV6=data[1];
  if(data[2]?.schema==='qvr-alerts-v6')alertsV6=data[2];
 }catch(e){}render();
}

function autoQualityPanel(){
  const entries=companies().map(c=>({c,a:autoAnalysis.companies?.[c.s]})).filter(x=>x.a);
  const ready=entries.filter(x=>x.a.status==='ready');
  const opportunities=ready.filter(x=>x.a.classification==='possible_discount' && x.a.adjustedRoic?.status==='available')
    .sort((a,b)=>(b.a.marginOfSafetyPct||0)-(a.a.marginOfSafetyPct||0));
  const unsupported=companies().length-ready.length;
  const card=(c,a)=>'<article class="stock-card"><div class="stock-card-title"><div><div class="eyebrow">'+esc(c.s)+' · SEC 10-K</div><h3>'+esc(c.n)+'</h3></div><span class="pill '+(a.classification==='possible_discount'?'':'amber')+'">'+(a.classification==='possible_discount'?'Posible descuento':'Revisar')+'</span></div>'+
    '<div class="card-prices"><div><small>Cierre '+esc(a.quote?.date||'sin fecha')+'</small><b>'+money(a.quote?.price,a.quote?.currency)+'</b></div><div><small>Valor modelo</small><b>'+money(a.fairValue,a.currency)+'</b></div></div>'+
    '<p class="stock-desc">Margen estimado: <b>'+pct(a.marginOfSafetyPct)+'</b> · FCF/acción norm.: '+money(a.normalizedFcfPerShare,a.currency)+' · P/FCF histórico mediano: '+(a.historicalPfcfMedian?fmtN(a.historicalPfcfMedian,1)+'×':'—')+'</p>'+
    '<div class="card-footer"><button class="btn btn-quiet btn-sm" data-auto-detail="'+esc(c.s)+'">Ver cálculo y advertencias →</button></div></article>';
  return '<section class="panel" style="margin-bottom:20px"><div class="panel-head"><div><h3>Motor de valoración automática</h3><p>'+esc(analysisStatus)+'</p></div><span class="pill neutral">'+ready.length+' / '+companies().length+' modelos completos</span></div>'+
    '<div class="info-note"><b>Filtro conservador:</b> flujo libre positivo en tres ejercicios, al menos tres múltiplos P/FCF históricos, ROIC ajustado NOPAT/capital invertido medio ≥15%, cotización reciente y margen mínimo del 25%. Si el cálculo es incompleto, no se clasifica como barata.</div>'+
    '<div class="stat-grid">'+
      statCard('Modelos completos',ready.length,'Comparables SEC 10-K y cotización fechada')+
      statCard('Posibles descuentos',opportunities.length,'Requieren revisión humana')+
      statCard('Sin cobertura completa',unsupported,'Excluidas o pendientes')+
      statCard('Tasa de descuento base','11,5 %','Hipótesis explícita, editable en código')+'</div>'+
    '<div class="cards-3">'+(opportunities.length?opportunities.map(({c,a})=>card(c,a)).join(''):'<div class="empty">Sin oportunidades que cumplan todos los requisitos. Esto no implica que las empresas estén caras.</div>')+'</div>'+
    productionPanel()+evidenceV13Panel()+closeoutV12Panel()+reconciliationV11Panel()+financialAuditV10Panel()+economicV9Panel()+opportunitiesV6Panel()+auditV8Panel()+sensitivityV7Panel()+reliabilityPanel()+internationalPanel()+
    '<details class="collapsible"><summary>Ver todas las valoraciones automáticas y datos insuficientes</summary><div class="table-wrap"><table class="data-table"><thead><tr><th>Empresa</th><th>Estado</th><th>Valor razonable*</th><th>Descuento</th><th></th></tr></thead><tbody>'+
    companies().map(c=>{const a=autoAnalysis.companies?.[c.s],reason=a?.reason||autoAnalysis.exclusions?.[c.s]||autoAnalysis.unavailable?.[c.s]||'Sin modelo verificable';return '<tr><td>'+esc(c.n)+' <small>'+esc(c.s)+'</small></td><td>'+(a?.status==='ready'?'Con modelo':esc(reason))+'</td><td>'+money(a?.fairValue,a?.currency)+'</td><td>'+pct(a?.status==='ready'?a.marginOfSafetyPct:null)+'</td><td>'+(a?'<button class="btn btn-quiet btn-sm" data-auto-detail="'+esc(c.s)+'">Detalles</button>':'—')+'</td></tr>'}).join('')+
    '</tbody></table></div></details><p class="tiny muted">* Mezcla 60% de DCF simplificado a 5 años sobre FCF normalizado y 40% de mediana histórica P/FCF, calculada con cotizaciones en fechas fiscales. No sustituye una valoración sectorial ni ajuste completo por deuda, SBC, adquisiciones o ciclo del capital de trabajo.</p></section>';
}
function internationalPanel(){
const list=Object.entries(internationalResearch.companies||{});
return '<section class="panel" style="margin:22px 0"><div class="panel-head"><div><h3>Valoraciones internacionales</h3><p>DCF de 5 años con flujos reportados por emisor, conversiones de moneda fechadas y sin señales automáticas</p></div></div><div class="cards-3">'+list.map(([ticker,c])=>{
 const v=c.valuation;
 const details=v?.status==='preliminary'
 ?'<div class="card-prices"><div><small>DCF base preliminar</small><b>'+money(v.base,v.tradingCurrency)+'</b></div><div><small>Cierre '+esc(v.quoteDate)+'</small><b>'+money(v.quotePrice,v.tradingCurrency)+'</b></div></div><p class="small">Distancia al valor base: '+pct(v.indicativeMarginPct)+'</p><p class="tiny muted">Prudente: '+money(v.bear,v.tradingCurrency)+' · Optimista: '+money(v.bull,v.tradingCurrency)+' · FX: '+fmtN(v.fx?.rate||1,4)+' ('+esc(v.fx?.date||'—')+')</p><div class="mini-note">Requiere revisión humana: '+esc(v.warning)+'</div><p class="tiny muted">Crecimiento FCF anual implícito en el precio: '+pct(v.marketImpliedFiveYearFcfGrowthPct)+' (reverse DCF; no es previsión de consenso)</p>'
 :'<p class="tiny muted">Pendiente de datos: '+esc(v?.reason||c.reason)+'</p>';
 return '<div class="stock-card"><div class="eyebrow">'+esc(ticker)+' · '+esc(c.reportPeriod)+'</div><h3>'+esc(c.name)+'</h3><p class="tiny muted">'+esc(c.country)+' · '+esc(c.standard)+' · '+esc(c.reportingCurrency)+'</p>'+details+'<p><a href="'+esc(c.sourceUrl)+'" rel="noopener noreferrer" target="_blank">Informe oficial ↗</a></p></div>';
}).join('')+'</div><p class="tiny muted">Los escenarios DCF internacionales no utilizan aún un P/FCF histórico independiente, y no califican automáticamente ninguna compañía como infravalorada.</p></section>';
}
function showAutoDetail(ticker){
 const a=autoAnalysis.companies?.[ticker];if(!a)return toast('No hay análisis automático completo.');
 const c=issuer(ticker);
 const safeLink=(url,label)=>/^https:\/\/(data\.sec\.gov|finance\.yahoo\.com)/.test(url||'')?'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+label+'</a>':'';
 const hist=(a.historicalPfcfObservations||[]).map(x=>'<tr><td>'+esc(x.fiscalEnd)+'</td><td>'+esc(x.priceDate)+'</td><td>'+fmtN(x.pfcf,2)+'×</td></tr>').join('');
 const html='<div class="eyebrow">Valoración económica · revisión requerida</div><h2>'+esc(c?.n||ticker)+' · '+esc(ticker)+'</h2>'+
 '<div class="info-note"><b>Estado:</b> '+esc(a.status)+' · '+esc(a.reason||'Modelo disponible para revisión')+'</div>'+
 '<div class="stat-grid">'+statCard('Escenario prudente',money(a.dcfBear,'USD'),'DCF supuesto conservador')+statCard('DCF central',money(a.dcfBase,'USD'),'5 años')+statCard('Escenario optimista',money(a.dcfBull,'USD'),'DCF supuesto optimista')+statCard('Valor validado',money(a.fairValue,'USD'),'Sin aprobación si falta SBC/M&A')+'</div>'+
 '<p>ROIC ajustado (mediana 3 años): <b>'+pct(a.adjustedRoic?.median3yPct)+'</b> · Trimestre/TTM: '+esc(a.recentFinancials?.periodEnd||'no disponible')+' ('+esc(a.recentFinancials?.status||'sin datos')+')</p>'+
 '<p>FCF/acción normalizado: <b>'+money(a.normalizedFcfPerShare,'USD')+'</b>. CAGR ingresos: '+pct(a.revenueCagrPct)+'. ROIC proxy mediano: '+pct(a.roicProxyMedianPct)+'. Deuda neta / FCF: '+(a.netDebtToFcf==null?'No comparable':fmtN(a.netDebtToFcf,2)+'×')+'.</p>'+
 '<p>Fecha último ejercicio: '+esc(a.fiscalEnd||'—')+'. Crecimiento base asumido: '+fmtN(a.assumptions?.baseGrowthPct||0,1)+'%; descuento 11,5%; crecimiento perpetuo 2,5%; descuento mínimo exigido 25%.</p>'+
 '<h3>Flujo de caja económico y contraste</h3><p>FCF del propietario / acción: '+money(a.economicReview?.ownerCashFlow?.normalizedOwnerFcfPerShare,'USD')+' · DCF con flujo ajustado: '+money(a.economicReview?.ownerCashFlow?.normalizedDcfBase,'USD')+' · Valor por múltiplo histórico: '+money(a.economicReview?.ownerCashFlow?.relativeHistoricalValue,'USD')+'</p><div class="mini-note">Situación: '+esc(a.economicReview?.status||'sin reconciliar')+' · '+esc((a.economicReview?.blocks||[]).join('; '))+'</div><h3>Múltiplos históricos por cierre fiscal</h3><div class="table-wrap"><table class="data-table"><thead><tr><th>Ejercicio</th><th>Fecha cotización</th><th>P/FCF</th></tr></thead><tbody>'+hist+'</tbody></table></div>'+
 '<p class="tiny muted">'+(a.warnings||[]).map(esc).join(' · ')+'</p><p class="small">'+safeLink(a.sourceUrl,'Estados financieros SEC ↗')+' · '+safeLink(a.priceHistoryUrl,'Histórico de cotización ↗')+'</p>'+
 '<div class="mini-note">Los cálculos del modelo anterior son orientativos. La señal de compra queda desactivada hasta conciliar SBC, adquisiciones y comparabilidad histórica.</div>';
 document.getElementById('modal-root').innerHTML='<div class="modal" role="dialog" aria-modal="true" aria-label="Detalle de valoración automática"><div class="modal-scroll">'+html+'</div><button class="btn btn-quiet" id="close-modal">Cerrar</button></div>';
 document.getElementById('modal-root').classList.remove('hidden');
 activeModal=null;
}
async function refreshInternational(){try{if(location.protocol==='file:')return;const r=await fetch('data/international.json',{cache:'no-store'});if(r.ok){const d=await r.json();if(d.schema==='qvr-international-v1')internationalResearch=d;}}catch(e){}render();}
async function refreshAutoAnalysis(){
 try{
  if(location.protocol==='file:')return;
  const r=await fetch('data/intrinsic.json',{cache:'no-store'});
  if(!r.ok)throw Error('HTTP '+r.status);
  const j=await r.json();
  if(j.schema!=='qvr-auto-v1'||!j.companies)throw Error('Formato no compatible');
  autoAnalysis=j;
  analysisStatus='Última ejecución: '+(j.generatedAt||'fecha desconocida')+' · '+Object.keys(j.companies).length+' análisis consultados';
 }catch(e){analysisStatus='Motor SEC pendiente de primera ejecución; ningún descuento se calcula automáticamente';}
 render();
}

function pageOverview(){const countAll=companies().length;const multi=companies().filter(overlap);
const focus=['CPRT','AMZN','CSU.TO'].map(issuer).filter(Boolean);
return `${topHeading('Visión general · '+TODAY(),'Un mapa para invertir con criterio','Rastrea empresas seguidas por inversores de calidad y valor, separando coincidencia, calidad y precio.','<button class="btn" data-page="radar">Abrir radar <span aria-hidden="true">↗</span></button>')}
<section class="hero"><div><div class="eyebrow">QUALITY FIRST · PRICE ALWAYS</div><h2>Grandes negocios.<br>Solo a precios que tengan sentido.</h2><p>Una coincidencia entre inversores es una pista para investigar, no una señal automática de compra. Antes de clasificar una empresa como barata, calcula un valor razonable propio y verifica su cotización.</p><div class="hero-highlight"><span class="pill">◈ Prioridad: Copart</span><span class="pill neutral">Inversión 5–10 años</span><span class="pill amber">Fuentes y fechas visibles</span></div></div><div style="min-width:205px;align-self:center"><div class="eyebrow">Proceso</div><div class="interactive-spark" aria-hidden="true">${[35,60,44,69,61,82,70,100,76].map(n=>`<i style="height:${n}%"></i>`).join('')}</div><div class="year-note" style="margin-top:9px">Investigación → valoración → disciplina</div></div></section>
<div class="stat-grid">${statCard('Empresas identificadas',countAll,'Universo proporcionado por el usuario')}${statCard('Fuentes / inversores',seed.investors.length,'Referencias actuales e históricas')}${statCard('Coincidencias no históricas',multi.length,'Sin contar dos fondos de una gestora','accent')}${statCard('Con precio fechado',companies().filter(c=>!!quote(c.s)).length,'Solo algunas cotizaciones verificadas')}</div>
<div class="twocol"><section class="panel"><div class="panel-head"><div><h3>Empresas prioritarias para estudiar</h3><p>Ordenadas por la convergencia de referencias y el interés cualitativo</p></div><button class="mini-action" data-page="radar">Ver radar →</button></div>${focus.map(shortCandidate).join('')}<div class="info-note" style="margin-top:18px">La posición de Amazon en Nick Sleep es <b>histórica</b>. Para Constellation Software no se ha acreditado una segunda posición. Solo Copart aparece expresamente en dos listas no históricas del material suministrado.</div></section><section class="panel"><div class="panel-head"><div><h3>Marco de decisión</h3><p>Seis comprobaciones antes de invertir</p></div></div><div class="method-list">${[
['01','Entender el negocio','Dónde gana dinero, unidad económica y clientes.'],
['02','Identificar el moat','Costes de cambio, efecto red, escala, marca o regulación.'],
['03','Evaluar rentabilidad','ROIC ajustado y reinversión, no ratios aislados.'],
['04','Examinar el balance','FCF, deuda y escenarios desfavorables.'],
['05','Valorar por escenarios','Modelo explícito, supuestos y margen de seguridad.'],
['06','Decidir o esperar','Ninguna obligación de comprar cada semana.']].map(x=>`<div class="method-step"><span class="step-no">${x[0]}</span><div><b>${x[1]}</b><p>${x[2]}</p></div></div>`).join('')}</div></section></div>
<div class="section-row"><div><h2>Tres negocios bajo vigilancia</h2><p>Los datos de calidad son apreciaciones cualitativas iniciales, no ROIC verificado.</p></div></div><div class="cards-3">${focus.map(companyCard).join('')}</div>`;
}
function companyCard(c){const q=quote(c.s),v=valuation(c);return `<article class="stock-card"><div class="stock-card-title"><div><div class="eyebrow">${esc(c.s)} · ${esc(c.country)}</div><h3>${esc(c.n)}</h3><p>${esc(c.sector)}</p></div><div title="Evaluación editorial inicial: no sustituye ROIC"> <span class="quality-number">${c.quality}</span><span class="muted tiny"> / 100</span></div></div><p class="stock-desc">${esc(c.moat)}</p><div class="card-prices"><div><small>Último precio</small><b>${q?money(q.price,q.currency):'No disponible'}</b><small>${q?esc(q.date):'—'} ${q&&!quoteFresh(q)?' · antiguo':''}</small></div><div style="text-align:right"><small>Valor propio</small><b>${v.fair?money(v.fair,q?.currency||c.currency):'—'}</b><small>${v.fair?v.source:'Pendiente'}</small></div></div><div class="card-footer">${chipStatus(c,true)}<button class="btn btn-quiet btn-sm" data-open="${esc(c.s)}">Abrir ficha →</button></div></article>`;}
function pageRadar(){const ordered=companies().filter(c=>allLinksCount(c)>=2).sort((a,b)=>fullLinksCount(b)-fullLinksCount(a)||b.quality-a.quality);
return `${topHeading('Investment radar','Coincidencias entre inversores','Distingue las coincidencias de listas no históricas, las referencias pasadas y las empresas de interés en seguimiento.')}\n${autoQualityPanel()}
<div class="info-note" style="margin-bottom:19px"><b>Regla de conteo:</b> distintos gestores, no distintos fondos. «Cubierta» no equivale a tenencia y «histórica» no se contabiliza como actual. Las listas del usuario no han sido contrastadas contra todas las declaraciones originales.</div>
<div class="cards-3">${ordered.length?ordered.map(companyCard).join(''):'<div class="empty">Sin coincidencias.</div>'}${issuer('CSU.TO') ? companyCard(issuer('CSU.TO')) : ''}</div>
<div class="twocol" style="margin-top:21px"><section class="panel"><div class="panel-head"><div><h3>Lectura de las coincidencias</h3><p>Prioridades de diligencia</p></div></div><div class="method-list"><div class="method-step"><span class="step-no">A</span><div><b>Copart · coincidencia expresa</b><p>Aparece en las listas de Galician Investor y Best Anchor Stocks proporcionadas. Conviene revisar resultados operativos recientes y valoración.</p></div></div><div class="method-step"><span class="step-no">B</span><div><b>Amazon · coincidencia mixta</b><p>Best Anchor Stocks la menciona y Nick Sleep fue inversor histórico. No se demuestra que ambos la posean en 2026.</p></div></div><div class="method-step"><span class="step-no">C</span><div><b>Constellation · gran negocio a validar</b><p>Solo se identifica con Best Anchor Stocks en el listado facilitado. Debe confirmarse cualquier atribución a Giverny o RV Capital.</p></div></div></div></section>
<section class="panel"><div class="panel-head"><div><h3>Configuración del radar</h3><p>Parámetros de valoración</p></div></div><div class="field"><label for="hurdle">Margen mínimo para destacar descuento (%)</label><input type="number" min="0" max="90" step="1" id="hurdle" value="${esc(state.settings.hurdle)}"></div><div class="mini-note" style="margin-top:15px">Una cotización baja respecto a su máximo no demuestra infravaloración. La etiqueta de descuento necesita un valor razonable calculado y una cotización fechada reciente.</div><div class="actions-row" style="margin-top:15px"><button class="btn" data-page="valuation">Calcular valor razonable</button></div></section></div>`;
}
function pageUniverse(){const f=state.filters;
const sectores=['all',...new Set(companies().map(x=>x.sector))].sort();
const sectorOpts=sectores.map(s=>({value:s,label:s==='all'?'Todos los sectores':s}));
const investorOpts=[{value:'all',label:'Todos los inversores'},...seed.investors.map(x=>({value:x.id,label:x.name}))];
let arr=companies().filter(c=> {
 const hay=`${c.n} ${c.s} ${c.country} ${c.sector} ${c.moat}`.toLowerCase();
 return (!f.term||hay.includes(f.term.toLowerCase()))&&(f.sector==='all'||c.sector===f.sector)&&(f.manager==='all'||c.links.some(l=>l[0]===f.manager))&&(f.overlap==='all'||(f.overlap==='true'&&overlap(c))||(f.overlap==='mixed'&&allLinksCount(c)>=2)||(f.overlap==='watch'&&state.watch.includes(c.s)));
});
const sorts={matches:(a,b)=>fullLinksCount(b)-fullLinksCount(a)||b.quality-a.quality,quality:(a,b)=>b.quality-a.quality,name:(a,b)=>a.n.localeCompare(b.n),discount:(a,b)=>(valuation(b).difference??-999)-(valuation(a).difference??-999)};
arr.sort(sorts[f.sort]||sorts.matches);
return `${topHeading('Stock universe','Empresas en seguimiento','Directorio inicial de todas las compañías mencionadas. Precios y modelos se completan progresivamente.','<button class="btn btn-secondary" data-add-company="1">+ Añadir empresa</button>')}
<section class="panel"><div class="panel-head"><div><h3>Explorador de compañías</h3><p>${arr.length} resultados · puntuación cualitativa de orientación, no recomendación</p></div><button class="btn btn-quiet btn-sm" data-export-csv="1">↓ Exportar CSV</button></div>
<div class="filterbar"><input type="search" id="search-company" placeholder="Buscar empresa, ticker o sector…" value="${esc(f.term)}" aria-label="Buscar empresas"><select id="filter-sector" aria-label="Filtrar sector">${selectOptions(sectorOpts,f.sector)}</select><select id="filter-manager" aria-label="Filtrar inversor">${selectOptions(investorOpts,f.manager)}</select><select id="filter-overlap" aria-label="Filtrar coincidencias">${selectOptions([{value:'all',label:'Todas'}, {value:'true',label:'Dos listas no históricas'}, {value:'mixed',label:'Incluye referencias históricas'}, {value:'watch',label:'Mis seguidas'}],f.overlap)}</select><select id="filter-sort" aria-label="Ordenar">${selectOptions([{value:'matches',label:'Por coincidencia'}, {value:'quality',label:'Por calidad inicial'}, {value:'name',label:'Alfabético'}, {value:'discount',label:'Por descuento propio'}],f.sort)}</select></div>
<div class="table-wrap"><table class="data-table"><thead><tr><th>Empresa / ticker</th><th>Sector</th><th>Inversores / referencias</th><th class="num">Calidad*</th><th class="num">Precio y fecha</th><th>Valoración</th><th></th></tr></thead><tbody>${arr.map(c=>{const q=quote(c.s);return `<tr><td><button class="link-button" data-open="${esc(c.s)}">${esc(c.n)}</button><div class="table-ticker">${esc(c.s)}</div></td><td>${esc(c.sector)}</td><td>${linkPills(c)}</td><td class="num"><span class="quality-number">${c.quality}</span>/100</td><td class="num">${q?`<b>${money(q.price,q.currency)}</b><div class="year-note">${esc(q.date)} ${quoteFresh(q)?'':'· antiguo'}</div>`:'<span class="muted">S/D</span>'}</td><td>${chipStatus(c,true)}</td><td><button class="btn btn-quiet btn-sm" data-watch="${esc(c.s)}">${state.watch.includes(c.s)?'★':'☆'}</button></td></tr>`;}).join('')}</tbody></table></div>
${arr.length?'':'<div class="empty">No hay empresas que cumplan los filtros.</div>'}<p class="tiny muted" style="margin-top:12px">* Puntuaciones de análisis cualitativo inicial, no métricas financieras auditadas.</p></section>`;
}
function pageInvestors(){return `${topHeading('La red de gestores','Inversores de referencia','Inspiración de carteras y metodologías con atribuciones delimitadas por su evidencia y antigüedad.')}
<div class="investor-grid">${seed.investors.map(x=>`<article class="investor-card"><div class="investor-head"><span class="investor-avatar">${esc(x.initials)}</span><div><div class="investor-name">${esc(x.name)}</div><div class="investor-method">${esc(x.method)}</div></div></div><p class="investor-detail">${esc(x.detail)}</p><div class="investor-foot"><span>${companyCount(x.id)} nombres asociados</span><button class="mini-action" data-filter-investor="${x.id}">Ver empresas →</button></div></article>`).join('')}</div>
<div class="panel" style="margin-top:19px"><div class="panel-head"><div><h3>Reglas de procedencia</h3><p>Por qué hacemos explícita la diferencia entre analizar y mantener</p></div></div><p class="small muted">Una lista de valores «en cartera / cubiertos» no es un informe regulatorio de posiciones. Los fondos de Cobas son varios productos de una misma gestora y no deben contar como varios inversores independientes. Las carteras históricas de Nick Sleep tampoco acreditan participaciones presentes.</p><p class="small muted">Para pasar de “referenciado” a “posición confirmada” haría falta documento del inversor y fecha: carta de accionistas, informe trimestral/semestral o registro 13F cuando sea aplicable. Las posiciones 13F solo recogen determinadas acciones estadounidenses y tienen retraso.</p></div>`;}
function pageValuation(){const c=issuer(state.selected)||companies()[0];if(!c)return '<div>Sin empresas</div>';const q=quote(c.s);const d=state.valuation[c.s]||{};const growth=d.growth??9;const disc=d.discount??10;const term=d.exitPe??24;const yrs=d.years??5;const val=valuation(c);
const eps=Number(d.eps||0),fv=(eps>0?eps*Math.pow(1+growth/100,yrs)*term/Math.pow(1+disc/100,yrs):null);
let scenario='<div class="empty"><span class="empty-icon">∑</span><strong>Introduce un beneficio normalizado por acción</strong>El sistema calculará tres escenarios transparentes y un precio actual descontado.</div>';
if(eps>0){const mults=[Math.max(5,+term-6),+term,+term+6],rates=[+growth-4,+growth,+growth+4];scenario=`<div class="table-wrap"><table class="scenario-table"><thead><tr><th>Crecimiento / PER salida</th>${mults.map(m=>`<th>${fmtN(m,0)}×</th>`).join('')}</tr></thead><tbody>${rates.map((g,i)=>`<tr><th>${fmtN(g,0)} % anual</th>${mults.map((m,j)=>{const p=eps*Math.pow(1+g/100,yrs)*m/Math.pow(1+disc/100,yrs);return `<td class="${i===1&&j===1?'mid':''}">${money(p,c.currency)}</td>`}).join('')}</tr>`).join('')}</tbody></table></div><p class="tiny muted">Cada casilla estima el valor actual de un precio de salida futuro: EPS normalizado × (1 + crecimiento)^años × PER de salida ÷ (1 + retorno exigido)^años. No incluye dividendos ni estructura de deuda.</p>`;}
return `${topHeading('Módulo de análisis','Valorador por escenarios','Modelo simplificado de beneficios normalizados (exit-PER). Es un filtro preliminar, no sustituye un DCF de flujos libres.')}
<div class="twocol"><section class="panel"><div class="panel-head"><div><h3>Supuestos de valoración</h3><p>Los cambios se guardan automáticamente en este dispositivo</p></div></div><div class="field"><label for="val-ticker">Compañía</label><select id="val-ticker">${selectOptions(companies().map(c=>({value:c.s,label:`${c.n} (${c.s})`})).sort((a,b)=>a.label.localeCompare(b.label)),c.s)}</select></div><div class="split-label">Escenario con múltiplo de salida</div><div class="control-grid"><div class="field"><label for="val-eps">EPS normalizado (${esc(c.currency)})</label><input type="number" id="val-eps" min="0" step="0.01" value="${esc(d.eps??'')}" placeholder="Sin dato" /></div><div class="field"><label for="val-growth">Crecimiento EPS %</label><input type="number" id="val-growth" min="-50" max="50" step="0.5" value="${growth}"></div><div class="field"><label for="val-pe">PER de salida</label><input type="number" id="val-pe" min="1" max="150" step="1" value="${term}"></div><div class="field"><label for="val-years">Años</label><input type="number" id="val-years" min="1" max="20" step="1" value="${yrs}"></div><div class="field"><label for="val-discount">Retorno exigido %</label><input type="number" id="val-discount" min="0" max="60" step="0.5" value="${disc}"></div><div class="field"><label for="val-fair">O valor razonable manual</label><input type="number" id="val-fair" min="0" step="0.01" value="${esc(d.fair??'')}" placeholder="Opcional"></div></div><div class="mini-note" style="margin:15px 0">El valor manual tiene prioridad sobre el modelo. El EPS debe estar documentado y ajustado a la divisa de cotización. Si el EPS es negativo, este método no es válido.</div><div class="actions-row"><button class="btn" id="save-valuation">Actualizar escenario</button><button class="btn btn-quiet" id="clear-valuation">Borrar valoración</button></div></section>
<section class="panel"><div class="panel-head"><div><h3>Resultado para ${esc(c.n)}</h3><p>Comparación entre cotización y valor propio</p></div></div><div class="result-grid" style="grid-template-columns:repeat(2,1fr)"><div class="result-tile"><small>Último precio</small><b>${q?money(q.price,q.currency):'—'}</b><div class="year-note">${q?esc(q.date):'Sin cotización'}</div></div><div class="result-tile"><small>Valor estimado</small><b>${val.fair?money(val.fair,c.currency):'—'}</b><div class="year-note">${val.source}</div></div></div><div style="margin:14px 0">${chipStatus(c)} ${q&&!quoteFresh(q)?'<span class="pill amber">Más de 7 días</span>':''}</div><div class="separator"></div><div class="panel-head" style="margin-bottom:10px"><div><h3>Sensibilidad</h3><p>Precio actual teórico para distintas hipótesis</p></div></div>${scenario}
<div class="actions-row" style="margin-top:20px"><button class="btn btn-secondary" data-open="${esc(c.s)}">Ficha de empresa</button><button class="btn btn-quiet" data-watch="${esc(c.s)}">${state.watch.includes(c.s)?'★ En seguimiento':'☆ Seguir'}</button></div></section></div>`;}
function pageSources(){return `${topHeading('Transparencia y mantenimiento','Fuentes y datos','Control de actualizaciones, entrada manual de cotizaciones y copia de seguridad para no depender de plataformas cerradas.')}
<div class="twocol"><section class="panel"><div class="panel-head"><div><h3>Estado de datos</h3><p>${esc(quotationsNotice)}</p></div></div><div class="info-note"><b>La app funciona sin backend.</b> Sus filtros, escenarios, seguimiento, importación y exportación operan localmente. Una tarea opcional de GitHub Actions puede actualizar <span class="mono">data/quotes.json</span> si los proveedores responden.</div><div class="split-label">Añadir o corregir un precio</div><div class="control-grid"><div class="field"><label for="quote-ticker">Ticker</label><select id="quote-ticker">${selectOptions(companies().map(c=>({value:c.s,label:c.s})),state.selected)}</select></div><div class="field"><label for="quote-price">Precio</label><input id="quote-price" type="number" min="0.0001" step="any" placeholder="Ej.: 28.50"></div><div class="field"><label for="quote-date">Fecha (AAAA-MM-DD)</label><input id="quote-date" type="date" value="${TODAY()}"></div></div><div class="actions-row" style="margin-top:14px"><button class="btn" id="save-quote">Guardar precio manual</button><button class="btn btn-secondary" id="remove-quote">Eliminar precio manual</button></div><div class="split-label">Importación por lotes</div><div class="field"><label for="quote-csv">Pega líneas: TICKER,PRECIO,FECHA (fecha ISO)</label><textarea id="quote-csv" placeholder="CPRT,28.15,2026-10-21&#10;AMZN,262.36,2026-10-21"></textarea></div><div class="actions-row" style="margin-top:10px"><button class="btn btn-secondary" id="import-quote-lines">Importar cotizaciones</button></div></section>
<section class="panel"><div class="panel-head"><div><h3>Persistencia y exportación</h3><p>Tu información permanece en el navegador hasta que la exportes</p></div></div><div class="method-list"><div class="method-step"><span class="step-no">↓</span><div><b>Copia de seguridad JSON</b><p>Incluye tus precios, escenarios, favoritos y notas; restaurable en otro dispositivo.</p></div></div><div class="method-step"><span class="step-no">⇥</span><div><b>Listado de empresas CSV</b><p>Para Excel o Google Sheets con codificación UTF-8.</p></div></div><div class="method-step"><span class="step-no">⟳</span><div><b>Actualización opcional vía GitHub</b><p>Workflow programado; los datos fallidos nunca se inventan.</p></div></div></div><div class="actions-row" style="margin-top:23px"><button class="btn" id="export-json">↓ Exportar JSON</button><button class="btn btn-secondary" id="export-csv">↓ Exportar CSV</button><label class="btn btn-quiet" for="restore-file">↑ Importar JSON</label><input id="restore-file" type="file" accept=".json,application/json" hidden></div><details class="collapsible"><summary>Reiniciar mis cambios</summary><div><p class="small muted">Restablece las valoraciones, notas, favoritos y precios editados. No elimina el universo inicial.</p><button class="btn btn-danger" id="reset-app">Restablecer mis datos</button></div></details></section></div>
<section class="panel"><div class="panel-head"><div><h3>Biblioteca de fuentes y advertencias</h3><p>Siempre comprobar fecha, alcance y fiabilidad antes de decidir</p></div></div>${seed.sources.map(s=>`<div class="source-card"><b>${s.url?`<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a>`:esc(s.title)}</b><small>${esc(s.kind)} · ${esc(s.date)}</small><p>${esc(s.description)}</p></div>`).join('')}<div class="mini-note" style="margin-top:18px">Los valores «futuros» de informes de terceros no son automáticamente valores intrínsecos presentes. La valoración requiere hipótesis actualizadas y sensibilidad a riesgos. No todos los mercados ofrecen precios gratis o licencias para redistribuirlos.</div></section>`;}
function modalFor(c){const d=seed.dossiers[c.s]||{};const q=quote(c.s),v=valuation(c);return `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><header><div><div class="eyebrow">FICHA DE INVERSIÓN · ${esc(c.s)}</div><h2 id="modal-title">${esc(c.n)}</h2><div class="muted small">${esc(c.sector)} · ${esc(c.country)}</div></div><button class="close-modal" id="close-modal" aria-label="Cerrar">×</button></header><main><div class="result-grid"><div class="result-tile"><small>Último precio</small><b>${q?money(q.price,q.currency):'—'}</b><div class="year-note">${q?esc(q.date):'Sin datos'}</div></div><div class="result-tile"><small>Calidad inicial*</small><b>${c.quality}/100</b><div class="year-note">Juicio cualitativo</div></div><div class="result-tile"><small>Valor propio</small><b>${v.fair?money(v.fair,c.currency):'—'}</b><div class="year-note">${v.source}</div></div></div><div class="detail-block"><h4>Ventaja competitiva potencial</h4><p>${esc(c.moat)}</p></div><div class="modal-cols"><div><div class="detail-block"><h4>Tesis preliminar</h4><p>${esc(d.summary||'Negocio en el universo inicial. Requiere documentación de estados financieros y análisis independiente.')}</p></div><div class="detail-block"><h4>Vigilancia / riesgos</h4><p>${esc(d.risk||'Valorar concentración de clientes, deuda, ciclo económico y presión competitiva.')}</p></div></div><div><div class="detail-block"><h4>Próxima comprobación</h4><p>${esc(d.check||'Identificar el ROIC histórico, FCF por acción, crecimiento normalizado y precio razonable.')}</p></div><div class="detail-block"><h4>Referencias a inversores</h4>${linkPills(c)}<p class="year-note" style="margin-top:9px">No implica que las acciones sigan en cartera.</p></div></div></div><div class="field"><label for="note-company">Mis notas sobre ${esc(c.s)}</label><textarea id="note-company" placeholder="Tesis, riesgos, fuente, decisión pendiente…">${esc(state.notes[c.s]||'')}</textarea></div><div class="actions-row" style="margin-top:16px">${watchButton(c.s)}<button class="btn btn-secondary" id="save-note">Guardar notas</button><button class="btn" data-valuate="${esc(c.s)}">Abrir valorador →</button></div><p class="tiny muted" style="margin-top:16px">* El 0–100 es un indicador editorial inicial. No expresa probabilidad de éxito ni retorno esperado.</p></main></div>`;}
function toast(msg){let el=document.createElement('div');el.className='toast';el.textContent=msg;document.getElementById('toasts').append(el);setTimeout(()=>el.remove(),4300);}
function showModal(s){const c=issuer(s);if(!c)return;activeModal=s;const root=document.getElementById('modal-root');root.innerHTML=modalFor(c);root.classList.remove('hidden');document.body.style.overflow='hidden';root.querySelector('.close-modal').focus();}
function closeModal(){activeModal=null;const root=document.getElementById('modal-root');root.classList.add('hidden');root.innerHTML='';document.body.style.overflow='';}
function navigate(p){const allowed=['overview','radar','universe','investors','valuation','sources'];state.page=allowed.includes(p)?p:'overview';persist();closeModal();render();window.scrollTo({top:0,behavior:'auto'});}
function render(){const body={overview:pageOverview,radar:pageRadar,universe:pageUniverse,investors:pageInvestors,valuation:pageValuation,sources:pageSources}[state.page]||pageOverview;document.getElementById('app').innerHTML=body();const labels={overview:'RESUMEN',radar:'RADAR',universe:'EMPRESAS',investors:'INVERSORES',valuation:'VALORACIÓN',sources:'FUENTES'};document.getElementById('crumb').textContent=labels[state.page]||'RADAR';document.querySelectorAll('[data-page]').forEach(b=>{b.classList.toggle('selected',b.dataset.page===state.page);b.classList.toggle('active',b.dataset.page===state.page)});document.getElementById('clock-chip').textContent=new Date().toLocaleDateString('es-ES',{timeZone:'Europe/Madrid',day:'2-digit',month:'short',year:'numeric'});}
function getValForm(){const g=id=>document.getElementById(id)?.value;return {eps:g('val-eps')===''?null:Number(g('val-eps')),growth:Number(g('val-growth')),exitPe:Number(g('val-pe')),years:Number(g('val-years')),discount:Number(g('val-discount')),fair:g('val-fair')===''?null:Number(g('val-fair'))};}
function saveVal(){const d=getValForm();if((d.eps!=null && d.eps<0)||(d.fair!=null&&d.fair<=0)||d.exitPe<1||d.years<1||d.years>20||d.discount<0||d.growth<=-100){toast('Revisa los supuestos: alguno no es válido.');return;}state.valuation[state.selected]=d;persist();render();toast('Valoración guardada.');}
function download(name,contents,mime='text/plain'){let blob=new Blob([contents],{type:mime});let url=URL.createObjectURL(blob);let a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1200);}
function exportJson(){download('quality-value-radar-backup.json',JSON.stringify({format:'quality-value-radar',version:1,exportedAt:new Date().toISOString(),state},null,2),'application/json;charset=utf-8');toast('Copia JSON creada.');}
function exportCsv(){const rows=[['Ticker','Empresa','Sector','País','Inversores','Calidad editorial','Precio','Divisa','Fecha precio','Valor propio','Descuento %','Precio actualizado'],...companies().map(c=>{const q=quote(c.s),v=valuation(c);return [c.s,c.n,c.sector,c.country,links(c).map(l=>l.investor.name+' ('+l.status+')').join(' | '),c.quality,q?.price??'',q?.currency??c.currency,q?.date??'',v.fair??'',v.difference??'',quoteFresh(q)?'Sí':'No'];})];const csv=rows.map(row=>row.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(';')).join('\r\n');download('quality-value-radar-empresas.csv','\uFEFF'+csv,'text/csv;charset=utf-8');toast('CSV creado para Excel.');}
function saveQuote(ticker,price,date,source='Manual',sourceUrl=''){const c=issuer(ticker);if(!c||!Number.isFinite(price)||price<=0||!/^\d{4}-\d\d-\d\d$/.test(date)||!Number.isFinite(Date.parse(date))||date>TODAY())return false;state.quoteOverrides[ticker]={price,date,currency:c.currency,source,sourceUrl,kind:'cierre'};return true;}
function importQuoteLines(){const v=document.getElementById('quote-csv').value.trim();let ok=0,bad=0;for(const line of v.split(/\r?\n/)){if(!line.trim())continue;const p=line.split(/[,;\t]/).map(x=>x.trim());const success=p.length>=3&&saveQuote(p[0].toUpperCase(),Number(p[1].replace(',','.')),p[2], 'Importación manual');success?ok++:bad++;}persist();render();toast(`${ok} precios importados${bad?` · ${bad} rechazados`:''}`);}
async function restoreJson(file){try{const data=JSON.parse(await file.text());if(data?.format!=='quality-value-radar'||data.version!==1||!data.state||!Array.isArray(data.state.watch)||typeof data.state.valuation!=='object'||typeof data.state.quoteOverrides!=='object')throw Error('Formato incompatible');if(!confirm('¿Restaurar esta copia y reemplazar tus cambios locales?'))return;state={...structuredClone(initial),...data.state,filters:{...initial.filters,...data.state.filters},settings:{...initial.settings,...data.state.settings}};persist();render();toast('Copia restaurada.');}catch(err){toast('No se pudo importar el archivo JSON.');}}
function addCompanyModal(){const root=document.getElementById('modal-root');root.innerHTML=`<div class="modal" role="dialog" aria-modal="true"><header><div><div class="eyebrow">EXPANDIR UNIVERSO</div><h2>Añadir empresa</h2></div><button class="close-modal" id="close-modal" aria-label="Cerrar">×</button></header><main><div class="control-grid"><div class="field"><label for="new-ticker">Ticker</label><input id="new-ticker" placeholder="EJEMPLO.US" maxlength="24"></div><div class="field"><label for="new-name">Empresa</label><input id="new-name" placeholder="Nombre"></div><div class="field"><label for="new-curr">Divisa</label><select id="new-curr">${selectOptions(['USD','EUR','CAD','GBP','GBp','JPY','PLN','SEK','NOK','HKD','BRL'].map(s=>({value:s,label:s})),'USD')}</select></div><div class="field"><label for="new-sector">Sector</label><input id="new-sector" placeholder="Software"></div><div class="field"><label for="new-country">País</label><input id="new-country" placeholder="España"></div><div class="field"><label for="new-quality">Calidad inicial (0–100)</label><input id="new-quality" type="number" min="0" max="100" value="50"></div></div><div class="field" style="margin-top:12px"><label for="new-moat">Ventaja competitiva a comprobar</label><textarea id="new-moat"></textarea></div><div class="field" style="margin-top:12px"><label for="new-investor">Inversor que menciona la empresa</label><select id="new-investor"><option value="">Ninguno / pendiente</option>${seed.investors.map(i=>`<option value="${i.id}">${esc(i.name)}</option>`).join('')}</select></div><div class="actions-row" style="margin-top:18px"><button class="btn" id="submit-company">Añadir al radar</button><button class="btn btn-quiet" id="close-modal-alt">Cancelar</button></div></main></div>`;root.classList.remove('hidden');document.body.style.overflow='hidden';root.querySelector('#new-ticker').focus();}
function saveCustomCompany(){const g=id=>document.getElementById(id)?.value.trim();const s=g('new-ticker').toUpperCase().replace(/\s/g,'');const name=g('new-name'),quality=Number(g('new-quality'));if(!/^[A-Z0-9.\-]{1,24}$/.test(s)||!name||issuer(s)||!Number.isFinite(quality)||quality<0||quality>100){toast('Ticker existente o datos no válidos.');return;}const investor=g('new-investor');state.custom.push({s,n:name,sector:g('new-sector')||'Otros',country:g('new-country')||'No indicado',currency:g('new-curr')||'USD',quality,moat:g('new-moat')||'Pendiente de estudio',links:investor?[[investor,'referencia']]:[]});persist();closeModal();navigate('universe');toast('Empresa añadida al universo.');}
async function refreshQuotes(){if(location.protocol==='file:'){quotationsNotice='Abierto como archivo local: las cotizaciones se leen de la copia de referencia.';return;}try{const r=await fetch('data/quotes.json',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(typeof d?.quotes!=='object'||!d.quotes)throw Error('Datos inválidos');const good={};for(const [s,q] of Object.entries(d.quotes)){if(issuer(s)&&q&&Number(q.price)>0&&/^\d{4}-\d\d-\d\d$/.test(q.date)&&typeof q.currency==='string'){good[s]=q;}}remoteQuotes=good;quotationsNotice=`Cotizaciones publicadas en archivo · ${d.generatedAt||d.asOf||'fecha desconocida'} · ${Object.keys(good).length} símbolos`;}catch(err){quotationsNotice='Usando cotizaciones de referencia incluidas; la actualización automática aún no está disponible.';}render();}

document.addEventListener('click',ev=>{const b=ev.target.closest('button,label');if(!b)return;const page=b.closest('[data-page]');if(page){navigate(page.dataset.page);return;}if(b.dataset.autoDetail){showAutoDetail(b.dataset.autoDetail);return;}if(b.dataset.open){showModal(b.dataset.open);return;}if(b.dataset.watch){let ticker=b.dataset.watch;state.watch=state.watch.includes(ticker)?state.watch.filter(x=>x!==ticker):[...state.watch,ticker];persist();if(activeModal)showModal(activeModal);else render();toast(state.watch.includes(ticker)?'Añadida al seguimiento':'Retirada del seguimiento');return;}if(b.id==='close-modal'||b.id==='close-modal-alt'){closeModal();return;}if(b.id==='save-note'){state.notes[activeModal]=document.getElementById('note-company').value;persist();toast('Notas guardadas.');return;}if(b.dataset.valuate){state.selected=b.dataset.valuate;navigate('valuation');return;}if(b.dataset.filterInvestor){state.filters.manager=b.dataset.filterInvestor;navigate('universe');return;}if(b.dataset.addCompany){addCompanyModal();return;}if(b.id==='submit-company'){saveCustomCompany();return;}if(b.id==='save-valuation'){saveVal();return;}if(b.id==='clear-valuation'){if(confirm('¿Eliminar la valoración de esta empresa?')){delete state.valuation[state.selected];persist();render();}return;}if(b.id==='save-quote'){const g=id=>document.getElementById(id).value;let success=saveQuote(g('quote-ticker'),Number(g('quote-price')),g('quote-date'));if(success){persist();render();toast('Precio manual guardado con su fecha.');}else toast('Precio o fecha inválidos.');return;}if(b.id==='remove-quote'){delete state.quoteOverrides[document.getElementById('quote-ticker').value];persist();render();toast('Se vuelve a la referencia disponible.');return;}if(b.id==='import-quote-lines'){importQuoteLines();return;}if(b.id==='export-json'||b.id==='backup-top'){exportJson();return;}if(b.id==='export-csv'||b.dataset.exportCsv){exportCsv();return;}if(b.id==='reset-app'){if(confirm('¿Borrar todas tus modificaciones locales? Esta acción no se puede deshacer.')){state=structuredClone(initial);persist();navigate('overview');toast('Datos personales restablecidos.');}return;}});
document.addEventListener('change',ev=>{const t=ev.target;if(t.id==='filter-sector'){state.filters.sector=t.value;persist();render();}else if(t.id==='filter-manager'){state.filters.manager=t.value;persist();render();}else if(t.id==='filter-overlap'){state.filters.overlap=t.value;persist();render();}else if(t.id==='filter-sort'){state.filters.sort=t.value;persist();render();}else if(t.id==='val-ticker'){state.selected=t.value;persist();render();}else if(t.id==='hurdle'){state.settings.hurdle=Math.max(0,Math.min(90,Number(t.value)||0));persist();render();}else if(t.id==='restore-file'&&t.files?.[0])restoreJson(t.files[0]);});
document.addEventListener('input',ev=>{if(ev.target.id==='search-company'){state.filters.term=ev.target.value;persist();const pos=ev.target.selectionStart;render();const el=document.getElementById('search-company');if(el){el.focus();el.setSelectionRange(pos,pos);}}});
document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&activeModal)closeModal();if(ev.key==='Escape'&&!document.getElementById('modal-root').classList.contains('hidden'))closeModal();});
document.getElementById('modal-root').addEventListener('click',ev=>{if(ev.target.id==='modal-root')closeModal();});
render();refreshQuotes();refreshAutoAnalysis();refreshInternational();refreshReliability();refreshOpportunityV6();refreshSensitivityV7();refreshAuditV8();refreshEconomicV9();refreshFinancialAuditV10();refreshReconciliationV11();refreshCloseoutV12();refreshEvidenceV13();refreshProduction();
if('serviceWorker' in navigator && (location.protocol==='https:'||location.hostname==='localhost'))navigator.serviceWorker.register('./sw.js').catch(()=>{});
})();
