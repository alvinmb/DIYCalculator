# Versioning

## Current state

The app version is currently hardcoded in three separate places, which
have to be kept in sync by hand on every release:

| File | Line | Purpose |
|---|---|---|
| `bin/beboputer_v7/__init__.py` | `__version__ = "7.0.0"` | Canonical version string. Not currently imported or displayed anywhere in the app. |
| `bin/beboputer_v7/beboputer_setup.iss` | `#define AppVersion "7.0.0"` | Windows installer (Inno Setup) version. |
| `bin/beboputer_v7/RPI_INSTALL/build_deb.sh` | `PKG_VERSION="7.0.0"` | Debian package version (`beboputer_<version>_all.deb`). |

`build_deb.bat`, `check_deb.bat`, and `RPI_INSTALL/README.txt` also
mention `7.0.0`, but only as plain-text references to the `.deb`
filename that `build_deb.sh` produces — they aren't independent
sources of truth, just copy that goes stale if the real version moves.

Nothing reads `__version__` back out, so today it's decorative: the
About dialog and window titles don't show a version at all, and
there's no automated check that the installer/package version matches
the app's own version.

## Recommended approach: single source of truth

Keep `__version__` in `bin/beboputer_v7/__init__.py` as the one
canonical value. Everything else — installers, packages, the About
dialog — should read it instead of storing its own copy.

1. **App code** (About dialog, window title, `--version` flag, etc.)
   imports it directly:

   ```python
   from beboputer_v7 import __version__
   ```

2. **Windows installer** (`beboputer_setup.iss`) shells out at build
   time instead of hardcoding `AppVersion`:

   ```
   #define AppVersion GetStringFileInfo("..\..\dist\Beboputer\Beboputer.exe", "ProductVersion")
   ```

   or, simpler, have `build_installer.bat` generate a small `version.iss`
   include file by running:

   ```bat
   for /f %%v in ('python -c "from beboputer_v7 import __version__; print(__version__)"') do set APPVER=%%v
   ```

   and passing `/DAppVersion=%APPVER%` to `iscc.exe`.

3. **Debian package** (`build_deb.sh`) drops its own `PKG_VERSION="7.0.0"`
   line and computes it instead:

   ```bash
   PKG_VERSION=$(python3 -c "from beboputer_v7 import __version__; print(__version__)")
   ```

With this in place, bumping a release is a **one-line change**:

```python
# bin/beboputer_v7/__init__.py
__version__ = "7.1.0"
```

Everything else (installer, .deb package, About dialog) picks it up
automatically on the next build — there's no second or third place to
remember to update, and it's mechanically impossible for the
installer/package version to drift from the app's own version.

## Version number scheme

Use [semantic versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

- **MAJOR** — breaking changes (e.g. `.ram`/`.lst` file format changes,
  removed CLI flags, dropped platform support).
- **MINOR** — new features that stay backward compatible (new assembler
  directives, new panels/tools, new sample programs).
- **PATCH** — bug fixes only, no new functionality.

## Suggested release checklist

1. Bump `__version__` in `bin/beboputer_v7/__init__.py`.
2. Rebuild (`build_installer.bat` / `build_deb.sh` / `build_mac.sh`) —
   version flows through automatically once step 1's plumbing is wired up.
3. Tag the release in git: `git tag v7.1.0 && git push --tags`.
4. Attach the built installer/`.deb`/`.app` to the GitHub release.
