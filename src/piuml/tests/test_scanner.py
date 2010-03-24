"""
piUML language parsing tests.
"""

import re
import unittest

from piuml.parser import RE_ID, RE_NAME, RE_ELEMENT, RE_COMMENT, \
    RE_STEREOTYPE, RE_ATTRIBUTE, RE_OPERATION, RE_STATTRIBUTES, \
    RE_ASSOCIATION_END, name_dequote

class RETestCase(unittest.TestCase):
    def test_id(self):
        """Test parsing id
        """
        r = re.compile(RE_ID)
        self.assertEquals('id1', r.search('id1').group(0))
        self.assertFalse(r.search('1id'))
        self.assertEquals('component1', r.search('component1').group(0))
        self.assertFalse(r.search('1component'))
        self.assertFalse(r.search('1component1'))
        self.assertFalse(r.search('component'))
        self.assertFalse(r.search('class'))


    def test_element(self):
        """Test element parsing
        """
        r = re.compile(RE_ELEMENT)
        self.assertTrue(r.search('class'))
        self.assertTrue(r.search('component'))
        self.assertFalse(r.search('none'))


    def test_name(self):
        """Test name parsing
        """
        r = re.compile(RE_NAME)
        self.assertEquals('"b\\"cd"', r.search('a"b\\"cd"ef').group(0))
        self.assertEquals('"b\\"cd"', r.search('a "b\\"cd" ef').group(0))
        self.assertEquals("'b\\'cd'", r.search('a\'b\\\'cd\'ef').group(0))


    def test_name_quotation(self):
        """Test name quotation
        """
        self.assertEquals('aaa', name_dequote('"aaa"'))
        self.assertEquals('aaa', name_dequote("'aaa'"))
        self.assertEquals(r'aa\a', name_dequote(r"'aa\\a'"))
        self.assertEquals('aa"a', name_dequote(r'"aa\"a"'))
        self.assertEquals(r'aa\'a', name_dequote(r"'aa\\\'a'"))
        self.assertEquals('aa"a', name_dequote(r"'aa\"a'"))
        self.assertEquals('aa#a', name_dequote(r"'aa\#a'"))


    def test_comment(self):
        """Test comment token parsing
        """
        r = re.compile(RE_COMMENT)
        self.assertTrue(r.search('# this is comment'))
        self.assertTrue(r.search('#this is comment'))
        self.assertTrue(r.search('this is not comment  # this is comment'))
        self.assertFalse(r.search(r'\# this is not comment'))


    def test_stereotype(self):
        """Test stereotype token parsing
        """
        r = re.compile(RE_STEREOTYPE)
        self.assertTrue(r.search('<<test>>'))
        self.assertTrue(r.search('<< test >>'))
        self.assertTrue(r.search('<<t1, t2>>'))
        self.assertTrue(r.search('<<t1,t2>>'))
        self.assertTrue(r.search('<<  t1,t2  >>'))
        self.assertTrue(r.search('<< t1 , t2 >>'))
        self.assertFalse(r.search(': <<test>>'))


    def test_attribute(self):
        """Test attribute token parsing
        """
        r = re.compile(RE_ATTRIBUTE)
        self.assertTrue(r.search(' : attr'))
        self.assertTrue(r.search(' :attr'))
        self.assertTrue(r.search(' : attr: int'))
        self.assertTrue(r.search(' : attr: int = 1'))
        self.assertTrue(r.search(' : attr = "test"'))
        self.assertTrue(r.search(' : attr: str = "test"'))
        self.assertTrue(r.search(' : attr: str = "test()"'))
        self.assertTrue(r.search(' : attr[11]'))
        self.assertTrue(r.search(' : attr [0..1]'))
        self.assertTrue(r.search(' : attr [n..m]'))
        self.assertTrue(r.search(' : [0..1]'))
        self.assertFalse(r.search(' : oper()'))
        self.assertFalse(r.search(' : oper(a: int, b: str)'))
        self.assertFalse(r.search(' : oper(a: int, b: str): double'))


    def test_operation(self):
        """Test operation token parsing
        """
        r = re.compile(RE_OPERATION)
        self.assertTrue(r.search(' : oper()'))
        self.assertTrue(r.search(' : oper(a: int)'))
        self.assertTrue(r.search(' : oper(a: int, b: str): double'))


    def test_association_end(self):
        """Test association end parsing
        """
        r = re.compile(RE_ASSOCIATION_END)
        mre = r.search('attr')
        self.assertEquals('attr', mre.group('name'))

        mre = r.search('attr [0..1]')
        self.assertEquals('attr', mre.group('name'))
        self.assertEquals('0..1', mre.group('mult'))

        mre = r.search('[0..1]')
        self.assertFalse(mre.group('name'))
        self.assertEquals('0..1', mre.group('mult'))

        mre = r.search('attr [n..m]')
        self.assertEquals('attr', mre.group('name'))
        self.assertEquals('n..m', mre.group('mult'))


    def test_st_attributes(self):
        """Test stereotype attributes token parsing
        """
        r = re.compile(RE_STATTRIBUTES)
        self.assertTrue(r.search(' : <<test>>'))
        self.assertFalse(r.search(' : <<t1, t2>>'))


