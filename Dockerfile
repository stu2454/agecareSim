FROM python:3.10-slim

# Install system-level packages needed by openpyxl
RUN apt-get update && apt-get install -y build-essential python3-dev libxml2 libxslt1-dev

WORKDIR /app

# Copy everything in, including Excel file and requirements
COPY . /app

# Install dependencies — explicitly add openpyxl
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir streamlit pandas plotly openpyxl

EXPOSE 8510

CMD ["streamlit", "run", "app.py", "--server.port=8510"]

