# frontent/Dockerfile

FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

# Copy the sql_app directory and tests directory
COPY ./sql_app /code/sql_app
COPY ./tests /code/tests
COPY ./pytest.ini /code/pytest.ini

# Set PYTHONPATH so imports work correctly
ENV PYTHONPATH=/code

# CMD ["uvicorn", "sql_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--root-path", "/api/v1"]

# use below to run locally - not sure why this is an issue?
CMD ["uvicorn", "sql_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

