# -*- coding: utf-8 -*-


from beaker.client.task_watcher import *
from beaker.client.convert import Convert
from beaker.client import BeakerCommand
from optparse import OptionValueError
import sys

class Job_Submit(BeakerCommand):
    """Submit job(s) to scheduler"""
    enabled = True

    def options(self):
        self.parser.usage = "%%prog %s" % self.normalized_name
        self.parser.add_option(
            "--debug",
            default=False,
            action="store_true",
            help="print the jobxml that it would submit",
        )
        self.parser.add_option(
            "--dryrun",
            default=False,
            action="store_true",
            help="Don't submit job to scheduler",
        )
        self.parser.add_option(
            "--convert",
            default=False,
            action="store_true",
            help="convert from legacy rhts xml to beaker xml",
        )
        self.parser.add_option(
            "--nowait",
            default=False,
            action="store_true",
            help="Don't wait on job completion",
        )



    def run(self, *args, **kwargs):
        username = kwargs.pop("username", None)
        password = kwargs.pop("password", None)
        convert  = kwargs.pop("convert", False)
        debug   = kwargs.pop("debug", False)
        dryrun  = kwargs.pop("dryrun", False)
        nowait  = kwargs.pop("nowait", False)

        jobs = args

        self.set_hub(username, password)
        submitted_jobs = []
        failed = False
        for job in jobs:
            jobxml = open(job, "r").read()
            if convert:
                jobxml = Convert.rhts2beaker(jobxml)
            if debug:
                print jobxml
            if not dryrun:
                try:
                    submitted_jobs.append(self.hub.jobs.upload(jobxml))
                except Exception, ex:
                    failed = True
                    print ex
        if not dryrun and not nowait:
            TaskWatcher.watch_tasks(self.hub, submitted_jobs)
            for submitted_job in submitted_jobs:
                print self.hub.taskactions.to_xml(submitted_job)
            if failed:
                sys.exit(1)
