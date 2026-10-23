/* CIIP v1.2: SEC FY history and quality-gated research radar. */
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
function ciipQualityPanel(ticker){
 const d=ciipHistorical(ticker),q=d?.history_quality,sector=d?.sector_control,shares=d?.share_reconciliation;
 if(!q?.normalized_fcf_status||!sector)return '<section class="panel"><h2>Control financiero v1.2</h2><p class="muted">Pendiente de nueva extracción SEC: no se validan acciones ni valoración sectorial.</p></section>';
 const n=v=>v===null||v===undefined?'—':ciipHistoryCurrency(v);
 const pct=v=>Number.isFinite(v)?ciipHistRatio(v):'—';
 const status={eligible:'Modelo genérico con revisión contable',review:'Revisión sectorial obligatoria',blocked:'DCF industrial bloqueado'};
 const shareStatus=shares?.status==='provisional_reconciled'?'Conciliación provisional disponible':'Conciliación manual pendiente';
 const shareFmt=x=>x?.value?ciipMoney(x.value/1000000)+' millones · '+esc(x.end):'—';
 const warnings=[...(q.normalization_notes||[]),...(shares?.notes||[])].map(x=>'<li>'+esc(x)+'</li>').join('');
 return '<section class="panel"><h2>Controles de calidad · inversiones, circulante y acciones</h2>'+
 '<p><b>Sector:</b> '+esc(sector.description)+' · '+esc(status[sector.status]||'Sin control')+'</p><p class="muted tiny">'+esc(sector.reason)+'</p>'+
 '<div class="ciip-history-cards">'+
 '<article class="panel"><span class="muted tiny">CFO mediano 3 años</span><h2>'+n(q.median_cfo_3y_usd)+'</h2></article>'+
 '<article class="panel"><span class="muted tiny">CAPEX mediano 3 años</span><h2>'+n(q.median_capex_3y_usd)+'</h2></article>'+
 '<article class="panel"><span class="muted tiny">FCF prudente normalizado</span><h2>'+n(q.normalized_fcf_3y_usd)+'</h2></article></div>'+
 '<p class="muted tiny">La base de valoración toma el menor entre mediana(CFO−CAPEX) y mediana(CFO)−mediana(CAPEX). El CAPEX total NO se sustituye por amortizaciones ni se asume qué parte corresponde al mantenimiento.</p>'+
 '<p><b>Circulante operativo parcial:</b> mayor variación anual de efectivo estimada '+n(q.partial_wc_largest_annual_cash_effect_usd)+
 '. Se calcula AR + inventario − proveedores; no equivale a la conciliación completa del CFO.</p>'+
 '<p><b>Acciones:</b> '+esc(shareStatus)+'. Acciones básicas SEC recientes: '+shareFmt(shares?.latest_basic)+
 '. Media diluida trimestral: '+shareFmt(shares?.latest_quarter_diluted)+'.</p>'+
 '<p class="muted tiny">Diferencia diluidas trimestrales / básicas: '+pct(shares?.quarter_diluted_vs_basic_pct)+
 ' · Acciones de media anual no son acciones actuales. Para multiclase se exige conciliación manual.</p>'+
 (warnings?'<div class="notice"><b>Revisión pendiente</b><ul>'+warnings+'</ul></div>':'')+
 '<p><a class="link" target="_blank" rel="noopener noreferrer" href="'+esc(d.url)+'">Abrir datos originales SEC ↗</a></p></section>';
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
 '<p>'+source+'</p>'+ciipQualityPanel(ticker)+
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
     q.status==='historical_ready'&&q.normalized_fcf_status==='ready_with_caveats'&&x.sector_control?.status!=='blocked',
     q.available_years>=5,
     q.positive_fcf_years>=5,
     q.revenue_cagr_pct!==null&&q.revenue_cagr_pct>=4,
     x.share_reconciliation?.status==='provisional_reconciled',
     price?.upToDate===true
   ];
   const score=qualityPoints.reduce((sum,v)=>sum+Number(!!v),0);
   const notes=[];
   if(!fcf||fcf<=0)notes.push('Sin FCF normalizado');
   if(x.sector_control?.status==='blocked')notes.push('Bloqueo sectorial');
   else if(x.sector_control?.status==='review')notes.push('Revisión sectorial');
   if(q.normalized_fcf_status==='working_capital_review')notes.push('Circulante relevante');
   if(x.share_reconciliation?.status!=='provisional_reconciled')notes.push('Acciones actuales sin conciliar');
   if(!q.diluted_shares_proxy_available)notes.push('Acciones históricas insuficientes');
   if(!price?.upToDate)notes.push('Cotización no reciente');
   if(q.available_years<5)notes.push('Menos de 5 ejercicios');
   if(q.latest_fy_age_days>520)notes.push('10-K desactualizado');
   const valuationCapable=!!(fcf>0&&q.normalized_fcf_status==='ready_with_caveats'&&x.sector_control?.status!=='blocked');
   // Screening never uses raw SEC weighted-average shares to produce a purchase signal.
   rows.push({ticker:c.Ticker,name:c.Empresa,score,fcf,years:q.available_years,
     positive:q.positive_fcf_years,cagr:q.revenue_cagr_pct,price:price?.price||null,
     valuationCapable,notes,age:q.latest_fy_age_days});
 }
 return rows.sort((a,b)=>b.score-a.score||(b.positive-a.positive)||a.ticker.localeCompare(b.ticker));
}
function ciipRadarGo(ticker){
  if(!companies.some(c=>c.Ticker===ticker))return;
  ciipValSelected=ticker;
  go('valuation');
}
function ciipRadarResearchPanel(){
 const records=ciipRadarModels();
 const firms=records.filter(x=>x.valuationCapable);
 const full=records.filter(x=>x.years>=5);
 const rows=records.slice(0,25).map(x=>'<tr><td><b>'+esc(x.ticker)+'</b><div class="muted tiny">'+esc(x.name)+'</div></td>'+
 '<td>'+x.score+' / 6</td><td>'+x.years+' / 5</td><td>'+x.positive+'</td><td>'+ciipHistRatio(x.cagr)+'</td>'+
 '<td>'+ (x.fcf>0?ciipHistoryCurrency(x.fcf):'—')+'</td>'+
 '<td>'+esc(x.notes.length?x.notes.join(' · '):'Datos para revisión')+'</td>'+
 '<td><button class="btn secondary" data-ticker="'+esc(x.ticker)+'" onclick="ciipRadarGo(this.dataset.ticker)">Valorar ↗</button></td></tr>');;
 if(!records.length)return '<section class="panel"><h2>Radar fundamental automático</h2><div class="notice">Los históricos aún no están cargados. La clasificación automática permanecerá desactivada hasta que el archivo SEC incluya datos comparables.</div></section>';
 return '<section class="panel"><h2>Radar fundamental automático · lista de investigación</h2>'+
 '<p class="muted">Priorización orientativa por cobertura y estabilidad, no clasificación de compra. Puntuación de 0 a 6: FCF normalizado, cinco ejercicios, cinco FCF positivos, CAGR ingresos ≥4 %, conciliación provisional de acciones y precio reciente. No es valoración ni rentabilidad esperada.</p>'+
 '<div class="ciip-history-cards"><article class="panel"><span class="muted tiny">Con histórico</span><h2>'+records.length+'</h2></article>'+
 '<article class="panel"><span class="muted tiny">Cinco ejercicios</span><h2>'+full.length+'</h2></article>'+
 '<article class="panel"><span class="muted tiny">FCF 3 años disponible</span><h2>'+firms.length+'</h2></article></div>'+
 table(['Empresa','Cobertura','Ejercicios','FCF > 0','CAGR ingresos','FCF normalizado','Pendientes','Ficha'],rows)+
 '<p class="muted tiny">No se consideran las puntuaciones provisionales del universo inicial como una validación de calidad. Las acciones SEC son una referencia pendiente de conciliar con dilución, clases y splits. Se excluyen recomendaciones automáticas.</p></section>';
}
