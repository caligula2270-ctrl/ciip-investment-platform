/* Universo inicial. Son empresas mencionadas por el usuario, NO confirmación de cartera actual. */
window.QVR_SEED = {
  version: 1,
  asOf: '2026-10-22',
  investors: [
    {id:'galician',name:'Galician Investor',initials:'GI',method:'Quality compounders · moats · largo plazo',nature:'inversor',detail:'Empresas destacadas en la información proporcionada; no equivale a una cartera trimestral completa.'},
    {id:'anchor',name:'Best Anchor Stocks',initials:'BA',method:'Quality growth · reinversión · estabilidad',nature:'investigación',detail:'Lista de empresas mantenidas o cubiertas según el prompt. Cubierta no significa necesariamente mantenida.'},
    {id:'rochon',name:'François Rochon / Giverny',initials:'FR',method:'Compounding · disciplina de capital',nature:'gestora',detail:'El prompt no identifica valores individuales verificables de su cartera. No se atribuyen posiciones por analogía.'},
    {id:'sleep',name:'Nick Sleep / Nomad',initials:'NS',method:'Scale economies shared · décadas',nature:'histórico',detail:'Referencias históricas a Amazon y Costco. No son posiciones actuales.'},
    {id:'vinall',name:'Rob Vinall / RV Capital',initials:'RV',method:'Empresas excepcionales · paciencia',nature:'gestora',detail:'No se proporcionaron posiciones concretas verificables. No se crean participaciones ficticias.'},
    {id:'cobas',name:'Cobas Asset Management',initials:'CO',method:'Value · margen de seguridad · contrarian',nature:'gestora',detail:'Compañías procedentes de sus dos carteras semestrales 2S25, según el prompt; varios fondos cuentan como un mismo gestor.'}
  ],
  companies: [
    {s:'KNSL',n:'Kinsale Capital',sector:'Seguros',country:'Estados Unidos',currency:'USD',moat:'Suscripción especializada E&S y disciplina de riesgo',quality:88,links:[['galician','referencia']]},
    {s:'CPRT',n:'Copart',sector:'Servicios',country:'Estados Unidos',currency:'USD',moat:'Red bilateral de compradores, parcelas y logística difícil de replicar',quality:93,links:[['galician','referencia'],['anchor','referencia']]},
    {s:'DNP.WA',n:'Dino Polska',sector:'Consumo',country:'Polonia',currency:'PLN',moat:'Densidad local, red logística y proximidad',quality:85,links:[['galician','referencia']]},
    {s:'CSU.TO',n:'Constellation Software',sector:'Software',country:'Canadá',currency:'CAD',moat:'Costes de cambio y adquisiciones disciplinadas en software vertical',quality:95,links:[['anchor','cobertura']]},
    {s:'ADBE',n:'Adobe',sector:'Software',country:'Estados Unidos',currency:'USD',moat:'Estándares creativos, ecosistema y costes de cambio',quality:86,links:[['anchor','cobertura']]},
    {s:'AMZN',n:'Amazon',sector:'Plataformas',country:'Estados Unidos',currency:'USD',moat:'Escala logística, AWS, Marketplace y Prime',quality:93,links:[['anchor','cobertura'],['sleep','historica']]},
    {s:'ASML',n:'ASML',sector:'Semiconductores',country:'Países Bajos',currency:'USD',moat:'Tecnología EUV, conocimiento y ecosistema de proveedores',quality:96,links:[['anchor','cobertura']]},
    {s:'ATCO-A.ST',n:'Atlas Copco',sector:'Industria',country:'Suecia',currency:'SEK',moat:'Servicio posventa, distribución y base instalada',quality:90,links:[['anchor','cobertura']]},
    {s:'AAON',n:'AAON',sector:'Industria',country:'Estados Unidos',currency:'USD',moat:'Especialización HVAC y configuración de equipos',quality:81,links:[['anchor','cobertura']]},
    {s:'DE',n:'Deere & Company',sector:'Industria',country:'Estados Unidos',currency:'USD',moat:'Red de distribuidores, servicio y marca',quality:85,links:[['anchor','cobertura']]},
    {s:'DGE.L',n:'Diageo',sector:'Consumo',country:'Reino Unido',currency:'GBp',moat:'Marcas premium y distribución',quality:82,links:[['anchor','cobertura']]},
    {s:'DHR',n:'Danaher',sector:'Salud',country:'Estados Unidos',currency:'USD',moat:'Procesos de negocio, instrumentos y consumibles',quality:89,links:[['anchor','cobertura']]},
    {s:'FIVE',n:'Five Below',sector:'Consumo',country:'Estados Unidos',currency:'USD',moat:'Formato minorista y ejecución; foso por comprobar',quality:65,links:[['anchor','cobertura']]},
    {s:'FOUR',n:'Shift4 Payments',sector:'Pagos',country:'Estados Unidos',currency:'USD',moat:'Integración de pagos en negocios y software',quality:78,links:[['anchor','cobertura']]},
    {s:'FRPH',n:'FRP Holdings',sector:'Inmobiliario',country:'Estados Unidos',currency:'USD',moat:'Ubicaciones y activos singulares',quality:73,links:[['anchor','cobertura']]},
    {s:'INTU',n:'Intuit',sector:'Software',country:'Estados Unidos',currency:'USD',moat:'Costes de cambio, datos y ecosistema fiscal',quality:91,links:[['anchor','cobertura']]},
    {s:'JDG.L',n:'Judges Scientific',sector:'Industria',country:'Reino Unido',currency:'GBp',moat:'Instrumentación científica de nicho',quality:83,links:[['anchor','cobertura']]},
    {s:'KEYS',n:'Keysight Technologies',sector:'Industria',country:'Estados Unidos',currency:'USD',moat:'Know-how, validación y equipamiento especializado',quality:86,links:[['anchor','cobertura']]},
    {s:'MEDP',n:'Medpace',sector:'Salud',country:'Estados Unidos',currency:'USD',moat:'Especialización CRO, confianza de clientes',quality:88,links:[['anchor','cobertura']]},
    {s:'7974.T',n:'Nintendo',sector:'Entretenimiento',country:'Japón',currency:'JPY',moat:'Franquicias, propiedad intelectual y ecosistema',quality:90,links:[['anchor','cobertura']]},
    {s:'RMD',n:'ResMed',sector:'Salud',country:'Estados Unidos',currency:'USD',moat:'Canal clínico, dispositivos y software conectado',quality:88,links:[['anchor','cobertura']]},
    {s:'STVN',n:'Stevanato Group',sector:'Salud',country:'Italia',currency:'USD',moat:'Cualificación farmacéutica y procesos críticos',quality:81,links:[['anchor','cobertura']]},
    {s:'TRUP',n:'Trupanion',sector:'Seguros',country:'Estados Unidos',currency:'USD',moat:'Distribución veterinaria y relación con clientes; incierto',quality:70,links:[['anchor','cobertura']]},
    {s:'TXN',n:'Texas Instruments',sector:'Semiconductores',country:'Estados Unidos',currency:'USD',moat:'Escala fabril, catálogo analógico y ciclos largos',quality:91,links:[['anchor','cobertura']]},
    {s:'ZTS',n:'Zoetis',sector:'Salud',country:'Estados Unidos',currency:'USD',moat:'Marcas, I+D veterinaria y red de distribución',quality:89,links:[['anchor','cobertura']]},
    {s:'COST',n:'Costco',sector:'Consumo',country:'Estados Unidos',currency:'USD',moat:'Beneficios de escala compartidos con socios y retención',quality:95,links:[['sleep','historica']]},
    {s:'GLNG',n:'Golar LNG',sector:'Energía',country:'Bermudas',currency:'USD',moat:'Activos FLNG escasos y contratos complejos',quality:70,links:[['cobas','fondo']]},
    {s:'0001.HK',n:'CK Hutchison',sector:'Infraestructura',country:'Hong Kong',currency:'HKD',moat:'Puertos, concesiones y activos diversos',quality:68,links:[['cobas','fondo']]},
    {s:'ATYM.L',n:'Atalaya Mining',sector:'Materiales',country:'España',currency:'GBp',moat:'Acceso a activos minerales; expuesta al cobre',quality:63,links:[['cobas','fondo']]},
    {s:'DAN.MI',n:'Danieli',sector:'Industria',country:'Italia',currency:'EUR',moat:'Ingeniería y relación con clientes siderúrgicos',quality:67,links:[['cobas','fondo']]},
    {s:'BWO.OL',n:'BW Offshore',sector:'Energía',country:'Noruega',currency:'NOK',moat:'Experiencia offshore y contratos FPSO',quality:67,links:[['cobas','fondo']]},
    {s:'BWE.OL',n:'BW Energy',sector:'Energía',country:'Noruega',currency:'NOK',moat:'Activos de producción; muy cíclica',quality:61,links:[['cobas','fondo']]},
    {s:'WIZZ.L',n:'Wizz Air',sector:'Transporte',country:'Reino Unido',currency:'GBp',moat:'Coste unitario; expuesta al ciclo aéreo',quality:56,links:[['cobas','fondo']]},
    {s:'BRAV3.SA',n:'Brava Energia',sector:'Energía',country:'Brasil',currency:'BRL',moat:'Producción de hidrocarburos; precio de mercado',quality:59,links:[['cobas','fondo']]},
    {s:'TGS.OL',n:'TGS',sector:'Energía',country:'Noruega',currency:'NOK',moat:'Biblioteca de datos sísmicos y relaciones sectoriales',quality:67,links:[['cobas','fondo']]},
    {s:'DBG.PA',n:'Derichebourg',sector:'Industria',country:'Francia',currency:'EUR',moat:'Escala en reciclaje y logística',quality:65,links:[['cobas','fondo']]},
    {s:'MEL.MC',n:'Meliá Hotels',sector:'Consumo',country:'España',currency:'EUR',moat:'Marca y gestión hotelera',quality:71,links:[['cobas','fondo']]},
    {s:'SCYR.MC',n:'Sacyr',sector:'Infraestructura',country:'España',currency:'EUR',moat:'Concesiones de larga duración',quality:70,links:[['cobas','fondo']]},
    {s:'TRE.MC',n:'Técnicas Reunidas',sector:'Industria',country:'España',currency:'EUR',moat:'Ingeniería especializada, riesgo de ejecución',quality:60,links:[['cobas','fondo']]},
    {s:'GRF.MC',n:'Grifols',sector:'Salud',country:'España',currency:'EUR',moat:'Red de centros de plasma y barreras regulatorias',quality:69,links:[['cobas','fondo']]},
    {s:'ALM.MC',n:'Almirall',sector:'Salud',country:'España',currency:'EUR',moat:'Dermatología y cartera de tratamientos',quality:69,links:[['cobas','fondo']]},
    {s:'GEST.MC',n:'Gestamp',sector:'Industria',country:'España',currency:'EUR',moat:'Relaciones de OEM; alta intensidad de capital',quality:60,links:[['cobas','fondo']]},
    {s:'DOM.MC',n:'Global Dominion',sector:'Industria',country:'España',currency:'EUR',moat:'Servicios de ingeniería y eficiencia',quality:66,links:[['cobas','fondo']]},
    {s:'MCM.MC',n:'Miquel y Costas',sector:'Materiales',country:'España',currency:'EUR',moat:'Papeles especializados y procesos',quality:73,links:[['cobas','fondo']]},
    {s:'TUB.MC',n:'Tubacex',sector:'Materiales',country:'España',currency:'EUR',moat:'Metalurgia especializada; demanda cíclica',quality:64,links:[['cobas','fondo']]}
  ],
  dossiers: {
    CPRT: {summary:'La tesis combina red internacional de compradores, ventajas logísticas y barreras físicas. El descenso de volúmenes puede ser temporal, pero hay que comprobar márgenes, frecuencia de siniestros y reinversión.',risk:'Volúmenes de vehículos siniestrados; cambio regulatorio; nuevos competidores; capital inmovilizado en terrenos.',check:'Revisar resultados trimestrales y sostenibilidad de free cash flow. No confundir caída bursátil con descuento probado.'},
    AMZN: {summary:'AWS, publicidad y logística ofrecen varios motores de monetización; la rentabilidad futura depende de cuánto capital consuman los centros de datos.',risk:'Capex masivo; rentabilidad del gasto en IA; competencia cloud; regulación y consumo.',check:'Separar AWS, publicidad y retail en valoración por partes; normalizar capex y FCF.'},
    'CSU.TO': {summary:'Software vertical y adquisiciones descentralizadas de nicho con recurrentes costes de cambio y un sofisticado proceso de asignación de capital.',risk:'Precios de adquisiciones, dilución y retornos incrementales; disrupción por IA.',check:'No usar PER GAAP aislado. Evaluar cash flow operativo, adquisiciones y crecimiento orgánico.'},
    'ATYM.L':{summary:'Cobre con activos reales y expansión potencial; la tesis depende del ciclo y los costes de explotación.',risk:'Precio del cobre, permisos, capex, ley mineral y ejecución.',check:'Valorar precio normalizado del cobre y escenarios de inversión; no asumir moat amplio.'}
  },
  sources: [
    {title:'Universo de inversores y carteras',kind:'Base inicial',date:'2026-10-22',url:'',description:'Información aportada en el prompt del usuario: NO representa comprobación de tenencias vigentes.'},
    {title:'Copart — histórico cotización',kind:'Cotización',date:'2026-10-20',url:'https://stockanalysis.com/stocks/cprt/history/',description:'Precio verificado para 20/10/2026; no es cotización en tiempo real.'},
    {title:'Amazon — histórico cotización',kind:'Cotización',date:'2026-10-21',url:'https://chartexchange.com/symbol/nasdaq-amzn/historical/',description:'Cierre publicado para 21/10/2026.'},
    {title:'Constellation — histórico cotización',kind:'Cotización',date:'2026-10-20',url:'https://ycharts.com/companies/CSU.TO/price',description:'Último cierre confirmado sin ambigüedad, 20/10/2026.'},
    {title:'Copart — modelo TIKR (mayo)',kind:'Valuación de terceros',date:'2026-05-26',url:'https://www.tikr.com/blog/copart-stock-record-auction-prices-and-39-street-upside-signal-a-mispricing-in-2026',description:'Objetivos futuros de terceros, no valor intrínseco actual ni garantía.'},
    {title:'Amazon — Morningstar (febrero)',kind:'Valuación de terceros',date:'2026-02-12',url:'https://www.morningstar.com/stocks/after-earnings-is-amazon-stock-buy-sell-or-fairly-valued-10',description:'Valor razonable histórico, que requiere actualización antes de usarse.'},
    {title:'Constellation — Morningstar (mayo)',kind:'Valuación de terceros',date:'2026-05-13',url:'https://www.morningstar.com/company-reports/1482009-constellation-software-is-deploying-more-capital-in-2026',description:'Perspectiva y valor razonable de terceros; usar como contraste, no cifra concluyente.'}
  ]
};
window.QVR_FALLBACK_QUOTES = {
  asOf: '2026-10-22',
  quotes: {
    'CPRT':{price:27.83,date:'2026-10-20',currency:'USD',source:'stockanalysis.com',sourceUrl:'https://stockanalysis.com/stocks/cprt/history/',kind:'cierre'},
    'AMZN':{price:262.36,date:'2026-10-21',currency:'USD',source:'ChartExchange',sourceUrl:'https://chartexchange.com/symbol/nasdaq-amzn/historical/',kind:'cierre'},
    'CSU.TO':{price:3240,date:'2026-10-20',currency:'CAD',source:'YCharts',sourceUrl:'https://ycharts.com/companies/CSU.TO/price',kind:'cierre'}
  }
};
