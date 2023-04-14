from abc import ABC, abstractmethod
from time import sleep

from docker.errors import APIError, NotFound

from .config import Config
from ..helpers.helpers import set_properties, remove_sha_prefix, get_id_from_image


class AbstractObject(ABC):
    def __init__(self, docker_client, object):
        self.docker = docker_client
        self.logger = self.docker.logger
        self.config = self.docker.config
        self.client = self.docker.client
        self.socket = self.docker.socket

        self.object = object

    @property
    def name(self):
        return self.object.name

    @abstractmethod
    def get_image_name(self):
        """Get image name"""

    @abstractmethod
    def get_tag(self):
        """Get image tag"""

    @abstractmethod
    def has_new_version(self):
        """Return true if there are a new version"""

    @abstractmethod
    def get_current_id(self):
        """Return the current id for notification"""

    @abstractmethod
    def get_latest_id(self):
        """Return the latest id for notification"""

    def _pull(self, name_with_tag):
        """Docker pull image tag"""
        self.logger.debug('Checking tag: %s', name_with_tag)
        try:
            if self.config.auth_json:
                self.client.login(self.config.auth_json.get("username"), self.config.auth_json.get("password"))

            # The authentification doesn't work with this call
            # See bugs https://github.com/docker/docker-py/issues/2225
            # return self.client.images.get_registry_data(tag)
            return self.client.images.pull(name_with_tag, auth_config=self.config.auth_json)
        except APIError as e:
            if '<html>' in str(e):
                self.logger.debug("Docker api issue. Ignoring")
                raise ConnectionError
            elif 'unauthorized' in str(e):
                raise ConnectionError
            elif 'Client.Timeout' in str(e):
                self.logger.critical(
                    "Couldn't find an image on docker.com for %s. Local Build?", name_with_tag)
                raise ConnectionError
            elif ('pull access' or 'TLS handshake') in str(e):
                self.logger.critical("Couldn't pull. Skipping. Error: %s", e)
                raise ConnectionError


class Container(AbstractObject):
    def __init__(self, docker_client, container):
        super().__init__(docker_client, container)
        self._latest_image = None
        self._current_id = None

    def get_image_name(self):
        return self.container.attrs['Config']['Image'].split(":", 1)[0]

    def get_tag(self):
        image = self.container.attrs['Config']['Image']
        if ":" in image:
            return image.split(":", 1)[1]
        if tags := self.client.images.get(self.get_image_name()).tags:
            tag = tags[0]
            return tag.split(":", 1)[1] if ":" in tag else "latest"

    @property
    def container(self):
        return self.object

    def get_current_id(self):
        return (self._current_id or "")[10:]

    def get_latest_id(self):
        return get_id_from_image(self._latest_image)[10:] if self._latest_image else ""

    def is_docupdater(self):
        docupdater = "docupdater" in self.container.attrs.get("Config", {}).get(
            "Image", self.name
        )
        if not docupdater:
            for history in self.container.image.history():
                if "docupdater" in (history.get("Tags", []) or []):
                    docupdater = True
                    break
        return bool(docupdater)

    def has_new_version(self):
        self.config = Config.from_labels(self.config, self.container.labels)

        current_image_name = self.get_image_name()
        current_tag = self.get_tag()
        self._current_id = remove_sha_prefix(self.container.attrs.get('Image', self.container.id))

        if self.config.latest:
            current_tag = "latest"

        try:
            latest_image = self._pull(f"{current_image_name}:{current_tag}")
            self._latest_image = latest_image
        except ConnectionError:
            return False

        latest_id = get_id_from_image(latest_image)

        return self._current_id != latest_id

    def update(self):
        if self.is_docupdater():
            self.logger.info("Docupdater container is ready to update")
            self.config.recreate_first = True  # Always recreate docupdater container first
        elif self.container.attrs['Config'].get('ExposedPorts') and self.config.recreate_first:
            self.config.recreate_first = False
            self.logger.warning(
                "Option recreate_first isn't compatible when container has exposed ports. Option is set to False."
            )

        if not self._current_id or not self._latest_image:
            self.has_new_version()

        if self.config.recreate_first:
            new_name = f"{self.name}_old"
            if self.is_docupdater():
                new_name = f"{self.name}_old_docupdater"
            self.container.rename(new_name)
        else:
            self.stop()
            self.remove()

        self.logger.info('%s will be updated', self.container.name)
        self.recreate()

        if self.is_docupdater():
            self.logger.info('Waiting for new docupdater container')
            sleep(600)

        if self.config.recreate_first:
            self.stop()
            self.remove()

        if self.config.cleanup:
            try:
                self.client.images.remove(self._current_id)
            except APIError as e:
                self.logger.error("Could not delete old image for %s, Error: %s", self.container.name, e)

    def stop(self):
        self.logger.debug('Stopping container: %s', self.object.name)

        if self.config.stop_signal:
            try:
                self.container.kill(signal=self.config.stop_signal)
            except APIError as e:
                self.logger.error('Cannot kill container using signal %s. stopping normally. Error: %s',
                                  self.object.stop_signal, e)
                self.container.stop()
        else:
            self.container.stop()

    def remove(self):
        self.logger.debug('Removing container: %s', self.container.name)
        if not self.container.attrs.get('HostConfig', {}).get('AutoRemove'):
            try:
                self.container.remove()
            except NotFound as e:
                self.logger.error("Could not remove container. Error: %s", e)
                return
        else:
            # Docker will remove container, but some time that take few seconds
            try:
                while True:
                    self.client.containers.get(self.name)
            except NotFound:
                pass

    def recreate(self):
        new_config = set_properties(
            old=self.container,
            new=self._latest_image,
            self_update=self.is_docupdater()
        )
        created = self.client.api.create_container(**new_config)
        new_container = self.client.containers.get(created.get("Id"))

        # connect the new container to all networks of the old container
        for network_name, network_config in self.container.attrs['NetworkSettings']['Networks'].items():
            network = self.client.networks.get(network_config['NetworkID'])
            try:
                network.disconnect(new_container.id, force=True)
            except APIError:
                pass
            new_network_config = {
                'container': new_container,
                'aliases': network_config['Aliases'],
                'links': network_config['Links'],
                'ipv4_address': network_config['IPAddress'],
                'ipv6_address': network_config['GlobalIPv6Address']
            }
            try:
                network.connect(**new_network_config)
            except APIError as e:
                if any(err in str(e) for err in ['user configured subnets', 'user defined networks']):
                    if new_network_config.get('ipv4_address'):
                        del new_network_config['ipv4_address']
                    if new_network_config.get('ipv6_address'):
                        del new_network_config['ipv6_address']
                    network.connect(**new_network_config)
                else:
                    self.logger.error('Unable to attach updated container to network "%s". Error: %s', network.name, e)

        new_container.start()


class Service(AbstractObject):
    def __init__(self, docker_client, service):
        super().__init__(docker_client, service)
        self._latest_sha = None
        self._current_sha = None

    def get_image_name(self):
        return self.service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split(":", 1)[0]

    def get_tag(self):
        tag = self.service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split(":", 1)
        if len(tag) == 2:
            tag = tag[1]
            if ":" in tag and "@" in tag:
                tag = tag.split("@")[0]
            return tag
        return "latest"

    def get_sha(self):
        tag = self.service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'].split(":", 1)
        if len(tag) == 2:
            tag = tag[1]
            sha = tag.split("@")[1] if ":" in tag and "@" in tag else ""
            return remove_sha_prefix(sha)
        return ""  # Empty, force to update this service for next time

    @property
    def service(self):
        return self.object

    def get_current_id(self):
        return (self._current_sha or "")[:10]

    def get_latest_id(self):
        return (self._latest_sha or "")[:10]

    def has_new_version(self):
        self.config = Config.from_labels(
            self.config, self.service.attrs.get('Spec', {}).get('Labels')
        )

        current_image_name = self.get_image_name()
        current_tag = self.get_tag()

        self.logger.debug("%s:%s", current_image_name, current_tag)

        current_sha = self.get_sha()
        if not current_sha:
            self.logger.error('No image SHA for %s. Update it for next time', current_image_name)

        if self.config.latest:
            current_tag = "latest"

        try:
            latest_image = self._pull(f"{current_image_name}:{current_tag}")
        except ConnectionError:
            return False

        latest_sha = self._get_digest(latest_image)
        self._latest_sha = latest_sha
        self._current_sha = current_sha
        return current_sha != latest_sha

    def update(self):
        if not self._latest_sha:
            self.has_new_version()

        self.logger.info('%s will be updated', self.name)
        self.service.update(image=f"{self.get_image_name()}:{self.get_tag()}@sha256:{self._latest_sha}")

    def _get_digest(self, image):
        digest = image.attrs.get(
            "Descriptor", {}
        ).get("digest") or image.attrs.get(
            "RepoDigests"
        )[0].split('@')[1] or image.id

        return remove_sha_prefix(digest)
