# Mainline

Mainline is a desktop application for building and training chess opening repertoires. The first milestone is a PySide6 application shell for Windows-focused desktop development.

## Current status

The project currently contains the stage 1 application skeleton:

- a `QMainWindow`-based main window;
- top-level menu categories: File, Edit, View, Help;
- an empty toolbar;
- a three-column central layout for Debuts, Chess Board, and Inspector panels;
- a status bar showing `Ready`.

No chess rules, database persistence, drill mode, or Stockfish integration are implemented yet.

## Requirements

- Python 3.12+
- PySide6
- python-chess (declared for upcoming chess logic stages, not used yet)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

## Run

```bash
python main.py
```

## Project structure

```text
main.py                  Application entry point
requirements.txt         Runtime dependencies
app/ui/main_window.py    Main application window shell
app/ui/widgets/          Reusable UI widgets
app/chess/               Future chess-domain logic
app/database/            Future SQLite persistence layer
app/models/              Future data models
app/services/            Future business services
app/resources/           Icons, pieces, and other assets
app/utils/               Shared helpers
tests/                   Automated tests
```
