FROM python:3.10.6-alpine
WORKDIR /app
COPY . .
RUN pip install six resolvelib pdm
RUN pdm install
CMD ["pdm", "run", "python", "main.py"]