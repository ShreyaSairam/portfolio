# Portfolio Hub

A single Streamlit multipage app that brings all five projects together
as pages in one sidebar, without changing how any of them work standalone.

```bash
streamlit run Home.py
```

`project_loader.py` loads each project's own `app.py` (unmodified) under
a unique module name and calls its `main()`, adding that project's
folder to `sys.path` first so its normal internal imports (`from engine
import ...`, `from recognizer import ...`, etc.) keep working. `views/`
holds one thin wrapper script per project that just calls
`run_project("<key>")` — that's what `st.navigation` in `Home.py` points
at.

Run each project's own setup (see its README) before using its page here
— the hub doesn't re-run any data prep or training itself.
