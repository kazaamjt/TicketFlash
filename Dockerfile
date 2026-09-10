FROM python:3.14-slim

RUN useradd --create-home ticket_flash
WORKDIR /TicketFlash

COPY --chown=ticket_flash:ticket_flash pyproject.toml .
COPY --chown=ticket_flash:ticket_flash README.md .
COPY --chown=ticket_flash:ticket_flash LICENSE .

COPY --chown=ticket_flash:ticket_flash ticket_flash/ ticket_flash/

RUN pip install --no-cache-dir .

USER ticket_flash

CMD [ "tf", "start" ]
