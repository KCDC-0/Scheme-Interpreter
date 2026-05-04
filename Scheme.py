import re
# from Evaluate import *



####################################
######################## Reader 
####################################


################### Syntactic Analysis (Parsing)

class Pair:
    """A Pair has a first and a second (rest) attribute."""
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __repr__(self):
        return f"Pair({repr(self.first)}, {repr(self.second)})"

    def __str__(self):
        res = f"({str(self.first)}"
        second = self.second
        while isinstance(second, Pair):
            res += f" {str(second.first)}"
            second = second.second
        if second is not nil:
            res += f" . {str(second)}"
        return res + ")"
    
    def map(self, fn):
        """Applies fn to every element in the list."""
        return Pair(fn(self.first), self.second.map(fn) if isinstance(self.second, Pair) else self.second)

    def to_py_list(self):
        """Converts a Scheme list to a Python list."""
        result = [self.first]
        curr = self.second
        while curr is not nil:
            if not isinstance(curr, Pair):
                result.append(curr)
                break
            result.append(curr.first)
            curr = curr.second
        return result

class nil:
    """Empty list"""
    def __len__(self): return 0
    def __repr__(self): return "nil"
    def __str__(self): return "()"

nil = nil() 


def scheme_read(tokens):
    """Read the next expression from tokens."""
    if not tokens:
        raise EOFError
    token = tokens.pop(0)
    
    if token == "(":
        return read_tail(tokens)
    elif token == ")":
        raise SyntaxError("unexpected )")
    else:
        return token

def read_tail(tokens):
    """Process the inside of a list until ')' is found."""
    if not tokens:
        raise SyntaxError("unexpected end of line")
    
    if tokens[0] == ")":
        tokens.pop(0)
        return nil
    
    first = scheme_read(tokens)
    rest = read_tail(tokens)
    return Pair(first, rest)



################### Lexical Analysis (Tokenizing)

def tokenize(s):
    """Convert a string into a list of tokens."""
    # Add spaces around parentheses so they separate from words
    s = re.sub(r'([()])', r' \1 ', s)
    s =re.sub(r'\s+', ' ', s).strip()
    
    tokens = []
    for line in s.split('\n'):
        # Remove comments
        line = line.split(';')[0]
        for token in line.split():
            tokens.append(type_check(token))
    return tokens

def type_check(token):
    """Convert token to boolean, int or float if possible; otherwise keep as string."""
    if token == "#t": 
        return True
    if token == "#f": 
        return False
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return token

def buffer_input(text):
    return tokenize(text)

def read_line(line):
    """Tokenize and parse a single line of Scheme code."""
    tokens = buffer_input(line)
    return scheme_read(tokens)





####################################
######################## Environments
####################################

class Frame:
    """An environment frame that holds symbol-to-value bindings."""
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def lookup(self, symbol):
        """Find the value of a symbol in this frame or its parents."""
        if symbol in self.bindings:
            return self.bindings[symbol]
        elif self.parent is not None:
            return self.parent.lookup(symbol)
        else:
            raise NameError(f"Symbol '{symbol}' not found.")

    def define(self, symbol, value):
        """Bind a symbol to a value in the current frame."""
        self.bindings[symbol] = value

    def set_variable(self, symbol, value):
        """Set a value to an existing binding in the nearest frame."""
        if symbol in self.bindings:
            self.bindings[symbol] = value
        elif self.parent is not None:
            self.parent.set_variable(symbol, value)
        else:
            raise NameError(f"Cannot set undefined symbol: {symbol}")





####################################
######################## Evaluator 
####################################


################## Eval / Apply

def scheme_eval(expr, env):
    """Evaluate a Scheme expression in environment env."""
    if isinstance(expr, (int, float)): # Rule 1
        return expr
    elif isinstance(expr, str): # Rule 2
        return env.lookup(expr)
    elif isinstance(expr, Pair): # Rule 3
        first = expr.first
        rest = expr.second

        if first == "define":
            return do_define_form(rest, env)
        elif first == "set":
            symbol = rest.first
            value = scheme_eval(rest.second.first, env)
            env.set_variable(symbol, value)
            return symbol
        elif first == "let":
            return do_let_form(rest, env)
        elif first == "quote":
            return rest.first
        elif first == "if":
            return do_if_form(rest, env)
        elif first == "cond": 
            return do_cond_form(rest, env)
        elif first == "lambda":
            return LambdaProcedure(rest.first, rest.second, env)
        elif first == "and":
            return do_and_form(rest, env)
        elif first == "or":
            return do_or_form(rest, env)


        operator = scheme_eval(first, env)
        operands = rest.map(lambda x: scheme_eval(x, env))
        
        return scheme_apply(operator, operands, env)
    else:
        raise TypeError(f"Unknown expression type: {expr}")

def scheme_apply(procedure, args, env):
    """Apply a procedure to a Scheme list of arguments."""
    if callable(procedure):
        return procedure(*args.to_py_list())
    
    elif isinstance(procedure, LambdaProcedure):
        # Create a new child frame
        new_env = Frame(procedure.env)
        
        # Bind formals to args
        formals = procedure.formals.to_py_list() if procedure.formals is not nil else []
        vals = args.to_py_list() if args is not nil else []
        
        if len(formals) != len(vals):
            raise TypeError(f"Expected {len(formals)} arguments, got {len(vals)}")
        
        for name, val in zip(formals, vals):
            new_env.define(name, val)
            
        # Evaluate the body
        curr = procedure.body
        result = None
        while curr is not nil:
            result = scheme_eval(curr.first, new_env)
            curr = curr.second
        return result
    
    else:
        raise TypeError(f"Cannot call {procedure}")





####################################
######################## Procedures 
####################################


import operator
from functools import reduce


################## Special Forms

def do_define_form(expressions, env):
    symbol = expressions.first
    value = scheme_eval(expressions.second.first, env)
    env.define(symbol, value)
    return symbol

def do_let_form(expressions, env):
    bindings = expressions.first
    body = expressions.second
    
    names = nil
    values = nil
    
    curr = bindings
    while curr is not nil:
        binding = curr.first
        names = Pair(binding.first, names)
        # Evaluate the value in the current environment
        val = scheme_eval(binding.second.first, env)
        values = Pair(val, values)
        curr = curr.second
        
    procedure = LambdaProcedure(names, body, env)
    return scheme_apply(procedure, values, env)

def do_if_form(expressions, env):
    condition = scheme_eval(expressions.first, env)
    if condition:
        exp = scheme_eval(expressions.second.first, env)
    else:
        exp = scheme_eval(expressions.second.second.first, env)
    return exp

def do_cond_form(clauses, env):
    while clauses is not nil:
        clause = clauses.first
        test = clause.first
        
        # Check if it's the 'else' clause or if the test is true
        if test == "else" or scheme_eval(test, env) is not False:
            if clause.second is nil:
                return True 
            return scheme_eval(clause.second.first, env)
        clauses = clauses.second
    return None

def do_and_form(expressions, env):
    if expressions is nil:
        return True
    
    curr = expressions
    while curr.second is not nil:
        val = scheme_eval(curr.first, env)
        if val is False:
            return False
        curr = curr.second
        
    return scheme_eval(curr.first, env)

def do_or_form(expressions, env):
    if expressions is nil:
        return False
    
    curr = expressions
    while curr is not nil:
        val = scheme_eval(curr.first, env)
        if val is not False:
            return val 
        curr = curr.second
        
    return False

class LambdaProcedure:
    """A procedure defined by a lambda expression."""
    def __init__(self, formals, body, env):
        self.formals = formals
        self.body = body
        self.env = env

    def __repr__(self):
        return f"LambdaProcedure({repr(self.formals)}, {repr(self.body)})"


################## Global procedures

def create_global_frame():
    global_env = Frame()
    global_env.define("+", lambda *args: sum(args))
    global_env.define("*", lambda *args: reduce(operator.mul, args, 1))
    global_env.define("-", lambda *args: args[0] - sum(args[1:]) if len(args) > 1 else -args[0])
    global_env.define("=", lambda x, y: x == y)
    global_env.define(">", lambda x, y: x > y)
    global_env.define("<", lambda x, y: x < y)
    global_env.define("abs", lambda x: abs(x))
    # global_env.define("and", lambda *args: reduce(lambda x, y: x and y, args))
    # global_env.define("or", lambda *args: reduce(lambda x, y: x or y, args))
    global_env.define("xor", lambda *args: reduce(lambda x, y: (x or y) and not (x and y), args))
    global_env.define("cons", lambda x, y: Pair(x, y))
    global_env.define("car", lambda p: p.first if isinstance(p, Pair) else TypeError("not a pair"))
    global_env.define("cdr", lambda p: p.second if isinstance(p, Pair) else TypeError("not a pair"))
    global_env.define("null?", lambda x: x is nil)
    global_env.define("list?", lambda x: isinstance(x, Pair) or x is nil)

    return global_env






####################################
######################## Initialising 
####################################


test1 = '''(+ 1 
            (* 2 3))'''


def repl():
    env = create_global_frame()
    while True:
        try:
            val = input("scheme> ")
            if val == "exit": break
            
            tokens = tokenize(val)
            expression = scheme_read(tokens)
            result = scheme_eval(expression, env)
            
            print(result)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    repl()

