/* CIIP v1.4 five-issuer source-backed research audits.
   Inputs are SEC companyfacts and a dated, curated evidence ledger. */
let ciipAuditData=null,ciipAuditError='',ciipAuditSelected='MSFT';
async function refreshCiipAudits(){
 try{
   const r=await fetch('./audits/latest.json?t='+Date.now(),{cache:'no-store'});
   if(!r.ok)throw Error('HTTP '+r.status);
   const d=await r.json();
   if(d.schema!=='ciip-issuer-research-audit-v1')throw Error('Formato no reconocido');
   ciipAuditData=d;ciipAuditError='';
 }catch(e){ciipAuditError=e.message;ciipAuditData=null;}
 if(state.tab==='audits')render();
}
function ciipAuditChoose(ticker){
  ciipAuditSelected=ticker;render();
}
function ciipAuditNumber(n,suffix=''){
  return typeof n==='number'&&Number.isFinite(n)?n.toLocaleString('es-ES',{maximumFractionDigits:1})+suffix:'—';
}
function ciipAuditReadout(){
 const d=ciipAuditData;
 if(!d)return '<section class="panel"><h2>Auditoría fundamental</h2><div class="notice">El expediente automático no está disponible todavía. '+esc(ciipAuditError||'Pendiente de la primera ejecución')+'</div></section>';
 const entries=d.companies||{},keys=Object.keys(entries);
 const selected=entries[ciipAuditSelected]?ciipAuditSelected:keys[0],item=entries[selected];
 if(!item)return '<div class="notice">Sin expedientes de compañías.</div>';
 const source=item.reference_filing, filing=item.latest_official_filing;
 const evidence=(item.evidence_ledger||[]).map((e,i)=>
  '<article style="padding:12px 0;border-bottom:1px solid #33455e">'+
  '<b>'+esc(e.topic)+'</b><p class="muted tiny">'+esc(e.fact)+'</p>'+
  '<p>'+esc(e.impact)+'</p>'+
  '<a class="link tiny" href="'+esc(e.source)+'" target="_blank" rel="noopener noreferrer">Nota original SEC / IR ↗</a>'+
  '<p class="muted tiny">Ubicación: '+esc(e.location)+'</p></article>').join('');
 const hist=item.financials_five_years||[];
 const rows=[
  ['Ingresos (M USD)','revenue_musd'],['Margen operativo (%)','operating_margin_pct'],
  ['Margen neto (%)','net_margin_pct'],['CFO (M USD)','cfo_musd'],
  ['CAPEX (M USD)','capex_musd'],['FCF reportado proxy (M USD)','reported_fcf_musd'],
  ['SBC (M USD)','sbc_musd'],['CAPEX/CFO (%)','capex_to_cfo_pct']
 ].map(([name,key])=>'<tr><td><b>'+esc(name)+'</b></td>'+
 hist.map(y=>'<td>'+ciipAuditNumber(y[key])+'</td>').join('')+'</tr>');
 const docs=item.manual_review_checklist||[];
 const opts=keys.map(k=>'<option value="'+esc(k)+'" '+(k===selected?'selected':'')+'>'+esc(k)+' · '+esc(entries[k].company)+'</option>').join('');
 const model=item.sector_valuation||{};
 const scenarios=Object.entries(model.scenarios_aggregate||{}).map(([k,v])=>
   '<article class="ciip-result-card" style="min-width:0"><div class="ciip-result-label">'+esc(k)+'</div>'+
   '<strong class="ciip-result-primary">'+ciipAuditNumber((v.equity_value_usd||0)/1000000)+' M USD</strong>'+
   '<p class="muted tiny">Importe agregado ilustrativo · peso terminal '+ciipAuditNumber(v.terminal_weight_pct,'%')+'</p></article>').join('');
 const issues=(item.open_issues||[]).map(x=>'<li>'+esc(x)+'</li>').join('');
 const sources=filing?.document_url?'<a class="link" href="'+esc(filing.document_url)+'" target="_blank" rel="noopener noreferrer">Última presentación SEC ↗</a>':'Índice SEC no disponible';
 return '<section class="panel"><h2>Auditoría fundamental · cinco compañías</h2>'+
  '<p class="muted">Informe de investigación con evidencias identificadas y controles reproducibles. No es una auditoría de cuentas independiente ni una recomendación de inversión. Se mantienen pendientes las notas no conciliadas.</p>'+
  '<select class="select" style="width:100%;max-width:560px" onchange="ciipAuditChoose(this.value)">'+opts+'</select>'+
  '<p class="muted tiny">Evidencias revisadas con corte '+esc(d.source_review_as_of)+' · extracción SEC '+esc(d.sec_generated_at)+' · generado '+esc(d.generated_at)+'</p></section>'+
  '<section class="panel"><h2>'+esc(item.company)+'</h2>'+
  '<p><b>Situación:</b> '+esc(item.quality_stage)+' · último expediente: '+esc(item.filing_status)+'</p>'+
  '<p><b>Modelo sectorial:</b> '+esc(model.model||'—')+' · '+esc(model.status||'—')+
  ' · acciones plenamente diluidas verificadas: <b>NO</b></p>'+
  '<p class="muted">'+esc(item.business_assessment||'')+'</p>'+
  '<p>'+sources+'</p><p><a class="link" href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">Documento base de la revisión ↗</a></p>'+
  (issues?'<div class="notice"><b>Cuestiones abiertas</b><ul>'+issues+'</ul></div>':'')+'</section>'+
  '<section class="panel"><h2>Serie anual SEC · cinco ejercicios</h2>'+
  table(['Indicador',...hist.map(x=>x.fy_end)],rows)+
  '<p class="muted tiny">CAPEX/CFO y CFO−CAPEX son cálculos, no medidas ajustadas auditadas. — indica dato ausente.</p></section>'+
  '<section class="panel"><h2>Modelo de escenarios sectoriales</h2>'+
  (scenarios?'<div class="ciip-result-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:12px">'+scenarios+'</div>':
  '<p class="muted">Bloqueado por datos o sector. No existe una valoración sustentada.</p>')+
  '<p class="muted tiny">No se publica valor por acción ni precio objetivo mientras no se verifique la dilución actual y los derechos económicos.</p></section>'+
  '<section class="panel"><h2>Revisión de notas y trazabilidad</h2>'+evidence+
  '<h3>Comprobaciones pendientes</h3><ul>'+docs.map(esc).map(x=>'<li>'+x+'</li>').join('')+'</ul>'+
  '<p class="muted tiny">'+esc(item.disclaimer||'')+'</p></section>';
}
