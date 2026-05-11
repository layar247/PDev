FROM python:3.9-slim

WORKDIR /bot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/bot

CMD /bin/bash -c "python database/init_data.py && python scripts/delete_cancel_topic.py && python main.py"