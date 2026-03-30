# Inventory Shop

PyQt6 Desktop app for inventory management.

## Setup & Run

1. MambaForge is installed at `C:\Users\ACER\mambaforge` (uses `conda.exe`).

2. Run the batch file:
```
inventory_shop/run.bat
```

It will create `inventory_env` conda environment with Python 3.9 and PyQt6 (prebuilt from conda-forge, no Visual C++ needed).

3. Login with username: `admin`, password: `admin123`

## Alternative: pip in venv (if you have Visual C++ Build Tools)

```
cd inventory_shop
venv\Scripts\activate
pip install -r requirements.txt --no-cache-dir
python main.py
```

## Features
- User management
- Products, services, customers, suppliers
- Sales & purchases with inventory tracking
- Reports
- SQLite database (inventory.db)

Enjoy!

