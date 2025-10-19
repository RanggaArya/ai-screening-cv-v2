# Spacefile
v: 0
micros:
  - name: api-service
    src: "."
    engine: "python3.12" # Sesuaikan dengan versi python Anda di WSL
    run: "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app"
    build: "sh build.sh"
    presets:
      env:
        - name: GOOGLE_API_KEY
          description: "API Key for Google Gemini"
          value: "AIzaSyCLwcIQJ-PWVfwiJuy3zRdUq7uzHkhu78k"