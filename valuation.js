/* CIIP DCF v1.2 — illustrative equity cash flow valuation. No trading or recommendation. */
const CIIP_DCF_DEFAULTS={
  prudente:{g1:3,g2:2,discount:12,terminal:2},
  base:{g1:7,g2:4,discount:10,terminal:2.5},
  optimista:{g1:11,g2:7,discount:9,terminal:3}
};
const CIIP_DCF_LABELS={prudente:'Conservador',base:'Base',optimista:'Optimista'};
let ciipValSelected='MSFT',ciipValSaved={};
try{
  const loaded=JSON.parse(localStorage.getItem('ciip_valuation_v1')||'{}');
  if(loaded&&typeof loaded==='object'&&!Array.isArray(loaded))ciipValSaved=loaded;
}catch(_error){ciipValSaved={}}
const ciipMoney=value=>Number.isFinite(value)?value.toLocaleString('es-ES',{minimumFractionDigits:2,maximumFractionDigits:2}):'—';
const ciipValuePct=value=>Number.isFinite(value)?value.toLocaleString('es-ES',{minimumFractionDigits:1,maximumFractionDigits:1})+' %':'—';
const ciipDcfCopy=()=>Object.fromEntries(Object.entries(CIIP_DCF_DEFAULTS).map(([k,v])=>[k,{...v}]));
function ciipValInputs(ticker){
  const obj=ciipValSaved[ticker]||{};
  const scenarios=ciipDcfCopy();
  for(const key of Object.keys(scenarios)){
    const o=obj.scenarios?.[key]||{};
    for(const prop of ['g1','g2','discount','terminal'])
      if(Number.isFinite(Number(o[prop]))&&o[prop]!==undefined)scenarios[key][prop]=Number(o[prop]);
  }
  return {sharesM:obj.sharesM||'',sharesSource:obj.sharesSource||'',scenarios};
}
function ciipValChoose(ticker){
  if(!companies.some(c=>c.Ticker===ticker))return;
  ciipValSelected=ticker;
  if(state.tab==='valuation')render();
}
function ciipValUseSecShares(){
 const sec=ciipHistorical(ciipValSelected),r=sec?.share_reconciliation;
 if(r?.status!=='provisional_reconciled'||!r.provisional_diluted_shares||!sec.url)return;
 if(!confirm('El dato SEC es la media diluida de un trimestre, NO acciones plenamente diluidas actuales. Se comparó con acciones básicas, pero requiere revisión de clases y emisiones posteriores. ¿Usarlo solo como hipótesis provisional?'))return;
 const el=document.getElementById('ciip-val-shares'),src=document.getElementById('ciip-val-source');
 if(el&&src){el.value=String(Math.round(r.provisional_diluted_shares/10000)/100);src.value=sec.url;ciipValUpdatePreview();}
}
function ciipValInput(label,id,value,step='0.1',min='-30',max='40'){
  return '<label style="display:block;min-width:0"><span class="muted tiny">'+esc(label)+'</span><input class="input" style="width:100%;min-width:0;margin-top:5px" type="number" id="'+esc(id)+'" value="'+esc(value)+'" min="'+esc(min)+'" max="'+esc(max)+'" step="'+esc(step)+'" oninput="ciipValUpdatePreview()"></label>';
}
function ciipValSourcePrice(ticker){
  const p=autoMarket?.prices?.[ticker];
  if(!p||p.currency!=='USD'||!Number.isFinite(Number(p.price))||Number(p.price)<=0)return null;
  const time=Date.parse(p.date+'T00:00:00Z');
  if(!Number.isFinite(time))return null;
  const age=Math.floor((Date.now()-time)/86400000);
  return {...p,age,upToDate:age>=0&&age<=10};
}
function ciipValDcf(fcfM,params){
  if(!Number.isFinite(fcfM)||fcfM<=0)return null;
  const r=params.discount/100,gt=params.terminal/100;
  if(!(r>gt+0.005)||r<=0||gt<-.05||gt>.05)return null;
  let fcf=fcfM,present=0,fcfYear5=0;
  for(let year=1;year<=10;year++){
    const growth=(year<=5?params.g1:params.g2)/100;
    fcf*=1+growth;
    present+=fcf/Math.pow(1+r,year);
    if(year===5)fcfYear5=fcf;
  }
  const terminal=fcf*(1+gt)/(r-gt);
  const terminalPV=terminal/Math.pow(1+r,10);
  const equityM=present+terminalPV;
  return Number.isFinite(equityM)&&equityM>0?{
    equityM,explicitPV:present,terminalPV,terminalWeight:terminalPV/equityM,
    fcfYear5,fcfYear10:fcf
  }:null;
}
function ciipValCompute(ticker,values){
  const c=companies.find(x=>x.Ticker===ticker);
  const f=c?financialRecord(c):null;
  const historical=ciipHistorical(ticker);
  const quality=ciipHistoricalQuality(ticker);
  const sector=historical?.sector_control;
  const specialist=['software','payment_network','capital_intensive','cyclical_semis','cloud_capex'].includes(sector?.profile);
  if(specialist)return {reason:'Esta compañía debe evaluarse mediante el modelo sectorial diferenciado (pestaña Sectores). El DCF genérico se deshabilita para evitar resultados contradictorios.',records:[],sectorControl:sector};
  const baseline=quality?.normalized_fcf_status==='ready_with_caveats'&&
    quality.status==='historical_ready'&&sector?.status!=='blocked'&&
    Number.isFinite(quality.normalized_fcf_3y_usd)&&quality.normalized_fcf_3y_usd>0
    ?quality.normalized_fcf_3y_usd:null;
  if(!f||!baseline)return {reason:sector?.status==='blocked'
    ?'Modelo industrial bloqueado para este negocio: '+sector.reason
    :quality?.normalized_fcf_status==='working_capital_review'
      ?'Revisión pendiente: el circulante parcial muestra fluctuaciones materiales. No se genera DCF.'
      :'Normalización o datos sectoriales insuficientes; no se emite valoración DCF.',records:[],
    historyQuality:quality,sectorControl:sector};
  const date=Date.parse(f.period+'T00:00:00Z');
  const ageMonths=Number.isFinite(date)?(Date.now()-date)/(86400000*30.44):Infinity;
  const price=ciipValSourcePrice(ticker);
  const shares=Number(values.sharesM);
  const source=String(values.sharesSource||'');
  const sharesDocumented=Number.isFinite(shares)&&shares>0&&shares<=1000000&&/^https:\/\/\S+/i.test(source);
  const scenarios=[];
  for(const key of ['prudente','base','optimista']){
    const dcf=ciipValDcf(baseline/1000000,values.scenarios[key]);
    if(!dcf)continue;
    const valuePerShare=sharesDocumented?dcf.equityM/shares:null;
    const priceComparable=!!(price?.upToDate&&valuePerShare&&ageMonths<=18);
    scenarios.push({key,label:CIIP_DCF_LABELS[key],...dcf,
      valuePerShare,marketPrice:priceComparable?Number(price.price):null,
      safety:priceComparable?(1-Number(price.price)/valuePerShare)*100:null});
  }
  const hurdles=[12,15].map(rate=>{
    const assumptions={...values.scenarios.base,discount:rate};
    const dcf=ciipValDcf(baseline/1000000,assumptions);
    return {rate,valueM:dcf?.equityM??null,
      valuePerShare:dcf&&sharesDocumented?dcf.equityM/shares:null};
  });
  return {f,price,ageMonths,sharesDocumented,shares,source,scenarios,records:scenarios,baselineFcfUsd:baseline,historyQuality:quality,hurdles};
}
function ciipValPersist(){
  const form=ciipValReadForm();
  if(form.errors.length){alert(form.errors.join('\n'));return}
  ciipValSaved[form.ticker]={...form.values,modified:new Date().toISOString()};
  try{localStorage.setItem('ciip_valuation_v1',JSON.stringify(ciipValSaved));}
  catch(error){alert('No se pudieron guardar las hipótesis: '+error.message);return}
  render();
}
function ciipValReset(){
  if(!confirm('¿Restaurar los supuestos de valoración de '+ciipValSelected+'?'))return;
  delete ciipValSaved[ciipValSelected];
  localStorage.setItem('ciip_valuation_v1',JSON.stringify(ciipValSaved));
  render();
}
function ciipValExport(){
  const ticker=ciipValSelected;
  const form=ciipValReadForm();
  if(form.errors.length){alert(form.errors.join('\n'));return}
  const input=form.values;
  const calc=ciipValCompute(ticker,input);
  const output={
    format:'CIIP_ILLUSTRATIVE_DCF_V1',ticker,exportedAt:new Date().toISOString(),
    assumptions:input,baseline:calc.f?{
      fcfM:calc.baselineFcfUsd/1000000,fiscalYearEnd:calc.historyQuality?.latest_fy_end||calc.f.period,normalization:'3-year median SEC 10-K CFO minus CAPEX',
      operatingCashFlow:calc.f.metrics.operating_cash_flow,
      capex:calc.f.metrics.capex,
      secUrl:calc.f.filing.url
    }:null,
    marketQuote:calc.price||null,
    valuation:calc.scenarios||[],notes:[
      'DCF de flujos potencialmente disponibles para accionistas (CFO - CAPEX). Se descuenta al coste de capital propio.',
      'No restar deuda ni sumar caja a estos resultados: no es un FCFF/enterprise DCF.',
      'Hipótesis ilustrativas no verificadas; acciones diluidas aportadas por usuario.',
      'No equivale a recomendación, valoración auditada ni rentabilidad futura garantizada.'
    ]
  };
  download(new Blob([JSON.stringify(output,null,2)],{type:'application/json'}),'ciip_dcf_'+ticker+'.json');
}
function ciipValResults(calc){
  const f=calc.f,price=calc.price;
  let results='<div class="notice">No es posible calcular todavía la valoración: faltan datos de FCF anual positivo y comparable. No se crearán precios objetivo a partir de cifras incompletas.</div>';
  if(f&&calc.scenarios.length){
    const tr=calc.scenarios.map(x=>{
      const warning=x.terminalWeight>.75?'<div class="muted tiny">Terminal >75 % del valor</div>':'';
      return '<tr><td><b>'+esc(x.label)+'</b></td><td>'+ciipMoney(x.equityM)+'</td><td>'+ciipValuePct(x.terminalWeight*100)+warning+'</td><td>'+ (x.valuePerShare===null?'—':ciipMoney(x.valuePerShare)+' USD')+'</td><td>'+(x.safety===null?'—':ciipValuePct(x.safety))+'</td></tr>';
    });
    const cards=calc.scenarios.map(x=>{
      const perShare=x.valuePerShare===null?'—':ciipMoney(x.valuePerShare)+' USD';
      const safety=x.safety===null?'—':ciipValuePct(x.safety);
      const shareHint=x.valuePerShare===null?'Pendiente: acciones diluidas y fuente':'Según las acciones aportadas';
      const safetyHint=x.safety===null?'Pendiente: precio reciente y valor por acción':'Diferencia entre el precio y el valor estimado';
      const terminalNote=x.terminalWeight>.75?'<span class="ciip-result-warning">El valor terminal supera el 75 %</span>':'';
      return '<article class="ciip-result-card" role="listitem">'+
        '<div class="ciip-result-card-title"><h3>'+esc(x.label)+'</h3><span class="ciip-result-label">Escenario DCF</span></div>'+
        '<div class="ciip-result-primary-block"><span class="ciip-result-label">Valor patrimonial estimado</span>'+
        '<strong class="ciip-result-primary">'+ciipMoney(x.equityM)+'</strong>'+
        '<span class="ciip-result-unit">millones USD</span></div>'+
        '<div class="ciip-result-pairs">'+
        '<div class="ciip-result-metric"><span class="ciip-result-label">Valor por acción</span><strong>'+perShare+'</strong><small>'+shareHint+'</small></div>'+
        '<div class="ciip-result-metric"><span class="ciip-result-label">Margen precio/valor</span><strong>'+safety+'</strong><small>'+safetyHint+'</small></div>'+
        '</div>'+
        '<div class="ciip-result-terminal"><span>Peso del valor terminal</span><strong>'+ciipValuePct(x.terminalWeight*100)+'</strong></div>'+
        terminalNote+'</article>';
    }).join('');
    results='<div class="ciip-result-cards" role="list" aria-label="Valoraciones por escenario">'+cards+'</div>'+
      '<div class="ciip-result-desktop-table">'+table(['Escenario','Valor patrimonial M USD','Peso terminal','Valor por acción','Margen precio/valor'],tr)+'</div>'+
      '<p class="muted tiny">Margen precio/valor = 100 × (1 − último precio / valor por acción). Negativo significa que el precio supera la valoración del escenario. Esta diferencia NO es una rentabilidad anual prevista.</p>';
  }
  const notices=[];
  if(f&&!calc.sharesDocumented)notices.push('Para calcular valores por acción introduce acciones diluidas en millones y URL de su fuente. El dato no se valida automáticamente.');
  if(f&&(!price||!price.upToDate))notices.push('Cotización automática no disponible o con más de 10 días de antigüedad: sin comparación de precio.');
  if(f&&calc.ageMonths>18)notices.push('FCF de ejercicio antiguo: no se muestra la comparación de precio.');
  if(f&&calc.scenarios.some(x=>x.terminalWeight>.75))notices.push('Uno o varios escenarios dependen en más de un 75 % del valor terminal.');
  const foot=notices.length?'<div class="notice">'+notices.map(esc).join(' ')+'</div>':'';
  const hurdle=calc.hurdles?.length?'<div class="ciip-result-cards ciip-return-hurdles" role="list" aria-label="Precios compatibles con rentabilidad exigida">'+
     calc.hurdles.map(x=>'<article class="ciip-result-card" role="listitem"><div class="ciip-result-label">Rentabilidad exigida '+x.rate+' % anual</div>'+
       '<strong class="ciip-result-primary">'+(x.valuePerShare===null?'—':ciipMoney(x.valuePerShare)+' USD/acción')+'</strong>'+
       '<p class="muted tiny">Valor patrimonial: '+(x.valueM===null?'—':ciipMoney(x.valueM)+' M USD')+'</p></article>').join('')+
     '</div><p class="muted tiny">Valores compatibles con tasas de descuento del 12 % y 15 %, según los supuestos editados del escenario Base. No son rentabilidades previstas ni garantizadas: requieren verificar acciones, estabilidad del FCF y crecimiento.</p>':'';
  return foot+results+(hurdle?'<section style="margin-top:16px"><h3>Umbrales de valoración · rentabilidad exigida</h3>'+hurdle+'</section>':'');
}
function ciipValReadForm(){
  const ticker=ciipValSelected;
  const sharesRaw=(document.getElementById('ciip-val-shares')?.value||'').trim();
  const source=(document.getElementById('ciip-val-source')?.value||'').trim();
  const errors=[],scenarios={};
  if(sharesRaw){
    const shares=Number(sharesRaw);
    if(!Number.isFinite(shares)||shares<=0||shares>1000000)
      errors.push('El número de acciones diluidas debe ser positivo y estar expresado en millones.');
    if(!/^https:\/\/\S+/i.test(source))
      errors.push('Para valorar por acción, indica una URL HTTPS de la fuente de acciones diluidas.');
  }
  for(const key of ['prudente','base','optimista']){
    const p={};
    let valid=true;
    for(const param of ['g1','g2','discount','terminal']){
      const raw=document.getElementById('ciip-'+key+'-'+param)?.value?.trim();
      if(raw===undefined||raw===''){valid=false;break;}
      p[param]=Number(raw);
      if(!Number.isFinite(p[param])){valid=false;break;}
    }
    if(!valid){
      errors.push('Completa los cuatro supuestos de '+CIIP_DCF_LABELS[key]+'.');
      continue;
    }
    if(p.g1< -30||p.g1>40||p.g2< -30||p.g2>40||p.discount<5||p.discount>30||
       p.terminal< -5||p.terminal>5||p.discount-p.terminal<=0.5){
      errors.push('Revisa '+CIIP_DCF_LABELS[key]+': crecimientos −30 % a 40 %, descuento 5 % a 30 %, terminal −5 % a 5 % y descuento más de 0,5 puntos superior al terminal.');
      continue;
    }
    scenarios[key]=p;
  }
  return {values:{sharesM:sharesRaw,sharesSource:source,scenarios},errors,ticker};
}
function ciipValUpdatePreview(){
  const target=document.getElementById('ciip-dcf-preview');
  if(!target||state.tab!=='valuation')return;
  const form=ciipValReadForm();
  const calc=form.errors.length?null:ciipValCompute(form.ticker,form.values);
  if(form.errors.length){
    target.innerHTML='<div class="notice">'+form.errors.map(esc).join(' ')+'</div>';
  }else{
    target.innerHTML=ciipValResults(calc);
  }
  for(const key of ['prudente','base','optimista']){
    const el=document.getElementById('ciip-inline-value-'+key);
    if(el){
      const scenario=calc?.scenarios?.find(x=>x.key===key);
      el.textContent=scenario?ciipMoney(scenario.equityM):'—';
    }
  }
  const status=document.getElementById('ciip-dcf-status');
  if(status)status.textContent='Vista previa actualizada al modificar los parámetros. Estos cambios aún no están guardados.';
}
function ciipValScrollToResults(){
  document.getElementById('ciip-valuation-results')?.scrollIntoView({behavior:'smooth',block:'start'});
}
function valuationView(){
  const preferred=companies.find(c=>c.Ticker===ciipValSelected)?ciipValSelected:'MSFT';
  ciipValSelected=preferred;
  const ticker=preferred,c=companies.find(x=>x.Ticker===ticker);
  const vals=ciipValInputs(ticker);
  const calc=ciipValCompute(ticker,vals);
  const select='<select class="select" aria-label="Seleccionar empresa" style="min-width:min(420px,100%);max-width:100%" onchange="ciipValChoose(this.value)">'+companies.map(x=>'<option value="'+esc(x.Ticker)+'" '+(x.Ticker===ticker?'selected':'')+'>'+esc(x.Ticker+' · '+x.Empresa)+'</option>').join('')+'</select>';
  const price=calc.price;
  const f=calc.f;
  const source=f?'<a class="link" href="'+esc(f.filing.url)+'" target="_blank" rel="noopener noreferrer">SEC Company Facts ↗</a>':'SEC sin datos comparables';
  const quote=price?(ciipMoney(Number(price.price))+' USD · '+esc(price.date)+' · '+esc(price.source)):'Sin precio USD automático';
  const warning=!calc.f?'<div class="notice">'+esc(calc.reason||'Valoración no disponible')+'</div>':
    '<p class="muted tiny">FCF normalizado: '+ciipMoney(f.fcf/1000000)+' M USD de FCF aproximado, ejercicio terminado '+esc(f.period)+'. '+source+'.'+(calc.ageMonths>18?' Ejercicio anterior a 18 meses: comparación con cotización deshabilitada.':'')+'</p>';
  let scenarios='';
  for(const key of ['prudente','base','optimista']){
    const p=vals.scenarios[key];
    const row=calc.scenarios?.find(x=>x.key===key);
    scenarios+='<section class="panel ciip-scenario-panel"><h2>'+esc(CIIP_DCF_LABELS[key])+'</h2><div class="grid ciip-scenario-fields" style="grid-template-columns:repeat(2,minmax(0,1fr));gap:10px">'+
      ciipValInput('Crecimiento FCF años 1–5 (%)','ciip-'+key+'-g1',p.g1)+
      ciipValInput('Crecimiento FCF años 6–10 (%)','ciip-'+key+'-g2',p.g2)+
      ciipValInput('Rentabilidad exigida (%)','ciip-'+key+'-discount',p.discount,'0.1','5','30')+
      ciipValInput('Crecimiento perpetuo (%)','ciip-'+key+'-terminal',p.terminal,'0.1','-5','5')+
    '</div><div class="ciip-scenario-inline"><span class="ciip-result-label">Valor patrimonial estimado (M USD)</span><strong id="ciip-inline-value-'+key+'">'+(row?ciipMoney(row.equityM):'—')+'</strong></div></section>';
  }
  const sectorLink=calc.sectorControl?.profile&&['software','payment_network','capital_intensive','cyclical_semis','cloud_capex'].includes(calc.sectorControl.profile)
    ?'<p>'+button('Abrir valoración sectorial','go(\\'sector\\')')+'</p>':'';
  const preview=ciipValResults(calc);
  return '<section class="panel"><h2>Valoración ilustrativa · flujos de caja del accionista</h2><p class="muted">Modelo a diez años con dos etapas y valor terminal (Gordon). Parte de CFO − CAPEX publicado para un mismo ejercicio fiscal, una aproximación de flujo atribuible al accionista. Se descuenta a una rentabilidad exigida al capital propio, por lo que NO se resta deuda ni se añade caja de nuevo. No es FCFF ni un DCF empresarial, no ajusta stock-based compensation, adquisiciones ni necesidades extraordinarias de caja.</p><div class="actions" style="align-items:center">'+select+button('Actualizar datos SEC','refreshFundamentals()')+button('Actualizar cotización','refreshAutoMarket()')+button('Ver resultados ↓','ciipValScrollToResults()')+'</div>'+warning+'<p class="muted tiny">Cotización para comparar: '+quote+'</p></section>'+
  '<section class="panel"><h2>Denominador por acción · aportación manual</h2><p class="muted tiny">Indica acciones diluidas (millones) del mismo emisor y clase económica. Para ADR y clases múltiples revisa sus conversiones y derechos. Si no hay un dato con fuente, el sistema solo mostrará importes agregados.</p><div class="grid ciip-share-fields" style="grid-template-columns:1fr 2fr;gap:12px">'+
  ciipValInput('Acciones diluidas (millones)','ciip-val-shares',vals.sharesM,'0.01','0','1000000')+
  '<label style="display:block"><span class="muted tiny">Enlace HTTPS a la fuente de acciones</span><input class="input" id="ciip-val-source" type="url" style="width:100%;min-width:0;margin-top:5px" placeholder="https://..." value="'+esc(vals.sharesSource)+'" oninput="ciipValUpdatePreview()"></label></div>'+
  (ciipHistorical(ticker)?.share_reconciliation?.status==='provisional_reconciled'?'<div class="actions" style="margin-top:10px">'+button('Usar acciones SEC (provisional)','ciipValUseSecShares()')+'</div>':'')+
  '<p class="muted tiny">Dato SEC provisional: media ponderada diluida trimestral, cotejada con acciones básicas. No es una cifra actual plenamente diluida; requiere confirmar clases, splits y emisiones. Se muestra el valor por acción solo tras introducir o aceptar explícitamente el denominador.</p></section>'+
  ciipQualityPanel(ticker)+
  '<details class="panel"><summary style="font-weight:750;cursor:pointer">Consultar cinco ejercicios SEC y controles de calidad</summary>'+ciipHistoryReadout(ticker)+'</details>'+
  '<div class="grid ciip-scenarios" style="grid-template-columns:repeat(3,minmax(0,1fr))">'+scenarios+'</div>'+
  '<section class="panel" id="ciip-valuation-results"><div class="actions" style="justify-content:space-between;align-items:center"><h2 style="margin:0">Resultados por escenario</h2><div class="actions">'+button('Guardar supuestos','ciipValPersist()','')+button('Restaurar','ciipValReset()')+button('Exportar análisis JSON','ciipValExport()')+'</div></div><p class="muted tiny" id="ciip-dcf-status">Los resultados se recalculan automáticamente al modificar los parámetros. «Guardar supuestos» conserva tus cambios en este dispositivo.</p><div id="ciip-dcf-preview" aria-live="polite" aria-atomic="true">'+preview+'</div></section>'+
  '<section class="panel"><h2>Alcance y limitaciones</h2><p class="muted">Las tres tasas son hipótesis iniciales ilustrativas, no previsiones del sistema. El flujo anual puede ser excepcional o estar distorsionado por capital circulante y compensación en acciones. La cifra de acciones procede exclusivamente del usuario; una fuente indicada no implica revisión documental. Este módulo NO clasifica empresas como READY, no genera órdenes ni emite recomendaciones de inversión. Antes de una decisión se requieren normalización plurianual, dilución, calidad de beneficio, deuda, sensibilidad y revisión de fuentes.</p></section>';
}
