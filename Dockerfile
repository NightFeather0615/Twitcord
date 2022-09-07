FROM python:3.10.6-slim-buster
WORKDIR /app
COPY . .
RUN pip install six resolvelib pdm
RUN pdm install
CMD ["pdm", "run", "python", "main.py"]