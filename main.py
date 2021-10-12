# imports temporary functions
from temp import *

# clears the console
print("\x1bc", end="\n")

f = open("code.slow++")
code = f.read()
f.close()

# token types
INT, STR, MAT, ASS, REF, PAR, LOG, EQU, FUN, INV, CUR, SQU, SEP, KEY, LIT, LST, DCT, SYM = "INT", "STR", "MAT", "ASS", "REF", "PAR", "LOG", "EQU", "FUN", "INV", "CUR", "SQU", "SEP", "KEY", "LIT", "LST", "DCT", "SYM"

SUBSCRIPT = ("STR", "LST", "DCT")

"""
TOKENS:
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
	LST -> a list
	DCT -> a dict
	SYM -> a symbol
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
		elif self.type == REF:
			if self.value in runner.localvars:
				return runner.localvars[self.value].detokenize()
			if self.value in runner.vars:
				return runner.vars[self.value].detokenize()
		elif self.type == LST:
			return self.value
		elif self.type == DCT:
			return self.value
		return self.value
	def __getitem__ (self, key):
		if self.type in (LST, DCT, STR):
			if self.type == STR:
				key += 1
			return self.value[key]
		else:
			raise TypeError(f"Line: {runner.executionline} Invalid Subscripting Get Operation")
	def __setitem__ (self, key, value):
		if self.type in (LST, DCT):
			self.value[key] = value
		else:
			raise TypeError(f"Line: {runner.executionline} Invalid Subscripting Set Operation")
	def __len__ (self):
		if self.type in (LST, DCT, STR):
			return len(self.value)
		else:
			raise TypeError(f"Line: {runner.executionline} Invalid Len Operation")
	def __bool__ (self):
		return bool(self.detokenize())
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
		self.statements = ("if", "elif", "else", "alias", "return", "for", "while", "in")
		# valid symbols
		self.symbols = (":", ".")
		# the line the interpreter is currently executing
		self.executionline = 0
		# config for showing flags
		self.sfconfig = [(0, "*")]
		# flags
		self.flags = {
			# debugging flags
			"showfams" : False,
			"showflags" : False,
			"showvars" : False,
			"showlocals" : False,
			"pel" : False,
			"funcnames" : False,
			"funclines" : False,
			"funcargs" : False,
			# temporary wrappers for list operations
			"tmp-list-join" : True,
			"tmp-list-append" : True,
			"tmp-list-pop" : True,
			"tmp-list-insert" : True,
			"tmp-list-count" : True,
			"tmp-list-extend" : True,
			"tmp-list-index" : True,
			"tmp-list-copy" : True,
			"tmp-list-reverse" : True,
			# temporary wrappers for dict operations
			"tmp-dict-update" : True,
			"tmp-dict-pop" : True,
			"tmp-dict-copy" : True,
			"tmp-dict-keys" : True,
			"tmp-dict-items" : True,
			"tmp-dict-values" : True,
		}
		# flag families
		self.ffams = {
			"ALL" : tuple(self.flags.keys()),
			"FUNCS" : ("funcnames", "funclines", "funcargs"),
			"VARS" : ("showvars", "showlocals"),
			"DEBUG" : ("!FUNCS", "!VARS", "pel", "showflags", "showfams"),
			"TMP" : ("!TMP-LIST", "!TMP-DICT"),
			"TMP-LIST" : ("tmp-list-join", "tmp-list-append", "tmp-list-pop", "tmp-list-insert", "tmp-list-count", "tmp-list-extend", "tmp-list-index", "tmp-list-copy", "tmp-list-reverse"),
			"TMP-DICT" : ("tmp-dict-update", "tmp-dict-pop", "tmp-dict-copy", "tmp-dict-keys", "tmp-dict-items", "tmp-dict-values"),
		}
		# temp names
		self.tmpnames = {
			# temp list funcs
			"tmp-list-join" : "ljoin",
			"tmp-list-append" : "lappend",
			"tmp-list-pop" : "lpop",
			"tmp-list-insert" : "linsert",
			"tmp-list-copy" : "lcopy",
			"tmp-list-count" : "lcount",
			"tmp-list-reverse" : "lreverse",
			"tmp-list-extend" : "lextend",
			"tmp-list-index" : "lindex",
			# temp dict funcs
			"tmp-dict-update" : "dupdate",
			"tmp-dict-pop" : "dpop",
			"tmp-dict-copy" : "dcopy",
			"tmp-dict-keys" : "dkeys",
			"tmp-dict-items" : "ditems",
			"tmp-dict-values" : "dvalues",
		}
		# temp funcs
		self.tmpfuncs = {
			# temp list funcs
			"tmp-list-join" : tmplistjoin,
			"tmp-list-append" : tmplistappend,
			"tmp-list-pop" : tmplistpop,
			"tmp-list-insert" : tmplistinsert,
			"tmp-list-copy" : tmplistcopy,
			"tmp-list-count" : tmplistcount,
			"tmp-list-reverse" : tmplistreverse,
			"tmp-list-extend" : tmplistextend,
			"tmp-list-index" : tmplistindex,
			# temp dict funcs
			"tmp-dict-update" : tmpdictupdate,
			"tmp-dict-pop" : tmpdictpop,
			"tmp-dict-copy" : tmpdictcopy,
			"tmp-dict-keys" : tmpdictkeys,
			"tmp-dict-items" : tmpdictitems,
			"tmp-dict-values" : tmpdictvalues,
		}
	def _displayfam (self, fam):
		allon = 1
		for m in self.ffams[fam]:
			if m[0] == "!":
				allon *= self._displayfam(m[1:])
			else:
				allon *= self.flags[m]
		return allon
	def _displayfams (self):
		for fam in self.ffams:
			output = {0:False, 1:True}[self._displayfam(fam)]
			print(f"{fam} : {output}")
	def _displayflags (self):
		for name in self.flags:
			passed = True
			for rule in self.sfconfig:
				t = rule[0]
				c = rule[1]
				if t == 1:
					if c not in name:
						passed = False
						break
				elif t == 2:
					if c in name:
						passed = False
						break
				elif t == 3:
					if name[c[0]:c[1]] != c[2]:
						passed = False
						break
				elif t == 4:
					if name[c[0]:c[1]] == c[2]:
						passed = False
						break
			if passed:
				print(f"{name} : {self.flags[name]}")
	def _flagshow (self, line):
		line = line.lstrip().rstrip()
		if line[line.index(" ")+1:].isalpha():
			self.flags["showflags"] = eval(line[line.index(" ")+1])
			return
		self.sfconfig = eval(line[line.index(" ")+1:])
	def _process_tmp_flags (self):
		for name in self.flags:
			if name[:3] != "tmp":
				continue
			if self.flags[name]:
				fname = self.tmpnames[name]
				self.builtins[fname] = self.tmpfuncs[name]
				self.funcnames.append(fname)
	def _setfamily (self, line):
		prop = line[2:line.index(" ")]
		val = eval(line[line.index(" ")+1:])
		if prop in self.ffams:
			for pname in self.ffams[prop]:
				if pname[0] == "!":
					self._setfamily("#"+pname+" "+str(val))
				else:
					self.flags[pname] = val
	def _setprop (self, line):
		if line[1] == "!":
			self._setfamily(line)
			return
		prop = line[1:line.index(" ")]
		if prop == "showflags":
			self._flagshow(line)
			return
		val = eval(line[line.index(" ")+1:])
		if prop in self.flags:
			self.flags[prop] = val
	def setflags (self):
		global code
		for i in range(len(code)):
			line = code[i]
			if len(line) == 0 or line[0] != "#":
				if len(line) > 1 and line[0:2] == "//":
					self.funclines.append(i)
					continue
				break
			self._setprop(line)
			self.funclines.append(i)
		self._process_tmp_flags()
	def listprops (self):
		d = self.__dict__
		for key in list(d.keys()):
			print(key, d[key])
	def ERROR (self, errorcode):
		line = self.executionline
		errinfo = f"Line: {line}: {code[line]}"
		# error code for unclosed string
		if errorcode == 0:
			raise SyntaxError(f"{errinfo} Unclosed String")
		# error code for unmatched parentheses
		elif errorcode == 1:
			raise SyntaxError(f"{errinfo} Unmatched Parentheses")
		# error code for unmatched square brackets
		elif errorcode == 2:
			raise SyntaxError(f"{errinfo} Unmatched Square Brackets")
		# error code for unmatched curly brackers
		elif errorcode == 3:
			raise SyntaxError(f"{errinfo} Unmatched Curly Brackets")
		# error code for redundant function definition
		elif errorcode == 4:
			raise NameError(f"{errinfo} Function Already Defined")
		# error code for attempting to set something other than a reference
		elif errorcode == 5:
			raise SyntaxError(f"{errinfo} Invalid Assignment")
		# error code for undefined variable
		elif errorcode == 6:
			raise NameError(f"{errinfo} Undefined Variable Name")
		# error code for unopened square bracket
		elif errorcode == 7:
			raise SyntaxError(f"{errinfo} Unopened Square Bracket")
		# error code for unoped curly bracket
		elif errorcode == 8:
			raise SyntaxError(f"{errinfo} Unopened Curly Bracket")
		# error code for invalid for loop parameters
		elif errorcode == 9:
			raise SyntaxError(f"{errinfo} Invalid For Loop Parameters")
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
			if chr.isdigit() or chr == "-":
				# type is int
				type = INT
				# builds the token's value
				while i < len(line):
					# checks that the next character is another digit or a decimal
					if not (line[i].isdigit() or line[i] in ".-"):
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
					# if not (line[i].isalnum() or line[i] == "."):
					if not line[i].isalnum():
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
				elif chr == '"' or chr == "'":
					endchr = chr
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
						if line[i] == endchr and not escaped:
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
				# if the character is a valid symbol
				elif chr in self.symbols:
					# type is symbol
					type = SYM
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
				elif token.type == REF:
					if i < len(tokenslice)-1:
						if tokenslice[i+1].type == ASS:
							continue
					v = token.value
					value = self.vars[v] if v in self.vars else self.localvars[v]
					tokenslice[i] = value
				elif token.type == SQU:
					if token.value == "[":
						if i > 0 and tokenslice[i-1].type in SUBSCRIPT:
							val, ending = self.retreive(tokenslice, i)
							nt = tokenslice[:i-1]
							nt.append(val)
							nt.extend(tokenslice[ending+1:])
							tokenslice = nt
						else:
							val, ending = self.assemblelist(tokenslice, i)
							nt = tokenslice[:i]
							nt.append(val)
							nt.extend(tokenslice[ending+1:])
							tokenslice = nt
						notdone = True
						break
				elif token.type == CUR:
					if token.value == "{":
						val, ending = self.assembledict(tokenslice, i)
						nt = tokenslice[:i]
						nt.append(val)
						nt.extend(tokenslice[ending+1:])
						tokenslice = nt
						notdone = True
						break
		return tokenslice
	def checktokens (self, tokens, checkstart, indices, type, value):
		for ind in indices:
			token = tokens[checkstart+ind]
			if token.type != type or token.value != value:
				return True
		return False
	def loop (self, tokens, init):
		if tokens[init+1].type != REF:
			self.ERROR(9)
		if tokens[init+2].type != PAR or tokens[init+2].value != "(":
			self.ERROR(9)
		if self.checktokens(tokens, init, (4, 6), SEP, ","):
			self.ERROR(9)
		loopvarname = tokens[init+1].value
		loopstart = tokens[init+3].detokenize()
		loopend = tokens[init+5].detokenize()
		loopstep = tokens[init+7].detokenize()
		self.executionline += 1
		startline = self.executionline
		for loop in range(loopstart, loopend, loopstep):
			self.localvars[loopvarname] = self.tokenize(str(loop))[0]
			v = self.looppass()
			if v:
				if v == 1:
					break
				elif v == 2:
					continue
			self.executionline = startline
		testline = startline
		while code[testline].lstrip("\t") != "}":
			testline += 1
		self.executionline = testline
	def whileloop (self, tokens, init):
		line = self.executionline
		self.executionline += 1
		while bool(self.evaltokens(self.tokenize(code[line])[init:-1]).detokenize()):
			v = self.looppass()
			if v:
				if v == 1:
					break
				elif v == 2:
					continue
		testline = line
		while code[testline].lstrip("\t") != "}":
			testline += 1
		self.executionline = testline
	def looppass (self):
		while code[self.executionline].lstrip("\t") != "}":
			if code[self.executionline].lstrip("\t") == "break":
				return 1
			elif code[self.executionline].lstrip("\t") == "continue":
				return 2
			self.runline(code[self.executionline])
			self.executionline += 1
	def doREF (self, tokens, i, inreturn=False):
		tokens = tokens.copy()
		token = tokens[i]
		if i < len(tokens)-1:
			if tokens[i+1].type == ASS:
				return
		v = token.value
		usevars = True
		if inreturn:
			if v in self.localvars:
				usevars = False
		if usevars:
			if v not in self.vars:
				if v not in self.localvars:
					self.ERROR(6)
				usevars = False
		if usevars:
			return self.vars[v]
		else:
			return self.localvars[v]
	def doFUN (self, tokens, i, inreturn=False):
		tokens = tokens.copy()
		if i < len(tokens)-1:
			if tokens[i+1].type == PAR and tokens[i+1].value == "(":
				val, end = self.hrunfunc(tokens, i)
				newtokens = tokens[:i]
				if val != None:
					newtokens.append(val)
				newtokens.extend(tokens[end:])
				tokens = newtokens
				return tokens
		return tokens
	def doSQU (self, tokens, i, inreturn=False):
		global DB1
		tokens = tokens.copy()
		if i > 0 and tokens[i-1].type in SUBSCRIPT:
			val, ending = self.retreive(tokens, i)
			nt = tokens[:i-1]
			nt.append(val)
			nt.extend(tokens[ending+1:])
			tokens = nt
		else:
			if DB1 == 0:
				raise Exception()
			DB1 -= 1
			val, ending = self.assemblelist(tokens, i)
			nt = tokens[:i]
			nt.append(val)
			nt.extend(tokens[ending+1:])
		return nt
	def doCUR (self, tokens, i, inreturn=False):
		val, ending = self.assembledict(tokens, i)
		nt = tokens[:i]
		nt.append(val)
		nt.extend(tokens[ending+1:])
		return nt
	def doASS (self, tokens, i, inreturn=False):
		namespace = self.vars
		if inreturn:
			namespace = self.localvars
		tokens = tokens.copy()
		token = tokens[i]
		if tokens[i-1].type != REF:
			self.ERROR(5)
		if tokens[i+1].type == REF:
			tokens[i+1] = self.doREF(tokens, i+1, inreturn)
		if tokens[i+1].type == FUN:
			tokens = self.doFUN(tokens, i+1)
		if tokens[i+1].type in (SQU, CUR) and tokens[i+1].value in "[{":
			if tokens[i+1].type == SQU:
				tokens = self.doSQU(tokens, i+1)
				namespace[tokens[i-1].detokenize()] = tokens[i+1]
				tokens.pop(i-1)
				tokens.pop(i-1)
				return tokens
			elif tokens[i+1].type == CUR:
				tokens = self.doCUR(tokens, i+1)
				namespace[tokens[i-1].detokenize()] = tokens[i+1]
				tokens.pop(i-1)
				tokens.pop(i-1)
				return tokens
		value = "\x89"
		if tokens[i+1].type == PAR and tokens[i+1].value == "(":
			calc = self.evalpar(tokens, i+1, inreturn)
			tokens = tokens[:i+1]
			tokens.extend(calc)
		tv = tokens[i-1].value
		# tv1 = self.evaltokens(tokens[:i])
		tv2 = self.evaltokens(tokens[i+1:])
		chosen = self.vars if tv in self.vars else self.localvars
		v = token.value
		if v == "=":
			value = tv2.detokenize()
		elif v == "+=":
			value = chosen[tv].detokenize() + tv2.detokenize()
		elif v == "-=":
			value = chosen[tv].detokenize() - tv2.detokenize()
		elif v == "*=":
			value = chosen[tv].detokenize() * tv2.detokenize()
		elif v == "/=":
			value = chosen[tv].detokenize() / tv2.detokenize()
		if type(value) == str:
			value = '"' + value + '"'
		else:
			value = str(value)
		value = self.tokenize(value)
		if value[0].type in (SQU, CUR):
			if value[0].type == SQU:
				value = self.doSQU(value, 0)[0]
			else:
				value = self.doCUR(value, 0)[0]
		if type(value) != Token:
			value = value[0]
		namespace[tv] = value
		tokens[i-1] = value
		tokens.pop(i)
		tokens.pop(i)
		return tokens
	def doKEY (self, tokens, i, inreturn=False):
		tokens = tokens.copy()
		token = tokens[i]
		if token.value == "alias":
			self.funcaliases[tokens[i+1].value] = tokens[i-1].value
			self.funcnames.append(tokens[i+1].value)
			tokens.pop(i-1)
			tokens.pop(i-1)
			tokens.pop(i-1)
			return 0, tokens
		elif token.value == "return":
			obj = self.evaltokens(tokens[i+1:], inreturn)
			return 2, obj
		elif token.value == "for":
			self.loop(tokens, i)
			return 1, None
		elif token.value == "while":
			self.whileloop(tokens, i+1)
			return 1, None
		elif token.value in ("else", "elif"):
			depth = 1
			testline = self.executionline+1
			while testline < len(code):
				depth -= code[testline].count("}")
				depth += code[testline].count("{")
				if depth == 0:
					self.executionline = testline
					return 1, None
				testline += 1
			return 1, None
		elif token.value == "if":
			val = bool(self.evalpar(tokens, i+1)[0])
			if val:
				return 1, None
			else:
				depth = 1
				testline = self.executionline+1
				while testline < len(code):
					depth -= code[testline].count("}")
					if depth == 0:
						if "elif" in code[testline]:
							testtokens = self.tokenize(code[testline].lstrip("\t"))
							for lp in range(len(testtokens)):
								token = testtokens[lp]
								if token.type == KEY and token.value == "elif":
									val = bool(self.evalpar(testtokens, lp+1)[0])
									if val:
										self.executionline = testline
										return 1, None
						elif "else" in code[testline]:
							testtokens = self.tokenize(code[testline].lstrip("\t"))
							for token in testtokens:
								if token.type == KEY and token.value == "else":
									self.executionline = testline
									return 1, None
					depth += code[testline].count("{")
					if depth == 0:
						self.executionline = testline
						return 1, None
					testline += 1
				self.executionline = testline+1
				return 1, None
		return 1, None
	def doMAT (self, tokens, i, inreturn=False):
		tokens = tokens.copy()
		token = tokens[i]
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
		return tokens
	def doLOG (self, tokens, i, inreturn=False):
		tokens = tokens.copy()
		token = tokens[i]
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
			return tokens
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
		return tokens
	def doEQU (self, tokens, i, inreturn=False):
		tokens = tokens.copy()
		token = tokens[i]
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
		return tokens
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
					tk = self.doFUN(tokens, i)
					if tk != None:
						tokens = tk
						notdone = True
						break
				elif token.type == KEY:
					vc, v = self.doKEY(tokens, i)
					if vc == 0:
						tokens = v
						notdone = True
						break
					elif vc == 1:
						return
					elif vc == 2:
						return v
				elif token.type == ASS:
					tokens = self.doASS(tokens, i, inreturn)
					notdone = True
					break
				elif token.type == MAT:
					tokens = self.doMAT(tokens, i, inreturn)
					notdone = True
					break
				elif token.type == REF:
					v = self.doREF(tokens, i)
					if v:
						tokens[i] = v
				elif token.type == LOG:
					tokens = self.doLOG(tokens, i)
					notdone = True
					break
				elif token.type == EQU:
					tokens = self.doEQU(tokens, i, inreturn)
					notdone = True
					break
				elif token.type == SQU:
					if token.value == "[":
						tokens = self.doSQU(tokens, i)
						notdone = True
						break
				elif token.type == CUR:
					if token.value == "{":
						tokens = self.doCUR(tokens, i)
						notdone = True
						break
		if len(tokens) == 0:
			return
		return tokens[0]
	def assembledict (self, tokens, init):
		cbd = 0
		endpos = init+1
		for i in range(init, len(tokens)):
			if tokens[i].value == "}":
				cbd -= 1
				if cbd == 0:
					endpos = i
					break
			elif tokens[i].value == "{":
				cbd += 1
		tokens = tokens[init+1:endpos]
		positions = [-1]
		bd = 0
		for i in range(len(tokens)):
			t = tokens[i]
			if t.type == SEP and t.value == ",":
				if bd == 0:
					positions.append(i)
			elif t.type == SQU or t.type == CUR:
				if t.value in "[{":
					bd += 1
				elif t.value in "]}":
					bd -= 1
		final = {}
		for i in range(len(positions)):
			if i == len(positions)-1:
				argtokens = tokens[positions[i]+1:]
			else:
				argtokens = tokens[positions[i]+1:positions[i+1]]
			splitind = -1
			for ind in range(len(argtokens)):
				t = argtokens[ind]
				if t.type == SYM and t.value == ":":
					splitind = ind
					break
			if splitind == -1:
				raise Exception()
			final[self.evaltokens(argtokens[:splitind]).detokenize()] = self.evaltokens(argtokens[splitind+1:]).detokenize()
		if len(tokens) == 0:
			final = {}
		return Token(DCT, final), endpos
	def assemblelist (self, tokens, init):
		sbd = 0
		endpos = init+1
		for i in range(init, len(tokens)):
			if tokens[i].value == "]":
				sbd -= 1
				if sbd == 0:
					endpos = i
					break
			elif tokens[i].value == "[":
				sbd += 1
		tokens = tokens[init+1:endpos]
		positions = [-1]
		bd = 0
		for i in range(len(tokens)):
			t = tokens[i]
			if t.type == SEP and t.value == ",":
				if bd == 0:
					positions.append(i)
			elif t.type == SQU or t.type == CUR:
				if t.value in "[{":
					bd += 1
				elif t.value in "]}":
					bd -= 1
		final = []
		for i in range(len(positions)):
			if i == len(positions)-1:
				argtokens = tokens[positions[i]+1:]
			else:
				argtokens = tokens[positions[i]+1:positions[i+1]]
			final.append(self.evaltokens(argtokens).detokenize())
		if len(tokens) == 0:
			final = []
		return Token(LST, final), endpos
	def retreive (self, tokens, init):
		sbd = 0
		endpos = init+1
		for i in range(init, len(tokens)):
			if tokens[i].value == "]":
				sbd -= 1
				if sbd == 0:
					endpos = i
					break
			elif tokens[i].value == "[":
				sbd += 1
		ind = self.evaltokens(tokens[init+1:endpos]).detokenize()
		val = tokens[init-1][ind]
		if type(val) == str:
			val = '"' + val + '"'
		else:
			val = str(val)
		val = self.tokenize(val)[0]
		return val, endpos
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
		pd = 0
		for i in range(len(tokens)):
			t = tokens[i]
			if t.type == PAR:
				if t.value == ")":
					pd -= 1
					if pd == 0:
						end = i
						break
				else:
					pd += 1
		# gets the contents of the call
		tokens = tokens[2:end]
		args = []
		positions = [-1]
		bd = 0
		# gets the positions of item seperators
		for i in range(len(tokens)):
			t = tokens[i]
			if t.type == SEP and t.value == ",":
				if bd == 0:
					positions.append(i)
			elif t.type in (SQU, CUR, PAR):
				if t.value in "([{":
					bd += 1
				elif t.value in ")]}":
					bd -= 1
		# evaluates function arguments
		for i in range(len(positions)):
			if i == len(positions)-1:
				argtokens = tokens[positions[i]+1:]
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
		return self.runfunc(name, *args), end+start+1
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
			# checks if the return value was a string
			if type(v) == str:
				v = '"' + v + '"'
			# returns the output of the function as a token
			if v != None:
				tks = self.tokenize(str(v))
				if tks[0].type not in (SQU, CUR):
					return tks[0]
				else:
					if tks[0].type == SQU:
						lst = self.doSQU(tks, 0)
						# print(lst, "lst")
						return lst[0]
					else:
						return self.doCUR(tks, 0)[0]
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
					self.executionline = stored
					return val
			self.executionline = stored
	def exit (self):
		if self.flags["showfams"]:
			self._displayfams()
		if self.flags["showflags"]:
			self._displayflags()
		if self.flags["showvars"]:
			print(self.vars)
		if self.flags["showlocals"]:
			print(self.localvars)
		if self.flags["pel"]:
			print(self.executionline)
		if self.flags["funcnames"]:
			print(self.funcnames)
		if self.flags["funclines"]:
			print(self.funclines)
		if self.flags["funcargs"]:
			print(self.funcargs)
	def run (self):
		global code
		code = self.breaklines(code)
		self.setflags()
		self.hoistfuncs()
		self.executionline = -1
		while self.executionline < len(code):
			self.executionline += 1
			if self.executionline in self.funclines:
				continue
			if self.executionline >= len(code):
				break
			try:
				self.runline(code[self.executionline])
			except:
				self.exit()
				raise
		self.exit()

DB1 = 5

runner = Runner()
runner.run()

# print("\x1b[38;2;255;0;0mHASH:", hash("y is true"), "\x1b[39m")