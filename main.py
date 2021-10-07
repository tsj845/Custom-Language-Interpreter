import sys
import traceback
import re
print("\x1bc", end="")

code = load_contents("code.slow++", False)

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

class Runner ():
	def __init__ (self):
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
		# builtin functions
		self.builtins = {
			"print":print,
			"input":input,
			"hash":hash,
		}
		# the names of all funcitons in program
		self.funcnames = list(self.builtins.keys())
		# statements
		self.statements = ["if", "elif", "else", "alias", "return"]
		# the line the interpreter is currently executing
		self.executionline = 0
	def listprops (self):
		d = self.__dict__
		for key in list(d.keys()):
			print(key, d[key])
	def ERROR (self, errorcode):
		line = self.executionline
		# error code for unclosed string
		if errorcode == 0:
			raise SyntaxError(f"Line: {line} Unclosed String")
		# error code for unmatched parentheses
		elif errorcode == 1:
			raise SyntaxError(f"Line: {line} Unmatched Parentheses")
		# error code for unmatched square brackets
		elif errorcode == 2:
			raise SyntaxError(f"Line: {line} Unmatched Square Brackets")
		# error code for unmatched curly brackers
		elif errorcode == 3:
			raise SyntaxError(f"Line: {line} Unmatched Curly Brackets")
		# error code for redundant function definition
		elif errorcode == 4:
			raise NameError(f"Line: {line} Function Already Defined")
		# error code for attempting to set something other than a reference
		elif errorcode == 5:
			raise SyntaxError(f"Line: {line} Invalid Assignment")
		# error code for undefined variable
		elif errorcode == 6:
			raise NameError(f"Line: {line} Undefined Variable Name")
	# splits the code into lines
	def breaklines (self, code):
		"""
		this function splits to code by newlines then joins the segments that were actually strings, this allows the programmer to use newlines within strings
		"""
		code = code.split("\n")
		isstr = False
		inlen = len(code)-1
		for i in range(len(code)):
			i = inlen - i
			if i > len(code)-1:
				break
			line = code[i]
			if line.count('"') % 2 != 0:
				if isstr:
					line = "\n" + code.pop(i+1)
					code[i] = line
				isstr = not isstr
			elif isstr:
				line += "\n" + code.pop(i+1)
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
			if "//" in test:
				if test.index("//") == 0:
					break
			# resets the part
			part = ""
			# gets the current character
			chr = line[i]
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
				elif chr in "^%&|!":
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
				# if the character is a comparason
				elif chr in "<>":
					# type is equality
					type = EQU
					# value is character
					part = chr
					if i < len(line)-1:
						if line[i+1] == "=":
							part += "="
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
			if "func " in line:
				if line.index("func ") == 0:
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
	def evalpar (self, tokens, sliceind, inreturn=False):
		tokenslice = tokens[sliceind+1:]
		notdone = True
		while notdone:
			notdone = False
			for i in range(len(tokenslice)):
				token = tokenslice[i]
				if token.type == PAR:
					if token.value == "(":
						tokenslice = tokenslice[:i].extend(self.evalpar(tokenslice, i, inreturn))
						notdone = True
						break
					else:
						tokenslice.pop(i)
						return tokenslice
				elif token.type == ASS:
					v = token.value
					if tokenslice[i-1].type != REF:
						self.ERROR(5)
					if tokenslice[i+1].type == REF:
						usevars = True
						v = tokenslice[i+1].value
						if inreturn:
							if v in self.localvars:
								usevars = False
						if usevars:
							if v not in self.vars:
								if v not in self.localvars:
									self.ERROR(6)
								usevars = False
						if usevars:
							tokenslice[i+1] = self.vars[v]
						else:
							tokenslice[i+1] = self.localvars[v]
					value = "\x89"
					if tokenslice[i+1].type == PAR and tokenslice[i+1].value == "(":
						calc = self.evalpar(tokenslice, i+1, inreturn)
						tokenslice = tokenslice[:i+1]
						tokenslice.extend(calc)
					if v == "=":
						value = tokenslice[i+1].detokenize()
					elif v == "+=":
						value = self.vars[tokenslice[i-1].value].detokenize() + tokenslice[i+1].detokenize()
					elif v == "-=":
						value = self.vars[tokenslice[i-1].value].detokenize() - tokenslice[i+1].detokenize()
					elif v == "*=":
						value = self.vars[tokenslice[i-1].value].detokenize() * tokenslice[i+1].detokenize()
					elif v == "/=":
						value = self.vars[tokenslice[i-1].value].detokenize() / tokenslice[i+1].detokenize()
					if type(value) == str:
						value = '"' + value + '"'
					else:
						value = str(value)
					value = self.tokenize(value)[0]
					namespace = self.vars
					if inreturn:
						namespace = self.localvars
					namespace[tokenslice[i-1].value] = value
					tokenslice[i-1] = value
					tokenslice.pop(i)
					tokenslice.pop(i)
					notdone = True
					break
				elif token.type == MAT:
					if tokenslice[i+1].type == PAR and tokenslice[i+1].value == "(":
						calc = self.evalpar(tokenslice, i+1, inreturn)
						tokenslice = tokenslice[:i+1]
						tokenslice.extend(calc)
					v = token.value
					calc = "\x89"
					if v == "+":
						calc = tokenslice[i-1].detokenize() + tokenslice[i+1].detokenize()
					elif v == "-":
						calc = tokenslice[i-1].detokenize() - tokenslice[i+1].detokenize()
					elif v == "*":
						calc = tokenslice[i-1].detokenize() * tokenslice[i+1].detokenize()
					elif v == "/":
						calc = tokenslice[i-1].detokenize() / tokenslice[i+1].detokenize()
					if type(calc) == str:
						calc = '"' + calc + '"'
					else:
						calc = str(calc)
					tokenslice[i-1] = self.tokenize(calc)[0]
					tokenslice.pop(i)
					tokenslice.pop(i)
					notdone = True
					break
				elif token.type == FUN:
					val, end = self.hrunfunc(tokenslice, i)
					newtokens = tokenslice[:i]
					newtokens.append(val)
					newtokens.extend(tokenslice[end:])
					tokenslice = newtokens
					notdone = True
					break
				elif token.type == LOG:
					if tokenslice[i+1].type == REF:
						usevars = True
						v = tokenslice[i+1].value
						if inreturn:
							if v in self.localvars:
								usevars = False
						if usevars:
							if v not in self.vars:
								if v not in self.localvars:
									self.ERROR(6)
								usevars = False
						if usevars:
							tokenslice[i+1] = self.vars[v]
						else:
							tokenslice[i+1] = self.localvars[v]
					v = token.value
					if v == "!":
						tokenslice[i] = self.tokenize(str(not tokenslice[i+1].detokenize()))[0]
						notdone = True
						break
					value = None
					v1 = tokenslice[i-1].detokenize()
					v2 = tokenslice[i+1].detokenize()
					if v == "^":
						value = v1 ^ v2
					elif v == "^":
						value = v1 % v2
					elif v == "&":
						value = v1 and v2
					elif v == "|":
						value = v1 or v2
					tokenslice[i-1] = self.tokenize(str(value))[0]
					tokenslice.pop(i)
					tokenslice.pop(i)
					notdone = True
					break
				elif token.type == EQU:
					if tokenslice[i+1].type == REF:
						usevars = True
						v = tokenslice[i+1].value
						if inreturn:
							if v in self.localvars:
								usevars = False
						if usevars:
							if v not in self.vars:
								if v not in self.localvars:
									self.ERROR(6)
								usevars = False
						if usevars:
							tokenslice[i+1] = self.vars[v]
						else:
							tokenslice[i+1] = self.localvars[v]
					value = None
					v = token.value
					v1 = tokenslice[i-1].detokenize()
					v2 = tokenslice[i+1].detokenize()
					if v == "==":
						value = v1 == v2
					elif v == ">=":
						value = v1 >= v2
					elif v == "<=":
						value = v1 <= v2
					elif v == ">":
						value = v1 > v2
					elif v == "<":
						value = v1 < v2
					tokenslice[i-1] = self.tokenize(str(value))[0]
					tokenslice.pop(i)
					tokenslice.pop(i)
					notdone = True
					break
				else:
					continue
		print(tokenslice)
		return tokenslice
	def evaltokens (self, tokens, inreturn=False):
		notdone = True
		while notdone:
			notdone = False
			for i in range(len(tokens)):
				token = tokens[i]
				if token.value == "/":
					if i < len(tokens)-1:
						if tokens[i+1].value == "/":
							break
				if token.type == PAR and token.value == "(":
					tokens[i] = self.evalpar(tokens, i, inreturn)[0]
				elif token.type == FUN:
					if i < len(tokens)-1:
						if tokens[i+1].type == PAR and tokens[i+1].value == "(":
							val, end = self.hrunfunc(tokens, i)
							newtokens = tokens[:i]
							if val != None:
								newtokens.append(val)
							newtokens.extend(tokens[end:])
							tokens = newtokens
							notdone = True
							break
				elif token.type == KEY:
					if token.value == "alias":
						self.funcaliases[tokens[i+1].value] = tokens[i-1].value
						self.funcnames.append(tokens[i+1].value)
						tokens.pop(i-1)
						tokens.pop(i-1)
						tokens.pop(i-1)
						notdone = True
						break
					elif token.value == "return":
						obj = self.evaltokens(tokens[i+1:], inreturn)
						return obj
				elif token.type == ASS:
					v = token.value
					if tokens[i-1].type != REF:
						self.ERROR(5)
					if tokens[i+1].type == REF:
						print(tokens[i+1])
						usevars = True
						v = tokens[i+1].value
						if inreturn:
							if v in self.localvars:
								usevars = False
						if usevars:
							if v not in self.vars:
								if v not in self.localvars:
									self.ERROR(6)
								usevars = False
						if usevars:
							tokens[i+1] = self.vars[v]
						else:
							tokens[i+1] = self.localvars[v]
					if tokens[i+1].type == FUN:
						if tokens[i+2].type == PAR and tokens[i+2].value == "(":
							val, end = self.hrunfunc(tokens, i+1)
							newtokens = tokens[:i+1]
							if val != None:
								newtokens.append(val)
							newtokens.extend(tokens[end+i+3:])
							tokens = newtokens
					value = "\x89"
					if tokens[i+1].type == PAR and tokens[i+1].value == "(":
						calc = self.evalpar(tokens, i+1, inreturn)
						tokens = tokens[:i+1]
						tokens.extend(calc)
					if v == "=":
						value = tokens[i+1].detokenize()
					elif v == "+=":
						value = self.vars[tokens[i-1].value].detokenize() + tokens[i+1].detokenize()
					elif v == "-=":
						value = self.vars[tokens[i-1].value].detokenize() - tokens[i+1].detokenize()
					elif v == "*=":
						value = self.vars[tokens[i-1].value].detokenize() * tokens[i+1].detokenize()
					elif v == "/=":
						value = self.vars[tokens[i-1].value].detokenize() / tokens[i+1].detokenize()
					if type(value) == str:
						value = '"' + value + '"'
					else:
						value = str(value)
					namespace = self.vars
					if inreturn:
						namespace = self.localvars
					value = self.tokenize(value)[0]
					namespace[tokens[i-1].value] = value
					tokens[i-1] = value
					tokens.pop(i)
					tokens.pop(i)
					notdone = True
					break
				elif token.type == MAT:
					if tokens[i+1].type == PAR and tokens[i+1].value == "(":
						calc = self.evalpar(tokens, i+1, inreturn)
						tokens = tokens[:i+1]
						tokens.extend(calc)
					v = token.value
					calc = "\x89"
					if v == "+":
						calc = tokens[i-1].detokenize() + tokens[i+1].detokenize()
					elif v == "-":
						calc = tokens[i-1].detokenize() - tokens[i+1].detokenize()
					elif v == "*":
						calc = tokens[i-1].detokenize() * tokens[i+1].detokenize()
					elif v == "/":
						calc = tokens[i-1].detokenize() / tokens[i+1].detokenize()
					if type(calc) == str:
						calc = '"' + calc + '"'
					else:
						calc = str(calc)
					tokens[i-1] = self.tokenize(calc)[0]
					tokens.pop(i)
					tokens.pop(i)
					notdone = True
					break
				elif token.type == REF:
					if i < len(tokens)-1:
						if tokens[i+1].type == ASS:
							continue
					v = token.value
					value = self.vars[v] if v in self.vars else self.localvars[v]
					tokens[i] = value
				elif token.type == LOG:
					if tokens[i+1].type == REF:
						usevars = True
						v = tokens[i+1].value
						if inreturn:
							if v in self.localvars:
								usevars = False
						if usevars:
							if v not in self.vars:
								if v not in self.localvars:
									self.ERROR(6)
								usevars = False
						if usevars:
							tokens[i+1] = self.vars[v]
						else:
							tokens[i+1] = self.localvars[v]
					v = token.value
					if v == "!":
						tokens[i] = self.tokenize(str(not tokens[i+1].detokenize()))[0]
						notdone = True
						break
					value = None
					v1 = tokens[i-1].detokenize()
					v2 = tokens[i+1].detokenize()
					if v == "^":
						value = v1 ^ v2
					elif v == "^":
						value = v1 % v2
					elif v == "&":
						value = v1 and v2
					elif v == "|":
						value = v1 or v2
					tokens[i-1] = self.tokenize(str(value))[0]
					tokens.pop(i)
					tokens.pop(i)
					notdone = True
					break
				elif token.type == EQU:
					if tokens[i+1].type == REF:
						usevars = True
						v = tokens[i+1].value
						if inreturn:
							if v in self.localvars:
								usevars = False
						if usevars:
							if v not in self.vars:
								if v not in self.localvars:
									self.ERROR(6)
								usevars = False
						if usevars:
							tokens[i+1] = self.vars[v]
						else:
							tokens[i+1] = self.localvars[v]
					value = None
					v = token.value
					v1 = tokens[i-1].detokenize()
					v2 = tokens[i+1].detokenize()
					if v == "==":
						value = v1 == v2
					elif v == ">=":
						value = v1 >= v2
					elif v == "<=":
						value = v1 <= v2
					elif v == ">":
						value = v1 > v2
					elif v == "<":
						value = v1 < v2
					tokens[i-1] = self.tokenize(str(value))[0]
					tokens.pop(i)
					tokens.pop(i)
					notdone = True
					break
		if len(tokens) == 0:
			return
		return tokens[0]
	def runline (self, line, infunc=False):
		line = line.lstrip("\t")
		tokens = self.tokenize(line)
		ret = self.evaltokens(tokens, infunc)
		if ret != None:
			return True, ret
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
				argtokens = tokens[positions[i]+1:]
				args.append(self.evaltokens(argtokens))
			else:
				argtokens = tokens[positions[i]+1:positions[i+1]]
				args.append(self.evaltokens(argtokens))
		# sets args to an empty list if no tokens where present in the content of the function call
		if len(tokens) == 0:
			args = []
		# converts refs to actual values
		for i in range(len(args)):
			if args[i].type == REF:
				args[i] = self.vars[args[i].value] if args[i].value in self.vars else self.localvars[args[i].value]
		return self.runfunc(name, *args), end-start+1
	# calls a function
	def runfunc (self, fname, *args):
		stored = self.executionline
		# resets localvars
		self.localvars = {}
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
				self.executionline = i
				ret, val = self.runline(code[i], True)
				if ret:
					return val
			self.executionline = stored
	def run (self):
		global code
		code = self.breaklines(code)
		self.hoistfuncs()
		for i in range(len(code)):
			if i in self.funclines:
				continue
			self.executionline = i
			try:
				self.runline(code[i])
			except:
				print(self.vars, self.localvars)
				raise

runner = Runner()
runner.run()