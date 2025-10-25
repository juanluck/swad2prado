# swad2prado

Conversor **SWAD → PRADO/Moodle XML** en modo CLI.

- Convierte ficheros de preguntas de **SWAD** a formato **PRADO/Moodle XML**.
- Usa **CDATA con HTML (`<p>…</p>`)** en los enunciados.
- La **categoría** se pasa por `--category` (obligatorio).
- **El mapping es opcional**: si no se indica `--mapping`, usa un **mapping integrado por defecto**.
- Sin dependencias externas (solo librerías estándar de Python).

---

## 🚀 Instalación en Linux (Ubuntu)

### 1️⃣ Clonar o copiar el proyecto
Descarga o clona el repositorio:
```bash
git clone https://github.com/tuusuario/swad2prado.git
cd swad2prado
```

### 2️⃣ Hacer el script ejecutable
```bash
chmod +x swad2prado.py
```

### 3️⃣ Añadirlo al PATH
Para instalarlo **solo para tu usuario** (sin root):
```bash
mkdir -p ~/.local/bin
cp swad2prado.py ~/.local/bin/swad2prado
chmod +x ~/.local/bin/swad2prado
```

Asegúrate de que `~/.local/bin` está en tu PATH (Ubuntu lo incluye por defecto).  
Si no, añade esta línea a tu `~/.bashrc` o `~/.zshrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Para hacerlo accesible a todos los usuarios:
```bash
sudo ln -s /ruta/a/swad2prado/swad2prado.py /usr/local/bin/swad2prado
```

### 4️⃣ Probar el comando
```bash
swad2prado --help
```

Deberías ver la ayuda del programa.  
Ya puedes ejecutar el comando desde cualquier directorio del sistema.

---

## 🧩 Uso básico

### Con mapping integrado (por defecto)
```bash
swad2prado examples/swad.xml output/prado_out.xml   --category "$course$/top/Banco importado desde SWAD"
```

### Con mapping personalizado
```bash
swad2prado examples/swad.xml output/prado_out.xml   --mapping mapping.json   --category "$course$/top/Tema 1"
```

### Otras opciones
- `--shuffle true|false` → baraja las respuestas (por defecto `true`).

---

## 🧠 Estructura del proyecto

```
.
├─ swad2prado.py           # Script principal (CLI ejecutable)
├─ mapping.json            # Mapping externo opcional
├─ examples/
│  ├─ swad.xml             # Ejemplo SWAD (cultura general)
│  ├─ prado_sample.xml     # Ejemplo PRADO/Moodle
│  └─ output/
│     └─ prado_out_demo.xml
├─ tests/
│  └─ test_basic.py
└─ .github/
   └─ workflows/
      └─ ci.yml
```

---

## 🧪 Tests

Para ejecutar los tests localmente:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

El repositorio incluye un **workflow de GitHub Actions** que ejecuta estos tests automáticamente en cada `push`.

---

## 📜 Licencia
GPL v3
---

## ✨ Créditos
Desarrollado por [Juanlu J. Laredo / UGR / ICAR].  
Inspirado en la necesidad de migrar bancos de preguntas desde **SWAD** a **PRADO** de forma automatizada y portable.
