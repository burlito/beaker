from bkr.server.bexceptions import BeakerException
import bkr.server.model as bkr_model
from bkr.server.model import TaskBase, LabController
from bkr.server.recipetasks import RecipeTasks
from bkr.server import scheduler
from turbogears import config as tg_config
from bkr.server.xmlrpccontroller import RPCRoot
from bkr.common.message_bus import BeakerBus
from bkr.common.helpers import BkrThreadPool
from time import sleep
from threading import Thread
import Queue

import logging
log = logging.getLogger(__name__)

try:
    from qpid.messaging.exceptions import NotFound
    from qpid.messaging import *
    from qpid import datatypes
except ImportError, e:
    pass


class ServerBeakerBus(BeakerBus):



    send_error_suffix = 'Cannot send message'
    rpcroot = RPCRoot()

    @classmethod
    def do_krb_auth(cls):
        from bkr.common.krb_auth import AuthManager
        principal = tg_config.get('identity.krb_auth_qpid_principal')
        keytab = tg_config.get('identity.krb_auth_qpid_keytab')
        cls._auth_mgr = AuthManager(primary_principal=principal, keytab=keytab)

    def __init__(self, *args, **kw):
        super(ServerBeakerBus, self).__init__(*args, **kw)
        self.thread_handlers.update({'beaker' : {'service_queue' : self._service_request_listener,  'expired_watchdogs' : self._expired_watchdogs_listener,},})

    def watchdog_notify_sender(self, session, status, watchdog, lc_fqdn, **kw):
            """Notify of watchdog change

            Will send a msg notifying of either a newly activated or newly expired watchdog

            """
            msg_kw = {}
            msg_kw['content'] = {'watchdog' : watchdog, 'status' : status }
            msg_kw['properties'] = { 'lc' : lc_fqdn }
            msg = Message(**msg_kw)
            snd = session.sender(self.headers_exchange)
            snd.send(msg)
            log.info('Sent msg %s' % msg)

    def task_update_sender(self, session, *args, **kw):
            """
            Send msg on Bus with subject 'TaskUpdate.Jx.RSx.Rx.Tx' only as far as the current task.
            i.e if we're updating a Recipe the subject will not include any tasks
            """
    
            try:
                task_id = kw.get('id',None)
                if task_id is None:
                    raise BeakerException(_('No valid id passed to task_update: %s' % self.send_error_suffix ))
                #Create full task structure for task i.e J:1.RS:3.R:5
                #FIXME need to create Job/RecipeSet/Recipe object from string here
                sub_subject = ".".join(TaskBase.get_by_t_id(task_id).build_ancestors() + (task_id,))
                msg_kw = {}
                msg_kw['subject'] = 'TaskUpdate.%s' % sub_subject #FIXME append task_id, get if from the args/kw
                content = kw #FIXME perhaps we don't need all the elements of the dict?
                msg_kw['content'] = content
                msg = Message(**msg_kw) 
                snd = session.sender(ServerBeakerBus.topic_exchange) 
                snd.send(msg)
                log.info('Sent msg %s' % msg_kw['subject'])
            except BeakerException, e:
                raise BeakerException("%s, %s" % (str(e), self.send_error_suffix))
            except Exception, e:
                raise Exception(("%s, %s" % (str(e), self.send_error_suffix)))


    def _service_queue_worker(self):
            tp = BkrThreadPool.get('service-queue')
            while True:
                try:
                    msg = tp.in_queue.get()
                    method = msg.properties['method']
                    method_args = msg.properties['args']
                    reply_to = msg.reply_to
                    msg_kw = {}
                    try:
                        val_to_return = self.rpcroot.process_rpc(method,method_args)
                        msg_kw['content'] = val_to_return
                    except Exception, e:
                        log.error(str(e))
                        msg_kw.setdefault('properties',{'error' : 1 })
                        msg_kw['content'] = str(e)
                    tp.out_queue.put((msg_kw, reply_to))
                    log.debug('Put response onto service_queue_out')
                except Exception, e:
                    log.exception(str(e))
                    continue

    def _service_request_listener(self, ssn, *args, **kw):
            log.debug('Creating service-queue receiver')
            queue_name= self.config.get('global', 'service_queue')
            try:
                receiver = ssn.receiver(queue_name + '; { create: always, ' +
                    '      node: { type: queue, durable: True, ' +
                    ' x-declare: { auto-delete: False }, ' +
                    'x-bindings: [ {  queue: "' + queue_name + '", } ] } }')

            except NotFound, e:
                log.error(e)

            #Start main workers
            tpool = BkrThreadPool.create_and_run('service-queue', target_f=self._service_queue_worker, target_args=[])

            #Start single response worker
            send_response_t = Thread(target=self._send_service_response, args=(ssn,))
            send_response_t.setDaemon(False)
            send_response_t.start()

            #Start single receiver
            self._fetch_service_request(receiver, ssn, *args, **kw)

    def _send_service_response(self, ssn):
            tp = BkrThreadPool.get('service-queue')
            while True:
                try:
                    log.debug('Waiting to get from service_queue_out')
                    msg_kw, address = tp.out_queue.get()
                    log.debug('Got from service_queue_out')
                    msg = Message(**msg_kw)
                    snd = ssn.sender(address)
                    log.debug('Sent msg %s' %  msg_kw['content'])
                    snd.send(msg)
                except Exception, e:
                    log.exception(str(e))
                    continue

    def _fetch_service_request(self, receiver, ssn, *args, **kw):
            #Make sure this thread pool has been created first
            tp = BkrThreadPool.get('service-queue')
            while True:
                try:
                    log.debug('Waiting to receive in _service_request')
                    msg = receiver.fetch()
                    tp.in_queue.put(msg)
                    ssn.acknowledge()
                except Exception, e:
                    log.exception(str(e))
                    continue


    def _expired_watchdogs_listener(self, ssn):
        rt = RecipeTasks()
        log.debug('Called _expired_watchdogs')
        while True:
            try:
                for lc_id, lc_fqdn in bkr_model.LabController.get_all():
                    watchdog = rt.watchdogs(lc=lc_fqdn, status='expired')
                    if watchdog:
                        log.info('Sending watchdog %s for lc %s' % (watchdog, lc_fqdn))
                        self.watchdog_notify_sender(ssn, 'expired', watchdog, lc_fqdn)
                sleep(60)
            except Exception, e:
                log.exception(str(e))
                continue

    def run(self, *args, **kw):
        listen_to = tg_config.get('beaker.qpid_listen_to', [])
        thread_handlers = self.thread_handlers
        log.debug('Going to Listen to %s' % listen_to)
        for service_msgtype in listen_to:
            try:
                service,type = service_msgtype.split(".")
            except ValueError:
                log.exception(_(u'%s is invalid. Bus services needs to have the format \
                    <system>.<service>' % service_msgtype))
                continue

            try:
                action_pointer = thread_handlers[service][type]
            except KeyError, e:
                log.exception(_(u'No action handler specified for %s'
                % service_msgtype))
                continue

            new_session = self.conn.session()
            log.info('Running %s as thread' % action_pointer)
            action_t = Thread(target=action_pointer, args=(new_session,))
            action_t.setDaemon(False)
            action_t.start()
