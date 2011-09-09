# -*- coding: utf-8 -*-
#
#   sponsor_metrics.py — rudimentary model for sponsor metrics
#
#   This file is part of debexpo - http://debexpo.workaround.org
#
#   Copyright © 2011 Arno Töll <debian@toell.net>
#
#   Permission is hereby granted, free of charge, to any person
#   obtaining a copy of this software and associated documentation
#   files (the "Software"), to deal in the Software without
#   restriction, including without limitation the rights to use,
#   copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following
#   conditions:
#
#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#   HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#   WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#   OTHER DEALINGS IN THE SOFTWARE.

"""
Holds Sponsor Metrics Model
"""

__author__ = 'Arno Töll'
__copyright__ = 'Copyright © 2011 Arno Töll'
__license__ = 'MIT'

import os
import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from debexpo.model import meta, OrmObject
from debexpo.model.users import User
from debexpo.lib import constants
import debexpo.lib.utils

t_sponsor_metrics = sa.Table(
    'sponsor_metrics', meta.metadata,
    sa.Column('user_id', sa.types.Integer, sa.ForeignKey('users.id'), primary_key=True),
    sa.Column('availability', sa.types.Integer, nullable=False),
    sa.Column('contact', sa.types.Integer, nullable=False),
    sa.Column('types', sa.types.Text, nullable=True),
    sa.Column('guidelines', sa.types.Integer, nullable=True),
    sa.Column('guidelines_text', sa.types.Text, nullable=True),
    sa.Column('social_requirements', sa.types.Text, nullable=True),
    )

t_sponsor_tags = sa.Table(
    'sponsor_tags', meta.metadata,
    sa.Column('tag_type', sa.types.Integer, nullable=False),
    sa.Column('tag', sa.types.Text, primary_key=True),
    sa.Column('label', sa.types.Text, nullable=False),
    sa.Column('long_description', sa.types.Text, nullable=False),
)

t_sponsor_metrics_tags = sa.Table(
    'sponsor_metrics_tags', meta.metadata,
    sa.Column('tag', sa.Integer, sa.ForeignKey('sponsor_tags.tag'), primary_key=True),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('sponsor_metrics.user_id'), primary_key=True),
)

class SponsorMetrics(OrmObject):
    foreign = ['user']
    #tags = orm.relationship('SponsorTags', secondary=t_sponsor_metrics_tags, backref=orm.backref('sponsors', lazy='dynamic'))

    def get_all_tags(self):
        return [x.tag for x in self.tags]

    def get_technical_tags(self):
        return [x.tag for x in self.get_technical_tags_full()]

    def get_social_tags(self):
        return [x.tag for x in self.get_social_tags_full()]

    def get_technical_tags_full(self):
        return [x for x in self.tags if x.tag_type == constants.SPONSOR_METRICS_TYPE_TECHNICAL]

    def get_social_tags_full(self):
        return [x for x in self.tags if x.tag_type == constants.SPONSOR_METRICS_TYPE_SOCIAL]

    def get_guidelines(self):
        """
        Return a formatted and sanitized string of the guidelines the sponsor
        configured
        """

        if self.guidelines == constants.SPONSOR_GUIDELINES_TYPE_TEXT:
            s = self.guidelines_text
            s = s.replace('<', '&lt;')
            s = s.replace('>', '&gt;')
            s = s.replace('\n', '<br />')
            return s
        elif self.guidelines == constants.SPONSOR_GUIDELINES_TYPE_URL:
            return "<a href=\"%s\">%s</a>" % (self.guidelines_text, self.guidelines_text)
        else:
            return ""


    def get_types(self):
        """
        Return a formatted and sanitized string of the packages the sponsor
        is interested in
        """

        if self.types:
            s = self.types
            s = s.replace('<', '&lt;')
            s = s.replace('>', '&gt;')
            s = s.replace('\n', '<br />')
            return s
        return ""

    def get_social_requirements(self):
        """
        Return a formatted and sanitized string of the social requirements the sponsor
        configured
        """

        if self.social_requirements:
            s = self.social_requirements
            s = s.replace('<', '&lt;')
            s = s.replace('>', '&gt;')
            s = s.replace('\n', '<br />')
            return s
        else:
            return ""

    def allowed(self, flag):
        """
        Returns true if the user associated with this object allowed to display a
        contact address. This method also honors the SPONSOR_METRICS_RESTRICTED flag

        ```flag``` A SPONSOR_CONTACT_METHOD_* flag which should be checked
        """
        if self.availability == constants.SPONSOR_METRICS_RESTRICTED and self.contact == flag:
            return True
        elif self.availability == constants.SPONSOR_METRICS_PUBLIC:
            return True
        return False


class SponsorTags(OrmObject):
    pass

class SponsorMetricsTags(OrmObject):
    # We need to filter on that object, so we must instantiate the M2M class
    pass

orm.mapper(SponsorMetrics, t_sponsor_metrics, properties={
    'user' : orm.relation(User, backref='sponsor_metrics'),
    'tags' : orm.relationship(SponsorTags, secondary=t_sponsor_metrics_tags, backref=orm.backref('sponsors', lazy='joined'))
})


orm.mapper(SponsorMetricsTags, t_sponsor_metrics_tags)
orm.mapper(SponsorTags, t_sponsor_tags)

def create_tags():
    import debexpo.model.data.tags
    import logging
    for metrics_type in [constants.SPONSOR_METRICS_TYPE_TECHNICAL, constants.SPONSOR_METRICS_TYPE_SOCIAL]:
        for (description, tag, long_description) in debexpo.model.data.tags.TAGS[metrics_type]:
            st = SponsorTags(tag_type=metrics_type, tag=tag, label=description, long_description=long_description)
            logging.info("Adding tag %s" % (tag))
            meta.session.merge(st)
    meta.session.commit()