def set_properties(old, new, self_update=False):
    """Store object for spawning new container in place of the one with outdated image"""
    labels = old.attrs['Config']['Labels']
    ports = (
        [
            (p.split('/')[0], p.split('/')[1])
            for p in old.attrs['Config']['ExposedPorts'].keys()
        ]
        if old.attrs['Config'].get('ExposedPorts')
        else None
    )

    if self_update:
        if ports:
            labels["docupdater.updater_port"] = ":".join([f"{a},{b}" for a, b in ports])
            ports = None
        elif labels.get("docupdater.updater_port"):
            ports = [(int(port.split(",")[0]), port.split(",")[1])
                     for port in labels.get("docupdater.updater_port").split(":")]
            labels["docupdater.updater_port"] = None
            del labels["docupdater.updater_port"]

    return {
        'name': old.name,
        'hostname': old.attrs['Config']['Hostname'],
        'user': old.attrs['Config']['User'],
        'detach': True,
        'domainname': old.attrs['Config']['Domainname'],
        'tty': old.attrs['Config']['Tty'],
        'ports': ports,
        'volumes': list(old.attrs['Config']['Volumes'].keys())
        if old.attrs['Config'].get('Volumes')
        else None,
        'working_dir': old.attrs['Config']['WorkingDir'],
        'image': new.tags[0],
        'command': old.attrs['Config']['Cmd'],
        'host_config': old.attrs['HostConfig'],
        'labels': labels,
        'entrypoint': old.attrs['Config']['Entrypoint'],
        'environment': old.attrs['Config']['Env'],
    }


def remove_sha_prefix(digest):
    return digest[7:] if digest.startswith("sha256:") else digest


def convert_to_boolean(value):
    return str(value).lower() in {"yes", "y", "true"}


def get_id_from_image(image):
    return remove_sha_prefix(image.attrs.get('Image', image.attrs.get(id, image.id)))
