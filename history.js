/* CIIP v1.1: SEC FY history and quality-gated research radar. */
const CIIP_HISTORY_REQUIREMENTS='Últimos cinco 10-K SEC; el historial no garantiza comparabilidad económica.';
function ciipHistorical(ticker){return fundamentals?.companies?.[ticker]||null}
function ciipHistoricalYears(ticker){return ciipHistorical(ticker)?.history||[]}
function ciipHistoricalQuality(ticker){return ciipHistorical(ticker)?.history_quality||null}
function ciipHistoryCurrency(v,unit='M USD'){
  return v===null||v===undefined||!Number.isFinite(Number(v))?'—':ciipMoney(Number(v)/1000000)+' '+unit;
}
function ciipHistRatio(v){return Number.isFinite(v)?ciipValuePct(v):'—'}
function ciipHistoryLabel(metric){
 return ({revenue:'Ingresos',net_income:'Beneficio neto',operating_income:'EBIT',
   operating_cash_flow:'Flujo operativo',capex:'CAPEX',diluted_shares:'Acciones diluidas ponderadas',
   equity:'Patrimonio',cash:'Efectivo',long_term_debt:'Deuda LP no corriente',
   current_long_term_debt:'Deuda LP corriente'})[metric]||metric;
}
function ciipHistoricQualityBadge(q){
 if(!q)return '<span class="tag warn">Historial pendiente de actualización</span>';
 return q.status==='historical_ready'?'<span class="tag">FCF 3 años comparable</span>':
 '<span class="tag warn">Cobertura insuficiente</span>';
}
function ciipHistoryReadout(ticker){
 const d=ciipHistorical(ticker),years=ciipHistoricalYears(ticker),q=ciipHistoricalQuality(ticker);
 if(!d||!Array.isArray(d.history)){
   return '<div class="notice">Todavía no se ha generado el histórico SEC de cinco ejercicios. Ejecuta CIIP Weekly SEC Fundamentals para actualizarlo; no se utilizará información de otro producto como sustituto.</div>';
 }
 const c=companies.find(x=>x.Ticker===ticker);
 const fields=[
   ['revenue','Ingresos (M USD)'],['operating_income','EBIT (M USD)'],
   ['net_income','Beneficio neto (M USD)'],
   ['operating_cash_flow','CFO (M USD)'],['capex','CAPEX (M USD)'],
   ['fcf_usd','FCF aproximado (M USD)'],['operating_margin_pct','Margen operativo'],
   ['diluted_shares','Acciones diluidas (M)']
 ];
 const headers=['Concepto',...years.map(y=>y.fy_end)];
 const rows=fields.map(([key,title])=>{
   const cells=years.map(y=>{
     if(key==='fcf_usd')return ciipHistoryCurrency(y.fcf_usd,'');
     if(key==='operating_margin_pct')return ciipHistRatio(y.operating_margin_pct);
     const item=y.metrics?.[key];if(!item)return '—';
     const val=key==='diluted_shares'?Number(item.value)/1000000:Number(item.value)/1000000;
     return Number.isFinite(val)?ciipMoney(val):'—';
   });
   return '<tr><td><b>'+esc(title)+'</b></td>'+cells.map(t=>'<td>'+t+'</td>').join('')+'</tr>';
 });
 const latest=years.at(-1);
 const notes=(q?.source_notes||[]).map(t=>'<li>'+esc(t)+'</li>').join('');
 const source='<a class="link" href="'+esc(d.url)+'" target="_blank" rel="noopener noreferrer">Consultar SEC Company Facts ↗</a>';
 return '<div class="ciip-history-cards">'+
  '<article class="panel"><span class="muted tiny">Ejercicios identificados</span><h2>'+years.length+' / 5</h2><span class="muted tiny">Solo SEC 10-K y 10-K/A</span></article>'+
  '<article class="panel"><span class="muted tiny">FCF normalizado · mediana 3 años</span><h2>'+ciipHistoryCurrency(q?.normalized_fcf_3y_usd)+'</h2>'+ciipHistoricQualityBadge(q)+'</article>'+
  '<article class="panel"><span class="muted tiny">CAGR ingresos · histórico comparable</span><h2>'+ciipHistRatio(q?.revenue_cagr_pct)+'</h2><span class="muted tiny">No es previsión futura</span></article></div>'+
 '<section class="panel"><h2>'+esc(c?.Empresa||ticker)+' · evolución anual</h2>'+
 '<p class="muted tiny">Importes en millones de dólares salvo porcentajes y fechas; — significa que la SEC no aporta un dato comparable bajo las etiquetas seleccionadas.</p>'+
 table(headers,rows)+
 '<p class="muted tiny">FCF = CFO − CAPEX; aproximación, no FCF ajustado. Acciones: media ponderada diluida, no capital emitido al cierre. Diferencias contables, adquisiciones y splits pueden distorsionar comparaciones.</p>'+
 '<p>'+source+'</p>'+
 (notes?'<div class="notice"><b>Controles de calidad</b><ul>'+notes+'</ul></div>':'')+
 '<p class="muted tiny">Detalles de cada dato disponibles en el archivo JSON, con etiqueta US-GAAP, fecha de presentación y número de acceso de su 10-K.</p></section>';
}
function historyView(){
 const options=companies.map(c=>'<option value="'+esc(c.Ticker)+'" '+(c.Ticker===ciipValSelected?'selected':'')+'>'+esc(c.Ticker+' · '+c.Empresa)+'</option>').join('');
 return '<section class="panel"><h2>Historial financiero de cinco ejercicios · SEC EDGAR</h2>'+
 '<p class="muted">Comprobación documental, no previsión. Los indicadores se calculan únicamente si se dispone de los ejercicios compatibles. Las cifras contables incompletas no se rellenan.</p>'+
 '<div class="actions"><select class="select" style="max-width:100%;min-width:0" aria-label="Empresa" onchange="ciipValChoose(this.value);render()">'+options+'</select>'+
 button('Actualizar lectura SEC','refreshFundamentals()')+'</div></section>'+ciipHistoryReadout(ciipValSelected);
}
function ciipRadarModels(){
 const rows=[];
 const records=fundamentals?.companies||{};
 for(const c of companies){
   const x=records[c.Ticker],q=x?.history_quality,h=x?.history;
   if(!q||!h||h.length<3)continue;
   const price=ciipValSourcePrice(c.Ticker);
   const fcf=q.normalized_fcf_3y_usd;
   const qualityPoints=[
     q.status==='historical_ready',
     q.available_years>=5,
     q.positive_fcf_years>=5,
     q.revenue_cagr_pct!==null&&q.revenue_cagr_pct>=4,
     q.diluted_shares_proxy_available,
     price?.upToDate===true
   ];
   const score=qualityPoints.reduce((sum,v)=>sum+Number(!!v),0);
   const notes=[];
   if(!fcf||fcf<=0)notes.push('Sin FCF normalizado');
   if(!q.diluted_shares_proxy_available)notes.push('Acciones sin validar');
   if(!price?.upToDate)notes.push('Cotización no reciente');
   if(q.available_years<5)notes.push('Menos de 5 ejercicios');
   if(q.latest_fy_age_days>520)notes.push('10-K desactualizado');
   const valuationCapable=!!(fcf>0&&q.status==='historical_ready');
   // Screening never uses raw SEC weighted-average shares to produce a purchase signal.
   rows.push({ticker:c.Ticker,name:c.Empresa,score,fcf,years:q.available_years,
     positive:q.positive_fcf_years,cagr:q.revenue_cagr_pct,price:price?.price||null,
     valuationCapable,notes,age:q.latest_fy_age_days});
 }
 return rows.sort((a,b)=>b.score-a.score||(b.positive-a.positive)||a.ticker.localeCompare(b.ticker));
}
function ciipRadarResearchPanel(){
 const records=ciipRadarModels();
 const firms=records.filter(x=>x.valuationCapable);
 const full=records.filter(x=>x.years>=5);
 const rows=records.slice(0,25).map(x=>'<tr><td><b>'+esc(x.ticker)+'</b><div class="muted tiny">'+esc(x.name)+'</div></td>'+
 '<td>'+x.score+' / 6</td><td>'+x.years+' / 5</td><td>'+x.positive+'</td><td>'+ciipHistRatio(x.cagr)+'</td>'+
 '<td>'+ (x.fcf>0?ciipHistoryCurrency(x.fcf):'—')+'</td>'+
 '<td>'+esc(x.notes.length?x.notes.join(' · '):'Datos para revisión')+'</td>'+
 '<td><button class="btn secondary" onclick="ciipValChoose(\\''+esc(x.ticker)+'\\');go(\\'valuation\\')">Valorar ↗</button></td></tr>');
 if(!records.length)return '<section class="panel"><h2>Radar fundamental automático</h2><div class="notice">Los históricos aún no están cargados. La clasificación automática permanecerá desactivada hasta que el archivo SEC incluya datos comparables.</div></section>';
 return '<section class="panel"><h2>Radar fundamental automático · lista de investigación</h2>'+
 '<p class="muted">Priorización orientativa por cobertura y estabilidad, no clasificación de compra. Puntuación de 0 a 6: FCF normalizado, cinco ejercicios, cinco FCF positivos, CAGR ingresos ≥4 %, serie de acciones diluidas sin saltos y precio reciente. No es valoración ni rentabilidad esperada.</p>'+
 '<div class="ciip-history-cards"><article class="panel"><span class="muted tiny">Con histórico</span><h2>'+records.length+'</h2></article>'+
 '<article class="panel"><span class="muted tiny">Cinco ejercicios</span><h2>'+full.length+'</h2></article>'+
 '<article class="panel"><span class="muted tiny">FCF 3 años disponible</span><h2>'+firms.length+'</h2></article></div>'+
 table(['Empresa','Cobertura','Ejercicios','FCF > 0','CAGR ingresos','FCF normalizado','Pendientes','Ficha'],rows)+
 '<p class="muted tiny">No se consideran las puntuaciones provisionales del universo inicial como una validación de calidad. Las acciones SEC son una referencia pendiente de conciliar con dilución, clases y splits. Se excluyen recomendaciones automáticas.</p></section>';
}
