/* CIIP per-share valuation v1: conditional scenario values with source hierarchy. */
let ciipPerShare=null,ciipPerShareError='';
async function refreshCiipPerShare(){
 try{
  const r=await fetch('./audits/per_share_latest.json?t='+Date.now(),{cache:'no-store'});
  if(!r.ok)throw Error('HTTP '+r.status);
  const d=await r.json();
  if(d.schema!=='ciip-per-share-valuation-v1')throw Error('Formato inesperado');
  ciipPerShare=d;ciipPerShareError='';
 }catch(e){ciipPerShare=null;ciipPerShareError=e.message}
 if(state.tab==='per_share')render();
}
function ciipPerShareView(){
 const d=ciipPerShare;
 if(!d)return '<section class="panel"><h2>Valoraciones individualizadas</h2><div class="notice">Pendiente de generación: '+esc(ciipPerShareError||'Sin resultados')+'</div></section>';
 const stocks=Object.values(d.companies||{});
 let cards=stocks.map(x=>{
  const base=x.scenario_values?.base;
  const bear=x.scenario_values?.conservador;
  const bull=x.scenario_values?.optimista;
  const quote=x.quote;
  const fmt=n=>typeof n==='number'?ciipMoney(n):'—';
  const price=quote?fmt(Number(quote.price))+' USD · '+esc(quote.date):'No verificable / sin cotización reciente';
  const margins=base?.margin_price_to_value_pct;
  const rowLabel='<strong>'+esc(x.ticker)+'</strong> · '+esc(x.company);
  return '<article class="ciip-result-card"><h3>'+rowLabel+'</h3>'+
   '<p class="muted tiny">Cierre proveedor: '+price+'</p>'+
   '<div class="ciip-result-primary-block"><span class="ciip-result-label">Valor por acción · escenario base</span>'+
   '<strong class="ciip-result-primary">'+fmt(base?.equity_per_share_usd)+' USD</strong>'+
   '<span class="ciip-result-unit">Modelo condicional — no precio objetivo certificado</span></div>'+
   '<div class="ciip-result-pairs">'+
   '<div class="ciip-result-metric"><span class="ciip-result-label">Conservador</span><strong>'+fmt(bear?.equity_per_share_usd)+'</strong></div>'+
   '<div class="ciip-result-metric"><span class="ciip-result-label">Optimista</span><strong>'+fmt(bull?.equity_per_share_usd)+'</strong></div>'+
   '</div>'+
   '<p class="muted tiny">Margen precio/valor base: '+(margins===null||margins===undefined?'—':fmt(margins)+'%')+
   ' · Acciones estimadas: '+fmt(x.denominator?.central_m)+' M</p>'+
   '<p class="muted tiny">Denominador: '+esc(x.denominator?.status||'no conciliado')+
   ' · Estado: '+esc(x.status||'pendiente')+'</p>'+
   '<button class="btn secondary" data-ticker="'+esc(x.ticker)+'" onclick="ciipPerShareSelect(this.dataset.ticker)">Consultar detalle</button></article>';
 }).join('');
 const chosen=d.companies[ciipAuditSelected]||stocks[0];
 const v=chosen;
 const detail=v?(()=>{
  const t=v.denominator;
  const notes=(v.additional_issues||[]).map(s=>'<li>'+esc(s)+'</li>').join('');
  const tableRows=Object.entries(v.scenario_values||{}).map(([label,s])=>'<tr><td>'+esc(label)+'</td>'+
    '<td>'+ciipMoney(s.analyst_assumptions.owner_cf1_m)+'</td>'+
    '<td>'+ciipValuePct(s.analyst_assumptions.g1_pct)+'</td>'+
    '<td>'+ciipValuePct(s.analyst_assumptions.ke_pct)+'</td>'+
    '<td>'+ciipMoney(s.equity_per_share_usd)+'</td>'+
    '<td>'+ciipMoney(s.share_count_sensitivity.high_dilution_value_usd)+' – '+
      ciipMoney(s.share_count_sensitivity.low_dilution_value_usd)+'</td></tr>');
  return '<section class="panel"><h2>'+esc(v.company)+' · conciliación y escenarios</h2>'+
   '<p class="muted">Acciones básicas y dilución proyectada corresponden a fechas diferentes. El sistema no puede certificar acciones plenamente diluidas actuales sin revisar emisiones posteriores, premios y posibles derechos de conversión.</p>'+
   '<p><b>Puente de acciones:</b> '+esc(t.formula)+'</p>'+
   '<p><b>Banda de dilución (millones):</b> '+ciipMoney(t.low_m)+' – '+ciipMoney(t.high_m)+
   ' · central '+ciipMoney(t.central_m)+'</p>'+
   table(['Caso','Caja inicial M USD','Crecimiento 1-5','Retorno exigido','USD por acción','Banda dilución USD'],tableRows)+
   '<p class="muted tiny">Las cifras del flujo inicial, crecimiento y coste de capital son hipótesis de analista, NO guidance. Cada FCF se incrementa ya en el primer año por el crecimiento asignado.</p>'+
   '<p><b>Caja inicial necesaria para justificar cotización manteniendo el caso base:</b> '+
   (v.base_cash_required_to_match_last_price_musd==null?'—':ciipMoney(v.base_cash_required_to_match_last_price_musd)+' M USD')+'</p>'+
   '<p><a class="link" target="_blank" rel="noopener noreferrer" href="'+esc(t.anchor_source||t.source)+'">Abrir presentación SEC usada para el denominador ↗</a></p>'+
   '<div class="notice"><b>Pendientes para aprobación</b><ul>'+notes+'</ul></div></section>';
 })():'';
 return '<section class="panel"><h2>Valoraciones por acción · cinco empresas</h2>'+
  '<p class="muted">Modelos condicionales con bandas de dilución, supuestos explícitos y cierres de proveedor de cotización. Ningún precio es definitivo o aprobado. El informe se recalcula al actualizar datos SEC.</p>'+
  '<p class="muted tiny">Datos hasta '+esc(d.as_of)+' · fase '+esc(d.readiness)+'</p></section>'+
  '<div class="ciip-result-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:12px">'+cards+'</div>'+detail;
}
function ciipPerShareSelect(ticker){ciipAuditSelected=ticker;render();}
