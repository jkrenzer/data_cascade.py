
# data-cascade

A composable directory-based data cascade loader/saver for Python (>=3.10). It merges files in a tree (YAML/JSON/TOML), keeps a per-key origin map for round-tripping, and offers both a **path API** and an **ergonomic proxy API** with **dirty-file saves**.

## Features

- Merge `__main__.*` into the current node and per-file trees by stem name.
- Directory-level `__config__.*` with `data.merge` options (dict/list modes, per-key overrides, excludes).
- Supports YAML (ruamel.yaml preferred, PyYAML fallback), JSON (stdlib), TOML (tomllib or tomli; writers via tomli-w or toml).
- Returns a `CascadeMap` mapping each merged key path to the source file and local path.
- `save_data_cascade` writes values back to their original files, or sensible defaults for new keys.
- `Cascade` object with:
  - Path API: `get("a.b[1]")`, `set("a.b[1]", value)`, `delete("a.b[1]")`
  - Proxy API: `c.node("a").b[1].set(value)` and `c.node().a.b[1].get()`
  - Dirty-file saves: `c.save()` only rewrites files you touched.

## Install (with Poetry)

```bash
poetry add data-cascade
# Optionally enable YAML and TOML writers/readers
poetry add data-cascade -E yaml -E toml
```

## Quick start

```python
from pathlib import Path
from data_cascade import load_data_cascade, save_data_cascade

data, cmap = load_data_cascade(Path("data"))
data["project"] = {"name": "Alpha"}
save_data_cascade(Path("data"), data, cmap)
```

### The Cascade object

```python
from data_cascade import make_cascade

c = make_cascade("data")

# Path API
members = c.get('team.members')
c.set('team.members[1]', 'Carol')
c.save()  # only touches the file that owns team.members

# Proxy API
node = c.node('a').b[1]
node.set(42)
print(node.get())
c.save()
```

### Configuring merge

Put a `__config__.yaml` in any directory. Example:

```yaml
__config__:
  data:
    merge:
      dict: deep            # deep | override | first_wins
      list:
        mode: merge_by_key  # replace | extend | unique | merge_by_key
        key: id
      per_key:
        tasks:
          list:
            mode: unique
      exclude: ["scratch"]  # skip stems or keys
```

### Handling missing libraries

YAML and TOML are optional. If a file is encountered and no handler exists for its extension, a warning is logged and the file is skipped/raises on save for that type. Install extras (`-E yaml`, `-E toml`) for full support.

## Tasks (poethepoet)

```bash
poe test   # run pytest
poe pack   # packaging info
poe fmt    # placeholder for formatters
```

## License

MIT
