# The Mars launch windows video

A 97-second narrated film of what [the scheduler](../RESULTS.md) found: the four
launch windows between 2028 and 2037, the trade between a cheap departure and a
gentle arrival, and why Mars's rotation makes the longitude free but the
latitude expensive.

Every number on screen is read from `public/data.json`, which `run.py` writes
from the real results. Nothing is typed in by hand.

```bash
npm install
python3 voiceover.py && python3 soundtrack.py   # voice, then music mixed under it
npm run render
```

The voice is [Piper](https://github.com/rhasspy/piper), run offline; download
`en_US-ryan-high.onnx` and its `.json` from the
[piper-voices](https://huggingface.co/rhasspy/piper-voices) repository into
`voice/`. The narration is in `vo/lines.txt`, one line per scene — edit a line,
regenerate, and render again.

The music is synthesized from scratch in `soundtrack.py`, so there is nothing
to license. Scene lengths live in `SCENES` at the bottom of `src/Film.jsx` and
must be kept in step with `VO_START` in `soundtrack.py`.
