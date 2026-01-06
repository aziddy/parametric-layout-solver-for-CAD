# Parametric Layout Solver for CAD

This project implements a solver to fit 4 rectangles of arbitrary sizes into the smallest possible bounding circle. It includes both a Graphical User Interface (GUI) and a Command Line Interface (CLI).

## Setup

### 1. Prerequisites

- Python 3.x installed.

### 2. Create and Activate Virtual Environment

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface (CLI)

**Option 1: JSON Input (Recommended)**
Define your shapes and constraints in a JSON file (see `input/exampleInput.json`).

```bash
python cli.py --json input/exampleInput.json
```

**Option 2: Direct Arguments**
Pass dimensions as `Width,Height`.

```bash
python cli.py 10,10 20,20 15,10 5,5
```

### Graphical User Interface (GUI)

Launch the interactive tool:

```bash
python gui.py
```

## Project Structure

- `solver.py`: Core logic ensuring non-overlap and minimal circle radius.
- `input_loader.py`: JSON parsing and validation.
- `gui.py`: Tkinter application.
- `cli.py`: Command-line entry point.
- `input/`: Directory for JSON input files.
