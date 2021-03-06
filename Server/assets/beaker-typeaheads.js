
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.

;(function ($) {

// Top-level JSON arrays are a security risk and Flask does not allow us to 
// return them:
// http://flask.pocoo.org/docs/security/#json-security
// so we need to give typeahead a filter function to extract the array.
var results_filter = function (response) {
    return response.data;
};

// window.beaker_url_prefix is set by master.kid
$.fn.beaker_typeahead = function (type) {
    var options = ({
        'group-name': {
            name: 'beaker-group-name',
            prefetch: {
                url: beaker_url_prefix + 'groups/+typeahead',
                filter: results_filter,
            },
            remote: {
                url: beaker_url_prefix + 'groups/+typeahead?q=%QUERY',
                filter: results_filter,
            },
            valueKey: 'group_name',
            limit: 8,
            template: JST['beaker-typeaheads/group-name'],
        },
        'user-name': {
            name: 'beaker-user-name',
            prefetch: {
                url: beaker_url_prefix + 'users/+typeahead',
                filter: results_filter,
            },
            remote: {
                url: beaker_url_prefix + 'users/+typeahead?q=%QUERY',
                filter: results_filter,
            },
            valueKey: 'user_name',
            limit: 10,
            template: JST['beaker-typeaheads/user-name'],
        },
    })[type];
    this.typeahead(options);

    return this;
};

})(jQuery);
