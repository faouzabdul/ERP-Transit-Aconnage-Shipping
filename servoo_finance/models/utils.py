# -*- coding: cp1252 -*-

"""
Traduction d'un nombre en texte.
Réalisation : Michel Claveau    http://mclaveau.com

SVP, n'enlevez pas mon adresse/URL ; merci d'avance

Usage : voir les exemples, à la fin du script.

Note : traduction franco-française, avec unités variables, orthographe géré, unités et centièmes.
"""

from odoo import _


def tradd(num):
    global t1, t2
    ch = ''
    if num == 0:
        ch = ''
    elif num < 20:
        ch = t1[num]
    elif num >= 20:
        if (70 <= num <= 79) or (num >= 90):
            z = int(num / 10) - 1
        else:
            z = int(num / 10)
        ch = t2[z]
        num = num - z * 10
        if (num == 1 or num == 11) and z < 8:
            ch = ch + _(' and')
        if num > 0:
            ch = ch + ' ' + tradd(num)
        else:
            ch = ch + tradd(num)
    return ch


def tradn(num):
    global t1, t2
    ch = ''
    flagcent = False
    if num >= 1000000000:
        z = int(num / 1000000000)
        ch = ch + tradn(z) + _(' billion')
        if z > 1:
            ch = ch + 's'
        num = num - z * 1000000000
    if num >= 1000000:
        z = int(num / 1000000)
        ch = ch + tradn(z) + _(' million')
        if z > 1:
            ch = ch + 's'
        num = num - z * 1000000
    if num >= 1000:
        if num >= 100000:
            z = int(num / 100000)
            if z > 1:
                ch = ch + ' ' + tradd(z)
            ch = ch + _(' hundred')
            flagcent = True
            num = num - z * 100000
            if int(num / 1000) == 0 and z > 1:
                ch = ch + 's'
        if num >= 1000:
            z = int(num / 1000)
            if (z == 1 and flagcent) or z > 1:
                ch = ch + ' ' + tradd(z)
            num = num - z * 1000
        ch = ch + _(' thousand')
    if num >= 100:
        z = int(num / 100)
        if z > 1:
            ch = ch + ' ' + tradd(z)
        ch = ch + _(" hundred")
        num = num - z * 100
        if num == 0 and z > 1:
            ch = ch + 's'
    if num > 0:
        ch = ch + " " + tradd(num)
    return ch


def translate(nb, unite="", decim=""):
    global t1, t2
    nb = round(nb, 2)
    t1 = ["", _("one"), _("two"), _("three"), _("four"), _("five"), _("six"), _("seven"), _("eight"), _("nine"),
          _("ten"), _("eleven"), _("twelve"), _("thirteen"),
          _("fourteen"), _("fifteen"), _("sixteen"), _("seventeen"), _("eighteen"), _("nineteen")]
    t2 = ["", _("ten"), _("twenty"), _("thirty"), _("forty"), _("fifty"), _("sixty"), _("seventy"), _("eighty"),
          _("ninety")]
    z1 = int(nb)
    z3 = (nb - z1) * 100
    z2 = int(round(z3, 0))
    if z1 == 0:
        ch = _("zero")
    else:
        ch = tradn(abs(z1))
    if z1 > 1 or z1 < -1:
        if unite != '':
            ch = ch + " " + unite + 's' if unite else ''
    else:
        ch = ch + " " + unite
    if z2 > 0:
        ch = ch + tradn(z2)
        if z2 > 1 or z2 < -1:
            if decim != '':
                ch = ch + " " + decim + 's' if decim else ''
        else:
            ch = ch + " " + decim
    if nb < 0:
        ch = "moins " + ch
    return ch
