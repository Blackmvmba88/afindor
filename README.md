# BlackMamba Tuner

Afinador cromático de guitarra en tiempo real construido sobre librerías de audio/DSP maduras, no sobre detección casera de frecuencia.

## Objetivo

- Captura de audio de baja latencia con `sounddevice` / PortAudio.
- Detección de pitch intercambiable mediante un `PitchEngine` común.
- Primer motor: `librosa.yin` con filtrado de señal y estabilización temporal.
- Nota musical, frecuencia, desviación en cents y estado de afinación.
- UI de escritorio con `PySide6`.
- Arquitectura preparada para añadir motores como Essentia o CREPE sin reescribir la aplicación.

## Estado

Repositorio inicializado. El MVP se desarrolla en una rama de feature y se integra mediante pull request.
