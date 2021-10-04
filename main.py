import sys
import traceback
import re
print("\x1bc", end="")

def load_contents (filepath, splitnew=True):
	f = open(filepath, "r")
	lines = f.read()
	f.close()
	if splitnew:
		lines = lines.split("\n")
	return lines

details = load_contents("syntax.txt")
code = load_contents("code."+details[0], False)

# token types
EOF, INT, STR, MAT, ASS, REF, PAR, LOG, EQU, FUN, INV, CUR, SQU, SEP, KEY, LIT = "EOF", "INT", "STR", "MAT", "ASS", "REF", "PAR", "LOG", "EQU", "FUN", "INV", "CUR", "SQU", "SEP", "KEY", "LIT"

"""
TOKENS:
	EOF -> end of file
	INT -> integer
	STR -> string
	MAT -> mathmatical operator
	ASS -> assignment operator
	REF -> reference
	PAR -> parentheses
	LOG -> logical operators
	EQU -> unique use case: testing conditions
	FUN -> function
	INV -> invalid token, used to mark unknown symbols within the code
	CUR -> marks where curly bracket is
	SQU -> marks where a square bracket is
	SEP -> marks a seperator
	KEY -> a statement
	LIT -> literal
"""

class Token ():
	def __init__ (self, type, value=None):
		self.type = type
		self.value = value
	def detokenize (self):
		if self.type == STR:
			return self.value.lstrip('"').rstrip('"')
		elif self.type == INT:
			if "." in self.value:
				return float(self.value)
			return int(self.value)
		elif self.type == LIT:
			return eval(self.value)
	def __str__ (self):
		return f"Token({self.type}, {self.value})"
	def __repr__ (self):
		return self.__str__()

class Searcher ():
	def __init__ (self):
		self.namespace = ""
	def findvalue (self, value):
		value = value.split("->")
		if self.namespace != "":
			value.insert(0, self.namespace)
		val = None
		search = details.copy()
		for i in range(len(value)):
			for ind in range(len(search)):
				line = search[ind]
				if len(line) > 0:
					if line[0] == "\t":
						line = line[1:]
				reg = re.compile(value[i]+"(\s|:)")
				re2 = re.compile(value[i]+"\s")
				match = reg.match(line)
				if match:
					if re2.match(line):
						search = search[ind:]
						search = search[:search.index("}")]
						break
					else:
						val = line[match.end():]
						if val[-1] == '"' or val[-1] == "'":
							val = val[1:-1]
						return val
		return val

searcher = Searcher()

# check for a return statement
regret = re.compile("^return\s")
# check for an if statement
regif = re.compile("^if\s")
# check for assignment
regass = re.compile("={1}")
# check for string
regstr = re.compile('"')
# check for alias
regali = re.compile("\salias\s")

class Runner ():
	def __init__ (self, details):
		# gets the newline
		self.newline = searcher.findvalue("newline")
		if self.newline != "\\n":
			self.newline += "\n"
		else:
			self.newline = "\n"
		searcher.namespace = "conditionals"
		# conditionals
		self.conditions = {
			searcher.findvalue("if"):"if", 
			searcher.findvalue("elif"):"elif", 
			searcher.findvalue("else"):"else"
		}
		searcher.namespace = "operators"
		# mathmatical operators
		self.operators = {
			searcher.findvalue("\\+"):"+",
			searcher.findvalue("-"):"-",
			searcher.findvalue("\\*"):"*",
			searcher.findvalue("/"):"/"
		}
		# logical operators
		self.logic = {
			searcher.findvalue("&"):"and",
			searcher.findvalue("\\|"):"or",
			searcher.findvalue("!"):"not",
			searcher.findvalue("%"):"%",
			searcher.findvalue("\\^"):"^"
		}
		searcher.namespace = ""
		# the symbols used to mark code blocks
		self.blocks = searcher.findvalue("blocks")
		# alias for print
		self.printline = searcher.findvalue("output")
		# alias for input
		self.inputline = searcher.findvalue("input")
		# gets the character(s) used to mark comments
		self.comment = searcher.findvalue("comments")
		# the keyword used to define functions
		self.funcdef = searcher.findvalue("funcdef")
		self.strings = ('"', "'")
		self.replacements = {
			self.printline:"print",
			self.inputline:"input"
		}
		self.replacements.update(self.conditions)
		self.replacements.update(self.operators)
		self.replacements.update(self.logic)
		# functions, maps from a name to the start and end lines of the function
		self.funcs = {}
		# function args
		self.funcargs = {}
		# aliases
		self.funcaliases = {}
		# variables
		self.vars = {
			"True":Token(LIT, "True"),
			"False":Token(LIT, "False"),
			"None":Token(LIT, "None")
		}
		# lines that are contained within function bodies, used to ensure that parts of functions are not executed outside of a function call
		self.funclines = []
		# variables specific to the local namespace
		self.localvars = {}
		# used to give "exec" and "eval" access to functions and variables
		self.access = {
			"print":print,
			"input":input,
			"vars":self.vars
		}
		# the names of all funcitons in program
		self.funcnames = [
			"print",
			"input"
		]
		# builtin functions
		self.builtins = {
			"print":print,
			"input":input,
		}
		# statements
		self.statements = list(self.conditions.keys())
		self.statements.extend(("alias", "return"))
		# the line the interpreter is currently executing
		self.executionline = 0
	def ERROR (self, errorcode):
		# error code for unclosed string
		if errorcode == 0:
			raise Exception("Unclosed String")
		# error code for unmatched parentheses
		elif errorcode == 1:
			raise Exception("Unmatched Parentheses")
		# error code for unmatched square brackets
		elif errorcode == 2:
			raise Exception("Unmatched Square Brackets")
		# error code for unmatched curly brackers
		elif errorcode == 3:
			raise Exception("Unmatched Curly Brackets")
		# error code for redundant function definition
		elif errorcode == 4:
			raise Exception("Function Already Defined")
		# error code for attempting to set something other than a reference
		elif errorcode == 5:
			raise Exception("Invalid Assignment")
		# error code for invalid arguments for a return statement
		elif errorcode == 6:
			raise Exception("Invalid Return Arguments")
	# splits the code into lines
	def breaklines (self, code):
		"""
		this function splits to code by newlines then joins the segments that were actually strings, this allows the programmer to use newlines within strings
		"""
		code = code.split(self.newline)
		# print(code)
		isstr = False
		inlen = len(code)-1
		for i in range(len(code)):
			i = inlen - i
			if i > len(code)-1:
				break
			line = code[i]
			# print(i, isstr, line.rstrip("\n"))
			if line.count('"') % 2 != 0:
				if isstr:
					line = self.newline + code.pop(i+1)
					code[i] = line
				isstr = not isstr
			elif isstr:
				line += self.newline + code.pop(i+1)
				code[i] = line
		return code
	# converts a line of code into a stream of tokens
	def tokenize (self, line):
		"""
		tokenizes a line of code
		"""
		# current position
		i = 0
		# the token value that is being built
		part = ""
		# the list of completed tokens
		tokens = []
		# if the tokenizer should ignore the next character
		cont = False
		while i < len(line):
			if cont:
				i += 1
				cont = False
				continue
			# tests for a comment
			test = line[i:]
			if self.comment in test:
				if test.index(self.comment) == 0:
					break
			# print(i)
			# resets the part
			part = ""
			# gets the current character
			chr = line[i]
			# print(chr)
			# token type defaults to invalid
			type = INV
			# if the character is a digit
			if chr.isdigit():
				# type is int
				type = INT
				# builds the token's value
				while i < len(line):
					# checks that the next character is another digit or a decimal
					if not (line[i].isdigit() or line[i] == "."):
						break
					# adds the character to the value
					part += line[i]
					# increments the position
					i += 1
				i -= 1
			# if the character is alpha, but not part of a string
			elif chr.isalpha():
				# type is reference
				type = REF
				while i < len(line):
					# checks that the character is alphanumeric or a dot
					if not (line[i].isalnum() or line[i] == "."):
						break
					part += line[i]
					i += 1
				# special cases for references
				# if the reference is to a function
				if part in self.funcnames:
					type = FUN
				# if the reference is to a key
				elif part in self.statements:
					type = KEY
				i -= 1
			else:
				# ignores whitespace
				if chr == " ":
					i += 1
					continue
				# string
				elif chr == '"':
					# stores the boolean if the string is closed
					unclosed = True
					# marks if the next character has been escaped
					escaped = False
					# type is string
					type = STR
					# sets i to the position of the first character in the string
					i += 1
					while i < len(line):
						# checks if the character marks the end of the string
						if line[i] == '"' and not escaped:
							# marks the string a closed
							unclosed = False
							break
						if line[i] != "\\" or escaped:
							part += line[i]
						elif line[i] == "\\":
							# marks the next character as escaped
							escaped = True
						# increments the position
						i += 1
					# adds the opening and closing quotations
					part = '"' + part + '"'
					# checks that the string was closed
					if unclosed:
						# raises an error if the string wasn't closed
						self.ERROR(0)
					# i -= 1
				# if the character is a parenthesis
				elif chr in "()":
					# type is parenthesis
					type = PAR
					# value is character
					part = chr
				# if the character is a mathmatical operator
				elif chr in "+-*/":
					# type is math
					type = MAT
					# value is character
					part = chr
					# if the next character is an equal sign
					if i < len(line)-1:
						if line[i+1] == "=":
							# type is assignment
							type = ASS
							# value is operator plus assignment
							part = chr+"="
							# ignore the next character
							cont = True
				# if the character is a logical operator
				elif chr in "^%":
					# type is logical
					type = LOG
					# value is character
					part = chr
				# if the character is an equal sign
				elif chr == "=":
					# type is assignment
					type = ASS
					# value is character
					part = chr
					# if the next character is also an equal sign
					if i < len(line)-1:
						if line[i+1] == "=":
							# type is equality
							type = EQU
							# value is equals
							part = "=="
							# ignore the next character
							cont = True
				# if the character is a squar bracket
				elif chr in "[]":
					# type is square braket
					type = SQU
					# value is character
					part = chr
				# if the charater is a curly bracket
				elif chr in "{}":
					# type is curly bracket
					type = CUR
					# value is character
					part = chr
				# if the character is a comma
				elif chr == ",":
					# type is seperator
					type = SEP
					# value is character
					part = chr
			# creates and adds a token to the list of tokens
			tokens.append(Token(type, part))
			# increments the position
			i += 1
		# returns the list of tokens
		return tokens
	# hoists function definitions
	def hoistfuncs (self):
		# start of funcion
		start = 0
		# the current line is a function
		isfunc = False
		# if the current code block isn't a function
		notfunc = False
		# the name of the function
		name = ""
		# the arguments the function takes
		args = []
		for i in range(len(code)):
			# gets the current line
			line = code[i]
			# checks if the line is a function definition
			if self.funcdef+" " in line:
				if line.index(self.funcdef+" ") == 0:
					isfunc = True
					# sets start
					start = i+1
					# sets name
					name = line[5:line.index("(")].rstrip(" ")
					# sets args
					args = line[line.index("(")+1:line.index(")")]
					args = ''.join(args.split(" "))
					args = args.split(",")
					if args[0] == "":
						args = []
			# if some other type of code block starts here
			elif line.rstrip(" ").endswith("{"):
				notfunc = True
			# if the line is in a function
			if isfunc and not notfunc:
				# add it to the list of lines contained in functions
				self.funclines.append(i)
			# if the line marks the end of the function
			if line == "}":
				# if the bracket is the end of a different type of code block
				if notfunc:
					notfunc = False
					continue
				isfunc = False
				# records the info about the function
				self.funcs[name] = (start, i)
				self.funcnames.append(name)
				self.funcargs[name] = args
	# processes tokens for return
	def processreturn (self, tokens):
		# the final value to return
		val = None
		cont = 0
		# replaces references
		for i in range(len(tokens)):
			token = tokens[i]
			if token.type == REF:
				if token.value not in self.vars:
					continue
				tokens[i] = self.vars[token.value]
		for i in range(len(tokens)):
			if cont > 0:
				cont -= 1
				continue
			token = tokens[i]
			if token.type == INV:
				continue
			elif token.type == KEY:
				self.ERROR(6)
			elif token.type == ASS:
				self.ERROR(6)
			elif token.type == MAT:
				calc = eval(tokens[i-1].value+token.value+tokens[i+1].value)
				if type(calc) == str:
					calc = '"' + calc + '"'
				tokens[i-1] = self.tokenize(calc)[0]
				if self.executionline == 11:
					print(tokens[i-1])
				cont = 1
			elif token.type == FUN:
				if i < len(tokens)-1:
					val, igc = self.hrunfunc(tokens, i)
					tokens[i] = val
					cont = igc
		if val == None and len(tokens) > 0:
			val = tokens[0]
		return True, val
		# return True, self.tokenize(str(val))
	# runs the given line of code
	def runline (self, line):
		# strips leading tabs
		line = line.lstrip("\t")
		# gets the line as a stream of tokens
		tokens = self.tokenize(line)
		# print(tokens, "tokens")
		# how many tokens to ignore
		cont = 0
		# print(self.localvars)
		# replaces references
		for i in range(len(tokens)):
			token = tokens[i]
			if token.type == REF:
				if token.value not in self.vars:
					if token.value in self.localvars:
						tokens[i] = self.localvars[token.value]
					continue
				tokens[i] = self.vars[token.value]
		# print(tokens, "tokens")
		for i in range(len(tokens)):
			# ignores tokens until cont is 0
			if cont > 0:
				cont -= 1
				continue
			# gets the token
			token = tokens[i]
			# print(token)
			# invalid
			if token.type == INV:
				continue
			# key
			if token.type == KEY:
				# aliased function
				if token.value == "alias":
					self.funcaliases[tokens[i+1].value] = tokens[i-1].value
					self.funcnames.append(tokens[i+1].value)
					cont = 1
				# return value
				elif token.value == "return":
					# print(tokens[1:])
					return self.processreturn(tokens[1:])
			# mathmatical operation
			elif token.type == MAT:
				tokens[i-1] = self.tokenize(eval(tokens[i-1].value+token.value+tokens[i+1].value))
				cont = 1
			# assignment
			elif token.type == ASS:
				if tokens[i-1].type != "REF":
					self.ERROR(5)
				if tokens[i+1].type == FUN:
					if i < len(tokens)-2:
						ntok = tokens[i+2]
						if ntok.type == PAR and ntok.value == "(":
							tokens[i+1], igc = self.hrunfunc(tokens, i+1)
							cont = igc
				if token.value == "=":
					self.vars[tokens[i-1].value] = tokens[i+1]
			# function
			elif token.type == FUN:
				if i < len(tokens)-1:
					ntok = tokens[i+1]
					if ntok.type == PAR and ntok.value == "(":
						tokens[i], igc = self.hrunfunc(tokens, i)
						cont = igc
		return False, None
	# helper function that calls functions given the token list and a start position
	def hrunfunc (self, tokens, start):
		# makes a copy of tokens
		tokens = tokens.copy()
		# drops everything before the start position
		tokens = tokens[start:]
		# gets the function name
		name = tokens[0].value
		# gets the end of the function call
		end = 0
		for i in range(len(tokens)):
			t = tokens[i]
			if t.type == PAR and t.value == ")":
				end = i
				break
		# gets the contents of the call
		tokens = tokens[2:end]
		args = []
		positions = [-1]
		# gets the positions of item seperators
		for i in range(len(tokens)):
			t = tokens[i]
			if t.type == SEP and t.value == ",":
				positions.append(i)
		# evaluates function arguments
		for i in range(len(positions)):
			if i == len(positions)-1:
				args.append(self.processreturn(tokens[positions[i]+1:])[1])
			else:
				args.append(self.processreturn(tokens[positions[i]+1:positions[i+1]])[1])
		# sets args to an empty list if no tokens where present in the content of the function call
		if len(tokens) == 0:
			args = []
		# print(args)
		return self.runfunc(name, *args), end-start+1
	# calls a function
	def runfunc (self, fname, *args):
		# resets localvars
		self.localvars = {}
		# print(fname, args)
		# converts args from a tuple to a list
		args = list(args)
		# checks that fname is valid
		if fname not in self.funcnames:
			raise NameError("function not defined")
		# checks if fname is a builtin function
		if fname not in self.funcs and fname in list(self.builtins.keys()):
			# converts args from tokens to standard data types
			for i in range(len(args)):
				args[i] = args[i].detokenize()
			# runs the function
			v = self.builtins[fname](*args)
			# checks if the return valud was a string
			if type(v) == str:
				v = '"' + v + '"'
			# returns the output of the function as a token
			if v != None:
				return self.tokenize(str(v))[0]
		# function defined in the script
		else:
			# checks if the function name is an alias
			if fname not in self.funcs and fname in list(self.funcaliases.keys()):
				fname = self.funcaliases[fname]
			# sets local variables
			for i in range(len(self.funcargs[fname])):
				self.localvars[self.funcargs[fname][i]] = args[i]
			# runs the function
			for i in range(*self.funcs[fname]):
				ret, val = self.runline(code[i])
				if ret:
					return val
	def run (self):
		global code
		code = self.breaklines(code)
		self.hoistfuncs()
		for i in range(len(code)):
			self.executionline += 1
			if i in self.funclines:
				continue
			# print("line", i+1)
			self.runline(code[i])

runner = Runner(details)
runner.run()