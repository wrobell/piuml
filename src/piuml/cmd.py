#
# piUML - UML diagram generator.
#
# Copyright (C) 2010 by Artur Wroblewski <wrobell@pld-linux.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Functions for running of external programs.
"""

import subprocess


class CmdError(RuntimeError):
    """
    Raised when running a program is not possible or it ended with an
    error.

    :Attributes:
     output
        Output of the running program (if any).
    """
    def __init__(self, output):
        self.output = output


def cmd(*args, **kw):
    """
    Run external program.

    :Parameters
     args
        Program to run (first item) and its paramters (rest of items).
     cwd
        Working directory.
    """
    cwd = kw.get('cwd', '.')
    p = subprocess.Popen(args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            cwd=cwd)
    out, err = p.communicate()
    if p.returncode != 0:
        raise CmdError(out + '\n' + err)
    return p.returncode


# vim: sw=4:et:ai
