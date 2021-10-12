## list funcs ##

def tmplistjoin (lst, chr):
	return chr.join(lst)

def tmplistappend (lst, item):
	lst.append(item)

def tmplistpop (lst, index=-1):
	return lst.pop(index)

def tmplistinsert (lst, index, item):
	lst.insert(index, item)

def tmplistindex (lst, item):
	return lst.index(item)

def tmplistcopy (lst):
	return lst.copy()

def tmplistcount (lst, item):
	return lst.count(item)

def tmplistreverse (lst):
	lst.reverse()

def tmplistextend (l1, l2):
	l1.extend(l2)

## dict funcs ##

def tmpdictupdate (d1, d2):
	d1.update(d2)

def tmpdictpop (d, key):
	return d.pop(key)

def tmpdictcopy (d):
	return d.copy()

def tmpdictkeys (d):
	return d.keys()

def tmpdictitems (d):
	return d.items()

def tmpdictvalues (d):
	return d.values()