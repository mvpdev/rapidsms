#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import fractions

from django.utils.translation import ugettext as _

class Percentage(fractions.Fraction):
    """
    This is exactly like :class:`fractions.Fraction` except
    that :class:`Percentage` never simplifies the numerator
    or denominator.
    """

    num = 0
    den = 1

    @property
    def empty(self):
        return (self.den == 0)

    def __new__(cls, n, d):
        obj = super(Percentage,cls).__new__(cls, n, 1 if (d == 0) else d)
        obj.num = n
        obj.den = d

        return obj


    def __repr__(self):
        return u"Percentage(%d, %d)" % (self.num, self.den)

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        return "%s (%d/%d)" % (self.short_str(), self.num, self.den)

    def __reduce__(self):
        return (self.__class__, (self.num, self.den))

    def short_str(self):
        return u'--' if self.empty else (u"%d%%" % int(100.0*self))

