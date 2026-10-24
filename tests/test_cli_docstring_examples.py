"""Every CLI command's docstring example runs, and asserts something.

``pytest --doctest-modules`` never collects these examples: ``@click.command`` and
``@click.group`` replace the function with a ``Command`` object, and doctest only walks real
functions and classes, so an example under a decorated callback can be false without anything
going red. This test finds every command registered on the root group, runs the example in its
callback's docstring through doctest with that module's globals, and refuses one that checks no
output: an example made only of imports passes doctest while showing nothing.
"""

from __future__ import annotations

import doctest
import sys

import click
import pytest

from bitranox_template_py_cli.adapters.cli.root import cli


def _commands(group: click.Group) -> dict[str, click.Command]:
    """The group itself plus every command under it, nested groups included."""
    found: dict[str, click.Command] = {group.name or "cli": group}
    for name, command in group.commands.items():
        found[name] = command
        if isinstance(command, click.Group):
            found |= _commands(command)
    return found


COMMANDS = _commands(cli)


def _doctest_for(command: click.Command) -> doctest.DocTest:
    callback = command.callback
    assert callback is not None, f"{command.name} has no callback"
    module = sys.modules[callback.__module__]
    return doctest.DocTestParser().get_doctest(
        callback.__doc__ or "", dict(vars(module)), command.name or "cli", module.__file__, 0
    )


@pytest.mark.os_agnostic
def test_the_root_group_and_its_commands_are_all_collected() -> None:
    # A collector that silently found nothing would pass every parametrized case below.
    assert "cli" in COMMANDS
    assert {"hello", "info", "fail", "config", "send-email"} <= COMMANDS.keys()


@pytest.mark.os_agnostic
@pytest.mark.parametrize("name", sorted(COMMANDS))
def test_the_docstring_example_checks_an_output(name: str) -> None:
    test = _doctest_for(COMMANDS[name])

    checked = [example for example in test.examples if example.want.strip()]

    assert checked, f"{name}: its docstring example shows no expected output, so it proves nothing"


@pytest.mark.os_agnostic
@pytest.mark.parametrize("name", sorted(COMMANDS))
def test_the_docstring_example_is_true(name: str, managed_traceback_state: None) -> None:
    test = _doctest_for(COMMANDS[name])
    report: list[str] = []
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

    result = runner.run(test, out=report.append)

    assert result.failed == 0, "".join(report)
