# Deboys 7.0 — packwiz source

Minecraft **1.21.1**, NeoForge **21.1.265**, Java **21**.

This directory is the repository root: publish **only its contents**, not the surrounding Minecraft instance. Worlds, player identities, servers.dat, logs, caches, options.txt and disabled mods are deliberately excluded. Active resource-pack ZIPs are represented by download manifests. Existing enabled resource-pack selections and key bindings are not distributed. The initial conversion preserved the original instance. Tetra and its unused dependency mutil were subsequently removed from active mods; their JARs are backed up in the parent instance's `removed-mods/tetra/` folder, outside this repository. Back up existing worlds before loading them without Tetra: its items and blocks may be lost.

## Bundled custom mods and publication review

Two exact installed builds are bundled directly in `mods/` as regular indexed files:

- `make-it-compatible-voxy-1.1.1-roxy.1.jar` — metadata declares MIT; authors: leon.raineri. This is a local Roxy adaptation; its embedded `MIC-ROXY-PATCH.txt` is preserved.
- `sablescalablelux-1.21.1-NeoForge-1.0.0.jar` — nested mod metadata declares MIT; authors: Leclowndu93150.

Packwiz downloads these files relative to the published pack URL; no separate Release assets or download manifests are needed. Commit both JARs together with `index.toml` and `pack.toml`. `UNRESOLVED.json` is now empty.

**Before public distribution:** neither archive contains the full MIT license/copyright notice. Obtain and include the applicable notices from the authors/source projects, and confirm coverage of the local adaptation and service wrapper. Metadata declarations alone do not supply the notices required by MIT. Technical index validation does not constitute license clearance.

Install the packwiz CLI following https://packwiz.infra.link/ . Run `packwiz refresh` after changing bundled JARs or other pack files.

Review `config/` before making the repository public: configuration can contain private endpoints, tokens or personal preferences. The conversion omits voicechat-server.properties but cannot guarantee every third-party configuration is safe. All selected configs are managed files and publisher edits can overwrite local customization. Review mod side declarations before using this as a dedicated-server pack; this conversion targets the existing client pack.

## Publish to GitHub

1. Create a GitHub repository. A public repository is simplest: installer downloads must be accessible without interactive authentication. Do not put GitHub tokens in launch commands.
2. Upload/commit the contents of this directory at the repository root. Do not upload the parent instance. No repository, branch, commit or remote has been created automatically.
3. Use the raw URL of `pack.toml` on your distribution branch. For example, the URL structure is `https://raw.githubusercontent.com/OWNER/REPOSITORY/main/pack.toml` — replace OWNER, REPOSITORY and the branch with your real values. No concrete repository URL has been configured yet.
4. Open that URL in a browser and confirm it serves TOML, not a GitHub HTML page.

GitHub Actions validates index hashes and deliberately fails release validation while unresolved files remain. Publishing a push is not gated by that workflow: use branch protection if you need to prevent broken updates reaching players.

## Auto-update in Prism Launcher

Use a **new test instance** first. Install Minecraft 1.21.1 and NeoForge 21.1.265 in Prism and select Java 21. Do not remove mods from your working instance.

1. Download the official `packwiz-installer-bootstrap.jar` using the installation guide: https://packwiz.infra.link/tutorials/installing/packwiz-installer/ . Place it in the instance's Minecraft folder. Obtain executable JARs only from the official source.
2. In Edit Instance → Settings → Custom commands, enable the pre-launch command and set:

      ```text
      "$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/OWNER/REPOSITORY/main/pack.toml
      ```

      Replace the example URL with the actual published pack URL. `$INST_JAVA` is Prism's Java executable variable. Keep the command's working directory as the instance Minecraft folder.

3. Launch. Bootstrap downloads the installer, which checks the pack and synchronizes managed files before Minecraft starts. Initial installation requires network access; downloading mods contacts the URLs in the manifests. Test failed-network behavior before relying on offline play.
4. Verify that all mods and configs arrive and the game loads before sharing the instance. Export a small Prism starter instance containing loader metadata, bootstrap and the pre-launch command; exclude accounts, worlds, personal data and downloaded mods.

Updates mean **players receive the versions you commit**, not that all upstream mods update automatically. Review and test updates before publishing. Packwiz installer does not replace Prism's Minecraft/NeoForge components; loader or Minecraft changes require updating the starter instance and existing launcher settings separately.

## Maintaining the pack

Run the packwiz CLI **inside this directory**:

```text
packwiz modrinth install <project-or-version-URL>
packwiz update <mod-name>
packwiz remove <mod-name>
packwiz refresh
py -3 tools/validate.py --release
```

Use `packwiz update --all` only when intentionally testing a broad upgrade. Review manifest/config changes, test a clean client, then commit and push `pack.toml`, `index.toml`, changed manifests and configs together. Players synchronize on their next launch, not while Minecraft is running. Back up worlds before gameplay-affecting updates. Never run installer synchronization against the authoring directory.

## Conversion tooling

`py -3 tools/convert.py` reconstructs the initial snapshot from the adjacent original Minecraft directory. It verifies Prism download metadata against local bytes and queries Modrinth by SHA-512 for unmatched mods/resource packs. This sends file hashes, not JAR contents. It excludes disabled `.jar.disabled` files. **Do not rerun it after maintaining this pack manually**: it replaces generated manifests/configs and resets the pack version to the original snapshot.

`py -3 tools/validate.py` checks local TOML and index integrity without downloads. Add `--release` to reject unresolved downloads. This is not a game-launch or dependency compatibility test.
