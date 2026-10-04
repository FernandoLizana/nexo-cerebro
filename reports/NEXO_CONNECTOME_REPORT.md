# Conectoma computacional v1

**Archivo:** `configs/connectome/connectome_v1.yaml`  
**Módulos:** 15  
**Conexiones:** 15  

## Propósito

Grafo funcional **operacional** (no escala 86B del blueprint legacy) para enrutar señales entre módulos cognitivos con peso, latencia y gating.

## Exportaciones

- `reports/CONNECTOME_GRAPH.json`
- `reports/CONNECTOME_GRAPH.graphml`

## Validación

```python
ConnectomeGraph.from_yaml(...).validate()  # sin errores
```

## Lesiones virtuales (planificado Sprint 10)

`nexo/interventions/lesion.py` — desactivar aristas o aumentar latencia.
