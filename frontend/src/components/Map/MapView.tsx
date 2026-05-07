import { useEffect, useRef, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
// @ts-ignore
import MapboxDraw from '@mapbox/mapbox-gl-draw'
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css'
import * as turf from '@turf/turf'
import type { AOIFeature } from '../../types'

/** Limite massimo AOI in km² — valori più grandi vengono rifiutati. */
const MAX_AREA_KM2 = 500

interface MapViewProps {
  onAOIChange: (aoi: AOIFeature | null, areaKm2: number) => void
  onDrawReady?: (drawPolygon: () => void, clearPolygon: () => void) => void
}

export default function MapView({ onAOIChange, onDrawReady }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const drawRef = useRef<MapboxDraw | null>(null)
  const onDrawReadyRef = useRef(onDrawReady)
  useEffect(() => { onDrawReadyRef.current = onDrawReady }, [onDrawReady])

  const handleDrawChange = useCallback(() => {
    if (!drawRef.current) return
    const data = drawRef.current.getAll() as GeoJSON.FeatureCollection

    if (!data.features.length) {
      onAOIChange(null, 0)
      _clearBbox(mapRef.current)
      return
    }

    // Combina tutti i poligoni disegnati in un'unica feature
    const feature = data.features[0] as AOIFeature
    const areaSqM = turf.area(feature)
    const areaKm2 = areaSqM / 1_000_000

    onAOIChange(areaKm2 <= MAX_AREA_KM2 ? feature : null, areaKm2)
    _updateBbox(mapRef.current, feature)
  }, [onAOIChange])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      // Maptiler free tiles (basta una chiave gratuita o tile OSM raster)
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxzoom: 19,
          },
        },
        layers: [
          {
            id: 'osm-tiles',
            type: 'raster',
            source: 'osm-tiles',
          },
        ],
      },
      center: [8.55, 47.37],   // Svizzera — default coerente con intelligeo.ch
      zoom: 8,
    })

    const draw = new MapboxDraw({
      displayControlsDefault: false,
      defaultMode: 'simple_select',
      styles: drawStyles(),
    })

    // MapboxDraw si aspetta gl come mapbox, ma funziona su maplibre via cast
    map.addControl(draw as unknown as maplibregl.IControl, 'top-left')
    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right')
    map.addControl(new maplibregl.GeolocateControl({ trackUserLocation: false }), 'top-right')

    map.on('draw.create', handleDrawChange)
    map.on('draw.update', handleDrawChange)
    map.on('draw.delete', handleDrawChange)

    mapRef.current = map
    drawRef.current = draw

    if (onDrawReadyRef.current) {
      onDrawReadyRef.current(
        () => draw.changeMode('draw_polygon'),
        () => { draw.deleteAll(); handleDrawChange() },
      )
    }

    return () => {
      map.remove()
      mapRef.current = null
      drawRef.current = null
    }
  }, [handleDrawChange])

  return (
    <div
      ref={containerRef}
      className="w-full map-full"
      aria-label="Interactive map — draw a polygon to define your area of interest"
    />
  )
}

// ── Bbox helpers ───────────────────────────────────────────────────────────

const BBOX_SOURCE = 'aoi-bbox'
const BBOX_LAYER  = 'aoi-bbox-line'
const EMPTY_FC: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }

function _ensureBboxLayer(map: maplibregl.Map) {
  if (!map.getSource(BBOX_SOURCE)) {
    map.addSource(BBOX_SOURCE, { type: 'geojson', data: EMPTY_FC })
    map.addLayer({
      id: BBOX_LAYER,
      type: 'line',
      source: BBOX_SOURCE,
      paint: {
        'line-color': '#2f5ff5',
        'line-width': 1.2,
        'line-opacity': 0.45,
        'line-dasharray': [5, 4],
      },
    })
  }
}

function _updateBbox(map: maplibregl.Map | null, feature: GeoJSON.Feature) {
  if (!map) return
  _ensureBboxLayer(map)
  const [w, s, e, n] = turf.bbox(feature)
  const bboxPoly = turf.bboxPolygon([w, s, e, n])
  ;(map.getSource(BBOX_SOURCE) as maplibregl.GeoJSONSource).setData(bboxPoly)
}

function _clearBbox(map: maplibregl.Map | null) {
  if (!map || !map.getSource(BBOX_SOURCE)) return
  ;(map.getSource(BBOX_SOURCE) as maplibregl.GeoJSONSource).setData(EMPTY_FC)
}

// ── Stili personalizzati per MapboxDraw ────────────────────────────────────
function drawStyles() {
  const FILL   = '#2f5ff5'
  const STROKE = '#1e44d4'
  const WHITE  = '#ffffff'
  const VERTEX = '#ffcb2f'

  return [
    { id: 'gl-draw-polygon-fill', type: 'fill', filter: ['all', ['==', '$type', 'Polygon'], ['!=', 'mode', 'static']], paint: { 'fill-color': FILL, 'fill-opacity': 0.18 } },
    { id: 'gl-draw-polygon-stroke-active', type: 'line', filter: ['all', ['==', '$type', 'Polygon'], ['!=', 'mode', 'static']], layout: { 'line-join': 'round', 'line-cap': 'round' }, paint: { 'line-color': STROKE, 'line-width': 2.5, 'line-dasharray': [0.8, 2] } },
    { id: 'gl-draw-polygon-fill-static', type: 'fill', filter: ['all', ['==', '$type', 'Polygon'], ['==', 'mode', 'static']], paint: { 'fill-color': FILL, 'fill-opacity': 0.1 } },
    { id: 'gl-draw-polygon-stroke-static', type: 'line', filter: ['all', ['==', '$type', 'Polygon'], ['==', 'mode', 'static']], layout: { 'line-join': 'round', 'line-cap': 'round' }, paint: { 'line-color': STROKE, 'line-width': 2 } },
    { id: 'gl-draw-point-active', type: 'circle', filter: ['all', ['==', '$type', 'Point'], ['==', 'meta', 'vertex']], paint: { 'circle-radius': 5, 'circle-color': VERTEX, 'circle-stroke-color': WHITE, 'circle-stroke-width': 2 } },
  ]
}
