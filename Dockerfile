# Folosim o imagine oficială și ușoară de Python
FROM python:3.12-slim

# Setăm directorul de lucru în interiorul containerului
WORKDIR /app

# Copiem fișierul cu cerințe prima dată (pentru a optimiza cache-ul Docker)
COPY requirements.txt .

# Instalăm bibliotecile necesare
RUN pip install --no-cache-dir -r requirements.txt

# Copiem tot restul codului sursă în container
COPY . .

# Expunem portul standard folosit de serverul web Streamlit
EXPOSE 8501

# Comanda de lansare a serverului pe localhost
CMD ["streamlit", "run", "web_animatie.py", "--server.port=8501", "--server.address=0.0.0.0"]