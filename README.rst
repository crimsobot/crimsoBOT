crimsoBOT
=========

crimsoBOT is a playful and somewhat poorly-coded Discord bot.

Installing
----------

- Python 3.7 or higher is required
- You'll need to have `poetry installed <https://python-poetry.org/docs/>`_.

.. code:: sh

    # first-run steps
    poetry install
    cp config.example.py config.py
    # edit config.py in your favorite editor
    poetry run python3 cli.py initdb

    poetry run bot

Links
-----

- `crimsoBOT Discord Server <https://discord.gg/Kj3WNHX>`_
- `Patreon <https://www.patreon.com/crimso>`_ (support the bot and get some stickers!)
- `Invite the bot to your server <https://discordapp.com/api/oauth2/authorize?client_id=552650993595318282&permissions=473300048&scope=bot>`_

Contributing
------------

A few tests are run whenever a PR is opened, and running these yourself locally can save you from having to make additional commits in the event that the tests fail because of silly mistakes.
Flake8 will check for general code style issues, while mypy will run type checks.

To run flake8:

.. code:: sh

    poetry run flake8

It's not too different for mypy:

.. code:: sh

    poetry run mypy


If you're working on a PR, there's a good chance that the topic of "where the hell do I put this" will come up.
Here's a project something-map just for that!

.. code::

    crimsoBOT
    └── crimsobot
        ├── cogs
        │
        │   This directory contains crimsoBOT's cogs. These are essentially "modules" for a discord.py bot,
        │   and are used to group commands and functionality. This is where most command implementations go.
        │
        ├── data
        │
        │   This directory contains.. data. Text, image and yaml files that the bot pulls from can be found here.
        │
        ├── extensions
        │
        │   This directory contains crimsoBOT's extensions. "Extensions" in this case are discord.py extensions,
        │   which allow more arbitrary python scripts to interact with the bot. Seldom used.
        │
        ├── handlers
        │
        │   This directory contains all the "handlers" that the bot uses to process messages and reactions for
        │   various games, such as Cringo! and madlibs. Note that handlers should be implemented as
        │   AbstractEventGatherer subclasses.
        │
        ├── models
        │
        │   This directory contains all of the Tortoise ORM database models that crimsoBOT uses.
        │
        ├── utils
        │
        │   This directory contains crimsoBOT's utility functions. Commands will call on functionality
        │   from this directory very often. Generally, code that will be reused often (or is bulky) should make its
        │   way here.
        │
        ├── cli.py
        │
        │   This is crimsoBOT's launcher script. Instantiation of crimsoBOT is handled here.
        │
        └── ##

