# Multi-Device Setup — Windows and Mac

How to run the schedule-assistant from any of your laptops, with one shared copy
of every project. This covers the one-time steps you do yourself; once they are
done, the assistant works the same on every machine.

## The model — two layers, kept apart

There are two very different things, and mixing them is what causes corruption
and stale-file errors. Keep them on separate sync mechanisms:

| Layer | What it is | How it syncs | Where it lives |
|---|---|---|---|
| **The plugin** | The tool — commands, scripts, the bundled skill. Versioned software. | **git / GitHub** | A plain folder *outside* cloud sync (`repos/`) |
| **Project data** | Each schedule — change-sets, XERs, logs. Working data that changes constantly. | **cloud sync** (OneDrive *or* Google Drive) | The cloud-synced folder |

The plugin is code: it belongs in version control, installs natively, and must
**never** sit inside a cloud-synced folder — a sync client corrupts a `.git`
folder and serves half-written copies of files a script is mid-write on. Project
data is not code: cloud sync handles it with zero effort.

## Layer 1 — the plugin (git)

The `schedule-assistant` plugin lives in one git repository. On each laptop:

```
/plugin marketplace add https://github.com/infrabloom/schedule-assistant
/plugin install schedule-assistant@schedule-assistant
```

Because the plugin bundles the `data-center-schedule` skill, that single install
gives the machine `/build-schedule`, `/update-schedule`, `/harvest-lessons`, and
the full domain skill — there is no separate skill file.

Clone the repo into a plain, non-synced folder:
- Windows — `C:\Users\<you>\repos\schedule-assistant`
- Mac — `~/repos/schedule-assistant`

**Updating every laptop:** push the change once; on each other laptop `git pull`
and refresh the plugin. When `/harvest-lessons` promotes a lesson, that is a
plugin change — commit and push, and every device picks it up on its next pull.

## Layer 2 — project data (cloud sync)

Pick **one** cloud service — OneDrive or Google Drive — and use it on every
laptop, signed into the **same account**. The steps below are identical for both.

**Folder layout.** One synced root holds every project as a sibling folder:

```
DC-Schedules/                 (the synced root)
  DC1/
    inputs/  outputs/  inbox/  changesets/
    build-brief.yaml  project.yaml  CHANGELOG.md  lessons-log.md
  DC2/
    ...
```

Each project carries its own `project.yaml`, which uses relative paths — so a
project folder is portable across machines as-is.

**Keep files on disk, not "online-only".** Right-click the active project folder
and choose **"Always keep on this device"** (OneDrive) / **"Available offline"**
(Google Drive). The scripts read real files; an online-only placeholder makes the
tooling stall or error because the file is not actually downloaded yet.

> A cloud **MCP connector** is *not* the mechanism here — it is an API layer with
> no clean in-place file update, so it would force a download/upload round-trip
> on every run. Day-to-day work uses the synced folder. A connector is optional,
> worth adding only to read a schedule from a device with no sync client.

## One-time setup per laptop

| | Windows | Mac |
|---|---|---|
| **Python 3.9+** | Install from python.org, tick "Add to PATH" | `python3 --version`; if < 3.9, `brew install python` |
| **Git** | Install from git-scm.com | `xcode-select --install` (or `brew install git`) |
| **PyYAML** | `pip install pyyaml` | `pip3 install pyyaml` |
| **Cowork / Claude Code** | Install and sign in | Install and sign in |
| **The plugin** | `git clone` into `repos\`, then `/plugin marketplace add` | `git clone` into `~/repos/`, then `/plugin marketplace add` |

The plugin code itself needs no per-OS change: it uses only `os.path`,
`${CLAUDE_PLUGIN_ROOT}`, and `sys.executable`, and `xer_io` preserves a file's
line endings — so an XER round-trips byte-faithfully whether it was saved on
Windows or Mac.

## The daily loop

1. **Start** — `git pull` the plugin repo if it changed. Confirm the project
   folder shows fully-synced on the laptop you are about to use.
2. **Work** — point Cowork at the project folder and run `/build-schedule`,
   `/update-schedule`, or `/harvest-lessons` as normal.
3. **Stop** — let cloud sync finish (the tray/menu-bar icon goes idle) before you
   walk away or switch machines.
4. **Improving the tool** — make plugin changes in the git repo, run
   `python -m unittest discover -s tests`, commit, push; other laptops pull.

## The hard rules

1. **The plugin never goes in a cloud-synced folder.** Git is its sync.
2. **One laptop at a time, per project.** Finish on laptop A, let sync complete,
   *then* open the project on laptop B. Two machines in one project folder at
   once makes the sync client silently keep one copy and rename the other.
3. **Let sync settle on handoff.** After switching laptops, give the sync client
   a moment to pull everything down before starting Cowork.

The sequential `CS-NNN` change-set numbering and the immutable-change-set rule
already protect the audit trail; these rules protect the files themselves.

## Checklist

- [ ] One cloud service chosen (OneDrive or Google Drive), same account on each laptop
- [ ] Sync client installed and signed in on each laptop
- [ ] Project root set to "always keep on this device" / available offline
- [ ] `DC-Schedules/DC1/` folder structure created; project data migrated in
- [ ] Plugin cloned into a non-synced `repos/` folder on each laptop
- [ ] Plugin installed from git on each laptop (it carries the skill)
- [ ] Python 3.9+, Git, and PyYAML present on each laptop
- [ ] Cowork pointed at the project folder on each laptop
