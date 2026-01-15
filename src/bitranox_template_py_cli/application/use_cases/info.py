"""Info use case.

Outputs package metadata information.

Example:
    >>> from io import StringIO
    >>> from bitranox_template_py_cli.application.use_cases import InfoUseCase
    >>> class TestAdapter:
    ...     def __init__(self):
    ...         self.buffer = StringIO()
    ...     def write(self, text: str) -> None:
    ...         self.buffer.write(text)
    ...     def write_line(self, text: str) -> None:
    ...         self.buffer.write(f"{text}\\n")
    >>> adapter = TestAdapter()
    >>> use_case = InfoUseCase(output=adapter)
"""

from dataclasses import dataclass

from ..ports.output import OutputPort


@dataclass(frozen=True, slots=True)
class InfoUseCase:
    """Use case that outputs package metadata.

    Writes package information to the output port using the
    static metadata from __init__conf__.

    Attributes:
        output: The output port to write metadata to.
    """

    output: OutputPort

    def execute(self) -> None:
        """Execute the use case by writing package metadata.

        Uses the print_info function from __init__conf__ to write
        the metadata. The output port is currently not used as
        print_info writes directly to stdout.
        """
        from ... import __init__conf__

        __init__conf__.print_info()


__all__ = [
    "InfoUseCase",
]
