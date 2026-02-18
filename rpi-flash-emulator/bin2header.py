#!/usr/bin/env python3
"""Convert a binary file to a C header with a 64K uint8_t array."""

import sys
import os

ROM_SIZE = 65536

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.bin> [output.h]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "rom.h"

    with open(input_path, "rb") as f:
        data = f.read()

    if len(data) > ROM_SIZE:
        print(f"Error: input file is {len(data)} bytes, exceeds {ROM_SIZE}", file=sys.stderr)
        sys.exit(1)

    # Pad to 64K with zeros
    data = data + b'\x00' * (ROM_SIZE - len(data))

    with open(output_path, "w") as f:
        f.write("#ifndef ROM_H\n")
        f.write("#define ROM_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write(f"// Generated from {os.path.basename(input_path)}\n")
        f.write(f"static uint8_t rom_bin[{ROM_SIZE}] __attribute__ ((aligned (65536))) = {{\n")

        for i in range(0, ROM_SIZE, 16):
            chunk = data[i:i+16]
            hex_vals = ", ".join(f"0x{b:02x}" for b in chunk)
            f.write(f"    {hex_vals},\n")

        f.write("};\n\n")
        f.write("#endif // ROM_H\n")

    print(f"Wrote {output_path} ({len(data)} bytes from {os.path.basename(input_path)})")

if __name__ == "__main__":
    main()
