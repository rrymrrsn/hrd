# -*- coding: utf-8 -*-
import urllib

from flask import Flask, request, abort
from flask.ext.sqlalchemy import SQLAlchemy



# FIXME need config file
secret_key = "ddSecretKeyForSessionSigning"

app = Flask(__name__)
app.debug = True
app.secret_key = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db = SQLAlchemy(app)


DEBUG = False

default_url_for = app.jinja_env.globals['url_for']

language_list = [
    ('en', u'English', 'ltr'),
    ('fr', u'français', 'ltr'),
    ('es', u'español', 'ltr'),
    ('ar', u'العربية', 'rtl'),
    # ('zh', u'中文', 'ltr'),
    ('ru', u'русский', 'ltr'),
]

lang_dir = {}
for code, name, dir_ in language_list:
    lang_dir[code] = dir_


lang_name = {}
for code, name, dir_ in language_list:
    lang_name[code] = name


lang_codes = []
for code, name, dir_ in language_list:
    lang_codes.append(code)


permission_list = [
    ('sys_admin', 'System administrator'),
    ('content_manage', 'Content managment'),
    ('translator', 'Content translation'),
    ('user_admin', 'User administrator'),
    ('user_manage', 'User management'),
]


def permission(permission):
    if permission not in request.permissions:
        if 'sys_admin' not in request.permissions:
            abort(403)


def permission_content(lang):
    if lang == 'en':
        permission('content_manage')
    else:
        permission('translation')


def lang_list():
    return language_list


def current_lang():
    return request.environ['LANG']


def current_lang_name():
    return lang_name[request.environ['LANG']]


def current_admin_lang():
    return lang_name[get_admin_lang()]


def lang_html():
    lang = request.environ['LANG']
    return 'lang="%s" dir="%s"' % (lang, lang_dir[lang])


def lang_pick(lang):
    current_url = request.environ['CURRENT_URL']
    current_url = '/%s%s' % (lang, current_url)
    return current_url


def url_for(*args, **kw):
    url = default_url_for(*args, **kw)
    lang = request.environ['LANG']
    url = '/%s%s' % (lang, url)
    return url


def url_for_fixed(url):
    lang = request.environ['LANG']
    url = '/%s%s' % (lang, url)
    return url


def url_for_admin(*args, **kw):
    if 'lang' not in kw:
        lang = request.args.get('lang')
        if lang:
            kw['lang'] = lang
    return url_for(*args, **kw)


def get_admin_lang():
    lang = request.args.get('lang')
    return lang or 'en'


def get_bool(field):
    return bool(request.form.get(field, False))


def get_str(field):
    return request.form.get(field, '')


def get_int(field, default):
    value = request.form.get(field, default)
    try:
        value = int(value)
    except ValueError:
        value = default
    return value

import helpers
import models
import views


@app.template_filter('sn')
def reverse_filter(s):
    if s is None:
        return ''
    return s


class I18nMiddleware(object):
    """I18n Middleware selects the language based on the url
    eg /fr/home is French"""

    def __init__(self, app):
        self.app = app
        self.default_locale = 'en'
        locale_list = []
        for code, lang, _dir in language_list:
            locale_list.append(code)
        self.locale_list = locale_list

    def __call__(self, environ, start_response):
        # strip the language selector from the requested url
        # and set environ variables for the language selected
        # LANG is the language code eg en, fr
        # CURRENT_URL is set to the current application url
        if 'LANG' not in environ:
            path_parts = environ['PATH_INFO'].split('/')
            if len(path_parts) > 1 and path_parts[1] in self.locale_list:
                environ['LANG'] = path_parts[1]
                # rewrite url
                if len(path_parts) > 2:
                    environ['PATH_INFO'] = '/'.join([''] + path_parts[2:])
                else:
                    environ['PATH_INFO'] = '/'
            else:
                environ['LANG'] = self.default_locale
            # Current application url
            path_info = environ['PATH_INFO']
            # sort out weird encodings
            path_info = '/'.join(urllib.quote(pce, '')
                                 for pce in path_info.split('/'))
            qs = environ.get('QUERY_STRING')
            if qs:
                # sort out weird encodings
                # qs = urllib.quote(qs, '')
                environ['CURRENT_URL'] = '%s?%s' % (path_info, qs)
            else:
                environ['CURRENT_URL'] = path_info
        return self.app(environ, start_response)


app = I18nMiddleware(app)
