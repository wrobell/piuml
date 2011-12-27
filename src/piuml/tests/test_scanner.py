#
# piUML - UML diagram generator.
#
# Copyright (C) 2010 by Artur Wroblewski <wrobell@pld-linux.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
piUML language parsing tests.
"""

import re
import unittest

from piuml.parser import parse, name_dequote, ParseError

class TokenTestCase(unittest.TestCase):
    def test_id(self):
        """
        Test parsing id
        """
        n = parse('class id1 "test"')
        self.assertEquals('id1', n[0].id)

        self.assertRaises(ParseError ,parse, 'class 1id "test"')

        n = parse('class class1 "test"')
        self.assertEquals('class1', n[0].id)

        self.assertRaises(ParseError ,parse, 'class 1class "test"')

        n = parse('class class "test"')
        self.assertEquals('class', n[0].id)


    def test_string(self):
        """
        Test string parsing
        """
        n = parse('class id1 "bc d"')
        self.assertEquals("bc d", n[0].name)

        n = parse('class id1 \'bc d\'')
        self.assertEquals("bc d", n[0].name)

        # " char inside string quoted with "
        n = parse('class id1 "b\\"cd"')
        self.assertEquals("'b\\'cd'", n[0].name)

        # ' char inside string quoted with '
        n = parse('class id1 \'b\\\'cd\'')
        self.assertEquals('"b\\"cd"', n[0].name)

        # \" string inside string quoted with '
        n = parse('class id1 \'a"b\\\\"cd"ef\'')
        self.assertEquals('a"b\\"cd"ef', n[0].name)


    def test_name_quotation(self):
        """
        Test name quotation
        """
        self.assertEquals('aaa', name_dequote('"aaa"'))
        self.assertEquals('aaa', name_dequote("'aaa'"))
        self.assertEquals(r'aa\a', name_dequote(r"'aa\\a'"))
        self.assertEquals('aa"a', name_dequote(r'"aa\"a"'))
        self.assertEquals(r'aa\'a', name_dequote(r"'aa\\\'a'"))
        self.assertEquals('aa"a', name_dequote(r"'aa\"a'"))
        self.assertEquals('aa#a', name_dequote(r"'aa\#a'"))


    def test_comment(self):
        """
        Test comment token parsing
        """
        parse('# this is comment')
        parse('#this is comment')
        self.assertRaises(ParseError, parse, 'this is not comment  # this is comment')
        self.assertRaises(ParseError, parse, r'\# this is not comment')


    def test_stereotype(self):
        """
        Test stereotype token parsing
        """
        n = parse('class id <<test>> "aa"')
        self.assertEquals(['test'], n[0].stereotypes)

        n = parse('class id << test >> "aa"')
        self.assertEquals(['test'], n[0].stereotypes)

        n = parse('class id <<t1, t2>> "aa"')
        self.assertEquals(['t1', 't2'], n[0].stereotypes)

        n = parse('class id <<t1,t2>> "aa"')
        self.assertEquals(['t1', 't2'], n[0].stereotypes)

        n = parse('class id <<  t1,t2  >> "aa"')
        self.assertEquals(['t1', 't2'], n[0].stereotypes)

        n = parse('class id << t1 , t2 >> "aa"')
        self.assertEquals(['t1', 't2'], n[0].stereotypes)


    def test_attribute(self):
        """
        Test attribute token parsing
        """
        n = parse('class a "a"\n    : attr')
        self.assertEquals('attr', n[0].data['attributes'][0].name)

        n = parse('class a "a"\n    :attr')
        self.assertEquals('attr', n[0].data['attributes'][0].name)

        n = parse('class a "a"\n    : attr: int')
        self.assertEquals('attr', n[0].data['attributes'][0].name)
        self.assertEquals('int', n[0].data['attributes'][0].type)

        n = parse('class a "a"\n    : attr: int = 1')
        self.assertEquals('attr', n[0].data['attributes'][0].name)
        self.assertEquals('int', n[0].data['attributes'][0].type)
        self.assertEquals('1', n[0].data['attributes'][0].value)

        n = parse('class a "a"\n    : attr = "test"')
        self.assertEquals('attr', n[0].data['attributes'][0].name)

        n = parse('class a "a"\n    : attr: str = "test"')
        self.assertEquals('attr', n[0].data['attributes'][0].name)

        n = parse('class a "a"\n    : attr: str = "test()"')
        self.assertEquals('attr', n[0].data['attributes'][0].name)

        n = parse('class a "a"\n    : attr[11]')
        self.assertEquals('attr', n[0].data['attributes'][0].name)

        n = parse('class a "a"\n    : attr [0..1]')
        self.assertEquals('attr', n[0].data['attributes'][0].name)

        n = parse('class a "a"\n    : attr [n..m]')
        self.assertEquals('attr', n[0].data['attributes'][0].name)


    def test_operation(self):
        """
        Test operation token parsing
        """
        n = parse('class a1 "a1"\n    : oper()')
        self.assertEquals('oper()', n[0].data['operations'][0].name)

        n = parse('class a1 "a1"\n    : oper(a: int)')
        self.assertEquals('oper(a: int)', n[0].data['operations'][0].name)

        n = parse('class a1 "a1"\n    : oper(a: int, b: str): double')
        self.assertEquals('oper(a: int, b: str): double',
                n[0].data['operations'][0].name)


    def test_association_end(self):
        """
        Test association end parsing
        """
        f = """
class c1 "C1"
class c2 "C2"

c1 == "An association" c2
    : """
        n = parse(f + 'attr')
        data = n[2].data
        self.assertEquals('attr', data['tail'][1].name)
        self.assertEquals('[0..*]', str(data['tail'][1].mult))

        n = parse(f + 'attr [0..1]')
        data = n[2].data
        self.assertEquals('attr', data['tail'][1].name)
        self.assertEquals('[0..1]', str(data['tail'][1].mult))

        n = parse(f + '[0..1]')
        data = n[2].data
        self.assertEquals('[0..1]', str(data['tail'][1].mult))
        self.assertEquals('', data['tail'][1].name)

        n = parse(f + 'attr[n..m]')
        data = n[2].data
        self.assertEquals('attr', data['tail'][1].name)
        self.assertEquals('[n..m]', str(data['tail'][1].mult))


    def test_st_attributes(self):
        """
        Test stereotype attributes token parsing
        """
        n = parse('class c1 "c1"\n    : <<test>> :\n        : attr = 1')
        n = parse('class c1 "c1"\n    : <<test>> :\n        : attr = "1"')
        n = parse('class c1 "c1"\n    : <<test>> :\n        : attr = abc')

        self.assertRaises(ParseError, parse,
                'class c1 "c1"\n    : <<t1, t2>>   :')


# vim: sw=4:et:ai
