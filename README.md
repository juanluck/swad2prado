# swad2prado

Conversor **SWAD → PRADO/Moodle XML** (CLI).  
- **Usa CDATA + HTML (`<p>…</p>`)** para los enunciados.  
- **La categoría se pasa por `--category`**.  
- **Sin dependencias externas** (solo Python stdlib).  
- Incluye ejemplos **dummy** de *cultura general* para probar el flujo.

## Estructura

```
.
├─ swad2prado.py
├─ mapping.json
├─ requirements.txt
├─ examples/
│  ├─ swad.xml             # SWAD ficticio (cultura general)
│  ├─ prado_sample.xml     # PRADO/Moodle ficticio de referencia
│  └─ output/
│     └─ prado_out_demo.xml  # Generado con este repo (CDATA + categoría demo)
├─ tests/
│  └─ test_basic.py
└─ .github/
   └─ workflows/
      └─ ci.yml
```

## Uso

```bash
python swad2prado.py examples/swad.xml examples/output/prado_out.xml   --mapping mapping.json   --category "$course$/top/Banco importado desde SWAD"   --shuffle true
```

## Mapping
El `mapping.json` está adaptado a `examples/swad.xml` (estructura SWAD con `<stem>` y opciones en `answer/option` con `correct="Yes|No"`).  
Ajusta rutas si tu XML varía.

## CI y tests

Este repo incluye un workflow de **GitHub Actions** que:
1. Ejecuta `swad2prado.py` sobre `examples/swad.xml` con `mapping.json`.
2. Valida que el XML resultante:
   - Tiene CDATA en `<questiontext>/<text>` con `<p>…</p>`.
   - Contiene la categoría pasada por `--category`.
   - Conserva el número de preguntas.
   - Asigna `-25` a las respuestas incorrectas.

Para ejecutarlo localmente:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Licencia
GPL v3
