"""Where the QE programs are, from the receipt the pw, ph and cp wrappers share (qe-v6, qe-v7).

The receipt points at pw.x. ph.x and cp.x are expected next to it.
"""

import os

from crab.wrappers.base import MissingBinaryError


def pw_from_receipt(receipt):
    """pw.x as the receipt gives it: a path, or a command name for a module install.

    None when there is no receipt or it names nothing.
    """
    if not receipt:
        return None
    base_path = receipt.get("binary_path", "")
    if not base_path:
        return None
    install_type = receipt.get("type", "source")

    if install_type == "module":
        return base_path

    if install_type == "binary":
        return os.path.join(base_path, "pw.x")

    # source: binary_path = target_dir/bin (CMake install prefix stub)
    # actual build output is at target_dir/build/bin/pw.x
    if base_path.endswith("bin"):
        base_path = os.path.dirname(base_path)
    return os.path.join(base_path, "build", "bin", "pw.x")


def _next_to(pw, program, benchmark_id):
    """`program` in pw.x's directory, or the bare command `program` when pw.x is a command name.

    Raises:
        MissingBinaryError: pw.x is a path and there is no `program` beside it.
    """
    if not pw:
        return None
    directory = os.path.dirname(pw)
    if not directory:
        return program
    path = os.path.join(directory, program)
    if not os.path.isfile(path):
        raise MissingBinaryError(
            f"No {program} at {path}, the directory of pw.x from receipt {benchmark_id!r} ({pw}). "
            f"Install {program} there, or set the app's 'binary' key in the config."
        )
    return path


def ph_next_to(pw, benchmark_id):
    """ph.x next to pw.x (see `_next_to`)."""
    return _next_to(pw, "ph.x", benchmark_id)


def cp_next_to(pw, benchmark_id):
    """cp.x next to pw.x (see `_next_to`)."""
    return _next_to(pw, "cp.x", benchmark_id)
