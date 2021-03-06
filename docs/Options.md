# Options usage

Command line arguments can be viewed by running:

```bash
docker run --rm docupdater/docupdater --help
```

All command line arguments can be substituted with an environment variable. All examples will be given as environment variables for a `docker run -e option=option_value`.

On a stack file (Docker swarm), you may set the environment variable like so:

```bash
version: "3.6"

services:
  docupdater:
    image: docupdater/docupdater
    environment:
        - INTERVAL=30
        - LABEL=true
    deploy:
      labels:
        docupdater.disable: "true"
      placement:
        constraints:
          - node.role == manager
```

> On stack mode, environment variables should not be enclosed in quotation marks.

***

* [Help](#help)
* [Version](#version)
* [Log Level](#log-level)
* [Scheduler](#scheduler)
  * [Interval](#interval)
  * [Cron](#cron)
  * [Run Once](#run-once)
* [Docker Specifics](#docker-specifics)
  * [Docker Sockets](#docker-sockets)
  * [Docker TLS Verify](#docker-tls-verify)
  * [Label](#label)
  * [Disable containers check](#disable-containers-check)
  * [Disable services check (swarm)](#disable-services-check-swarm)
  * [Cleanup](#cleanup)
  * [Latest](#latest)
  * [Repository User](#repository-user)
  * [Repository Password](#repository-password)
  * [Wait time](#wait-time)
  * [Recreate first](#recreate-first)
* [Notifications](#notifications)
  * [Notifiers](#notifiers)
  * [Template file](#template-file)
  * [Skip start notification](#skip-start-notification)

***

### Help

**Type:** Boolean - Interrupting  
**Command Line:**  `-h, --help`  

Shows the help message then exits

### Version

**Type:** Boolean - Interrupting  
**Command Line:**  `-v, --version`  

Shows the current version number then exits

### Log Level

**Type:** String - Choice  
**Command Line:**  `-l, --log-level`  
**Environment Variable:** `LOG_LEVEL`  
**Choices:**

* debug
* info
* warn
* error
* critical

**Default:** `info`  
**Example:** `-e LOG_LEVEL=info`  

Sets your logging verbosity level.

## Scheduler

### Interval

**Type:** Integer  
**Command Line:**  `-i, --interval`  
**Environment Variable:** `INTERVAL`
**Default**: `300`  
**Example:** `-e INTERVAL=300`  

The interval in seconds between checking for updates. There is a hard-coded 30 second minimum. Anything lower than that will set to 30. 

### Cron

**Type:** String  
**Command Line:**  `-C, --cron`  
**Environment Variable:** `CRON`  
**Default**: `None`  
**Example:** `-e CRON="*/5 * * * *"`   

The schedule defined when to check for updates. If not defined, runs at interval.

### Run Once

**Type:** Boolean - Interrupting  
**Command Line:**  `-o, --run-once`  
**Environment Variable:** `RUN_ONCE`  
**Default:** `False`  

Docupdater will only do a single pass of all container checks, and then exit. This is a great way to granularly control scheduling with an outside scheduler like cron. If during the single pass docupdater has to self-update, it will do another full pass after updating itself to ensure that all containers were checked.

## Docker Specifics

### Docker Socket

**Type:** List - Space separated
**Command Line:**  `-d, --docker-sockets`  
**Environment Variable:** `DOCKER_SOCKETS`  
**Default:** `unix://var/run/docker.sock`  
**Example:** `-e DOCKER_SOCKETS="unix://var/run/docker.sock tcp://192.168.1.100:2376"`  

Allows you to define the docker socket.

### Docker TLS

**Type:** Boolean  
**Command Line:**  `-t, --docker-tls`  
**Environment Variable:** `DOCKER_TLS`  
**Default:** `False`  
**Example:** `-e DOCKER_TLS=true -v $DOCKER_CERT_FOLDER:/root/.docker/`  

Enables docker TLS secure client connections by certificate

### Docker TLS Verify

**Type:** Boolean  
**Command Line:**  `-T, --docker-tls-verify`  
**Environment Variable:** `DOCKER_TLS_VERIFY`  
**Default:** `True`  
**Example:** `-e DOCKER_TLS_VERIFY=false`  

Verify CA certificate for docker deamon

### Label

**Type:** Boolean  
**Command Line:**  `-k, --label`  
**Environment Variable:** `LABEL`  
**Default:** `False`  
**Example:** `-e LABEL=true`  

This flag allows a more strict control over docupdater's updates. If the container or service does not have a `docupdater.enable` label, it will be ignored completely. See [Labels](Labels.md) for a list of all available labels.

### Disable services check (swarm)

**Type:** Boolean  
**Command Line:**  `--disable-services-check`  
**Environment Variable:** `DISABLE_SERVICES_CHECK`  
**Default:** `False`  
**Example:** `-e DISABLE_SERVICES_CHECK=true`  

Disable the scan for services (swarm). With this flag only standalone container will be updated.

### Disable containers check

**Type:** Boolean  
**Command Line:**  `--disable-containers-check`  
**Environment Variable:** `DISABLE_CONTAINERS_CHECK`  
**Default:** `False`  
**Example:** `-e DISABLE_CONTAINERS_CHECK=true`  

Disable the scan for standalone containers.

### Cleanup

**Type:** Boolean  
**Command Line:**  `-c, --cleanup`  
**Environment Variable:** `CLEANUP`  
**Default:** `False`  
**Example:** `-e CLEANUP=true`  

Remove the old images after updating. If you have multiple containers using the same image, it will ensure all containers are updated before successfully removing the image.

### Latest

**Type:** Boolean  
**Command Line:**  `-L, --latest`  
**Environment Variable:** `LATEST`  
**Default:** `False`  
**Example:** `-e LATEST=true`  

Pull the `:latest` tags and update all containers to it, regardless of the current tag the container is running as. Can be override with the label `docupdater.latest`. See [Labels](Labels.md) for a list of all available labels.

### Repository User

**Type:** String  
**Command Line:**  `-r, --repo-user`  
**Environment Variable:** `REPO_USER`  
**Default:** `None`  
**Example:** `-e REPO_USER=johndoe1970`  

Define a username for repository authentication. Will be ignored without defining a repository password.

### Repository Password

**Type:** String  
**Command Line:**  `-R, --repo-pass`  
**Environment Variable:** `REPO_PASS`  
**Default:** `None`  
**Example:** `-e REPO_PASS=0791eodnhoj`  

Define a password for repository authentication. Will be ignored without defining a repository username.

### Stop signal

**Type:** Int  
**Command Line:**  `--stop-signal`  
**Environment Variable:** `STOP_SIGNAL`  
**Default:** `None`  
**Example:** `-e STOP_SIGNAL=12`  

Define a stop signal to send to the container instead of SIGKILL. Default behavior is to use default docker stop command. Only for standalone container. Can be override with the label `docupdater.stop_signal`.

### Wait time

**Type:** Int  
**Command Line:**  `-w, --wait`  
**Environment Variable:** `WAIT`  
**Default:** `0`  
**Example:** `-e WAIT=60`  

Define a time in seconds to wait after an update before updating any others containers or services. Can be override with the label `docupdater.wait`.

### Recreate first

**Type:** Int  
**Command Line:**  `-F, --recreate-first`  
**Environment Variable:** `RECREATE_FIRST`  
**Default:** `0`  
**Example:** `-e RECREATE_FIRST=true`  

Work only with standalone container. To minimize application down time, we could create the new container before deleting the old.

Warning: This feature doesn't work if you have exposed ports. We highly recommend to use a load balancer like [Traefik](https://traefik.io/) if you need to use exposed ports with docupdater.

Self update of docupdater always use this feature. Can be override with the label `docupdater.recreate_first`.

## Notifications

### Notifiers

**Type:** List - Space separated  
**Command Line:**  `-N, --notifiers`  
**Environment Variable:** `NOTIFIERS`  
**Default:** `None`  
**Example:** `-e NOTIFIERS="mailtos://myUsername:myPassword@gmail.com?to=receivingAddress@gmail.com jsons://webhook.site/something"`  

Docupdater uses [apprise](https://github.com/caronc/apprise) to support a large variety of notification platforms.

Notifications are sent for every update. The notification contains the container/service updated.

More information can be found in the [notifications docs](Notifications.md). Can be override or disable with the label `docupdater.notifiers`.

### Template file

**Type:** Path  
**Command Line:**  `--template-file`  
**Environment Variable:** `TEMPLATE_FILE`  
**Default:** `None`  
**Example:** `-e TEMPLATE_FILE="/template.j2"`  

Use this template instead of default template file. We use jinja2 template style to parse the template. Must be a valid path, don't forget to mount the template in the container.

See this example of template file:
```
{{ object.name }} ({{ object.get_image_name() }}:{{ object.get_tag() }}) updated from {{ object.get_current_id() }} to {{ object.get_latest_id() }}
```

Can be override with the label `docupdater.template_file`.

### Skip start notification

**Type:**  Boolean
**Command Line:**  `--skip-start-notif`  
**Environment Variable:** `SKIP_START_NOTIF`  
**Default:** `False`  
**Example:** `-e SKIP_START_NOTIF=true`  

Docupdater send a notification when it start. That option disable this notification.

***

Next: [Customize usage with labels](Labels.md)
