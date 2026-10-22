/* CIIP DCF v0.8 — illustrative equity cash flow valuation. No trading or recommendation. */
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
function ciipValInput(label,id,value,step='0.1',min='-30',max='40'){
  return '<label style="display:block;min-width:0"><span class="muted tiny">'+esc(label)+'</span><input class="input" style="width:100%;min-width:0;margin-top:5px" type="number" id="'+esc(id)+'" value="'+esc(value)+'" min="'+esc(min)+'" max="'+esc(max)+'" step="'+esc(step)+'"></label>';
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
  if(!f||!Number.isFinite(f.fcf)||f.fcf<=0)return {reason:'No existe un FCF anual positivo y comparable (flujo operativo menos CAPEX) para esta empresa.',records:[]};
  const date=Date.parse(f.period+'T00:00:00Z');
  const ageMonths=Number.isFinite(date)?(Date.now()-date)/(86400000*30.44):Infinity;
  const price=ciipValSourcePrice(ticker);
  const shares=Number(values.sharesM);
  const source=String(values.sharesSource||'');
  const sharesDocumented=Number.isFinite(shares)&&shares>0&&shares<=1000000&&/^https:\/\/\S+/i.test(source);
  const scenarios=[];
  for(const key of ['prudente','base','optimista']){
    const dcf=ciipValDcf(f.fcf/1000000,values.scenarios[key]);
    if(!dcf)continue;
    const valuePerShare=sharesDocumented?dcf.equityM/shares:null;
    const priceComparable=!!(price?.upToDate&&valuePerShare&&ageMonths<=18);
    scenarios.push({key,label:CIIP_DCF_LABELS[key],...dcf,
      valuePerShare,marketPrice:priceComparable?Number(price.price):null,
      safety:priceComparable?(1-Number(price.price)/valuePerShare)*100:null});
  }
  return {f,price,ageMonths,sharesDocumented,shares,source,scenarios,records:scenarios};
}
function ciipValPersist(){
  const ticker=ciipValSelected;
  const sharesRaw=document.getElementById('ciip-val-shares')?.value.trim()||'';
  const source=document.getElementById('ciip-val-source')?.value.trim()||'';
  if(sharesRaw){
    const shares=Number(sharesRaw);
    if(!Number.isFinite(shares)||shares<=0||shares>1000000){alert('Introduce un número de acciones diluidas válido, expresado en millones.');return}
    if(!/^https:\/\/\S+/i.test(source)){alert('Indica una URL HTTPS con la fuente del número de acciones.');return}
  }
  const scenarios={};
  for(const key of ['prudente','base','optimista']){
    const o={};
    for(const param of ['g1','g2','discount','terminal']){
      const el=document.getElementById('ciip-'+key+'-'+param);
      if(!el||!el.value.trim()){alert('Falta un supuesto de '+CIIP_DCF_LABELS[key]);return}
      o[param]=Number(el.value);
      if(!Number.isFinite(o[param])){alert('Se ha introducido un dato no numérico.');return}
    }
    if(o.g1< -30||o.g1>40||o.g2< -30||o.g2>40||o.discount<5||o.discount>30||o.terminal< -5||o.terminal>5||o.discount-o.terminal<=0.5){
      alert('Revisa '+CIIP_DCF_LABELS[key]+': crecimientos entre −30 % y 40 %, descuento entre 5 % y 30 %, crecimiento terminal entre −5 % y 5 %, y descuento superior al terminal en más de 0,5 puntos.');
      return;
    }
    scenarios[key]=o;
  }
  ciipValSaved[ticker]={sharesM:sharesRaw,sharesSource:source,scenarios,modified:new Date().toISOString()};
  try{localStorage.setItem('ciip_valuation_v1',JSON.stringify(ciipValSaved));}
  catch(error){alert('El navegador no permite guardar las hipótesis: '+error.message);return;}
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
  const input=ciipValInputs(ticker);
  const calc=ciipValCompute(ticker,input);
  const output={
    format:'CIIP_ILLUSTRATIVE_DCF_V1',ticker,exportedAt:new Date().toISOString(),
    assumptions:input,baseline:calc.f?{
      fcfM:calc.f.fcf/1000000,fiscalYearEnd:calc.f.period,
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
  const warning=!f?'<div class="notice">'+esc(calc.reason)+'</div>':
    '<p class="muted tiny">Base histórica: '+ciipMoney(f.fcf/1000000)+' M USD de FCF aproximado, ejercicio terminado '+esc(f.period)+'. '+source+'.'+(calc.ageMonths>18?' Ejercicio anterior a 18 meses: comparación con cotización deshabilitada.':'')+'</p>';
  let scenarios='';
  for(const key of ['prudente','base','optimista']){
    const p=vals.scenarios[key];
    scenarios+='<section class="panel"><h2>'+esc(CIIP_DCF_LABELS[key])+'</h2><div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr));gap:10px">'+
      ciipValInput('Crecimiento FCF años 1–5 (%)','ciip-'+key+'-g1',p.g1)+
      ciipValInput('Crecimiento FCF años 6–10 (%)','ciip-'+key+'-g2',p.g2)+
      ciipValInput('Rentabilidad exigida (%)','ciip-'+key+'-discount',p.discount,'0.1','5','30')+
      ciipValInput('Crecimiento perpetuo (%)','ciip-'+key+'-terminal',p.terminal,'0.1','-5','5')+
    '</div></section>';
  }
  let results='<div class="notice">No es posible calcular todavía la valoración: faltan datos de FCF anual positivo y comparable. No se crearán precios objetivo a partir de cifras incompletas.</div>';
  if(f&&calc.scenarios.length){
    const tr=calc.scenarios.map(x=>{
      const warning=x.terminalWeight>.75?'<div class="muted tiny">Terminal >75 % del valor</div>':'';
      return '<tr><td><b>'+esc(x.label)+'</b></td><td>'+ciipMoney(x.equityM)+'</td><td>'+ciipValuePct(x.terminalWeight*100)+warning+'</td><td>'+ (x.valuePerShare===null?'—':ciipMoney(x.valuePerShare)+' USD')+'</td><td>'+(x.safety===null?'—':ciipValuePct(x.safety))+'</td></tr>';
    });
    results=table(['Escenario','Valor patrimonial M USD','Peso terminal','Valor por acción','Margen precio/valor'],tr)+
    '<p class="muted tiny">Margen precio/valor = 100 × (1 − último precio / valor por acción). Negativo significa que el precio supera la valoración del escenario. Esta diferencia NO es una rentabilidad anual prevista.</p>';
  }
  const notices=[];
  if(f&&!calc.sharesDocumented)notices.push('Para calcular valores por acción introduce acciones diluidas en millones y URL de su fuente. El dato no se valida automáticamente.');
  if(f&&(!price||!price.upToDate))notices.push('Cotización automática no disponible o con más de 10 días de antigüedad: sin comparación de precio.');
  if(f&&calc.ageMonths>18)notices.push('FCF de ejercicio antiguo: no se muestra la comparación de precio.');
  if(f&&calc.scenarios.some(x=>x.terminalWeight>.75))notices.push('Uno o varios escenarios dependen en más de un 75 % del valor terminal.');
  const foot=notices.length?'<div class="notice">'+notices.map(esc).join(' ')+'</div>':'';
  return '<section class="panel"><h2>Valoración ilustrativa · flujos de caja del accionista</h2><p class="muted">Modelo a diez años con dos etapas y valor terminal (Gordon). Parte de CFO − CAPEX publicado para un mismo ejercicio fiscal, una aproximación de flujo atribuible al accionista. Se descuenta a una rentabilidad exigida al capital propio, por lo que NO se resta deuda ni se añade caja de nuevo. No es FCFF ni un DCF empresarial, no ajusta stock-based compensation, adquisiciones ni necesidades extraordinarias de caja.</p><div class="actions" style="align-items:center">'+select+button('Actualizar datos SEC','refreshFundamentals()')+button('Actualizar cotización','refreshAutoMarket()')+'</div>'+warning+'<p class="muted tiny">Cotización para comparar: '+quote+'</p></section>'+
  '<section class="panel"><h2>Denominador por acción · aportación manual</h2><p class="muted tiny">Indica acciones diluidas (millones) del mismo emisor y clase económica. Para ADR y clases múltiples revisa sus conversiones y derechos. Si no hay un dato con fuente, el sistema solo mostrará importes agregados.</p><div class="grid" style="grid-template-columns:1fr 2fr;gap:12px">'+
  ciipValInput('Acciones diluidas (millones)','ciip-val-shares',vals.sharesM,'0.01','0','1000000')+
  '<label style="display:block"><span class="muted tiny">Enlace HTTPS a la fuente de acciones</span><input class="input" id="ciip-val-source" type="url" style="width:100%;min-width:0;margin-top:5px" placeholder="https://..." value="'+esc(vals.sharesSource)+'"></label></div></section>'+
  '<div class="grid" style="grid-template-columns:repeat(3,minmax(0,1fr))">'+scenarios+'</div>'+
  '<section class="panel"><div class="actions" style="justify-content:space-between;align-items:center"><h2 style="margin:0">Resultados por escenario</h2><div class="actions">'+button('Guardar supuestos','ciipValPersist()','')+button('Restaurar','ciipValReset()')+button('Exportar análisis JSON','ciipValExport()')+'</div></div><p class="muted tiny">Pulsa «Guardar supuestos» para actualizar los resultados con tus parámetros; se conservarán únicamente en este dispositivo.</p>'+foot+results+'</section>'+
  '<section class="panel"><h2>Alcance y limitaciones</h2><p class="muted">Las tres tasas son hipótesis iniciales ilustrativas, no previsiones del sistema. El flujo anual puede ser excepcional o estar distorsionado por capital circulante y compensación en acciones. La cifra de acciones procede exclusivamente del usuario; una fuente indicada no implica revisión documental. Este módulo NO clasifica empresas como READY, no genera órdenes ni emite recomendaciones de inversión. Antes de una decisión se requieren normalización plurianual, dilución, calidad de beneficio, deuda, sensibilidad y revisión de fuentes.</p></section>';
}
