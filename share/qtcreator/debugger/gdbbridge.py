
import binascii
try:
    import __builtin__
except:
    import builtins
try:
    import gdb
except:
    pass

import inspect
import os
import os.path
import sys
import tempfile
import traceback
import struct


def warn(message):
    print("XXX: %s\n" % message.encode("latin1"))

from dumper import *
from qttypes import *
from stdtypes import *
from misctypes import *
from boosttypes import *
from creatortypes import *


#######################################################################
#
# Infrastructure
#
#######################################################################

def savePrint(output):
    try:
        print(output)
    except:
        out = ""
        for c in output:
            cc = ord(c)
            if cc > 127:
                out += "\\\\%d" % cc
            elif cc < 0:
                out += "\\\\%d" % (cc + 256)
            else:
                out += c
        print(out)

def registerCommand(name, func):

    class Command(gdb.Command):
        def __init__(self):
            super(Command, self).__init__(name, gdb.COMMAND_OBSCURE)
        def invoke(self, args, from_tty):
            savePrint(func(args))

    Command()

def parseAndEvaluate(exp):
    return gdb.parse_and_eval(exp)

def listOfLocals(varList):
    frame = gdb.selected_frame()
    try:
        frame = gdb.selected_frame()
        #warn("FRAME %s: " % frame)
    except RuntimeError as error:
        warn("FRAME NOT ACCESSIBLE: %s" % error)
        return []
    except:
        warn("FRAME NOT ACCESSIBLE FOR UNKNOWN REASONS")
        return []

    try:
        block = frame.block()
        #warn("BLOCK: %s " % block)
    except RuntimeError as error:
        #warn("BLOCK IN FRAME NOT ACCESSIBLE: %s" % error)
        return []
    except:
        warn("BLOCK NOT ACCESSIBLE FOR UNKNOWN REASONS")
        return []

    items = []
    shadowed = {}
    while True:
        if block is None:
            warn("UNEXPECTED 'None' BLOCK")
            break
        for symbol in block:
            name = symbol.print_name

            if name == "__in_chrg" or name == "__PRETTY_FUNCTION__":
                continue

            # "NotImplementedError: Symbol type not yet supported in
            # Python scripts."
            #warn("SYMBOL %s  (%s): " % (symbol, name))
            if name in shadowed:
                level = shadowed[name]
                name1 = "%s@%s" % (name, level)
                shadowed[name] = level + 1
            else:
                name1 = name
                shadowed[name] = 1
            #warn("SYMBOL %s  (%s, %s)): " % (symbol, name, symbol.name))
            item = LocalItem()
            item.iname = "local." + name1
            item.name = name1
            try:
                item.value = frame.read_var(name, block)
                #warn("READ 1: %s" % item.value)
                if not item.value.is_optimized_out:
                    #warn("ITEM 1: %s" % item.value)
                    items.append(item)
                    continue
            except:
                pass

            try:
                item.value = frame.read_var(name)
                #warn("READ 2: %s" % item.value)
                if not item.value.is_optimized_out:
                    #warn("ITEM 2: %s" % item.value)
                    items.append(item)
                    continue
            except:
                # RuntimeError: happens for
                #     void foo() { std::string s; std::wstring w; }
                # ValueError: happens for (as of 2010/11/4)
                #     a local struct as found e.g. in
                #     gcc sources in gcc.c, int execute()
                pass

            try:
                #warn("READ 3: %s %s" % (name, item.value))
                item.value = gdb.parse_and_eval(name)
                #warn("ITEM 3: %s" % item.value)
                items.append(item)
            except:
                # Can happen in inlined code (see last line of
                # RowPainter::paintChars(): "RuntimeError:
                # No symbol \"__val\" in current context.\n"
                pass

        # The outermost block in a function has the function member
        # FIXME: check whether this is guaranteed.
        if not block.function is None:
            break

        block = block.superblock

    return items


def catchCliOutput(command):
    try:
        return gdb.execute(command, to_string=True).split("\n")
    except:
        pass
    filename = createTempFile()
    gdb.execute("set logging off")
#        gdb.execute("set logging redirect off")
    gdb.execute("set logging file %s" % filename)
#        gdb.execute("set logging redirect on")
    gdb.execute("set logging on")
    msg = ""
    try:
        gdb.execute(command)
    except RuntimeError as error:
        # For the first phase of core file loading this yield
        # "No symbol table is loaded.  Use the \"file\" command."
        msg = str(error)
    except:
        msg = "Unknown error"
    gdb.execute("set logging off")
#        gdb.execute("set logging redirect off")
    if len(msg):
        # Having that might confuse result handlers in the gdbengine.
        #warn("CLI ERROR: %s " % msg)
        removeTempFile(filename)
        return "CLI ERROR: %s " % msg
    temp = open(filename, "r")
    lines = []
    for line in temp:
        lines.append(line)
    temp.close()
    removeTempFile(filename)
    return lines

def selectedInferior():
    try:
        # Does not exist in 7.3.
        return gdb.selected_inferior()
    except:
        pass
    # gdb.Inferior is new in gdb 7.2
    return gdb.inferiors()[0]

#######################################################################
#
# Types
#
#######################################################################

PointerCode = gdb.TYPE_CODE_PTR
ArrayCode = gdb.TYPE_CODE_ARRAY
StructCode = gdb.TYPE_CODE_STRUCT
UnionCode = gdb.TYPE_CODE_UNION
EnumCode = gdb.TYPE_CODE_ENUM
FlagsCode = gdb.TYPE_CODE_FLAGS
FunctionCode = gdb.TYPE_CODE_FUNC
IntCode = gdb.TYPE_CODE_INT
FloatCode = gdb.TYPE_CODE_FLT # Parts of GDB assume that this means complex.
VoidCode = gdb.TYPE_CODE_VOID
#SetCode = gdb.TYPE_CODE_SET
RangeCode = gdb.TYPE_CODE_RANGE
StringCode = gdb.TYPE_CODE_STRING
#BitStringCode = gdb.TYPE_CODE_BITSTRING
#ErrorTypeCode = gdb.TYPE_CODE_ERROR
MethodCode = gdb.TYPE_CODE_METHOD
MethodPointerCode = gdb.TYPE_CODE_METHODPTR
MemberPointerCode = gdb.TYPE_CODE_MEMBERPTR
ReferenceCode = gdb.TYPE_CODE_REF
CharCode = gdb.TYPE_CODE_CHAR
BoolCode = gdb.TYPE_CODE_BOOL
ComplexCode = gdb.TYPE_CODE_COMPLEX
TypedefCode = gdb.TYPE_CODE_TYPEDEF
NamespaceCode = gdb.TYPE_CODE_NAMESPACE
#Code = gdb.TYPE_CODE_DECFLOAT # Decimal floating point.
#Code = gdb.TYPE_CODE_MODULE # Fortran
#Code = gdb.TYPE_CODE_INTERNAL_FUNCTION


#######################################################################
#
# Step Command
#
#######################################################################

def sal(args):
    (cmd, addr) = args.split(",")
    lines = catchCliOutput("info line *" + addr)
    fromAddr = "0x0"
    toAddr = "0x0"
    for line in lines:
        pos0from = line.find(" starts at address") + 19
        pos1from = line.find(" ", pos0from)
        pos0to = line.find(" ends at", pos1from) + 9
        pos1to = line.find(" ", pos0to)
        if pos1to > 0:
            fromAddr = line[pos0from : pos1from]
            toAddr = line[pos0to : pos1to]
    gdb.execute("maint packet sal%s,%s,%s" % (cmd,fromAddr, toAddr))

registerCommand("sal", sal)


#######################################################################
#
# Convenience
#
#######################################################################

# Just convienience for 'python print ...'
class PPCommand(gdb.Command):
    def __init__(self):
        super(PPCommand, self).__init__("pp", gdb.COMMAND_OBSCURE)
    def invoke(self, args, from_tty):
        print(eval(args))

PPCommand()

# Just convienience for 'python print gdb.parse_and_eval(...)'
class PPPCommand(gdb.Command):
    def __init__(self):
        super(PPPCommand, self).__init__("ppp", gdb.COMMAND_OBSCURE)
    def invoke(self, args, from_tty):
        print(gdb.parse_and_eval(args))

PPPCommand()


def scanStack(p, n):
    p = int(p)
    r = []
    for i in xrange(n):
        f = gdb.parse_and_eval("{void*}%s" % p)
        m = gdb.execute("info symbol %s" % f, to_string=True)
        if not m.startswith("No symbol matches"):
            r.append(m)
        p += f.type.sizeof
    return r

class ScanStackCommand(gdb.Command):
    def __init__(self):
        super(ScanStackCommand, self).__init__("scanStack", gdb.COMMAND_OBSCURE)
    def invoke(self, args, from_tty):
        if len(args) == 0:
            args = 20
        savePrint(scanStack(gdb.parse_and_eval("$sp"), int(args)))

ScanStackCommand()

def registerDumper(funcname, function):
    global qqDumpers, qqFormats, qqEditable
    try:
        #warn("FUNCTION: %s " % funcname)
        #funcname = function.func_name
        if funcname.startswith("qdump__"):
            type = funcname[7:]
            qqDumpers[type] = function
            qqFormats[type] = qqFormats.get(type, "")
        elif funcname.startswith("qform__"):
            type = funcname[7:]
            formats = ""
            try:
                formats = function()
            except:
                pass
            qqFormats[type] = formats
        elif funcname.startswith("qedit__"):
            type = funcname[7:]
            try:
                qqEditable[type] = function
            except:
                pass
    except:
        pass

def bbsetup(args = ''):
    global qqDumpers, qqFormats, qqEditable, typeCache
    qqDumpers = {}
    qqFormats = {}
    qqEditable = {}
    typeCache = {}
    module = sys.modules[__name__]

    #warn("KEYS: %s " % module.__dict__.keys())
    for name in module.__dict__.keys():
        #warn("KEY: %s " % name)
        #warn("FUNCT: %s " % module.__dict__[name])
        registerDumper(name, module.__dict__[name])

    result = "dumpers=["
    #qqNs = qtNamespace() # This is too early
    for key, value in qqFormats.items():
        if key in qqEditable:
            result += '{type="%s",formats="%s",editable="true"},' % (key, value)
        else:
            result += '{type="%s",formats="%s"},' % (key, value)
    result += ']'
    #result += ',namespace="%s"' % qqNs
    print(result)
    return result

registerCommand("bbsetup", bbsetup)


#######################################################################
#
# Import plain gdb pretty printers
#
#######################################################################

class PlainDumper:
    def __init__(self, printer):
        self.printer = printer

    def __call__(self, d, value):
        printer = self.printer.gen_printer(value)
        lister = getattr(printer, "children", None)
        children = [] if lister is None else list(lister())
        d.putType(self.printer.name)
        val = printer.to_string().encode("hex")
        d.putValue(val, Hex2EncodedLatin1)
        d.putValue(printer.to_string())
        d.putNumChild(len(children))
        if d.isExpanded():
            with Children(d):
                for child in children:
                    d.putSubItem(child[0], child[1])

def importPlainDumper(printer):
    global qqDumpers, qqFormats
    name = printer.name.replace("::", "__")
    qqDumpers[name] = PlainDumper(printer)
    qqFormats[name] = ""

def importPlainDumpers(args):
    return
    for obj in gdb.objfiles():
        for printers in obj.pretty_printers + gdb.pretty_printers:
            for printer in printers.subprinters:
                importPlainDumper(printer)

registerCommand("importPlainDumpers", importPlainDumpers)


#gdb.Value.child = impl_Value_child

# Fails on SimulatorQt.
tempFileCounter = 0
try:
    # Test if 2.6 is used (Windows), trigger exception and default
    # to 2nd version.
    file = tempfile.NamedTemporaryFile(prefix="py_",delete=True)
    file.close()
    def createTempFile():
        file = tempfile.NamedTemporaryFile(prefix="py_",delete=True)
        file.close()
        return file.name

except:
    def createTempFile():
        global tempFileCounter
        tempFileCounter += 1
        fileName = "%s/py_tmp_%d_%d" \
            % (tempfile.gettempdir(), os.getpid(), tempFileCounter)
        return fileName

def removeTempFile(name):
    try:
        os.remove(name)
    except:
        pass



#
# VTable
#
def hasVTable(type):
    fields = type.fields()
    if len(fields) == 0:
        return False
    if fields[0].is_base_class:
        return hasVTable(fields[0].type)
    return str(fields[0].type) ==  "int (**)(void)"

def dynamicTypeName(value):
    if hasVTable(value.type):
        #vtbl = str(parseAndEvaluate("{int(*)(int)}%s" % int(value.address)))
        try:
            # Fails on 7.1 due to the missing to_string.
            vtbl = gdb.execute("info symbol {int*}%s" % int(value.address),
                to_string = True)
            pos1 = vtbl.find("vtable ")
            if pos1 != -1:
                pos1 += 11
                pos2 = vtbl.find(" +", pos1)
                if pos2 != -1:
                    return vtbl[pos1 : pos2]
        except:
            pass
    return str(value.type)

def downcast(value):
    try:
        return value.cast(value.dynamic_type)
    except:
        pass
    #try:
    #    return value.cast(lookupType(dynamicTypeName(value)))
    #except:
    #    pass
    return value

def expensiveDowncast(value):
    try:
        return value.cast(value.dynamic_type)
    except:
        pass
    try:
        return value.cast(lookupType(dynamicTypeName(value)))
    except:
        pass
    return value

typeCache = {}

typesToReport = {}
typesReported = {}

def addToCache(type):
    global typesReported
    global typesToReport
    typename = str(type)
    if typename in typesReported:
        return
    typesReported[typename] = True
    typesToReport[typename] = type

def lookupType(typestring):
    global typeCache
    global typesToReport
    type = typeCache.get(typestring)
    #warn("LOOKUP 1: %s -> %s" % (typestring, type))
    if not type is None:
        return type

    if typestring == "void":
        type = gdb.lookup_type(typestring)
        typeCache[typestring] = type
        typesToReport[typestring] = type
        return type

    #try:
    #    type = gdb.parse_and_eval("{%s}&main" % typestring).type
    #    if not type is None:
    #        typeCache[typestring] = type
    #        typesToReport[typestring] = type
    #        return type
    #except:
    #    pass

    # See http://sourceware.org/bugzilla/show_bug.cgi?id=13269
    # gcc produces "{anonymous}", gdb "(anonymous namespace)"
    # "<unnamed>" has been seen too. The only thing gdb
    # understands when reading things back is "(anonymous namespace)"
    if typestring.find("{anonymous}") != -1:
        ts = typestring
        ts = ts.replace("{anonymous}", "(anonymous namespace)")
        type = lookupType(ts)
        if not type is None:
            typeCache[typestring] = type
            typesToReport[typestring] = type
            return type

    #warn(" RESULT FOR 7.2: '%s': %s" % (typestring, type))

    # This part should only trigger for
    # gdb 7.1 for types with namespace separators.
    # And anonymous namespaces.

    ts = typestring
    while True:
        #warn("TS: '%s'" % ts)
        if ts.startswith("class "):
            ts = ts[6:]
        elif ts.startswith("struct "):
            ts = ts[7:]
        elif ts.startswith("const "):
            ts = ts[6:]
        elif ts.startswith("volatile "):
            ts = ts[9:]
        elif ts.startswith("enum "):
            ts = ts[5:]
        elif ts.endswith(" const"):
            ts = ts[:-6]
        elif ts.endswith(" volatile"):
            ts = ts[:-9]
        elif ts.endswith("*const"):
            ts = ts[:-5]
        elif ts.endswith("*volatile"):
            ts = ts[:-8]
        else:
            break

    if ts.endswith('*'):
        type = lookupType(ts[0:-1])
        if not type is None:
            type = type.pointer()
            typeCache[typestring] = type
            typesToReport[typestring] = type
            return type

    try:
        #warn("LOOKING UP '%s'" % ts)
        type = gdb.lookup_type(ts)
    except RuntimeError as error:
        #warn("LOOKING UP '%s': %s" % (ts, error))
        # See http://sourceware.org/bugzilla/show_bug.cgi?id=11912
        exp = "(class '%s'*)0" % ts
        try:
            type = parseAndEvaluate(exp).type.target()
        except:
            # Can throw "RuntimeError: No type named class Foo."
            pass
    except:
        #warn("LOOKING UP '%s' FAILED" % ts)
        pass

    if not type is None:
        typeCache[typestring] = type
        typesToReport[typestring] = type
        return type

    # This could still be None as gdb.lookup_type("char[3]") generates
    # "RuntimeError: No type named char[3]"
    typeCache[typestring] = type
    typesToReport[typestring] = type
    return type

def extractTemplateArgument(type, position):
    level = 0
    skipSpace = False
    inner = ""
    type = str(type)
    for c in type[type.find('<') + 1 : -1]:
        if c == '<':
            inner += c
            level += 1
        elif c == '>':
            level -= 1
            inner += c
        elif c == ',':
            if level == 0:
                if position == 0:
                    return inner
                position -= 1
                inner = ""
            else:
                inner += c
                skipSpace = True
        else:
            if skipSpace and c == ' ':
                pass
            else:
                inner += c
                skipSpace = False
    return inner

def templateArgument(type, position):
    try:
        # This fails on stock 7.2 with
        # "RuntimeError: No type named myns::QObject.\n"
        return type.template_argument(position)
    except:
        # That's something like "myns::QList<...>"
        return lookupType(extractTemplateArgument(type.strip_typedefs(), position))


# Workaround for gdb < 7.1
def numericTemplateArgument(type, position):
    try:
        return int(type.template_argument(position))
    except RuntimeError as error:
        # ": No type named 30."
        msg = str(error)
        msg = msg[14:-1]
        # gdb at least until 7.4 produces for std::array<int, 4u>
        # for template_argument(1): RuntimeError: No type named 4u.
        if msg[-1] == 'u':
           msg = msg[0:-1]
        return int(msg)


class OutputSafer:
    def __init__(self, d):
        self.d = d

    def __enter__(self):
        self.savedOutput = self.d.output
        self.d.output = []

    def __exit__(self, exType, exValue, exTraceBack):
        if self.d.passExceptions and not exType is None:
            showException("OUTPUTSAFER", exType, exValue, exTraceBack)
            self.d.output = self.savedOutput
        else:
            self.savedOutput.extend(self.d.output)
            self.d.output = self.savedOutput
        return False



def value(expr):
    value = parseAndEvaluate(expr)
    try:
        return int(value)
    except:
        return str(value)


#def couldBePointer(p, align):
#    type = lookupType("unsigned int")
#    ptr = gdb.Value(p).cast(type)
#    d = int(str(ptr))
#    warn("CHECKING : %s %d " % (p, ((d & 3) == 0 and (d > 1000 or d == 0))))
#    return (d & (align - 1)) and (d > 1000 or d == 0)


Value = gdb.Value


qqNs = None

def qtNamespace():
    # FIXME: This only works when call from inside a Qt function frame.
    global qqNs
    if not qqNs is None:
        return qqNs
    try:
        str = gdb.execute("ptype QString::Null", to_string=True)
        # The result looks like:
        # "type = const struct myns::QString::Null {"
        # "    <no data fields>"
        # "}"
        pos1 = str.find("struct") + 7
        pos2 = str.find("QString::Null")
        if pos1 > -1 and pos2 > -1:
            qqNs = str[pos1:pos2]
            return qqNs
        return ""
    except:
        return ""

def stripTypedefs(type):
    type = type.unqualified()
    while type.code == TypedefCode:
        type = type.strip_typedefs().unqualified()
    return type


#######################################################################
#
# LocalItem
#
#######################################################################

# Contains iname, name, and value.
class LocalItem:
    pass


#######################################################################
#
# Edit Command
#
#######################################################################

def bbedit(args):
    global qqEditable
    (type, expr, value) = args.split(",")
    type = b16decode(type)
    ns = qtNamespace()
    if type.startswith(ns):
        type = type[len(ns):]
    type = type.replace("::", "__")
    pos = type.find('<')
    if pos != -1:
        type = type[0:pos]
    expr = b16decode(expr)
    value = b16decode(value)
    #warn("EDIT: %s %s %s %s: " % (pos, type, expr, value))
    if qqEditable.has_key(type):
        qqEditable[type](expr, value)
    else:
        gdb.execute("set (%s)=%s" % (expr, value))

registerCommand("bbedit", bbedit)


#######################################################################
#
# Frame Command
#
#######################################################################

def bb(args):
    global typesToReport
    output = Dumper(args).output
    output.append('],typeinfo=[')
    for name in typesToReport.keys():
        type = typesToReport[name]
        # Happens e.g. for '(anonymous namespace)::InsertDefOperation'
        if not type is None:
            output.append('{name="%s",size="%s"}'
                % (b64encode(name), type.sizeof))
    output.append(']')
    typesToReport = {}
    return "".join(output)


def p1(args):
    import cProfile
    cProfile.run('bb("%s")' % args, "/tmp/bbprof")
    import pstats
    pstats.Stats('/tmp/bbprof').sort_stats('time').print_stats()
    return ""


def p2(args):
    import timeit
    return timeit.repeat('bb("%s")' % args,
        'from __main__ import bb', number=10)

registerCommand("bb", bb)
registerCommand("p1", p1)
registerCommand("p2", p2)

def extractQtVersion():
    version = str(gdb.parse_and_eval("qVersion()"))
    (major, minor, patch) = version[version.find('"')+1:version.rfind('"')].split('.')
    return 0x10000 * int(major) + 0x100 * int(minor) + int(patch)


#######################################################################
#
# The Dumper Class
#
#######################################################################


class Dumper(DumperBase):

    def __init__(self, args):
        DumperBase.__init__(self)

        self.isGdb = True
        self.output = []
        self.currentIName = ""
        self.currentPrintsAddress = True
        self.currentChildType = ""
        self.currentChildNumChild = -1
        self.currentMaxNumChild = -1
        self.currentNumChild = -1
        self.currentValue = None
        self.currentValuePriority = -100
        self.currentValueEncoding = None
        self.currentType = None
        self.currentTypePriority = -100
        self.currentAddress = None
        self.typeformats = {}
        self.formats = {}
        self.useDynamicType = True
        self.expandedINames = {}
        self.childEventAddress = None
        self.cachedQtVersion = None

        watchers = ""
        resultVarName = ""
        options = []
        varList = []

        self.output.append('data=[')
        for arg in args.split(' '):
            pos = arg.find(":") + 1
            if arg.startswith("options:"):
                options = arg[pos:].split(",")
            elif arg.startswith("vars:"):
                if len(arg[pos:]) > 0:
                    varList = arg[pos:].split(",")
            elif arg.startswith("resultvarname:"):
                resultVarName = arg[pos:]
            elif arg.startswith("expanded:"):
                self.expandedINames = set(arg[pos:].split(","))
            elif arg.startswith("typeformats:"):
                for f in arg[pos:].split(","):
                    pos = f.find("=")
                    if pos != -1:
                        type = b16decode(f[0:pos])
                        self.typeformats[type] = int(f[pos+1:])
            elif arg.startswith("formats:"):
                for f in arg[pos:].split(","):
                    pos = f.find("=")
                    if pos != -1:
                        self.formats[f[0:pos]] = int(f[pos+1:])
            elif arg.startswith("watchers:"):
                watchers = b16decode(arg[pos:])

        self.useDynamicType = "dyntype" in options
        self.useFancy = "fancy" in options
        self.passExceptions = "pe" in options
        #self.passExceptions = True
        self.autoDerefPointers = "autoderef" in options
        self.partialUpdate = "partial" in options
        self.tooltipOnly = "tooltiponly" in options
        self.noLocals = "nolocals" in options
        self.ns = qtNamespace()

        #warn("NAMESPACE: '%s'" % self.ns)
        #warn("VARIABLES: %s" % varList)
        #warn("EXPANDED INAMES: %s" % self.expandedINames)
        #warn("WATCHERS: %s" % watchers)
        #warn("PARTIAL: %s" % self.partialUpdate)
        #warn("NO LOCALS: %s" % self.noLocals)
        module = sys.modules[__name__]

        #
        # Locals
        #
        locals = []
        fullUpdateNeeded = True
        if self.partialUpdate and len(varList) == 1 and not self.tooltipOnly:
            #warn("PARTIAL: %s" % varList)
            parts = varList[0].split('.')
            #warn("PARTIAL PARTS: %s" % parts)
            name = parts[1]
            #warn("PARTIAL VAR: %s" % name)
            #fullUpdateNeeded = False
            try:
                frame = gdb.selected_frame()
                item = LocalItem()
                item.iname = "local." + name
                item.name = name
                item.value = frame.read_var(name)
                locals = [item]
                #warn("PARTIAL LOCALS: %s" % locals)
                fullUpdateNeeded = False
            except:
                pass
            varList = []

        if fullUpdateNeeded and not self.tooltipOnly and not self.noLocals:
            locals = listOfLocals(varList)

        # Take care of the return value of the last function call.
        if len(resultVarName) > 0:
            try:
                item = LocalItem()
                item.name = resultVarName
                item.iname = "return." + resultVarName
                item.value = self.parseAndEvaluate(resultVarName)
                locals.append(item)
            except:
                # Don't bother. It's only supplementary information anyway.
                pass

        for item in locals:
            value = downcast(item.value) if self.useDynamicType else item.value
            with OutputSafer(self):
                self.anonNumber = -1

                type = value.type.unqualified()
                typeName = str(type)

                # Special handling for char** argv.
                if type.code == PointerCode \
                        and item.iname == "local.argv" \
                        and typeName == "char **":
                    n = 0
                    p = value
                    # p is 0 for "optimized out" cases. Or contains rubbish.
                    try:
                        if not self.isNull(p):
                            while not self.isNull(p.dereference()) and n <= 100:
                                p += 1
                                n += 1
                    except:
                        pass

                    with TopLevelItem(self, item.iname):
                        self.put('iname="local.argv",name="argv",')
                        self.putItemCount(n, 100)
                        self.putType(typeName)
                        self.putNumChild(n)
                        if self.currentIName in self.expandedINames:
                            p = value
                            with Children(self, n):
                                for i in xrange(n):
                                    self.putSubItem(i, p.dereference())
                                    p += 1
                    continue

                else:
                    # A "normal" local variable or parameter.
                    with TopLevelItem(self, item.iname):
                        self.put('iname="%s",' % item.iname)
                        self.put('name="%s",' % item.name)
                        self.putItem(value)

        #
        # Watchers
        #
        with OutputSafer(self):
            if len(watchers) > 0:
                self.put(",")
                for watcher in watchers.split("##"):
                    (exp, iname) = watcher.split("#")
                    self.handleWatch(exp, iname)

        #print('data=[' + locals + sep + watchers + ']\n')


    def enterSubItem(self, item):
        if not item.iname:
            item.iname = "%s.%s" % (self.currentIName, item.name)
        #warn("INAME %s" % item.iname)
        self.put('{')
        #if not item.name is None:
        if isinstance(item.name, str):
            self.put('name="%s",' % item.name)
        item.savedIName = self.currentIName
        item.savedValue = self.currentValue
        item.savedValuePriority = self.currentValuePriority
        item.savedValueEncoding = self.currentValueEncoding
        item.savedType = self.currentType
        item.savedTypePriority = self.currentTypePriority
        item.savedCurrentAddress = self.currentAddress
        self.currentIName = item.iname
        self.currentValuePriority = -100
        self.currentValueEncoding = None
        self.currentType = ""
        self.currentTypePriority = -100
        self.currentAddress = None

    def exitSubItem(self, item, exType, exValue, exTraceBack):
        #warn(" CURRENT VALUE: %s %s %s" % (self.currentValue,
        #    self.currentValueEncoding, self.currentValuePriority))
        if not exType is None:
            if self.passExceptions:
                showException("SUBITEM", exType, exValue, exTraceBack)
            self.putNumChild(0)
            self.putValue("<not accessible>")
        try:
            #warn("TYPE VALUE: %s" % self.currentValue)
            typeName = stripClassTag(self.currentType)
            #warn("TYPE: '%s'  DEFAULT: '%s' % (typeName, self.currentChildType))

            if len(typeName) > 0 and typeName != self.currentChildType:
                self.put('type="%s",' % typeName) # str(type.unqualified()) ?
            if  self.currentValue is None:
                self.put('value="<not accessible>",numchild="0",')
            else:
                if not self.currentValueEncoding is None:
                    self.put('valueencoded="%d",' % self.currentValueEncoding)
                self.put('value="%s",' % self.currentValue)
        except:
            pass
        if not self.currentAddress is None:
            self.put(self.currentAddress)
        self.put('},')
        self.currentIName = item.savedIName
        self.currentValue = item.savedValue
        self.currentValuePriority = item.savedValuePriority
        self.currentValueEncoding = item.savedValueEncoding
        self.currentType = item.savedType
        self.currentTypePriority = item.savedTypePriority
        self.currentAddress = item.savedCurrentAddress
        return True

    def parseAndEvaluate(self, exp):
        return gdb.parse_and_eval(exp)

    def call2(self, value, func, args):
        # args is a tuple.
        arg = ""
        for i in range(len(args)):
            if i:
                arg += ','
            a = args[i]
            if (':' in a) and not ("'" in a):
                arg = "'%s'" % a
            else:
                arg += a

        #warn("CALL: %s -> %s(%s)" % (value, func, arg))
        type = stripClassTag(str(value.type))
        if type.find(":") >= 0:
            type = "'" + type + "'"
        # 'class' is needed, see http://sourceware.org/bugzilla/show_bug.cgi?id=11912
        exp = "((class %s*)%s)->%s(%s)" % (type, value.address, func, arg)
        #warn("CALL: %s" % exp)
        result = None
        try:
            result = self.parseAndEvaluate(exp)
        except:
            pass
        #warn("  -> %s" % result)
        return result

    def call(self, value, func, *args):
        return self.call2(value, func, args)

    def makeValue(self, type, init):
        type = "::" + stripClassTag(str(type));
        # Avoid malloc symbol clash with QVector.
        gdb.execute("set $d = (%s*)calloc(sizeof(%s), 1)" % (type, type))
        gdb.execute("set *$d = {%s}" % init)
        value = parseAndEvaluate("$d").dereference()
        #warn("  TYPE: %s" % value.type)
        #warn("  ADDR: %s" % value.address)
        #warn("  VALUE: %s" % value)
        return value

    def makeExpression(self, value):
        type = "::" + stripClassTag(str(value.type))
        #warn("  TYPE: %s" % type)
        #exp = "(*(%s*)(&%s))" % (type, value.address)
        exp = "(*(%s*)(%s))" % (type, value.address)
        #warn("  EXP: %s" % exp)
        return exp

    def makeStdString(init):
        # Works only for small allocators, but they are usually empty.
        gdb.execute("set $d=(std::string*)calloc(sizeof(std::string), 2)");
        gdb.execute("call($d->basic_string(\"" + init +
            "\",*(std::allocator<char>*)(1+$d)))")
        value = parseAndEvaluate("$d").dereference()
        #warn("  TYPE: %s" % value.type)
        #warn("  ADDR: %s" % value.address)
        #warn("  VALUE: %s" % value)
        return value

    def childAt(self, value, index):
        field = value.type.fields()[index]
        if len(field.name):
            return value[field.name]
        # FIXME: Cheat. There seems to be no official way to access
        # the real item, so we pass back the value. That at least
        # enables later ...["name"] style accesses as gdb handles
        # them transparently.
        return value

    def fieldAt(self, type, index):
        return type.fields()[index]

    def directBaseClass(self, typeobj, index = 0):
        # FIXME: Check it's really a base.
        return typeobj.fields()[index]

    def checkPointer(self, p, align = 1):
        if not self.isNull(p):
            p.dereference()

    def pointerValue(self, p):
        return toInteger(p)

    def isNull(self, p):
        # The following can cause evaluation to abort with "UnicodeEncodeError"
        # for invalid char *, as their "contents" is being examined
        #s = str(p)
        #return s == "0x0" or s.startswith("0x0 ")
        #try:
        #    # Can fail with: "RuntimeError: Cannot access memory at address 0x5"
        #    return p.cast(self.lookupType("void").pointer()) == 0
        #except:
        #    return False
        try:
            # Can fail with: "RuntimeError: Cannot access memory at address 0x5"
            return toInteger(p) == 0
        except:
            return False

    def templateArgument(self, typeobj, position):
        return templateArgument(typeobj, position)

    def numericTemplateArgument(self, typeobj, position):
        return numericTemplateArgument(typeobj, position)

    def lookupType(self, typeName):
        return lookupType(typeName)

    def handleWatch(self, exp, iname):
        exp = str(exp)
        escapedExp = b64encode(exp);
        #warn("HANDLING WATCH %s, INAME: '%s'" % (exp, iname))
        if exp.startswith("[") and exp.endswith("]"):
            #warn("EVAL: EXP: %s" % exp)
            with TopLevelItem(self, iname):
                self.put('iname="%s",' % iname)
                self.put('wname="%s",' % escapedExp)
                try:
                    list = eval(exp)
                    self.putValue("")
                    self.putNoType()
                    self.putNumChild(len(list))
                    # This is a list of expressions to evaluate
                    with Children(self, len(list)):
                        itemNumber = 0
                        for item in list:
                            self.handleWatch(item, "%s.%d" % (iname, itemNumber))
                            itemNumber += 1
                except RuntimeError as error:
                    warn("EVAL: ERROR CAUGHT %s" % error)
                    self.putValue("<syntax error>")
                    self.putNoType()
                    self.putNumChild(0)
                    self.put("children=[],")
            return

        with TopLevelItem(self, iname):
            self.put('iname="%s",' % iname)
            self.put('wname="%s",' % escapedExp)
            if len(exp) == 0: # The <Edit> case
                self.putValue(" ")
                self.putNoType()
                self.putNumChild(0)
            else:
                try:
                    value = self.parseAndEvaluate(exp)
                    self.putItem(value)
                except RuntimeError:
                    self.currentType = " "
                    self.currentValue = "<no such value>"
                    self.currentChildNumChild = -1
                    self.currentNumChild = 0
                    self.putNumChild(0)

    def intType(self):
        return self.lookupType('int')

    def charType(self):
        return self.lookupType('char')

    def sizetType(self):
        return self.lookupType('size_t')

    def charPtrType(self):
        return self.lookupType('char*')

    def intPtrType(self):
        return self.lookupType('int*')

    def voidPtrType(self):
        return self.lookupType('void*')

    def addressOf(self, value):
        return toInteger(value.address)

    def createPointerValue(self, address, pointeeType):
        # This might not always work:
        # a Python 3 based GDB due to the bug addressed in
        # https://sourceware.org/ml/gdb-patches/2013-09/msg00571.html
        try:
            return gdb.Value(address).cast(pointeeType.pointer())
        except:
            # Try _some_ fallback (good enough for the std::complex dumper)
            return gdb.parse_and_eval("(%s*)%s" % (pointeeType, address))

    def intSize(self):
        return 4

    def ptrSize(self):
        return self.lookupType('void*').sizeof

    def createValue(self, address, referencedType):
        try:
            return gdb.Value(address).cast(referencedType.pointer()).dereference()
        except:
            # Try _some_ fallback (good enough for the std::complex dumper)
            return gdb.parse_and_eval("{%s}%s" % (referencedType, address))

    def readRawMemory(self, addr, size):
        mem = gdb.selected_inferior().read_memory(addr, size)
        if sys.version_info[0] >= 3:
            mem.tobytes()
        return mem

    # FIXME: The commented out versions do not work with
    # a Python 3 based GDB due to the bug addressed in
    # https://sourceware.org/ml/gdb-patches/2013-09/msg00571.html
    def dereference(self, addr):
        #return long(gdb.Value(addr).cast(self.voidPtrType().pointer()).dereference())
        return struct.unpack("P", self.readRawMemory(addr, self.ptrSize()))[0]

    def extractInt64(self, addr):
        return struct.unpack("q", self.readRawMemory(addr, 8))[0]

    def extractInt(self, addr):
        #return long(gdb.Value(addr).cast(self.intPtrType()).dereference())
        return struct.unpack("i", self.readRawMemory(addr, 4))[0]

    def extractByte(self, addr):
        #return long(gdb.Value(addr).cast(self.charPtrType()).dereference()) & 0xFF
        return struct.unpack("b", self.readRawMemory(addr, 1))[0]

    # Do not use value.address here as this might not have one,
    # i.e. be the result of an inferior call
    def dereferenceValue(self, value):
        return toInteger(value.cast(self.voidPtrType()))

    def isQObject(self, value):
        try:
        #if True:
            vtable = self.dereference(toInteger(value.address)) # + ptrSize
            metaObjectEntry = self.dereference(vtable) # It's the first entry.
            #warn("MO: 0x%x " % metaObjectEntry)
            s = gdb.execute("info symbol 0x%x" % metaObjectEntry, to_string=True)
            #warn("S: %s " % s)
            #return s.find("::metaObject() const") > 0
            return s.find("::metaObject() const") > 0 or s.find("10metaObjectEv") > 0
            #return str(metaObjectEntry).find("::metaObject() const") > 0
        except:
            return False

    def isQObject_B(self, value):
        # Alternative: Check for specific values, like targeting the
        # 'childEvent' member which is typically not overwritten, slot 8.
        # ~"Symbol \"Myns::QObject::childEvent(Myns::QChildEvent*)\" is a
        #  function at address 0xb70f691a.\n"
        if self.childEventAddress == None:
            try:
                loc = gdb.execute("info address ::QObject::childEvent", to_string=True)
                self.childEventAddress = toInteger(loc[loc.rfind(' '):-2], 16)
            except:
                self.childEventAddress = 0

        try:
            vtable = self.dereference(toInteger(value.address))
            return self.childEventAddress == self.dereference(vtable + 8 * self.ptrSize())
        except:
            return False

    def put(self, value):
        self.output.append(value)

    def putField(self, name, value):
        self.put('%s="%s",' % (name, value))

    def childRange(self):
        if self.currentMaxNumChild is None:
            return xrange(0, toInteger(self.currentNumChild))
        return xrange(min(toInteger(self.currentMaxNumChild), toInteger(self.currentNumChild)))

    def qtVersion(self):
        if self.cachedQtVersion is None:
            try:
                self.cachedQtVersion = extractQtVersion()
            except:
                try:
                    # This will fail on Qt 5
                    gdb.execute("ptype QString::shared_empty", to_string=True)
                    self.cachedQtVersion = 0x040800
                except:
                    self.cachedQtVersion = 0x050000
        return self.cachedQtVersion

    # Convenience function.
    def putItemCount(self, count, maximum = 1000000000):
        # This needs to override the default value, so don't use 'put' directly.
        if count > maximum:
            self.putValue('<>%s items>' % maximum)
        else:
            self.putValue('<%s items>' % count)

    def putType(self, type, priority = 0):
        # Higher priority values override lower ones.
        if priority >= self.currentTypePriority:
            self.currentType = str(type)
            self.currentTypePriority = priority

    def putNoType(self):
        # FIXME: replace with something that does not need special handling
        # in SubItem.__exit__().
        self.putBetterType(" ")

    def putInaccessible(self):
        #self.putBetterType(" ")
        self.putNumChild(0)
        self.currentValue = None

    def putBetterType(self, type):
        self.currentType = str(type)
        self.currentTypePriority = self.currentTypePriority + 1

    def putAddress(self, addr):
        if self.currentPrintsAddress:
            try:
                # addr can be "None", int(None) fails.
                #self.put('addr="0x%x",' % int(addr))
                self.currentAddress = 'addr="0x%x",' % toInteger(addr)
            except:
                pass

    def putNumChild(self, numchild):
        #warn("NUM CHILD: '%s' '%s'" % (numchild, self.currentChildNumChild))
        if numchild != self.currentChildNumChild:
            self.put('numchild="%s",' % numchild)

    def putEmptyValue(self, priority = -10):
        if priority >= self.currentValuePriority:
            self.currentValue = ""
            self.currentValuePriority = priority
            self.currentValueEncoding = None

    def putSimpleValue(self, value, encoding = None, priority = 0):
        self.putValue(value, encoding, priority)

    def putValue(self, value, encoding = None, priority = 0):
        # Higher priority values override lower ones.
        if priority >= self.currentValuePriority:
            self.currentValue = value
            self.currentValuePriority = priority
            self.currentValueEncoding = encoding

    def putPointerValue(self, value):
        # Use a lower priority
        if value is None:
            self.putEmptyValue(-1)
        else:
            self.putValue("0x%x" % value.cast(
                self.lookupType("unsigned long")), None, -1)

    def putDisplay(self, format, value = None, cmd = None):
        self.put('editformat="%s",' % format)
        if cmd is None:
            if not value is None:
                self.put('editvalue="%s",' % value)
        else:
            self.put('editvalue="%s|%s",' % (cmd, value))

    def putName(self, name):
        self.put('name="%s",' % name)

    def isExpanded(self):
        #warn("IS EXPANDED: %s in %s: %s" % (self.currentIName,
        #    self.expandedINames, self.currentIName in self.expandedINames))
        return self.currentIName in self.expandedINames

    def isExpandedSubItem(self, component):
        iname = "%s.%s" % (self.currentIName, component)
        #warn("IS EXPANDED: %s in %s" % (iname, self.expandedINames))
        return iname in self.expandedINames

    def stripNamespaceFromType(self, typeName):
        type = stripClassTag(typeName)
        if len(self.ns) > 0 and type.startswith(self.ns):
            type = type[len(self.ns):]
        pos = type.find("<")
        # FIXME: make it recognize  foo<A>::bar<B>::iterator?
        while pos != -1:
            pos1 = type.rfind(">", pos)
            type = type[0:pos] + type[pos1+1:]
            pos = type.find("<")
        return type

    def isMovableType(self, type):
        if type.code == PointerCode:
            return True
        if self.isSimpleType(type):
            return True
        return self.isKnownMovableType(self.stripNamespaceFromType(str(type)))

    def putIntItem(self, name, value):
        with SubItem(self, name):
            self.putValue(value)
            self.putType("int")
            self.putNumChild(0)

    def putBoolItem(self, name, value):
        with SubItem(self, name):
            self.putValue(value)
            self.putType("bool")
            self.putNumChild(0)

    def putGenericItem(self, name, type, value, encoding = None):
        with SubItem(self, name):
            self.putValue(value, encoding)
            self.putType(type)
            self.putNumChild(0)

    def currentItemFormat(self):
        format = self.formats.get(self.currentIName)
        if format is None:
            format = self.typeformats.get(stripForFormat(str(self.currentType)))
        return format

    def putSubItem(self, component, value, tryDynamic=True):
        with SubItem(self, component):
            self.putItem(value, tryDynamic)

    def putNamedSubItem(self, component, value, name):
        with SubItem(self, component):
            self.putName(name)
            self.putItem(value)

    def isSimpleType(self, typeobj):
        code = typeobj.code
        return code == BoolCode \
            or code == CharCode \
            or code == IntCode \
            or code == FloatCode \
            or code == EnumCode

    def simpleEncoding(self, typeobj):
        code = typeobj.code
        if code == BoolCode or code == CharCode:
            return Hex2EncodedInt1
        if code == IntCode:
            if str(typeobj).find("unsigned") >= 0:
                if typeobj.sizeof == 1:
                    return Hex2EncodedUInt1
                if typeobj.sizeof == 2:
                    return Hex2EncodedUInt2
                if typeobj.sizeof == 4:
                    return Hex2EncodedUInt4
                if typeobj.sizeof == 8:
                    return Hex2EncodedUInt8
            else:
                if typeobj.sizeof == 1:
                    return Hex2EncodedInt1
                if typeobj.sizeof == 2:
                    return Hex2EncodedInt2
                if typeobj.sizeof == 4:
                    return Hex2EncodedInt4
                if typeobj.sizeof == 8:
                    return Hex2EncodedInt8
        if code == FloatCode:
            if typeobj.sizeof == 4:
                return Hex2EncodedFloat4
            if typeobj.sizeof == 8:
                return Hex2EncodedFloat8
        return None

    def tryPutArrayContents(self, typeobj, base, n):
        enc = self.simpleEncoding(typeobj)
        if not enc:
            return False
        size = n * typeobj.sizeof;
        self.put('childtype="%s",' % typeobj)
        self.put('addrbase="0x%x",' % toInteger(base))
        self.put('addrstep="0x%x",' % toInteger(typeobj.sizeof))
        self.put('arrayencoding="%s",' % enc)
        self.put('arraydata="')
        self.put(self.readMemory(base, size))
        self.put('",')
        return True

    def isReferenceType(self, typeobj):
        return typeobj.code == gdb.TYPE_CODE_REF

    def isStructType(self, typeobj):
        return typeobj.code == gdb.TYPE_CODE_STRUCT

    def putPlotData(self, type, base, n, plotFormat):
        if self.isExpanded():
            self.putArrayData(type, base, n)
        if not hasPlot():
            return
        if not self.isSimpleType(type):
            #self.putValue(self.currentValue + " (not plottable)")
            self.putValue(self.currentValue)
            self.putField("plottable", "0")
            return
        global gnuplotPipe
        global gnuplotPid
        format = self.currentItemFormat()
        iname = self.currentIName
        #if False:
        if format != plotFormat:
            if iname in gnuplotPipe:
                os.kill(gnuplotPid[iname], 9)
                del gnuplotPid[iname]
                gnuplotPipe[iname].terminate()
                del gnuplotPipe[iname]
            return
        base = base.cast(type.pointer())
        if not iname in gnuplotPipe:
            gnuplotPipe[iname] = subprocess.Popen(["gnuplot"],
                    stdin=subprocess.PIPE)
            gnuplotPid[iname] = gnuplotPipe[iname].pid
        f = gnuplotPipe[iname].stdin;
        # On Ubuntu install gnuplot-x11
        f.write("set term wxt noraise\n")
        f.write("set title 'Data fields'\n")
        f.write("set xlabel 'Index'\n")
        f.write("set ylabel 'Value'\n")
        f.write("set grid\n")
        f.write("set style data lines;\n")
        f.write("plot  '-' title '%s'\n" % iname)
        for i in range(1, n):
            f.write(" %s\n" % base.dereference())
            base += 1
        f.write("e\n")


    def putArrayData(self, type, base, n,
            childNumChild = None, maxNumChild = 10000):
        if not self.tryPutArrayContents(type, base, n):
            base = base.cast(type.pointer())
            with Children(self, n, type, childNumChild, maxNumChild,
                    base, type.sizeof):
                for i in self.childRange():
                    self.putSubItem(i, (base + i).dereference())

    def putCallItem(self, name, value, func, *args):
        result = self.call2(value, func, args)
        with SubItem(self, name):
            self.putItem(result)

    def putItem(self, value, tryDynamic=True):
        if value is None:
            # Happens for non-available watchers in gdb versions that
            # need to use gdb.execute instead of gdb.parse_and_eval
            self.putValue("<not available>")
            self.putType("<unknown>")
            self.putNumChild(0)
            return

        global qqDumpers, qqFormats

        type = value.type.unqualified()
        typeName = str(type)
        tryDynamic &= self.useDynamicType
        addToCache(type) # Fill type cache
        if tryDynamic:
            self.putAddress(value.address)

        # FIXME: Gui shows references stripped?
        #warn(" ")
        #warn("REAL INAME: %s " % self.currentIName)
        #warn("REAL TYPE: %s " % value.type)
        #warn("REAL CODE: %s " % value.type.code)
        #warn("REAL VALUE: %s " % value)

        if type.code == ReferenceCode:
            try:
                # Try to recognize null references explicitly.
                if toInteger(value.address) == 0:
                    self.putValue("<null reference>")
                    self.putType(typeName)
                    self.putNumChild(0)
                    return
            except:
                pass

            if tryDynamic:
                try:
                    # Dynamic references are not supported by gdb, see
                    # http://sourceware.org/bugzilla/show_bug.cgi?id=14077.
                    # Find the dynamic type manually using referenced_type.
                    value = value.referenced_value()
                    value = value.cast(value.dynamic_type)
                    self.putItem(value)
                    self.putBetterType("%s &" % value.type)
                    return
                except:
                    pass

            try:
                # FIXME: This throws "RuntimeError: Attempt to dereference a
                # generic pointer." with MinGW's gcc 4.5 when it "identifies"
                # a "QWidget &" as "void &" and with optimized out code.
                self.putItem(value.cast(type.target().unqualified()))
                self.putBetterType(typeName)
                return
            except RuntimeError:
                self.putValue("<optimized out reference>")
                self.putType(typeName)
                self.putNumChild(0)
                return

        if type.code == IntCode or type.code == CharCode:
            self.putType(typeName)
            if value.is_optimized_out:
                self.putValue("<optimized out>")
            else:
                self.putValue(value)
            self.putNumChild(0)
            return

        if type.code == FloatCode or type.code == BoolCode:
            self.putType(typeName)
            if value.is_optimized_out:
                self.putValue("<optimized out>")
            else:
                self.putValue(value)
            self.putNumChild(0)
            return

        if type.code == EnumCode:
            self.putType(typeName)
            if value.is_optimized_out:
                self.putValue("<optimized out>")
            else:
                self.putValue("%s (%d)" % (value, value))
            self.putNumChild(0)
            return

        if type.code == ComplexCode:
            self.putType(typeName)
            if value.is_optimized_out:
                self.putValue("<optimized out>")
            else:
                self.putValue("%s" % value)
            self.putNumChild(0)
            return

        if type.code == TypedefCode:
            if typeName in qqDumpers:
                self.putType(typeName)
                qqDumpers[typeName](self, value)
                return

            type = stripTypedefs(type)
            # The cast can destroy the address?
            #self.putAddress(value.address)
            # Workaround for http://sourceware.org/bugzilla/show_bug.cgi?id=13380
            if type.code == ArrayCode:
                value = self.parseAndEvaluate("{%s}%s" % (type, value.address))
            else:
                try:
                    value = value.cast(type)
                except:
                    self.putValue("<optimized out typedef>")
                    self.putType(typeName)
                    self.putNumChild(0)
                    return

            self.putItem(value)
            self.putBetterType(typeName)
            return

        if type.code == ArrayCode:
            qdump____c_style_array__(self, value)
            return

        if type.code == PointerCode:
            #warn("POINTER: %s" % value)

            # This could still be stored in a register and
            # potentially dereferencable.
            if value.is_optimized_out:
                self.putValue("<optimized out>")

            try:
                value.dereference()
            except:
                # Failure to dereference a pointer should at least
                # show the value of a pointer.
                self.putValue(cleanAddress(value))
                self.putType(typeName)
                self.putNumChild(0)
                return

            if self.isNull(value):
                #warn("NULL POINTER")
                self.putType(typeName)
                self.putValue("0x0")
                self.putNumChild(0)
                return

            innerType = type.target()
            innerTypeName = str(innerType.unqualified())
            format = self.formats.get(self.currentIName)
            if format is None:
                format = self.typeformats.get(stripForFormat(str(type)))

            if innerType.code == VoidCode:
                #warn("VOID POINTER: %s" % format)
                self.putType(typeName)
                self.putValue(str(value))
                self.putNumChild(0)
                return

            if format == None and innerTypeName == "char":
                # Use Latin1 as default for char *.
                self.putType(typeName)
                self.putValue(self.encodeCharArray(value), Hex2EncodedLatin1)
                self.putNumChild(0)
                return

            if format == 0:
                # Explicitly requested bald pointer.
                self.putType(typeName)
                self.putPointerValue(value)
                self.putNumChild(1)
                if self.currentIName in self.expandedINames:
                    with Children(self):
                        with SubItem(self, '*'):
                            self.putItem(value.dereference())
                return

            if format == 1:
                # Explicitly requested Latin1 formatting.
                self.putType(typeName)
                self.putValue(self.encodeCharArray(value), Hex2EncodedLatin1)
                self.putNumChild(0)
                return

            if format == 2:
                # Explicitly requested UTF-8 formatting.
                self.putType(typeName)
                self.putValue(self.encodeCharArray(value), Hex2EncodedUtf8)
                self.putNumChild(0)
                return

            if format == 3:
                # Explicitly requested local 8 bit formatting.
                self.putType(typeName)
                self.putValue(self.encodeCharArray(value), Hex2EncodedLocal8Bit)
                self.putNumChild(0)
                return

            if format == 4:
                # Explicitly requested UTF-16 formatting.
                self.putType(typeName)
                self.putValue(self.encodeChar2Array(value), Hex4EncodedLittleEndian)
                self.putNumChild(0)
                return

            if format == 5:
                # Explicitly requested UCS-4 formatting.
                self.putType(typeName)
                self.putValue(self.encodeChar4Array(value), Hex8EncodedLittleEndian)
                self.putNumChild(0)
                return

            if format == 6:
                # Explicitly requested formatting as array of 10 items.
                self.putType(typeName)
                self.putItemCount(10)
                self.putNumChild(10)
                self.putArrayData(innerType, value, 10)
                return

            if format == 7:
                # Explicitly requested formatting as array of 1000 items.
                self.putType(typeName)
                self.putItemCount(1000)
                self.putNumChild(1000)
                self.putArrayData(innerType, value, 1000)
                return

            if innerType.code == MethodCode or innerType.code == FunctionCode:
                # A function pointer with format None.
                self.putValue(str(value))
                self.putType(typeName)
                self.putNumChild(0)
                return

            #warn("AUTODEREF: %s" % self.autoDerefPointers)
            #warn("INAME: %s" % self.currentIName)
            if self.autoDerefPointers or self.currentIName.endswith('.this'):
                ## Generic pointer type with format None
                #warn("GENERIC AUTODEREF POINTER: %s AT %s TO %s"
                #    % (type, value.address, innerTypeName))
                # Never dereference char types.
                if innerTypeName != "char" \
                        and innerTypeName != "signed char" \
                        and innerTypeName != "unsigned char"  \
                        and innerTypeName != "wchar_t":
                    self.putType(innerType)
                    savedCurrentChildType = self.currentChildType
                    self.currentChildType = stripClassTag(innerTypeName)
                    self.putItem(value.dereference())
                    self.currentChildType = savedCurrentChildType
                    #self.putPointerValue(value)
                    self.put('origaddr="%s",' % value.address)
                    return

            # Fall back to plain pointer printing.
            #warn("GENERIC PLAIN POINTER: %s" % value.type)
            #warn("ADDR PLAIN POINTER: %s" % value.address)
            self.putType(typeName)
            self.putField("aaa", "1")
            #self.put('addr="0x%x",' % toInteger(value.address))
            #self.putAddress(value.address)
            self.putField("bbb", "1")
            #self.putPointerValue(value)
            self.putValue("0x%x" % value.cast(self.lookupType("unsigned long")))
            self.putField("ccc", "1")
            self.putNumChild(1)
            if self.currentIName in self.expandedINames:
                with Children(self):
                    with SubItem(self, "*"):
                        self.putItem(value.dereference())
            return

        if type.code == MethodPointerCode \
                or type.code == MethodCode \
                or type.code == FunctionCode \
                or type.code == MemberPointerCode:
            self.putType(typeName)
            self.putValue(value)
            self.putNumChild(0)
            return

        if typeName.startswith("<anon"):
            # Anonymous union. We need a dummy name to distinguish
            # multiple anonymous unions in the struct.
            self.putType(type)
            self.putValue("{...}")
            self.anonNumber += 1
            with Children(self, 1):
                self.listAnonymous(value, "#%d" % self.anonNumber, type)
            return

        if type.code == StringCode:
            # FORTRAN strings
            size = type.sizeof
            data = self.readMemory(value.address, size)
            self.putValue(data, Hex2EncodedLatin1, 1)
            self.putType(type)

        if type.code != StructCode and type.code != UnionCode:
            warn("WRONG ASSUMPTION HERE: %s " % type.code)
            check(False)


        if tryDynamic:
            self.putItem(expensiveDowncast(value), False)
            return

        format = self.formats.get(self.currentIName)
        if format is None:
            format = self.typeformats.get(stripForFormat(typeName))

        if self.useFancy and (format is None or format >= 1):
            self.putType(typeName)

            nsStrippedType = self.stripNamespaceFromType(typeName)\
                .replace("::", "__")

            # The following block is only needed for D.
            if nsStrippedType.startswith("_A"):
                # DMD v2.058 encodes string[] as _Array_uns long long.
                # With spaces.
                if nsStrippedType.startswith("_Array_"):
                    qdump_Array(self, value)
                    return
                if nsStrippedType.startswith("_AArray_"):
                    qdump_AArray(self, value)
                    return

            #warn(" STRIPPED: %s" % nsStrippedType)
            #warn(" DUMPERS: %s" % qqDumpers)
            #warn(" DUMPERS: %s" % (nsStrippedType in qqDumpers))
            dumper = qqDumpers.get(nsStrippedType, None)
            if not dumper is None:
                if tryDynamic:
                    dumper(self, expensiveDowncast(value))
                else:
                    dumper(self, value)
                return

        # D arrays, gdc compiled.
        if typeName.endswith("[]"):
            n = value["length"]
            base = value["ptr"]
            self.putType(typeName)
            self.putItemCount(n)
            if self.isExpanded():
                self.putArrayData(base.type.target(), base, n)
            return

        #warn("GENERIC STRUCT: %s" % type)
        #warn("INAME: %s " % self.currentIName)
        #warn("INAMES: %s " % self.expandedINames)
        #warn("EXPANDED: %s " % (self.currentIName in self.expandedINames))
        if self.isQObject(value):
            self.putQObjectNameValue(value)  # Is this too expensive?
        self.putType(typeName)
        self.putEmptyValue()
        self.putNumChild(len(type.fields()))

        if self.currentIName in self.expandedINames:
            innerType = None
            with Children(self, 1, childType=innerType):
                self.putFields(value)

    def putPlainChildren(self, value):
        self.putEmptyValue(-99)
        self.putNumChild(1)
        if self.currentIName in self.expandedINames:
            with Children(self):
               self.putFields(value)

    def readMemory(self, base, size):
        inferior = selectedInferior()
        mem = inferior.read_memory(base, size)
        if sys.version_info[0] >= 3:
            return bytesToString(binascii.hexlify(mem.tobytes()))
        return binascii.hexlify(mem)

    def putFields(self, value, dumpBase = True):
            fields = value.type.fields()

            #warn("TYPE: %s" % type)
            #warn("FIELDS: %s" % fields)
            baseNumber = 0
            for field in fields:
                #warn("FIELD: %s" % field)
                #warn("  BITSIZE: %s" % field.bitsize)
                #warn("  ARTIFICIAL: %s" % field.artificial)

                if field.name is None:
                    type = stripTypedefs(value.type)
                    innerType = type.target()
                    p = value.cast(innerType.pointer())
                    for i in xrange(int(type.sizeof / innerType.sizeof)):
                        with SubItem(self, i):
                            self.putItem(p.dereference())
                        p = p + 1
                    continue

                # Ignore vtable pointers for virtual inheritance.
                if field.name.startswith("_vptr."):
                    with SubItem(self, "[vptr]"):
                        # int (**)(void)
                        n = 100
                        self.putType(" ")
                        self.putValue(value[field.name])
                        self.putNumChild(n)
                        if self.isExpanded():
                            with Children(self):
                                p = value[field.name]
                                for i in xrange(n):
                                    if toInteger(p.dereference()) != 0:
                                        with SubItem(self, i):
                                            self.putItem(p.dereference())
                                            self.putType(" ")
                                            p = p + 1
                    continue

                #warn("FIELD NAME: %s" % field.name)
                #warn("FIELD TYPE: %s" % field.type)
                if field.is_base_class:
                    # Field is base type. We cannot use field.name as part
                    # of the iname as it might contain spaces and other
                    # strange characters.
                    if dumpBase:
                        baseNumber += 1
                        with UnnamedSubItem(self, "@%d" % baseNumber):
                            self.put('iname="%s",' % self.currentIName)
                            self.put('name="[%s]",' % field.name)
                            self.putItem(value.cast(field.type), False)
                elif len(field.name) == 0:
                    # Anonymous union. We need a dummy name to distinguish
                    # multiple anonymous unions in the struct.
                    self.anonNumber += 1
                    self.listAnonymous(value, "#%d" % self.anonNumber,
                        field.type)
                else:
                    # Named field.
                    with SubItem(self, field.name):
                        #bitsize = getattr(field, "bitsize", None)
                        #if not bitsize is None:
                        #    self.put("bitsize=\"%s\"" % bitsize)
                        self.putItem(downcast(value[field.name]))


    def listAnonymous(self, value, name, type):
        for field in type.fields():
            #warn("FIELD NAME: %s" % field.name)
            if len(field.name) > 0:
                with SubItem(self, field.name):
                    self.putItem(value[field.name])
            else:
                # Further nested.
                self.anonNumber += 1
                name = "#%d" % self.anonNumber
                #iname = "%s.%s" % (selitem.iname, name)
                #child = SameItem(item.value, iname)
                with SubItem(self, name):
                    self.put('name="%s",' % name)
                    self.putEmptyValue()
                    fieldTypeName = str(field.type)
                    if fieldTypeName.endswith("<anonymous union>"):
                        self.putType("<anonymous union>")
                    elif fieldTypeName.endswith("<anonymous struct>"):
                        self.putType("<anonymous struct>")
                    else:
                        self.putType(fieldTypeName)
                    with Children(self, 1):
                        self.listAnonymous(value, name, field.type)

#######################################################################
#
# ThreadNames Command
#
#######################################################################

def threadname(arg):
    try:
        e = gdb.selected_frame()
    except:
        return
    d = Dumper("")
    out = ""
    maximalStackDepth = int(arg)
    ns = qtNamespace()
    while True:
        maximalStackDepth -= 1
        if maximalStackDepth < 0:
            break
        e = e.older()
        if e == None or e.name() == None:
            break
        if e.name() == ns + "QThreadPrivate::start" \
                or e.name() == "_ZN14QThreadPrivate5startEPv@4":
            try:
                thrptr = e.read_var("thr").dereference()
                obtype = d.lookupType(ns + "QObjectPrivate").pointer()
                d_ptr = thrptr["d_ptr"]["d"].cast(obtype).dereference()
                try:
                    objectName = d_ptr["objectName"]
                except: # Qt 5
                    p = d_ptr["extraData"]
                    if not d.isNull(p):
                        objectName = p.dereference()["objectName"]
                if not objectName is None:
                    data, size, alloc = d.stringData(objectName)
                    if size > 0:
                         s = d.readMemory(data, 2 * size)

                thread = gdb.selected_thread()
                inner = '{valueencoded="';
                inner += str(Hex4EncodedLittleEndianWithoutQuotes)+'",id="'
                inner += str(thread.num) + '",value="'
                inner += s
                #inner += d.encodeString(objectName)
                inner += '"},'

                out += inner
            except:
                pass
    return out


def threadnames(arg):
    out = '['
    oldthread = gdb.selected_thread()
    try:
        inferior = selectedInferior()
        for thread in inferior.threads():
            thread.switch()
            out += threadname(arg)
    except:
        pass
    oldthread.switch()
    return out + ']'

registerCommand("threadnames", threadnames)


#######################################################################
#
# Mixed C++/Qml debugging
#
#######################################################################

def qmlb(args):
    # executeCommand(command, to_string=True).split("\n")
    warm("RUNNING: break -f QScript::FunctionWrapper::proxyCall")
    output = catchCliOutput("rbreak -f QScript::FunctionWrapper::proxyCall")
    warn("OUTPUT: %s " % output)
    bp = output[0]
    warn("BP: %s " % bp)
    # BP: ['Breakpoint 3 at 0xf166e7: file .../qscriptfunction.cpp, line 75.\\n'] \n"
    pos = bp.find(' ') + 1
    warn("POS: %s " % pos)
    nr = bp[bp.find(' ') + 1 : bp.find(' at ')]
    warn("NR: %s " % nr)
    return bp

registerCommand("qmlb", qmlb)

bbsetup()
