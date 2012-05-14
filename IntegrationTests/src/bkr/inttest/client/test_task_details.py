
import unittest
from turbogears.database import session
from bkr.inttest import data_setup
from bkr.inttest.client import run_client

class TaskDetailsTest(unittest.TestCase):

    # https://bugzilla.redhat.com/show_bug.cgi?id=624417
    def test_details_include_owner_and_priority(self):
        with session.begin():
            owner = data_setup.create_user(user_name=u'besitzer@leo.org')
            task = data_setup.create_task(owner=owner, priority=u'Low')
        out = run_client(['bkr', 'task-details', task.name])
        details = eval(out[len(task.name) + 1:]) # XXX dodgy
        self.assertEquals(details['owner'], u'besitzer@leo.org')
        self.assertEquals(details['priority'], u'Low')

    def test_details_without_owner(self):
        # We no longer permit empty Owner but older tasks may still lack it
        with session.begin():
            task = data_setup.create_task()
            task.owner = None
        out = run_client(['bkr', 'task-details', task.name])
        details = eval(out[len(task.name) + 1:]) # XXX dodgy
        self.assertEquals(details['owner'], None)

    def test_details_without_uploader(self):
        # We now always record Uploader, but older tasks may lack it
        with session.begin():
            task = data_setup.create_task()
            task.uploader = None
        out = run_client(['bkr', 'task-details', task.name])
        details = eval(out[len(task.name) + 1:]) # XXX dodgy
        self.assertEquals(details['uploader'], None)

    def test_details_invalid_tasks(self):
        with session.begin():
            task = data_setup.create_task(name='invalid_task', valid=False)
            task.uploader = None
        out = run_client(['bkr', 'task-details', '--invalid', task.name])
        details = eval(out[len(task.name) + 1:]) # XXX dodgy
        self.assertEquals(details['name'], 'invalid_task')