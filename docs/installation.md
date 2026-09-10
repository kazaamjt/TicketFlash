# Installation

This guide will show you how to get either a DEV or a Production grade instance of TicketFlash up and running.  
The DEV or development version is meant for local testing.  

This guide assumes some knowledge of computers, operating systems and terminals/command-line interfaces.  

## Table of contents

- [DEV](#dev)
  - [Prerequisites](#prerequisites)
    - [Git](#git)
    - [Docker](#docker)
  - [Up and running](#up-and-running)
  - [Shutdown](#shutdown)
  - [Removal](#removal)

## DEV

_WE STRONGLY ADVISE AGAINST RUNNING THIS SETUP IN PRODUCTION ENVIRONMENTS_  

This will go over how to simply and quickly set up an instance of both the TicketFlash software
and other software required, such as postgres for the database.  

For the DEV environment, most software is bundled in a docker compose file.  
The total time to walk through this process should not be more then a couple minutes.  

The `production` grade installation is more involved and takes longer.  

### Prerequisites

Some other software, all of it open source, is required before being able to run TicketFlash.  

#### Git

Git is our version control system.  
It is required to obtain a local copy of our code, which in turn is required to run the software.  
Simply follow the instructions on how to install from Git's own website:  

[How to install Git](https://git-scm.com/install/)

Once installed navigate to where you would like to install the project, such us under your user, or under `/opt` and execute the following:  

```shell
/opt $> git clone https://github.com/kazaamjt/TicketFlash.git
```

This will create a directory called TicketFlash

#### Docker

Next, install Docker for your operating system:  

[How to install Docker](https://docs.docker.com/engine/install/)

### Up and Running

With the prerequisites installed we can move on to getting the TicketFlash software itself up and running.  
First, create a file called `.env` in the root of the project, with the following contents:  

```txt
TF_PG_HOST=postgres
TF_PG_USER=ticket_flash
TF_PG_PASS=
TF_PG_ADMIN_PASS=
TF_PG_DB_NAME=TicketFlash
TF_LOG_LEVEL=DEBUG
TF_HTTP_BIND_IP=0.0.0.0
```

Be sure to fill in the required passwords, do not leave these blank!  

Next, start the database and database management software:  

```bash
docker compose -d up
```

Give this a bit of time as it takes a minute or two to get the pgadmin (database management software) to get up and running.  
Once it is up and running, you should be able to visit `http://localhost:8888` or [local pgadmin](http://localhost:8888).  

The default admin user is `admin@local.tf.dev` and the password is whatever you choose for `TF_PG_ADMIN_PASS`.  

In this interface, right-click `Servers` and select `Register > Server..`.  
In the panel that pops up choose a name (EG.: `TicketFlash`), then under `Connection`, fill in the following:

- `Hostname/address`: `postgres`
- `Username`: `postgres`
- `Password`: the value of `TF_PG_ADMIN_PASS`
- Toggle the `Save Password?` button to on

Then press `Save`.  
For more info about PGAdmin, visit [the PGAdmin Docs](https://www.pgadmin.org/docs/).  

Next, build the TicketFlash Container:  

```bash
docker build -t ticket_flash .
```

Then init the database:  

```bash
docker run --rm -it \
    --name ticketflash-db-init \
    --network ticket-flash-network \
    --env-file .env \
    ticket_flash \
    tf database init
```

This will run you through the database setup, just follow the on-screen instructions.  
Once it is done the container used for the setup will be removed automatically.  
This should produce an output similar to this:  

```txt
2026-09-10 16:16:04,083 - ticket_flash.backend.database - DEBUG - Connecting to database.
2026-09-10 16:16:04,258 - ticket_flash.backend.database - INFO - Connected to database.
2026-09-10 16:16:04,258 - ticket_flash.backend.database - INFO - Creating new postgres user 'ticket_flash'.
2026-09-10 16:16:04,284 - ticket_flash.backend.database - INFO - Creating new postgres database 'TicketFlash'.
2026-09-10 16:16:04,478 - ticket_flash.backend.database - DEBUG - Disconnecting from database.
2026-09-10 16:16:04,482 - ticket_flash.backend.database - DEBUG - Disconnected from database.
Populating new database.
2026-09-10 16:16:04,482 - ticket_flash.backend.database - DEBUG - Connecting to database.
2026-09-10 16:16:04,618 - ticket_flash.backend.database - INFO - Connected to database.
2026-09-10 16:16:04,618 - ticket_flash.backend.database - DEBUG - Schema version: 1
2026-09-10 16:16:04,651 - ticket_flash.backend.database - DEBUG - Disconnecting from database.
2026-09-10 16:16:04,655 - ticket_flash.backend.database - DEBUG - Disconnected from database.
```

Finally, we are ready to run our container:

```bash
docker run --rm -it -d \
    --name ticket_flash \
    --network ticket-flash-network \
    --env-file .env \
    -p 3000:3000 \
    ticket_flash
```

Test whether everything is functional either by surfing to the [health page](http://localhost:3000/health) or
by curling the health page:

```bash
curl http://localhost:3000/health
```

This should produce the following output:

```txt
{"status all": "ok", "web": {"status": "ok", "version": "v1"}, "database": {"status": "ok", "schema version": 1}}
```

### shutdown

The shutdown procedure stops the applications, but preserves the data.  
To shutdown, run the following:  

```bash
docker stop ticket_flash
docker compose down
```

To bring the application back online, simply navigate to the install location and run:

```bash
docker compose up -d
docker run --rm -it -d \
    --name ticket_flash \
    --network ticket-flash-network \
    --env-file .env \
    -p 3000:3000 \
    ticket_flash
```

### Removal

To fully remove the application and its data, please run:

```bash
docker stop ticket_flash
docker rmi ticket_flash
docker builder prune
docker compose down --rmi all --remove-orphans --volumes
```
