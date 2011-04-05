# Beaker
#
# Copyright (c) 2010 Red Hat, Inc. All rights reserved. This copyrighted material 
# is made available to anyone wishing to use, modify, copy, or
# redistribute it subject to the terms and conditions of the GNU General
# Public License v.2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import unittest
import logging
import time
import tempfile
from turbogears.database import session

from bkr.server.test.selenium import SeleniumTestCase
from bkr.server.test import data_setup

class TestJobMatrix(SeleniumTestCase):
    
    @classmethod
    def setupClass(cls):
        cls.job_whiteboard = u'DanC says hi'
        cls.recipe_whiteboard = u'breakage lol \'#&^!<'
        cls.passed_job = data_setup.create_completed_job(
                whiteboard=cls.job_whiteboard, result=u'Pass',
                recipe_whiteboard=cls.recipe_whiteboard,
                distro=data_setup.create_distro(arch=u'i386'))
        cls.warned_job = data_setup.create_completed_job(
                whiteboard=cls.job_whiteboard, result=u'Warn',
                recipe_whiteboard=cls.recipe_whiteboard,
                distro=data_setup.create_distro(arch=u'ia64'))
        cls.failed_job = data_setup.create_completed_job(
                whiteboard=cls.job_whiteboard, result=u'Fail',
                recipe_whiteboard=cls.recipe_whiteboard,
                distro=data_setup.create_distro(arch=u'x86_64'))
        session.flush()
        cls.selenium = cls.get_selenium()
        cls.selenium.start()

    @classmethod
    def teardown(cls):
        cls.selenium.stop()

    def test_generate_by_whiteboard(self):
        sel = self.selenium
        sel.open('matrix')
        sel.wait_for_page_to_load('30000')
        sel.select('whiteboard', self.job_whiteboard)
        sel.click('//select[@name="whiteboard"]//option[@value="%s"]'
                % self.job_whiteboard)
        sel.click('//input[@value="Generate"]')
        sel.wait_for_page_to_load('30000')
        body = sel.get_text('//body')
        self.assert_('Pass: 1' in body)
        new_job = data_setup.create_completed_job(
            whiteboard=self.job_whiteboard, result=u'Pass',
            recipe_whiteboard=self.recipe_whiteboard,
            distro=data_setup.create_distro(arch=u'i386'))
        session.flush()
        sel.click('//input[@value="Generate"]')
        sel.wait_for_page_to_load('30000')
        body_2 = sel.get_text('//body')
        self.assert_('Pass: 2' in body_2)
        session.delete(new_job)
        session.flush()

    def test_it(self):
        sel = self.selenium
        sel.open('')
        sel.click('link=Matrix')
        sel.wait_for_page_to_load('30000')
        sel.type('remote_form_whiteboard_filter', self.job_whiteboard)
        sel.click('//input[@value="Generate"]')
        sel.wait_for_page_to_load('30000')
        # why are both .select and .click necessary?? weird
        # Because there are two fields and we need to know from which we are
        # generating our result
        sel.select('whiteboard', 'label=%s' % self.job_whiteboard)
        sel.click('//select[@name="whiteboard"]//option[@value="%s"]'
                % self.job_whiteboard)
        sel.click('//input[@value="Generate"]')
        sel.wait_for_page_to_load('30000')

        self.assertEqual(sel.get_table("//div[@class='dataTables_scrollHeadInner']/table[@class=' FixedColumns_Cloned'].0.0"), 'Task')
        self.assertEqual(sel.get_table("//div[@class='dataTables_scrollHeadInner']/table.0.1"),
            'i386')
        self.assertEqual(sel.get_table("//div[@class='dataTables_scrollHeadInner']/table.0.2"),
            'ia64')
        self.assertEqual(sel.get_table("//div[@class='dataTables_scrollHeadInner']/table.0.3"),
            'x86_64')

        # get_table('matrix_datagrid') doesn't seem to return anything
        # possibly because of elements inside table
        body = sel.get_text("//table[@id='matrix_datagrid']/tbody")
        self.assert_('Pass: 1' in body)
        self.assert_('Warn: 1' in body)
        self.assert_('Fail: 1' in body)

        self.assertEqual(sel.get_table("//div[@class='dataTables_scrollHeadInner']/table.1.1"),
            '%s' % self.recipe_whiteboard)
        self.assertEqual(sel.get_table("//div[@class='dataTables_scrollHeadInner']/table.1.2"),
            '%s' % self.recipe_whiteboard)
        self.assertEqual(sel.get_table("//div[@class='dataTables_scrollHeadInner']/table.1.3"),
            '%s' % self.recipe_whiteboard)
        sel.click('link=Pass: 1')
        sel.wait_for_page_to_load('3000')
        self.assertEqual(sel.get_title(), 'Executed Tasks')
        self.assertEqual(sel.get_value('whiteboard'), self.recipe_whiteboard)
        self.assertEqual(sel.get_table('css=.list.1.0'),
                self.passed_job.recipesets[0].recipes[0].tasks[0].t_id)
        sel.go_back()
        sel.wait_for_page_to_load('3000')
        sel.click('link=Warn: 1')
        sel.wait_for_page_to_load('3000')
        self.assertEqual(sel.get_title(), 'Executed Tasks')
        self.assertEqual(sel.get_value('whiteboard'), self.recipe_whiteboard)
        self.assertEqual(sel.get_table('css=.list.1.0'),
                self.warned_job.recipesets[0].recipes[0].tasks[0].t_id)
        sel.go_back()
        sel.wait_for_page_to_load('3000')

        sel.click('link=Fail: 1')
        sel.wait_for_page_to_load('3000')
        self.assertEqual(sel.get_title(), 'Executed Tasks')
        self.assertEqual(sel.get_value('whiteboard'), self.recipe_whiteboard)
        self.assertEqual(sel.get_table('css=.list.1.0'),
                self.failed_job.recipesets[0].recipes[0].tasks[0].t_id)