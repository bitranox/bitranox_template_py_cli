"""Core demonstration helpers exercised by the CLI transport.

This module holds the minimal domain-level behaviors that the CLI exposes while
the real logging helpers are under construction. Keeping the greeting and
intentional failure logic here means the CLI can validate stdout handling and
error propagation without depending on yet-to-be-built Rich logging features.

Contents
--------
* :func:`hello_world` – emits the canonical greeting used in documentation and
  smoke tests. This gives developers a stable, human-readable success path.
* :func:`i_should_fail` – raises an intentional error so that failure handling
  and traceback controls can be validated end-to-end.

System Context
--------------
The CLI adapter defined in :mod:`bitranox_template_py_cli.cli` delegates to
these helpers to keep the transport thin. The system design reference in
``docs/systemdesign/module_reference.md`` links back to this module so that the
relationship between the CLI surface and the placeholder domain logic remains
clear during incremental feature development.
"""

from __future__ import annotations


def hello_world() -> None:
    """Emit the canonical greeting used to verify the happy-path workflow.

    Why
        The scaffold ships with a deterministic success path so developers can
        check their packaging, CLI wiring, and documentation quickly without
        waiting for the richer logging helpers.

    What
        Prints the literal ``"Hello World"`` string followed by a newline to
        ``stdout``.

    Side Effects
        Writes directly to the process ``stdout`` stream.

    Examples
    --------
    >>> hello_world()
    Hello World
    """

    print("Hello World")


def i_should_fail() -> None:
    """Intentionally raise ``RuntimeError`` to test error propagation paths.

    Why
        The CLI and integration tests need a deterministic failure scenario to
        ensure traceback toggling and exit-code mapping stay correct as the
        project evolves.

    What
        Raises ``RuntimeError`` with the message ``"I should fail"`` every time
        it is called.

    Side Effects
        None besides raising the exception.

    Raises
        RuntimeError: Always, so downstream adapters can verify their error
        handling branches.

    Examples
    --------
    >>> i_should_fail()
    Traceback (most recent call last):
    ...
    RuntimeError: I should fail
    """

    raise RuntimeError("I should fail")
