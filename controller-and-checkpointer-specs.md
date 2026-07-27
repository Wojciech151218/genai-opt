# Specyfikacja: Experiment Controller UI i Database Checkpointer

## 1. Experiment Controller z komunikacją dwukierunkową

Zaimplementować klasę dziedziczącą po:

`src/genai_opt/optimizer_engine/experiment_controller/experiment_controller.py`

Kontroler ma łączyć się z UI (webowym lub desktopowym) przez **komunikację dwukierunkową** (np. WebSocket).

### Wymagania

- Dziedziczenie po `ExperimentController`
- Realizacja istniejących metod: `setup`, `control_iteration`, `control_operation`, `pause` / `resume`
- Dwukierunkowy kanał z UI (np. WebSocket):
  - **backend → UI**: status eksperymentu, metadane iteracji, operacje
  - **UI → backend**: pause, resume i inne komendy sterujące

---

## 2. UI webowe lub desktopowe

Zaimplementować interfejs użytkownika (web lub desktop) do sterowania eksperymentem.

### Wymagania

- Spójne, dopracowane style
- Dobre UX (czytelny przepływ, feedback, stany loading / error / paused)
- Pełne pokrycie funkcji udostępnianych przez `ExperimentController`:
  - podgląd przebiegu iteracji
  - podgląd operacji w fazach
  - pause / resume
  - stany eksperymentu

---

## 3. Database Checkpointer

Zaimplementować klasę dziedziczącą po:

`src/genai_opt/optimizer_engine/checkpointer/checkpointer.py`

Checkpointer ma zapisywać eksperymenty w bazie danych (np. **PostgreSQL** lub **SQLite**).

### Wymagania

- Dziedziczenie po `Checkpointer[P, Inv]`
- Implementacja:
  - `save_checkpoint(state, iteration_metadata)` — zapis stanu silnika
  - `load(**context)` — odczyt zapisanego stanu (lub `None`)
- Trwałe przechowywanie w bazie (Postgres / SQLite)

---

## 4. Synergia pomiędzy modułami

Dowolna interpretacja — kontroler UI i checkpointer powinny współpracować w spójny sposób (np. UI pokazuje historię checkpointów, wznawianie z bazy, status zapisu).
