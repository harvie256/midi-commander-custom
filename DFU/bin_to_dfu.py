#! env python3
# -*- coding: utf-8 -*-
"""Pack a firmware image into a DfuSe (.dfu) file.

This replaces the Windows-only DfuFileMgr.exe for building the upload package,
so a .dfu can be produced on any platform that runs Python.

The output is a DfuSe v1.1a file containing a single target with a single
element, which is what DfuFileMgr.exe produces for this project and what the
STM32 bootloader expects.

File layout:

    prefix    11 bytes   b"DfuSe", version, image size, number of targets
    target   274 bytes   b"Target", alt setting, name, size, element count
    element    8 bytes   load address, data length
    data                 the firmware image itself
    suffix    16 bytes   USB ids, DFU version, b"UFD", length, CRC32
"""
import argparse
import binascii
import struct
import sys
from pathlib import Path
from typing import List, Tuple

# The STM32 system bootloader enumerates as 0483:df11. DfuFileMgr.exe leaves
# the product id as 0x0000 unless told otherwise, but writing the real id lets
# dfu-util verify the file matches the connected device.
DEFAULT_VENDOR_ID = 0x0483
DEFAULT_PRODUCT_ID = 0xDF11

# Alternate setting 0 is the internal flash. See the `dfu-util --list` output
# in the README for the other settings the bootloader advertises.
DEFAULT_ALT_SETTING = 0

DFUSE_VERSION = 0x01
BCD_DFU = 0x011A
SUFFIX_LENGTH = 16
TARGET_NAME_LENGTH = 255


def parse_intel_hex(text: str) -> Tuple[int, bytes]:
    """Return the start address and contiguous data of an Intel HEX file.

    Only the record types produced by objcopy are handled. Gaps between
    records are padded with 0xFF, matching erased flash.
    """
    chunks: List[Tuple[int, bytes]] = []
    base = 0

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if not line.startswith(":"):
            raise ValueError(f"line {lineno}: record does not start with ':'")

        try:
            record = binascii.unhexlify(line[1:])
        except binascii.Error as exc:
            raise ValueError(f"line {lineno}: {exc}") from exc

        if len(record) < 5:
            raise ValueError(f"line {lineno}: record is too short")
        if sum(record) & 0xFF:
            raise ValueError(f"line {lineno}: checksum mismatch")

        count, offset, rectype = struct.unpack(">BHB", record[:4])
        data = record[4:-1]
        if len(data) != count:
            raise ValueError(f"line {lineno}: byte count does not match payload")

        if rectype == 0x00:  # data
            chunks.append((base + offset, data))
        elif rectype == 0x01:  # end of file
            break
        elif rectype == 0x04:  # extended linear address
            base = struct.unpack(">H", data)[0] << 16
        elif rectype == 0x05:  # start linear address, carries no image data
            continue
        else:
            raise ValueError(f"line {lineno}: unsupported record type {rectype:#04x}")

    if not chunks:
        raise ValueError("file contains no data records")

    chunks.sort(key=lambda c: c[0])
    start = chunks[0][0]
    image = bytearray()
    for address, data in chunks:
        cursor = start + len(image)
        if address < cursor:
            raise ValueError(f"overlapping data at {address:#010x}")
        image += b"\xff" * (address - cursor)
        image += data

    return start, bytes(image)


def build_dfu(
    data: bytes,
    address: int,
    vendor_id: int,
    product_id: int,
    device_id: int,
    alt_setting: int,
    target_name: str,
) -> bytes:
    """Wrap a raw firmware image in the DfuSe container."""
    name = target_name.encode("ascii")
    if len(name) > TARGET_NAME_LENGTH:
        raise ValueError(f"target name must be {TARGET_NAME_LENGTH} characters or less")

    element = struct.pack("<II", address, len(data)) + data
    target = (
        struct.pack(
            "<6sBI255sII",
            b"Target",
            alt_setting,
            1,  # the name field is in use
            name.ljust(TARGET_NAME_LENGTH, b"\x00"),
            len(element),
            1,  # one element
        )
        + element
    )

    # The size in the prefix covers the prefix itself and every target, but not
    # the suffix.
    prefix = struct.pack("<5sBIB", b"DfuSe", DFUSE_VERSION, 11 + len(target), 1)

    body = prefix + target
    suffix = struct.pack(
        "<HHHH3sB",
        device_id,
        product_id,
        vendor_id,
        BCD_DFU,
        b"UFD",
        SUFFIX_LENGTH,
    )

    # The CRC covers everything ahead of it, and is stored inverted.
    crc = 0xFFFFFFFF ^ binascii.crc32(body + suffix)
    return body + suffix + struct.pack("<I", crc)


def auto_int(text: str) -> int:
    return int(text, 0)


def main(args: argparse.Namespace) -> int:
    source = Path(args.firmware)

    if source.suffix.lower() in (".hex", ".ihx"):
        try:
            address, data = parse_intel_hex(source.read_text())
        except ValueError as exc:
            print(f"error: {source}: {exc}", file=sys.stderr)
            return 1
        if args.address is not None:
            address = args.address
    else:
        if args.address is None:
            print(
                f"error: {source} is a raw binary, so --address is required "
                "(use 0x8003000 for a DFU Release build)",
                file=sys.stderr,
            )
            return 1
        address = args.address
        data = source.read_bytes()

    if not data:
        print(f"error: {source} contains no data", file=sys.stderr)
        return 1

    package = build_dfu(
        data,
        address,
        args.vid,
        args.pid,
        args.device,
        args.alt,
        args.target_name,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(package)

    print(f"Wrote {output}")
    print(f"  load address : {address:#010x}")
    print(f"  image size   : {len(data)} bytes")
    print(f"  usb ids      : {args.vid:04x}:{args.pid:04x}, alt setting {args.alt}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Pack a firmware .bin or .hex into a DfuSe .dfu file for "
        "upload to the Midi Commander.",
    )
    p.add_argument(
        "firmware",
        help="Path to the firmware image. A .hex carries its own load address; "
        "a .bin needs --address.",
    )
    p.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path of the .dfu file to write",
    )
    p.add_argument(
        "-a",
        "--address",
        type=auto_int,
        help="Load address, e.g. 0x8003000. Required for a .bin, and overrides "
        "the address found in a .hex.",
    )
    # These match what DfuFileMgr.exe wrote and should not normally be changed.
    p.add_argument(
        "--vid", type=auto_int, default=DEFAULT_VENDOR_ID, help=argparse.SUPPRESS
    )
    p.add_argument(
        "--pid", type=auto_int, default=DEFAULT_PRODUCT_ID, help=argparse.SUPPRESS
    )
    p.add_argument("--device", type=auto_int, default=0x0000, help=argparse.SUPPRESS)
    p.add_argument(
        "--alt", type=auto_int, default=DEFAULT_ALT_SETTING, help=argparse.SUPPRESS
    )
    p.add_argument("--target-name", default="ST...", help=argparse.SUPPRESS)
    sys.exit(main(p.parse_args()))
