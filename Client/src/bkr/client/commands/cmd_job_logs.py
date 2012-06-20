# -*- coding: utf-8 -*-

"""
bkr job-logs: Print URLs of Beaker recipe log files
===================================================

.. program:: bkr job-logs

Synopsis
--------

:program:`bkr job-logs` [*options*] <taskspec>...

Description
-----------

Specify one or more <taskspec> arguments to be exported. A list of the 
log files for each argument will be printed to stdout.

The <taskspec> arguments follow the same format as in other :program:`bkr` 
subcommands (for example, ``J:1234``). See :ref:`Specifying tasks <taskspec>` 
in :manpage:`bkr(1)`. Doesn't work for  T:$TASKID and TR:$RESULTID.

Options
-------

Common :program:`bkr` options are described in the :ref:`Options 
<common-options>` section of :manpage:`bkr(1)`.

Exit status
-----------

Non-zero on error, otherwise zero.

Examples
--------

Display logs for job 12345::

    bkr job-logs J:12345

See also
--------

:manpage:`bkr(1)`
"""

import sys
from bkr.client import BeakerCommand
from optparse import OptionValueError
from bkr.client.task_watcher import *
import libxml2

class Job_Logs(BeakerCommand):
    """Print URLs of recipe log files"""
    enabled = True

    def options(self):
        self.parser.usage = "%%prog %s [options] <taskspec>..." % self.normalized_name


    def run(self, *args, **kwargs):
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)

        self.set_hub(username, password)
        for task in args:
            recipes = libxml2.parseDoc(self.hub.taskactions.to_xml(task))\
                    .xpathNewContext().xpathEval("//recipe")
            if not recipes:
                sys.stderr.write('No recipes found for %s. Specify J, RS, or R.\n' % task)
                sys.exit(1)
            for recipe in recipes:
               logfiles = self.hub.recipes.files(recipe.prop('id'))
               for log in logfiles:
                   print log['url']