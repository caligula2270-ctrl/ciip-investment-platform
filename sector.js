/* CIIP v1.3: segregated sector research models and official SEC filings.
 * These are indicative aggregate models, not verified equity-per-share targets. */
function ciipSectorMoney(v){
  return typeof v==="number"&&Number.isFinite(v)
    ?ciipMoney(v/1000000)+" M USD":"—";
}
function ciipSectorPct(v){
  return typeof v==="number"&&Number.isFinite(v)?ciipValuePct(v):"—";
}
function ciipSectorModelLabel(code){
  return ({
    software_owner_cash_sbc_stress:"Software · beneficio del propietario con coste SBC",
    payments_income_capped_cashflow:"Redes de pagos · caja limitada por beneficio",
    capital_heavy_peak_capex_stress:"Capital intensivo · estrés de inversiones",
    standard_dcf:"Modelo sectorial específico pendiente"
  })[code]||"Pendiente de clasificación sectorial";
}
function ciipSectorModelPanel(ticker){
  const record=ciipHistorical(ticker);
  if(!record?.sector_valuation){
    return '<section class="panel"><h2>Valoración sectorial</h2><div class="notice">Pendiente de nueva extracción SEC. No se han inventado escenarios sectoriales.</div></section>';
  }
  const m=record.sector_valuation;
  const sc=m.scenarios||{};
  const group=["conservador","base","optimista"].map(key=>{
    const r=sc[key];
    if(!r)return '';
    const title=key==="base"?"Base":key==="conservador"?"Conservador":"Optimista";
    return '<article class="ciip-result-card">'+
      '<div class="ciip-result-label">'+title+' · importe agregado</div>'+
      '<strong class="ciip-result-primary">'+ciipSectorMoney(r.equity_value_usd)+'</strong>'+
      '<div class="ciip-result-terminal"><span>Peso terminal</span><strong>'+ciipSectorPct(r.terminal_weight_pct)+'</strong></div>'+
      '<p class="muted tiny">Crecimiento '+ciipSectorPct(r.growth_1_5_pct)+' / '+ciipSectorPct(r.growth_6_10_pct)+' · tasa exigida '+ciipSectorPct(r.discount_pct)+'</p>'+
      '</article>';
  }).join('');
  const status=({
    not_applicable:"Sector no modelado",
    insufficient:"Datos insuficientes",
    review_required:"Estimación sujeta a revisión",
    aggregate_research_only:"Solo importes patrimoniales agregados"
  })[m.status]||m.status;
  const warning=(m.warnings||[]).map(x=>'<li>'+esc(x)+'</li>').join('');
  const assumptions=m.adjustments||{};
  const rows=Object.entries(assumptions).filter(([k,v])=>typeof v==="number").map(([k,v])=>
    '<tr><td>'+esc(k.replaceAll('_',' '))+'</td><td>'+ciipSectorMoney(v)+'</td></tr>');
  return '<section class="panel"><h2>Modelo sectorial diferenciado</h2>'+
   '<p><b>'+esc(ciipSectorModelLabel(m.model))+'</b> · '+esc(status)+'</p>'+
   '<p class="muted">Los modelos son ilustrativos y presentan únicamente valoraciones agregadas. No calculan un precio de compra verificable por acción, no sustituyen las notas de capital y no emiten recomendaciones.</p>'+
   '<p><span class="muted tiny">Caja de referencia del modelo:</span> <b>'+ciipSectorMoney(m.normalized_cash_usd)+'</b></p>'+
   (group?'<div class="ciip-result-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:12px">'+group+'</div>':'<div class="notice">Modelo sectorial bloqueado por información insuficiente. No se ofrece valoración.</div>')+
   (rows.length?table(['Ajuste / concepto','Importe'],rows):'')+
   (warning?'<div class="notice"><b>Limitaciones y revisión necesaria</b><ul>'+warning+'</ul></div>':'')+
   '</section>';
}
function ciipCapitalNotesPanel(ticker){
 const d=ciipHistorical(ticker),c=d?.capital_filings,shares=d?.share_reconciliation;
 if(!c)return '<section class="panel"><h2>Conciliación de acciones y notas de capital</h2><div class="notice">Faltan referencias a las últimas presentaciones SEC. Requiere actualización antes de verificar acciones.</div></section>';
 const files=(c.filings||[]).map(f=>'<li><a class="link" href="'+esc(f.document_url)+'" rel="noopener noreferrer" target="_blank">'+
    esc(f.form)+' · '+esc(f.filed)+' · documento original SEC ↗</a></li>').join('');
 const checklist=(c.review_topics||[]).map(x=>'<li>'+esc(x)+'</li>').join('');
 const delta=shares?.quarter_diluted_vs_basic_pct;
 const source=shares?.latest_quarter_diluted;
 return '<section class="panel"><h2>Conciliación de acciones · documentos oficiales</h2>'+
  '<p class="muted">Las fechas de las presentaciones y sus documentos se obtienen del índice oficial de la SEC. <b>Las notas de capital todavía no se han revisado ni reconciliado documentalmente.</b></p>'+
  '<p><b>Acciones plenamente diluidas actuales verificadas: NO DISPONIBLES.</b></p>'+
  '<p class="muted tiny">Dato XBRL de media ponderada trimestral: '+
   (source?ciipMoney(source.value/1000000)+' millones ('+esc(source.end)+')':'—')+
   '. Diferencia media trimestral/básicas: '+ciipSectorPct(delta)+'. No equivale a acciones actuales plenamente diluidas.</p>'+
  '<h3>Últimas presentaciones</h3><ul>'+(files||'<li>Sin presentaciones descargadas</li>')+'</ul>'+
  '<h3>Notas que deben conciliarse</h3><ul>'+checklist+'</ul>'+
  '<div class="notice">Estado: '+esc(c.status)+'. '+esc(c.warning||'Revisión documental pendiente')+'</div>'+
 '</section>';
}
function ciipSectorResearchView(){
 const selected=companies.find(c=>c.Ticker===ciipValSelected)?ciipValSelected:"MSFT";
 const options=companies.map(c=>'<option value="'+esc(c.Ticker)+'" '+(c.Ticker===selected?'selected':'')+'>'+esc(c.Ticker+' · '+c.Empresa)+'</option>').join('');
 return '<section class="panel"><h2>Sector y estructura de capital</h2>'+
  '<p class="muted">Modelos de análisis distintos para software, redes de pagos y empresas intensivas en inversión; no sustituyen la valoración financiera completa.</p>'+
  '<select aria-label="Seleccionar compañía" class="select" style="width:100%;max-width:560px" onchange="ciipValSelected=this.value;render()">'+options+'</select></section>'+
  ciipSectorModelPanel(selected)+ciipCapitalNotesPanel(selected);
}
