<p align="center">
  <h1 align="center">iPA Edit</h1>
  <p align="center">
    A powerful cross-platform tool for modifying, signing, and tweaking iOS <code>.ipa</code> files.
    <br /><br />
    <img src="https://img.shields.io/badge/version-v1.3-6b63ff?style=flat-square" alt="Version" />
    <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/license-GPLv3-green?style=flat-square" alt="License" />
    <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Platform" />
    <br /><br />
    <a href="https://github.com/SHAJON-404/iPA-Edit/releases">📦 Download</a>
    ·
    <a href="https://github.com/SHAJON-404/iPA-Edit/issues">Report Bug</a>
    ·
    <a href="https://github.com/SHAJON-404/iPA-Edit/issues">Request Feature</a>
  </p>
</p>

---

## ✨ Features

- **Inject tweaks** — add `.dylib` and `.deb` tweaks from the `tweaks/` folder, with automatic CydiaSubstrate bundling (via ElleKit) and `@rpath` patching
- **Remove injected tweaks** — delete tweaks from `Frameworks/` and strip their load commands via `zsign`
- **Export tweaks** — extract existing `.dylib` and `.framework` tweaks from an IPA to the `tweaks_extracted/` folder
- **Code signing** — sign iPAs using `zsign` with auto-detected certificates
- **Interactive mode** — run without arguments for a guided menu-driven experience
- **Cross-platform** — works on Windows, macOS, and Linux

## 📁 Project Structure

```
iPA-Edit/
├── ipa-edit.py              # entry point (~55 lines)
├── modules/                 # core logic package
│   ├── __constants.py       # shared colors & style
│   ├── __deb_extractor.py   # .deb (ar) archive extractor
│   ├── __macho_utils.py     # Mach-O binary patching
│   ├── __ipa_editor.py      # IPAEditor class
│   ├── __tweak_manager.py   # tweak inject / remove
│   └── __menu.py            # interactive CLI menus
├── certificate/             # place signing certificates here
│   ├── *.p12
│   └── *.mobileprovision
├── tweaks/                  # place .dylib or .deb tweaks here
├── tweaks_extracted/        # exported tweaks land here (auto-created)
├── zsign/                   # bundled zsign binaries (auto-detected)
│   ├── windows/zsign.exe
│   ├── mac/zsign
│   └── linux/zsign
├── Signed/                  # signed output (auto-created)
└── Unsigned/                # unsigned output (auto-created)
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**

### Installation

```bash
git clone --depth=1 https://github.com/SHAJON-404/iPA-Edit.git
cd iPA-Edit
```

### Signing Setup *(optional)*

1. Place your `.p12` certificate and `.mobileprovision` profile in the `certificate/` folder.
2. The matching `zsign` binary for your OS is detected automatically from the `zsign/` directory.

### Tweak Setup

Place any `.dylib` or `.deb` tweak files in the `tweaks/` folder. They will appear in the numbered list when using option **2** in the menu.

## 🖥️ Platform Support

| Feature | Windows | macOS | Linux |
|:--|:--:|:--:|:--:|
| iPA signing | ✅ | ✅ | ✅ |
| Tweak injection | ✅ | ✅ | ✅ |
| Tweak removal | ✅ | ✅ | ✅ |
| Tweak export | ✅ | ✅ | ✅ |

## 📖 Usage

### Interactive Mode

Simply run with no arguments:

```bash
python ipa-edit.py
```

You'll see a menu:

```
--------------------------------------------------------------------------------
                    iPA Edit - By S. SHAJON
--------------------------------------------------------------------------------
1. Inject tweaks
2. Remove tweaks
3. Export tweaks from iPA
4. Sign IPA with certificate
5. Exit
```

### Command-Line Mode

```bash
python ipa-edit.py -i <input.ipa> -o <output.ipa> [options]
```

| Flag | Description |
|:--|:--|
| `-i` | Input `.ipa` file |
| `-o` | Output path or filename |
| `-tw` | Inject tweaks from `tweaks/` folder |
| `-rm-tw` | Remove tweaks by name (comma-separated) |
| `-d` / `--export-tweaks` | Export `.dylib` / `.framework` tweaks |

### Examples

```bash
# Inject tweaks (interactive selection)
python ipa-edit.py -i app.ipa -tw

# Remove specific tweaks by name
python ipa-edit.py -i app.ipa -rm-tw "TweakName.dylib,OtherTweak"

# Export existing tweaks
python ipa-edit.py -i app.ipa -d
```

## 💉 Tweak Injection

Place `.dylib` or `.deb` files in the `tweaks/` folder, then select option **2** (or use `-tw`):

```
[*] Available tweaks:
  1: AboutME.dylib  (518 KB)
  2: blatantsPatch.dylib  (103 KB)
  3: some_tweak.deb  (1.2 MB)

[?] use , for multiple | 'all' for every tweak | 'exit' to cancel
[?] Tweak number(s) to inject: 1,2,3
```

**Advanced Injection System:**
- **.deb Support**: Automatically extracts `.deb` archives and locates `MobileSubstrate` dynamic libraries.
- **Auto-Substrate Bundling**: If any tweak requires `CydiaSubstrate`, `CydiaSubstrate.framework` from `ellekit.deb` is automatically bundled into the app.
- **Path Patching**: Fixes hardcoded jailbreak paths (e.g. `/Library/Frameworks/...`) to standard `@rpath/` iOS paths before injection, preventing AMFI/sandbox crashes on jailed devices.

## 🔧 Tweak Removal

Select option **2** (or use `-rm-tw`). The tool will:

1. Scan the IPA's `Frameworks/` folder and list all injected `.dylib` and `.framework` files.
2. Remove selected files from the archive.
3. Use `zsign` to strip the corresponding `LC_LOAD_WEAK_DYLIB` load commands from the main binary.
4. Optionally re-sign the output with your certificate.

## 🔐 Certificate & Zsign Auto-Detection

When signing, certificates and the signing tool are resolved automatically:

**zsign** — checked in order:
1. Bundled binary from `zsign/{windows,mac,linux}/`
2. `zsign` on system `PATH`
3. Manual prompt as fallback

**Certificate** — checked in order:
1. `certificate/` folder (`.p12` + `.mobileprovision`)
2. Manual prompt as fallback

## 📝 License

This project is licensed under the **GPLv3** License.

## 🙏 Credits

- Original project by [binnichtaktiv](https://github.com/binnichtaktiv)
- Rewritten and maintained by [SHAJON-404](https://github.com/SHAJON-404)

---

<p align="center">
  <a href="https://github.com/SHAJON-404/iPA-Edit/issues">Issues</a> · <a href="https://shajon.dev">Contact</a>
</p>

[![Stargazers over time](https://starchart.cc/SHAJON-404/iPA-Edit.svg?background=%231e1e1e&axis=%23f9f9f9&line=%236b63ff)](https://starchart.cc/SHAJON-404/iPA-Edit)
