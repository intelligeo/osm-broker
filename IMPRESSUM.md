# Impressum — OSM Broker

> Documento legale e informativo relativo all'applicazione **OSM Broker**,
> sviluppata e mantenuta da [INTELLIGEO.ch](https://www.intelligeo.ch).

---

## 1. Gestore del servizio

**INTELLIGEO.ch**  
Consulenza e sviluppo GIS / Web  
Terre di Pedemonte, Svizzera  
E-mail: [ask@intelligeo.ch](mailto:ask@intelligeo.ch)  
Web: [https://www.intelligeo.ch](https://www.intelligeo.ch)

---

## 2. Licenza del software

Il codice sorgente di OSM Broker è rilasciato sotto licenza **MIT**.

```
MIT License
Copyright (c) 2026 INTELLIGEO.ch

La presente licenza autorizza chiunque a usare, copiare, modificare, unire,
pubblicare, distribuire, sub-licenziare e/o vendere copie del Software,
a condizione che l'avviso di copyright e la presente licenza siano inclusi
in tutte le copie o parti sostanziali del Software.

IL SOFTWARE È FORNITO "COSÌ COM'È", SENZA GARANZIA DI ALCUN TIPO.
```

Testo completo: [LICENSE](./LICENSE)

### Librerie di terze parti principali

| Libreria | Licenza |
|---|---|
| [MapLibre GL JS](https://maplibre.org/) | BSD-3-Clause |
| [@mapbox/mapbox-gl-draw](https://github.com/mapbox/mapbox-gl-draw) | ISC |
| [FastAPI](https://fastapi.tiangolo.com/) | MIT |
| [GDAL/OGR](https://gdal.org/) | MIT / X11 |
| [DuckDB](https://duckdb.org/) | MIT |
| [React](https://react.dev/) | MIT |
| [Turf.js](https://turfjs.org/) | MIT |

---

## 3. Licenza dei dati

I dati geografici forniti dall'applicazione provengono da
**[OpenStreetMap](https://www.openstreetmap.org/copyright)**.

> © I collaboratori di OpenStreetMap  
> I dati di OpenStreetMap sono disponibili sotto licenza
> **[Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/)**.

### Obblighi per chi usa i dati esportati

- **Attribuzione**: qualsiasi prodotto derivato deve indicare chiaramente
  *"© Collaboratori di OpenStreetMap"* come fonte.
- **Share-alike**: le banche dati derivate devono essere distribuite con la
  stessa licenza ODbL.
- **Keep open**: se distribuisci una versione "chiusa" (Produced Work),
  devi comunque rendere disponibile la banca dati sottostante in forma aperta.

Il recupero dei dati avviene tramite la
**[HOT Raw Data API](https://github.com/hotosm/raw-data-api)**
(Humanitarian OpenStreetMap Team), che opera sullo stesso dataset OSM con
aggiornamento giornaliero.

---

## 4. Simbologia QGIS SwissMap

I file `.qml` inclusi facoltativamente negli ZIP esportati sono basati sullo
stile **SwissMap** per QGIS, sviluppato da INTELLIGEO.ch.  
Sono rilasciati sotto licenza **MIT** con lo stesso copyright del software.

---

## 5. Politica di uso corretto (Fair Use)

OSM Broker è un servizio gratuito offerto a titolo non commerciale.
Per garantirne la disponibilità a tutti si applicano le seguenti regole:

| Parametro | Limite |
|---|---|
| Area massima per esportazione | **500 km²** |
| Richieste simultanee per IP | **3** |
| Richieste totali al giorno per IP | **50** |
| Dimensione massima output stimata | ~ 500 MB |

**Usi non consentiti senza accordo scritto**:

- Scraping automatizzato o bulk download sistematico.
- Rivendita dei dati esportati come prodotto a pagamento.
- Integrazione in pipeline di produzione industriale ad alto volume.

Per esigenze oltre i limiti sopra indicati contattare
[ask@intelligeo.ch](mailto:ask@intelligeo.ch) per valutare un accordo dedicato.

INTELLIGEO.ch si riserva il diritto di sospendere l'accesso in caso di utilizzo
abusivo senza preavviso.

---

## 6. Esclusione di responsabilità

I dati OSM sono prodotti dalla comunità e possono contenere errori o lacune.
INTELLIGEO.ch non garantisce l'accuratezza, la completezza o l'idoneità dei
dati per scopi specifici. L'uso è a rischio e pericolo dell'utente.

---

## 7. Protezione dei dati

OSM Broker non raccoglie dati personali degli utenti. Le query e le aree di
interesse non vengono associate a identità individuali. I log del server
possono contenere indirizzi IP a scopo di diagnostica e anti-abuso, e vengono
conservati per un massimo di 30 giorni.

---

## 8. Contatto per supporto

Per bug, richieste di funzionalità o domande di natura tecnica:

- **E-mail**: [ask@intelligeo.ch](mailto:ask@intelligeo.ch)
- **GitHub Issues**: [github.com/intelligeo/osm-broker/issues](https://github.com/intelligeo/osm-broker/issues)

---

*Ultimo aggiornamento: maggio 2026*
