django-chatbot
==============

**django-chatbot** is Django application for building database-driven telegram bots.
It uses `Celery <https://docs.celeryproject.org/en/stable/>`_ as an asynchronous task queue to handle telegram webhook
updates in the background.



Test app installation
---------------------
The test app is a simple bot for adding notes.  You have to have `ngrok <https://ngrok.com/>`_ to run the bot
on your machine.
The easiest way to install needed services (posgresql and redis broker) is to use docker:

.. code-block::

    $ git clone https://github.com/vyvojer/django-chatbot/
    $ cd django-chatbot
    $ docker docker-compose up -d

Run ngrok in another terminal window:

.. code-block::

    $ ngrok http 8000

Create the ``.env`` file the in current directory:

.. code-block::

    SECRET_KEY=...
    CHATBOT_WEBHOOK_DOMAIN=https://...ngrok.io
    CHATBOT_NAME=@...
    CHATBOT_TOKEN=...

Put there a django ``SECRET_KEY``, the ngrok domain. Then create a new telegram bot via ``@BotFather``.
Add unique bot name (the good idea is to use the real bot name) and the bot token.

Create a virtual environment, install the requirements, run django server:

.. code-block::

    $ python3 -m venv ./venv/
    $ source ./venv/bin/activate
    $ cd tests
    $ python manage.py runserver

And finally run celery worker in another terminal window:

.. code-block::

    $ celery -A django_chatbot worker -l DEBUG
