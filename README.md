# keyd_manager

`keyd_manager` formalizes the old ad hoc keyd helper into a real app under `~/Apps`.

It manages one user-editable config:

- `~/.config/keyd_manager/keyd.config`

## Usage

```text
keyd_manager -h
keyd_manager -v
keyd_manager -u
keyd_manager conf
keyd_manager apply
keyd_manager status
```

## Install

```bash
./install.sh -u
```

That installs the latest released `keyd_manager` into `~/.keyd_manager/bin/keyd_manager`.

## Release

```bash
./push_release_upgrade.sh
```

That pushes the current branch, tags the next patch release, waits for the GitHub release asset, and upgrades the installed app.
