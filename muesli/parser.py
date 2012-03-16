# muesli/parser.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2011, Matthias Kuemmerer <matthias (at) matthias-k.org>
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
# -*- coding: utf-8 -*-
#
# Inspired by SimpleCalc.py (http://pyparsing.wikispaces.com/file/view/SimpleCalc.py)
# 

from __future__ import division

import re
from pyparsing import Word, alphas, ParseException, Literal, CaselessLiteral \
, Combine, Optional, nums, Or, Forward, ZeroOrMore, StringEnd, alphanums, nestedExpr, delimitedList, CaselessKeyword
import math
from decimal import Decimal

# Debugging flag can be set to either "debug_flag=True" or "debug_flag=False"
debug_flag=True

class Parser(object):
	def __init__(self):
		# define grammar
		point = Literal('.')
		e = CaselessLiteral('E')
		plusorminus = Literal('+') | Literal('-')
		number = Word(nums) 
		integer = Combine( Optional(plusorminus) + number )
		floatnumber = Combine( integer +
							Optional( point + Optional(number) ) +
							Optional( e + integer )
							)

		ident = Word('$',alphanums + '_') 

		plus  = Literal( "+" )
		minus = Literal( "-" )
		mult  = Literal( "*" )
		div   = Literal( "/" )
		lpar  = Literal( "(" ).suppress()
		rpar  = Literal( ")" ).suppress()
		addop  = plus | minus
		multop = mult | div
		expop = Literal( "^" )	

		expr = Forward()
		def defineFunction(name, parameterCount=None):
			keyword = CaselessKeyword(name).setParseAction(self.pushEnd)
			funcPattern = keyword + lpar
			if parameterCount == None:
				funcPattern += Optional(expr+ZeroOrMore(Literal(',')+expr))
			elif parameterCount > 0:
				funcPattern += expr
				for i in range(parameterCount-1):
					funcPattern += Literal(',') + expr
			funcPattern += rpar
			return funcPattern.setParseAction(self.pushFirst)
		maxFunc = defineFunction('max')
		minFunc = defineFunction('min')
		casesFunc = defineFunction('cases')
		cases1Func = defineFunction('cases1', parameterCount = 5)
		cases2Func = defineFunction('cases2', parameterCount = 8)
		cases3Func = defineFunction('cases3', parameterCount = 11)
		
		#func = (funcident.setParseAction(self.pushEnd)+lpar +Optional(expr+ZeroOrMore(Literal(',')+expr))+rpar).setParseAction(self.pushFirst)
		atom = ( maxFunc | minFunc | casesFunc | cases1Func | cases2Func | cases3Func | ( e | floatnumber | integer | ident ).setParseAction(self.pushFirst) | 
				( lpar + expr.suppress() + rpar ) 
			)
				
		factor = Forward()
		factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( self.pushFirst ) )
				
		term = factor + ZeroOrMore( ( multop + factor ).setParseAction( self.pushFirst ) )
		expr << term + ZeroOrMore( ( addop + term ).setParseAction( self.pushFirst ) )

		self.pattern =  expr + StringEnd()
		# map operator symbols to corresponding arithmetic operations
		self.opn = { "+" : self.handleNone( lambda a,b: a + b ),
				"-" : self.handleNone( lambda a,b: a - b ),
				"*" : self.handleNone( lambda a,b: a * b, none_survives=True ),
				"/" : self.handleNone( lambda a,b: a / b, none_survives=True ),
				"^" : self.handleNone( lambda a,b: a ** b, none_survives=True ) }
		self.functions = { 'max': max,
			'min': self.min,
			'cases': self.cases,
			'cases1': self.cases1,
			'cases2': self.cases2,
			'cases3': self.cases3
			}
	def min(self, arr):
		arr = filter(lambda a: a != None, arr)
		return min(arr)
	def handleNone(self, func, none_survives=False):
		def newFunc(a, b):
			if a == None:
				if none_survives:
					return None
				else:
					return b
			if b == None:
				if none_survives:
					return None
				else: return a
			else:
				return func(a,b)
		return newFunc
	def parseString(self, string):
		self.exprStack = []
		self.variables = {}
		#try:
		self.L=self.pattern.parseString(string )
		#except ParseException,err:
		#	self.L=['Parse Failure', string]
		#	print 'Parse Failure'
		#	print err.line
		#	print " "*(err.column-1) + "^"
		#	print err
	def pushFirst(self, str, loc, toks ):
		self.exprStack.append( toks[0] )
	def pushEnd(self, str, loc, toks):
		self.exprStack.append('END')
	def calculate(self, variables):
		self.variables = variables
		s = list(self.exprStack)
		return self.evaluateStack(s)
	# Recursive function that evaluates the stack
	def evaluateStack(self, s ):
		op = s.pop()
		#print "evaluating", op
		if op in "+-*/^":
			op2 = self.evaluateStack( s )
			op1 = self.evaluateStack( s )
			return self.opn[op]( op1, op2 )
		elif op == 'END':
			return op
		elif op in self.functions:
			ops = []
			newop = self.evaluateStack( s )
			while newop != 'END':
				ops.append(newop)
				newop = self.evaluateStack(s)
			ops.reverse()
			return self.functions[op](ops)
		elif op == "PI":
			return Decimal(math.pi)
		elif op == "E":
			return Decimal(math.e)
		elif re.search('^\$[a-zA-Z0-9_]*$',op):
			if self.variables.has_key(op):
				return self.variables[op]
			else:
				return None
		elif re.search('^[-+]?[0-9]+$',op):
			return long( op )
		else:
			return Decimal( op )
	def cases(self, parameters):
		val = parameters[0]
		if val == None:
			return None
		bs = parameters[2::2]
		results = parameters[1::2]
		if len(bs)+1 != len(results):
			raise Exception('Not enough results or boundaries')
		if val < bs[0]:
			return results[0]
		for b,r in reversed(zip(bs,results[1:])):
			if val >= b: return r
		raise Exception('could not evaluate cases')
	def cases1(self, parameters):
		p = parameters
		casesParameters = [p[0], 5.0, p[1], 4.0, p[2], 3.0, p[3], 2.0, p[4], 1.0]
		return self.cases(casesParameters)
	def cases2(self, parameters):
		p = parameters
		casesParameters = [p[0], 5.0, p[1], 4.0, p[2], 3.5, p[3], 3.0, p[4], 2.5, p[5], 2.0, p[6], 1.5, p[7], 1.0]
		return self.cases(casesParameters)
	def cases3(self, parameters):
		p = parameters
		casesParameters = [p[0], 1.0, p[1], 1.3, p[2], 1.7, p[3], 2.0, p[4], 2.3, p[5], 2.7,
			p[6], 3.0, p[7], 3.3, p[8], 3.7, p[9], 4.0, p[10], 5.0]
		return self.cases(casesParameters)


if __name__ == '__main__':
	p = Parser()
	input_string = raw_input("> ")
	p.parseString(input_string)
	print p.calculate({})
  
  ## Display instructions on how to quit the program
  #print "Type in the string to be parse or 'quit' to exit the program"
  #input_string = raw_input("> ")
  
  #while input_string != 'quit':
    ## Start with a blank exprStack and a blank varStack
    #exprStack = []
    #varStack  = []
  
    #if input_string != '':
      ## try parsing the input string
      #try:
        #L=pattern.parseString( input_string )
      #except ParseException,err:
        #L=['Parse Failure',input_string]
      
      ## show result of parsing the input string
      #if debug_flag: print input_string, "->", L
      #if len(L)==0 or L[0] != 'Parse Failure':
        #if debug_flag: print "exprStack=", exprStack
  
        ## calculate result , store a copy in ans , display the result to user
        #result=evaluateStack(exprStack)
        #variables['ans']=result
        #print result
  
        ## Assign result to a variable if required
        #if debug_flag: print "var=",varStack
        #if len(varStack)==1:
          #variables[varStack.pop()]=result
        #if debug_flag: print "variables=",variables
      #else:
        #print 'Parse Failure'
        #print err.line
        #print " "*(err.column-1) + "^"
        #print err
  
    ## obtain new input string
    #input_string = raw_input("> ")
  
  ## if user type 'quit' then say goodbye
  #print "Good bye!"


