"""
macho_utils.py — Mach-O binary patching utilities.

Functions for injecting LC_LOAD_WEAK_DYLIB load commands and patching
hardcoded dylib paths inside fat/thin Mach-O binaries.
"""

import struct
from .__constants import RED, RESET


def inject_lc_load_weak_dylib(data: bytearray, dylib_path_str: str) -> None:
    """Append one LC_LOAD_WEAK_DYLIB load command to every Mach-O slice."""
    magic = struct.unpack_from("<I", data, 0)[0]
    if magic in (0xCAFEBABE, 0xBEBAFECA):
        nfat = struct.unpack_from(">I", data, 4)[0]
        for idx in range(nfat):
            off = 8 + idx * 20
            sl  = struct.unpack_from(">I", data, off + 8)[0]
            _inject_lc_into_slice(data, sl, dylib_path_str)
    elif magic in (0xFEEDFACE, 0xFEEDFACF):
        _inject_lc_into_slice(data, 0, dylib_path_str)


def _inject_lc_into_slice(data: bytearray, base: int, dylib_path_str: str) -> None:
    """Inject LC_LOAD_DYLIB/WEAK into one Mach-O slice."""
    LC_LOAD_WEAK  = 0x80000018
    LC_LOAD_DYLIB = 0x0c
    LC_SEGMENT    = 0x01
    LC_SEGMENT_64 = 0x19
    DYLIB_CMD_SIZE = 24   # sizeof(dylib_command)

    sl_magic   = struct.unpack_from("<I", data, base)[0]
    is64       = sl_magic == 0xFEEDFACF
    hdr_size   = 32 if is64 else 28
    ncmds      = struct.unpack_from("<I", data, base + 16)[0]
    sizeofcmds = struct.unpack_from("<I", data, base + 20)[0]

    offset   = base + hdr_size
    cmds_end = base + hdr_size + sizeofcmds
    text_section_fileoff: int | None = None

    for _ in range(ncmds):
        if offset >= cmds_end:
            break
        cmd     = struct.unpack_from("<I", data, offset)[0]
        cmdsize = struct.unpack_from("<I", data, offset + 4)[0]
        if cmdsize == 0:
            break

        if cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK):
            name_off = struct.unpack_from("<I", data, offset + 8)[0]
            ns = offset + name_off
            if 0 in data[ns: offset + cmdsize]:
                ne = data.index(0, ns)
            else:
                ne = offset + cmdsize
            if data[ns:ne].decode("utf-8", "replace") == dylib_path_str:
                return  # already injected

        if cmd in (LC_SEGMENT, LC_SEGMENT_64):
            seg_name = data[offset + 8: offset + 24].rstrip(b"\x00").decode("utf-8", "replace")
            if seg_name == "__TEXT":
                if is64:
                    nsects     = struct.unpack_from("<I", data, offset + 64)[0]
                    sect_start = offset + 72
                    sect_size  = 80
                    sect_off_field = 48
                else:
                    nsects     = struct.unpack_from("<I", data, offset + 52)[0]
                    sect_start = offset + 56
                    sect_size  = 68
                    sect_off_field = 40
                for j in range(nsects):
                    s = sect_start + j * sect_size
                    sname = data[s:s + 16].rstrip(b"\x00").decode("utf-8", "replace")
                    if sname == "__text":
                        text_section_fileoff = struct.unpack_from("<I", data, s + sect_off_field)[0]
                        break

        offset += cmdsize

    if text_section_fileoff is not None and text_section_fileoff > (sizeofcmds + hdr_size):
        free_space = text_section_fileoff - sizeofcmds - hdr_size
    else:
        free_space = 0

    path_encoded = dylib_path_str.encode("utf-8")
    path_len     = len(path_encoded)
    padding      = 8 - (path_len % 8)
    new_cmdsize  = DYLIB_CMD_SIZE + path_len + padding

    if free_space > 0 and free_space < new_cmdsize:
        print(f"{RED}[-] No free space for LC ({dylib_path_str}): need {new_cmdsize}, have {free_space}{RESET}")
        return

    cmd_bytes  = struct.pack("<IIII", LC_LOAD_WEAK, new_cmdsize, DYLIB_CMD_SIZE, 2)
    cmd_bytes += struct.pack("<II", 0, 0)
    cmd_bytes += path_encoded
    cmd_bytes += b"\x00" * padding

    assert len(cmd_bytes) == new_cmdsize, f"cmd_bytes length mismatch: {len(cmd_bytes)} != {new_cmdsize}"

    insert_at = base + hdr_size + sizeofcmds
    data[insert_at: insert_at + new_cmdsize] = cmd_bytes

    struct.pack_into("<I", data, base + 16, ncmds + 1)
    struct.pack_into("<I", data, base + 20, sizeofcmds + new_cmdsize)


def change_macho_dylib_path(filepath: str, old_path: str, new_path: str) -> None:
    """Patch a hardcoded dylib path inside a Mach-O binary (fat or thin)."""
    old_b = old_path.encode("utf-8")
    new_b = new_path.encode("utf-8")

    with open(filepath, "rb") as f:
        data = bytearray(f.read())

    changed = False

    def patch_slice(base: int) -> None:
        nonlocal changed
        magic  = struct.unpack_from("<I", data, base)[0]
        is64   = magic == 0xFEEDFACF
        hdr    = 32 if is64 else 28
        ncmds  = struct.unpack_from("<I", data, base + 16)[0]
        szcmds = struct.unpack_from("<I", data, base + 20)[0]

        LC_LOAD_DYLIB = 0x0c
        LC_LOAD_WEAK  = 0x80000018

        off = base + hdr
        for _ in range(ncmds):
            if off >= base + hdr + szcmds:
                break
            cmd     = struct.unpack_from("<I", data, off)[0]
            cmdsize = struct.unpack_from("<I", data, off + 4)[0]
            if cmdsize == 0:
                break

            if cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK):
                name_off = struct.unpack_from("<I", data, off + 8)[0]
                ns = off + name_off
                ne = data.index(0, ns) if 0 in data[ns: off + cmdsize] else off + cmdsize
                p  = data[ns:ne]

                if p == old_b:
                    if len(new_b) <= len(old_b):
                        data[ns: ns + len(new_b)] = new_b
                        data[ns + len(new_b): ne] = b"\x00" * (len(old_b) - len(new_b))
                        changed = True

            off += cmdsize

    magic = struct.unpack_from("<I", data, 0)[0]
    if magic in (0xCAFEBABE, 0xBEBAFECA):
        nfat = struct.unpack_from(">I", data, 4)[0]
        for i in range(nfat):
            off = struct.unpack_from(">I", data, 8 + i * 20 + 8)[0]
            patch_slice(off)
    elif magic in (0xFEEDFACE, 0xFEEDFACF):
        patch_slice(0)

    if changed:
        with open(filepath, "wb") as f:
            f.write(data)
