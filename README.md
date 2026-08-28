# BlackMamba Tuner

Afinador cromático de guitarra en tiempo real construido sobre librerías maduras de audio y DSP, no sobre detección casera de frecuencia.

## Arquitectura

```text
Guitarra / mic / interfaz
        │
        ▼
sounddevice / PortAudio
        │
        ▼
ring buffer de audio
        │
        ▼
PitchEngine
  └─ LibrosaPyinEngine
        │
        ▼
Hz + confidence
        │
        ▼
nota + target Hz + cents
        │
        ▼
PySide6 UI
        │
        ├─ themes.py
        └─ QSettings
```

La captura, el detector de pitch, la lógica musical y la apariencia están desacoplados. El motor puede sustituirse después por Essentia, CREPE u otro detector sin reescribir la aplicación; las paletas visuales pueden crecer sin mezclar colores con la lógica del afinador.

## Base actual

- Captura mono de baja latencia con `sounddevice` / PortAudio.
- Ring buffer de 8192 muestras para análisis estable.
- Ciclo de vida de audio idempotente: `Start/Stop` repetible sin dejar streams abiertos.
- Detección probabilística con `librosa.pyin`.
- Frame DSP de 4096 muestras para conservar confianza en las cuerdas graves.
- Confidence gating para rechazar señal poco fiable.
- Conversión cromática a nota, octava y frecuencia objetivo.
- Desviación de afinación en cents.
- Suavizado temporal de la aguja mediante mediana móvil.
- Estados `FLAT`, `SHARP` e `IN TUNE`.
- Worker DSP con cierre seguro de `QThread`.
- Interfaz de escritorio con `PySide6`.
- Temas persistentes: `Mamba Gold`, `Venom`, `Crimson` y `Midnight`.
- Preferencias nativas mediante `QSettings`.
- Tests para lógica musical, ring buffer, configuración DSP y temas.
- CI que instala el proyecto real antes de ejecutar `pytest` y `ruff`.

## Instalación

Requiere Python 3.11 o superior.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip3 install -e ".[dev]"
```

## Ejecutar

```bash
blackmamba-tuner
```

También puede arrancarse con:

```bash
python3 -m blackmamba_tuner.app
```

Al pulsar **Start tuner**, la aplicación abre la entrada de audio predeterminada del sistema y empieza a mostrar nota, frecuencia detectada, frecuencia objetivo, cents y confianza.

## Temas

El selector de tema vive en la cabecera de la aplicación. La selección se guarda con `QSettings`, por lo que se conserva entre ejecuciones.

Las paletas están centralizadas en `src/blackmamba_tuner/themes.py`; ningún componente necesita inventar sus propios colores.

## Permiso de micrófono en macOS

macOS controla el permiso del micrófono mediante TCC. Ese primer consentimiento lo decide el sistema y no debe intentarse evitar. La aplicación está preparada para que, al empaquetarse como `.app`, use una identidad estable y una descripción explícita del uso del micrófono en `packaging/macos/Info.plist`.

Mientras se ejecuta desde Terminal, macOS puede asociar el permiso de captura al terminal o al intérprete de Python. La versión empaquetada deberá conservar el mismo bundle identifier y firma para que el permiso sea estable entre actualizaciones normales.

## Pruebas

```bash
pytest -q
ruff check src tests
```

## Siguiente fase

- Selector de dispositivo de entrada.
- Afinaciones de guitarra: Standard, Drop D, D Standard, Open G y personalizadas.
- A4 configurable (por defecto 440 Hz).
- Motor de pitch alternativo de alta precisión.
- Calibración de latencia y ruido por dispositivo.
- Historial de estabilidad por cuerda.
- Empaquetado macOS firmado con identidad estable.
