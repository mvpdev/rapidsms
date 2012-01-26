#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
# maintainer: rgaudin

''' functions to transform recipient ID's (numbers)

takes a message as parameter
returns a string (the ID) '''


# Object-receiving functions
def nothing(obj):
    ''' returns as sent '''
    return snothing(obj.connection.identity)


def intl2dom1(obj):
    ''' removes first 2 chars. targets US-like numbers +1 xxx'''
    return sintl2dom1(obj.connection.identity)


def intl2dom2(obj):
    ''' removes first 3 chars. targets EU-like numbers: +22 xxxx'''
    return sintl2dom2(obj.connection.identity)


def intl2dom3(obj):
    ''' removes first 2 chars. targets Africa-like numbers +223 xxx to xxx'''
    return sintl2dom3(obj.connection.identity)


def intl2dom1zero(obj):
    ''' replace first 2 chars with 0. '''
    return sintl2dom1zero(obj.connection.identity)


def intl2dom2zero(obj):
    ''' replace first 3 chars with 0. France model: +33xxxx to 0xxxx'''
    return sintl2dom2zero(obj.connection.identity)


def intl2dom3zero(obj):
    ''' replace first 4 chars with 0.'''
    return sintl2dom3zero(obj.connection.identity)


# String-receiving functions
def snothing(number):
    ''' returns as sent '''
    return number


def sintl2dom1(number):
    ''' removes first 2 chars. targets US-like numbers +1 xxx'''
    return number[2:]


def sintl2dom2(number):
    ''' removes first 3 chars. targets EU-like numbers: +22 xxxx'''
    return number[3:]


def sintl2dom3(number):
    ''' removes first 2 chars. targets Africa-like numbers +223 xxx to xxx'''
    return number[4:]


def sintl2dom1zero(number):
    ''' replace first 2 chars with 0. '''
    return '0' + number[2:]


def sintl2dom2zero(number):
    ''' replace first 3 chars with 0. France model: +33xxxx to 0xxxx'''
    return '0' + number[3:]


def sintl2dom3zero(number):
    ''' replace first 4 chars with 0.'''
    return '0' + number[4:]
