
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import os
import tempfile
import shutil
import webassets
from webassets.bundle import get_all_bundle_files
from webassets.filter.jst import JST
import threading
from turbogears import config

# Custom filter to use external ycssmin
# (There is a python cssmin implementation, we could use that instead)
from webassets.filter import ExternalTool
class YCSSMin(ExternalTool):
    name = 'ycssmin'
    def input(self, in_, out, source_path, **kwargs):
        self.subprocess(['cssmin'], out, in_)


# Environment is lazily initialised because it requires config to be loaded
_env = None
_env_lock = threading.Lock()

def _create_env(source_dir, output_dir, **kwargs):
    # some pieces of webassets assume the directories are absolute
    source_dir = os.path.abspath(source_dir)
    output_dir = os.path.abspath(output_dir)
    env = webassets.Environment(directory=output_dir, url='/assets/generated',
            manifest='cache', **kwargs)
    env.append_path(source_dir, url='/assets')
    env.config['UGLIFYJS_EXTRA_ARGS'] = ['--mangle', '--compress']
    env.register('css',
            'style.less',
            filters=['less', 'cssrewrite', YCSSMin()],
            output='beaker-%(version)s.css',
            depends=['*.less', 'bootstrap/less/*.less', 'font-awesome/less/*.less',
                'bootstrap-datepicker/less/*.less',
                'bootstrap-select/bootstrap-select.css'])
    env.register('js',
            # third-party
            'bootstrap/js/bootstrap-transition.js',
            'bootstrap/js/bootstrap-modal.js',
            'bootstrap/js/bootstrap-dropdown.js',
            'bootstrap/js/bootstrap-tab.js',
            'bootstrap/js/bootstrap-alert.js',
            'bootstrap/js/bootstrap-button.js',
            'bootstrap/js/bootstrap-collapse.js',
            'typeahead.js/dist/typeahead.js',
            'bootstrap-datepicker/js/bootstrap-datepicker.js',
            'bootstrap-select/bootstrap-select.js',
            'bootstrap-growl/jquery.bootstrap-growl.js',
            'bootbox/bootbox.js',
            'moment/moment.js',
            'URI.js/src/URI.js',
            'underscore/underscore.js',
            'backbone/backbone.js',
            'backbone-pageable/lib/backbone-pageable.js',
            'backgrid/lib/backgrid.js',
            # ours
            webassets.Bundle(
                'jst/*/*.html',
                'jst/*.html',
                filters=[JST(template_function='_.template')],
                output='beaker-jst-%(version)s.js'),
            'local-datetime.js',
            'link-tabs-to-anchor.js',
            'beaker-backgrid.js',
            'beaker-typeaheads.js',
            'beaker-bootbox.js',
            'bootstrap-select-defaults.js',
            'distro-model.js',
            'distro-picker.js',
            'query-builder.js',
            'recipe-tasks.js',
            'reserve-workflow.js',
            'system-access-policy.js',
            'system-activity.js',
            'system-add.js',
            'system-commands.js',
            'system-hardware.js',
            'system-loan.js',
            'system-model.js',
            'system-owner.js',
            'system-power-settings.js',
            'system-provision.js',
            'system-quick-info.js',
            'system-rename.js',
            'system-report-problem.js',
            'system-scheduler-settings.js',
            filters=['uglifyjs'],
            output='beaker-%(version)s.js')
    return env

def _create_runtime_env():
    source_dir = config.get('basepath.assets')
    output_dir = config.get('basepath.assets_cache')
    debug = config.get('assets.debug')
    auto_build = config.get('assets.auto_build')
    return _create_env(source_dir=source_dir, output_dir=output_dir,
            debug=debug, auto_build=auto_build)

def get_assets_env():
    global _env
    if _env is None:
        with _env_lock:
            if _env is None:
                _env = _create_runtime_env()
    return _env

def build_assets():
    env = get_assets_env()
    for bundle in env:
        bundle.build()

def list_asset_sources(source_dir):
    """
    Returns a list of paths (relative to the given source_dir) of all asset 
    sources files defined in the assets environment.
    """
    # This is called during package build, so we create a new env specially to 
    # refer to the given source dir.
    # We aren't going to produce any generated files so output_dir is unused 
    # and cache can be discarded.
    source_dir = os.path.abspath(source_dir)
    cache_dir = tempfile.mkdtemp(prefix='beaker-build-assets-cache')
    try:
        env = _create_env(source_dir=source_dir, output_dir='/unused',
                cache=cache_dir, debug=False, auto_build=False)
        paths = []
        for bundle in env:
            for path in get_all_bundle_files(bundle, env):
                paths.append(os.path.relpath(path, source_dir))
        # site.less should be skipped because it's a symlink
        paths.remove('site.less')
        # font-awesome is currently not managed by webassets because webassets 
        # breaks on non-UTF8 input files
        paths.extend([
            'font-awesome/fonts/fontawesome-webfont.eot',
            'font-awesome/fonts/fontawesome-webfont.svg',
            'font-awesome/fonts/fontawesome-webfont.ttf',
            'font-awesome/fonts/fontawesome-webfont.woff',
        ])
        return paths
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)
