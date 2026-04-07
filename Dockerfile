# Folosim o imagine oficială și ușoară de Python
FROM python:3.10-slim

# Setăm directorul de lucru în interiorul containerului
WORKDIR /app

# Copiem fișierul cu cerințe prima dată (pentru a optimiza cache-ul Docker)
COPY requirements.txt .

# Instalăm bibliotecile necesare
RUN pip install --no-cache-dir -r requirements.txt

# Copiem tot restul codului sursă în container
COPY . .

# Setăm comanda implicită atunci când pornește containerul
# Implicit, îl vom pune să ruleze analiza de date
CMD ["python", "Analysis.py"]