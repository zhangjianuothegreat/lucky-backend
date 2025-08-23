FROM heroku/heroku:24

WORKDIR /app
COPY . /app

RUN chmod +x ./build.sh
RUN ./build.sh

CMD ["gunicorn", "--bind", ":8080", "--workers", "2", "app:app"]