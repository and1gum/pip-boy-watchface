# Release signing and migration

[Українською](release-signing.uk.md) · [Installation](install.md)

Release 0.3.0 uses a dedicated RSA-4096 key, valid for 30 years, and a cryptographically authenticated signing lineage from the project's original debug certificate. On Android 15+ this permits an in-place update to the new key with `install -r`. The APK's current signer is **Pip-Boy Release**, not Android Debug. Android documents this mechanism in [APK signature scheme v3](https://source.android.com/docs/security/features/apksigning/v3) and [apksigner](https://developer.android.com/tools/apksigner).

Public SHA-256 certificate fingerprints:

| Certificate | SHA-256 |
| --- | --- |
| Original project debug | `4d4d850ac4b7bd2cda61b2d269e4a6bace213e23866621e105b5c65624635601` |
| Project release | `94f7ecd7517e92587828869c09d03d621561ec277c53c7e5e5fd76871f24da91` |

Both project APKs use the same lineage. It grants migration of installed data and disables return to the old debug signer. The package IDs, WFF configuration IDs (`hr2`–`hr5`), slot IDs/order and provider component names remain unchanged. The transition keeps the installation and its data; it does not export and reconstruct Wear OS's private watch-face configuration.

## Project maintainer: initialize once

Use the **existing** project signing directory for future official builds. Never generate a new key for each release. Private signing material defaults to `~/.local/share/pip-boy-signing/`; the password is read from its private `password` file and never passed as literal command-line text. Set `PIPBOY_SIGNING_DIR` to use a restored directory elsewhere. Keep this directory, its password and lineage out of Git and release assets.

For a new independent distribution, setup is explicit and refuses to overwrite existing signing material:

```bash
bash scripts/init-release-key.sh \
  --old-key "$HOME/.android/debug.keystore" \
  --reference-apk artifacts/PipBoy-0.2.0-debug.apk \
  --reference-apk artifacts/PipBoy-Compass-0.2.0-debug.apk \
  --backup-dir /absolute/path/outside/repository/pip-boy-signing-backup
bash scripts/build-release.sh
```

The initializer verifies that the old key matches both reference APKs, generates the permanent release key and rotation proof, and verifies the separate backup byte for byte. An independent developer's debug key cannot produce updates for the project's installed debug APKs. Their newly generated release key also cannot update the official release. Download the official APKs for that installation.

To recover build signing, restore **all files** from the private signing backup into a private directory, set `PIPBOY_SIGNING_DIR` to it, and run the release build. The public certificate or an old APK cannot replace a lost private key. Preserve the original debug keystore separately as well.

## Preserving the watch configuration

Run the checked installer before considering manual changes:

```bash
bash scripts/install-release.sh --serial WATCH_IP:CONNECT_PORT
```

It pulls the installed APKs, compares version codes and uses Android's `apksig` library to verify the actual signing lineage and installed-data capability for the device API level. Both packages must pass before either is installed. An unrelated signature or a downgrade stops the process. There is no uninstall/clear-data fallback.

Before installation the script saves the previous APKs, available debug preference archives, package permission dumps, wallpaper dump and a screenshot under `~/.local/state/pip-boy/backups/`. This is an audit checkpoint. Wear OS owns face customization and complication bindings outside the two APKs' data directories; these dumps cannot automatically restore those settings after uninstall or factory reset. Private snapshots can contain location/history data; retain them privately.

The direct signing migration is the mechanism for retaining these settings. If the actual watch rejects it, keep the debug installation untouched and investigate the rejection; do not uninstall it and assume the snapshot can restore everything. On-watch migration and active/AOD/provider validation remain pending until a watch is connected. Cryptographic verifier tests alone do not prove Samsung's runtime behavior.

After migrating, use release-signed builds for updates. The old debug signature cannot replace release. To return to earlier source behavior, build that behavior with the **release** key, the retained lineage and an adequate version code.

## Local rollback checkpoint

Before these changes, source revision `014cf17` and both 0.2.0 debug APKs were saved locally with checksums and an independent copy. The source bundle reconstructs the prior source checkout. These APKs are useful before migration; after key rotation they are not a direct downgrade path. The checkpoint does not contain a restorable copy of system-owned watch settings.
