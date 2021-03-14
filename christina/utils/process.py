from subprocess import Popen, PIPE
from typing import List, Union, Any


def subprocess(cmd: Union[str, List[str]], *values: Any):
    if isinstance(cmd, str):
        items = cmd.split()

        placeholders_count = sum(1 for item in items if '{}' in item)

        if placeholders_count != len(values):
            raise ValueError(
                f'The values does not have the same length as the placeholders. '
                f'(placeholders: {placeholders_count}, values: {len(values)})')

        # convert to list so we can pop() it
        values = list(values)

        # substitute the placeholders
        cmd = [item.format(values.pop(0)) if '{}' in item else item for item in items]

    p = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)

    output, error = p.communicate()

    if p.returncode != 0:
        raise ChildProcessError(
            f'Executing "{" ".join(cmd)}" failed with code {p.returncode}. Details:\n{output}\n{error}')

    return output
