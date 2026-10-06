import sys
from pathlib import Path

# scripts/ no es un paquete instalado (está fuera de src/), así que se añade
# al path de los tests para poder hacer "import fetch_data" directamente,
# igual que lo ejecutaría un usuario con "python scripts/fetch_data.py".
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
