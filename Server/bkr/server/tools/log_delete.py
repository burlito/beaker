import errno, shutil, datetime
from bkr import __version__ as bkr_version
from optparse import OptionParser
from bkr.server.model import Job
from bkr.server.util import load_config
from turbogears.database import session
from bkr.common.dav import BeakerRequest, DavDeleteErrorHandler, RedirectHandler
import urllib2 as u2
from urllib2_kerberos import HTTPKerberosAuthHandler
import logging

logger = logging.getLogger(__name__)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
logger.addHandler(stream_handler)
logger.setLevel(logging.ERROR)

__description__ = 'Script to delete expired log files'

def main():

    parser = OptionParser('usage: %prog [options]',
            description='Permanently deletes log files from Beaker and/or \
                archive server',
            version=bkr_version)
    parser.add_option('-c', '--config', metavar='FILENAME',
            help='Read configuration from FILENAME')
    parser.add_option('-v', '--verbose', action='store_true',
            help='Return deleted files')
    parser.add_option('--dry-run', action='store_true',
            help='Execute deletions, but issue ROLLBACK instead of COMMIT, \
                and do not actually delete files')
    parser.set_defaults(verbose=False, dry_run=False)
    options, args = parser.parse_args()
    load_config(options.config)
    log_delete(options.verbose, options.dry_run)

def log_delete(verb=False, dry=False):
    # The only way to override default HTTPRedirectHandler
    # is to pass it into build_opener(). Appending does not work
    opener = u2.build_opener(RedirectHandler())
    opener.add_handler(HTTPKerberosAuthHandler())
    opener.add_handler(DavDeleteErrorHandler())
    if dry:
        print 'Dry run only'
    if verb:
        print 'Getting expired jobs'

    for job, logs in Job.expired_logs():
        try:
            job.deleted = datetime.datetime.utcnow()
            for log in logs:
                session.begin()
                if not dry:
                    if 'http' in log:
                        url = log
                        req = BeakerRequest('DELETE', url=url)
                        opener.open(req)
                    else:
                        try:
                            shutil.rmtree(log)
                        except OSError, e:
                            if e.errno == errno.ENOENT:
                                pass
                    session.commit()
                    session.close()

                else:
                    session.close()

                if verb:
                    print log

        except Exception, e:
            session.close()
            logger.error(str(e))
            continue

if __name__ == '__main__':
    main()
