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
```

La captura, el detector de pitch y la lógica musical están desacoplados. El motor puede sustituirse después por Essentia, CREPE u otro detector sin reescribir la aplicación.

## MVP

- Captura mono de baja latencia con `sounddevice` / PortAudio.
- Ring buffer de 8192 muestras para análisis estable.
- Detección probabilística con `librosa.pyin`.
- Confidence gating para rechazar señal poco fiable.
- Conversión cromática a nota, octava y frecuencia objetivo.
- Desviación de afinación en cents.
- Suavizado temporal de la aguja mediante mediana móvil.
- Estados `FLAT`, `SHARP` e `IN TUNE`.
- Interfaz de escritorio con `PySide6`.
- Tests unitarios para la capa musical.
- CI con `pytest` y `ruff`.

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
