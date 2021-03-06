############################################################################
#
# Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
# Contact: http://www.qt-project.org/legal
#
# This file is part of Qt Creator.
#
# Commercial License Usage
# Licensees holding valid commercial Qt licenses may use this file in
# accordance with the commercial license agreement provided with the
# Software or, alternatively, in accordance with the terms contained in
# a written agreement between you and Digia.  For licensing terms and
# conditions see http://qt.digia.com/licensing.  For further information
# use the contact form at http://qt.digia.com/contact-us.
#
# GNU Lesser General Public License Usage
# Alternatively, this file may be used under the terms of the GNU Lesser
# General Public License version 2.1 as published by the Free Software
# Foundation and appearing in the file LICENSE.LGPL included in the
# packaging of this file.  Please review the following information to
# ensure the GNU Lesser General Public License version 2.1 requirements
# will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
#
# In addition, as a special exception, Digia gives you certain additional
# rights.  These rights are described in the Digia Qt LGPL Exception
# version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
#
#############################################################################

from dumper import *


def qdump__QAtomicInt(d, value):
    d.putValue(int(value["_q_value"]))
    d.putNumChild(0)


def qdump__QBasicAtomicInt(d, value):
    d.putValue(int(value["_q_value"]))
    d.putNumChild(0)


def qdump__QAtomicPointer(d, value):
    d.putType(value.type)
    q = value["_q_value"]
    p = int(q)
    d.putValue("@0x%x" % p)
    d.putNumChild(1 if p else 0)
    if d.isExpanded():
        with Children(d):
           d.putSubItem("_q_value", q.dereference())

def qform__QByteArray():
    return "Inline,As Latin1 in Separate Window,As UTF-8 in Separate Window"

def qdump__QByteArray(d, value):
    d.putByteArrayValue(value)
    data, size, alloc = d.byteArrayData(value)
    d.putNumChild(size)
    format = d.currentItemFormat()
    if format == 1:
        d.putDisplay(StopDisplay)
    elif format == 2:
        d.putField("editformat", DisplayLatin1String)
        d.putField("editvalue", d.encodeByteArray(value))
    elif format == 3:
        d.putField("editformat", DisplayUtf8String)
        d.putField("editvalue", d.encodeByteArray(value))
    if d.isExpanded():
        d.putArrayData(d.charType(), data, size)

def qdump__QByteArrayData(d, value):
    data, size, alloc = d.byteArrayDataHelper(d.addressOf(value))
    d.putValue(d.readMemory(data, size), Hex2EncodedLatin1)
    d.putNumChild(1)
    if d.isExpanded():
        with Children(d):
            d.putIntItem("size", size)
            d.putIntItem("alloc", alloc)

def qdump__QChar(d, value):
    d.putValue(int(value["ucs"]))
    d.putNumChild(0)


def qform__QAbstractItemModel():
    return "Normal,Enhanced"

def qdump__QAbstractItemModel(d, value):
    format = d.currentItemFormat()
    if format == 1:
        d.putPlainChildren(value)
        return
    #format == 2:
    # Create a default-constructed QModelIndex on the stack.
    try:
        ri = d.makeValue(d.qtNamespace() + "QModelIndex", "-1, -1, 0, 0")
        this_ = d.makeExpression(value)
        ri_ = d.makeExpression(ri)
        rowCount = int(d.parseAndEvaluate("%s.rowCount(%s)" % (this_, ri_)))
        columnCount = int(d.parseAndEvaluate("%s.columnCount(%s)" % (this_, ri_)))
    except:
        d.putPlainChildren(value)
        return
    d.putValue("%d x %d" % (rowCount, columnCount))
    d.putNumChild(rowCount * columnCount)
    if d.isExpanded():
        with Children(d, numChild=rowCount * columnCount, childType=ri.type):
            i = 0
            for row in xrange(rowCount):
                for column in xrange(columnCount):
                    with SubItem(d, i):
                        d.putName("[%s, %s]" % (row, column))
                        mi = d.parseAndEvaluate("%s.index(%d,%d,%s)"
                            % (this_, row, column, ri_))
                        #warn("MI: %s " % mi)
                        #name = "[%d,%d]" % (row, column)
                        #d.putValue("%s" % mi)
                        d.putItem(mi)
                        i = i + 1
                        #warn("MI: %s " % mi)
                        #d.putName("[%d,%d]" % (row, column))
                        #d.putValue("%s" % mi)
                        #d.putNumChild(0)
                        #d.putType(mi.type)
    #gdb.execute("call free($ri)")

def qform__QModelIndex():
    return "Normal,Enhanced"

def qdump__QModelIndex(d, value):
    format = d.currentItemFormat()
    if format == 1:
        d.putPlainChildren(value)
        return
    r = value["r"]
    c = value["c"]
    try:
        p = value["p"]
    except:
        p = value["i"]
    m = value["m"]
    if d.isNull(m) or r < 0 or c < 0:
        d.putValue("(invalid)")
        d.putPlainChildren(value)
        return

    mm = m.dereference()
    mm = mm.cast(mm.type.unqualified())
    ns = d.qtNamespace()
    try:
        mi = d.makeValue(ns + "QModelIndex", "%s,%s,%s,%s" % (r, c, p, m))
        mm_ = d.makeExpression(mm)
        mi_ = d.makeExpression(mi)
        rowCount = int(d.parseAndEvaluate("%s.rowCount(%s)" % (mm_, mi_)))
        columnCount = int(d.parseAndEvaluate("%s.columnCount(%s)" % (mm_, mi_)))
    except:
        d.putEmptyValue()
        d.putPlainChildren(value)
        return

    try:
        # Access DisplayRole as value
        val = d.parseAndEvaluate("%s.data(%s, 0)" % (mm_, mi_))
        v = val["d"]["data"]["ptr"]
        d.putStringValue(d.makeValue(ns + 'QString', v))
    except:
        d.putValue("(invalid)")

    d.putNumChild(rowCount * columnCount)
    if d.isExpanded():
        with Children(d):
            i = 0
            for row in xrange(rowCount):
                for column in xrange(columnCount):
                    with UnnamedSubItem(d, i):
                        d.putName("[%s, %s]" % (row, column))
                        mi2 = d.parseAndEvaluate("%s.index(%d,%d,%s)"
                            % (mm_, row, column, mi_))
                        d.putItem(mi2)
                        i = i + 1
            #d.putCallItem("parent", val, "parent")
            #with SubItem(d, "model"):
            #    d.putValue(m)
            #    d.putType(ns + "QAbstractItemModel*")
            #    d.putNumChild(1)
    #gdb.execute("call free($mi)")


def qdump__QDate(d, value):
    jd = int(value["jd"])
    if int(jd):
        d.putValue(jd, JulianDate)
        d.putNumChild(1)
        if d.isExpanded():
            qt = d.qtNamespace() + "Qt::"
            if d.isLldb:
                qt += "DateFormat::" # FIXME: Bug?...
            # FIXME: This improperly uses complex return values.
            with Children(d):
                d.putCallItem("toString", value, "toString", qt + "TextDate")
                d.putCallItem("(ISO)", value, "toString", qt + "ISODate")
                d.putCallItem("(SystemLocale)", value, "toString",
                    qt + "SystemLocaleDate")
                d.putCallItem("(Locale)", value, "toString", qt + "LocaleDate")
    else:
        d.putValue("(invalid)")
        d.putNumChild(0)


def qdump__QTime(d, value):
    mds = int(value["mds"])
    if mds >= 0:
        d.putValue(mds, MillisecondsSinceMidnight)
        d.putNumChild(1)
        if d.isExpanded():
            ns = d.qtNamespace()
            qtdate = ns + "Qt::"
            qttime = ns + "Qt::"
            if d.isLldb:
                qtdate += "DateFormat::" # FIXME: Bug?...
            # FIXME: This improperly uses complex return values.
            with Children(d):
                d.putCallItem("toString", value, "toString", qtdate + "TextDate")
                d.putCallItem("(ISO)", value, "toString", qtdate + "ISODate")
                d.putCallItem("(SystemLocale)", value, "toString",
                     qtdate + "SystemLocaleDate")
                d.putCallItem("(Locale)", value, "toString", qtdate + "LocaleDate")
    else:
        d.putValue("(invalid)")
        d.putNumChild(0)


def qdump__QDateTime(d, value):
    qtVersion = d.qtVersion()
    isValid = False
    # This relies on the Qt4/Qt5 internal structure layout:
    # {sharedref(4), ...
    base = d.dereferenceValue(value)
    if qtVersion >= 0x050200:
        dateBase = base + d.ptrSize() # Only QAtomicInt, but will be padded.
        ms = d.extractInt64(dateBase)
        offset = d.extractInt(dateBase + 12)
        isValid = ms > 0
        if isValid:
            d.putValue("%s" % (ms - offset * 1000), MillisecondsSinceEpoch)
    else:
        # This relies on the Qt4/Qt5 internal structure layout:
        # {sharedref(4), date(8), time(4+x)}
        # QDateTimePrivate:
        # - QAtomicInt ref;    (padded on 64 bit)
        # -     [QDate date;]
        # -      -  uint jd in Qt 4,  qint64 in Qt 5.0 and Qt 5.1; padded on 64 bit
        # -     [QTime time;]
        # -      -  uint mds;
        # -  Spec spec;
        dateSize = 8 if qtVersion >= 0x050000 else 4 # Qt5: qint64, Qt4 uint
        # 4 byte padding after 4 byte QAtomicInt if we are on 64 bit and QDate is 64 bit
        refPlusPadding = 8 if qtVersion >= 0x050000 and not d.is32bit() else 4
        dateBase = base + refPlusPadding
        timeBase = dateBase + dateSize
        mds = d.extractInt(timeBase)
        isValid = mds > 0
        if isValid:
            jd = d.extractInt(dateBase)
            d.putValue("%s/%s" % (jd, mds), JulianDateAndMillisecondsSinceMidnight)
    if isValid:
        d.putNumChild(1)
        if d.isExpanded():
            # FIXME: This improperly uses complex return values.
            with Children(d):
                qtdate = d.qtNamespace() + "Qt::"
                qttime = qtdate
                if d.isLldb:
                    qtdate += "DateFormat::" # FIXME: Bug?...
                    qttime += "TimeSpec::" # FIXME: Bug?...
                d.putCallItem("toTime_t", value, "toTime_t")
                d.putCallItem("toString", value, "toString", qtdate + "TextDate")
                d.putCallItem("(ISO)", value, "toString", qtdate + "ISODate")
                d.putCallItem("(SystemLocale)", value, "toString", qtdate + "SystemLocaleDate")
                d.putCallItem("(Locale)", value, "toString", qtdate + "LocaleDate")
                d.putCallItem("toUTC", value, "toTimeSpec", qttime + "UTC")
                d.putCallItem("toLocalTime", value, "toTimeSpec", qttime + "LocalTime")
    else:
        d.putValue("(invalid)")
        d.putNumChild(0)


def qdump__QDir(d, value):
    d.putNumChild(1)
    privAddress = d.dereferenceValue(value)
    bit32 = d.is32bit()
    qt5 = d.qtVersion() >= 0x050000
    # QDirPrivate:
    # QAtomicInt ref
    # QStringList nameFilters;
    # QDir::SortFlags sort;
    # QDir::Filters filters;
    # // qt3support:
    # QChar filterSepChar;
    # bool matchAllDirs;
    # // end qt3support
    # QScopedPointer<QAbstractFileEngine> fileEngine;
    # bool fileListsInitialized;
    # QStringList files;
    # QFileInfoList fileInfos;
    # QFileSystemEntry dirEntry;
    # QFileSystemEntry absoluteDirEntry;
    qt3SupportAddition = 0 if qt5 else d.ptrSize() # qt5 doesn't have qt3support
    filesOffset = (24 if bit32 else 40) + qt3SupportAddition
    fileInfosOffset = filesOffset + d.ptrSize()
    dirEntryOffset = fileInfosOffset + d.ptrSize()
    # QFileSystemEntry:
    # QString m_filePath
    # QByteArray m_nativeFilePath
    # qint16 m_lastSeparator
    # qint16 m_firstDotInFileName
    # qint16 m_lastDotInFileName
    # + 2 byte padding
    fileSystemEntrySize = 2 * d.ptrSize() + 8
    absoluteDirEntryOffset = dirEntryOffset + fileSystemEntrySize
    d.putStringValueByAddress(privAddress + dirEntryOffset)
    if d.isExpanded():
        with Children(d):
            ns = d.qtNamespace()
            d.call(value, "count")  # Fill cache.
            #d.putCallItem("absolutePath", value, "absolutePath")
            #d.putCallItem("canonicalPath", value, "canonicalPath")
            with SubItem(d, "absolutePath"):
                typ = d.lookupType(ns + "QString")
                d.putItem(d.createValue(privAddress + absoluteDirEntryOffset, typ))
            with SubItem(d, "entryInfoList"):
                typ = d.lookupType(ns + "QList<" + ns + "QFileInfo>")
                d.putItem(d.createValue(privAddress + fileInfosOffset, typ))
            with SubItem(d, "entryList"):
                typ = d.lookupType(ns + "QStringList")
                d.putItem(d.createValue(privAddress + filesOffset, typ))


def qdump__QFile(d, value):
    try:
        # Try using debug info first.
        ptype = d.lookupType(d.qtNamespace() + "QFilePrivate").pointer()
        d_ptr = value["d_ptr"]["d"]
        fileNameAddress = d.addressOf(d_ptr.cast(ptype).dereference()["fileName"])
        d.putNumChild(1)
    except:
        if d.qtVersion() >= 0x050000:
            offset = 176 if d.is32bit() else 280
        else:
            offset = 140 if d.is32bit() else 232
        privAddress = d.dereference(d.addressOf(value) + d.ptrSize())
        fileNameAddress = privAddress + offset
        d.putNumChild(0)
    d.putStringValueByAddress(fileNameAddress)
    if d.isExpanded():
        with Children(d):
            base = d.fieldAt(value.type, 0).type
            d.putSubItem("[%s]" % str(base), value.cast(base), False)
            d.putCallItem("exists", value, "exists")


def qdump__QFileInfo(d, value):
    privAddress = d.dereferenceValue(value)
    #bit32 = d.is32bit()
    #qt5 = d.qtVersion() >= 0x050000
    #try:
    #    d.putStringValue(value["d_ptr"]["d"].dereference()["fileNames"][3])
    #except:
    #    d.putPlainChildren(value)
    #    return
    filePathAddress = privAddress + d.ptrSize()
    d.putStringValueByAddress(filePathAddress)
    d.putNumChild(1)
    if d.isExpanded():
        ns = d.qtNamespace()
        with Children(d, childType=d.lookupType(ns + "QString")):
            d.putCallItem("absolutePath", value, "absolutePath")
            d.putCallItem("absoluteFilePath", value, "absoluteFilePath")
            d.putCallItem("canonicalPath", value, "canonicalPath")
            d.putCallItem("canonicalFilePath", value, "canonicalFilePath")
            d.putCallItem("completeBaseName", value, "completeBaseName")
            d.putCallItem("completeSuffix", value, "completeSuffix")
            d.putCallItem("baseName", value, "baseName")
            if False:
                #ifdef Q_OS_MACX
                d.putCallItem("isBundle", value, "isBundle")
                d.putCallItem("bundleName", value, "bundleName")
            d.putCallItem("fileName", value, "fileName")
            d.putCallItem("filePath", value, "filePath")
            # Crashes gdb (archer-tromey-python, at dad6b53fe)
            #d.putCallItem("group", value, "group")
            #d.putCallItem("owner", value, "owner")
            d.putCallItem("path", value, "path")

            d.putCallItem("groupid", value, "groupId")
            d.putCallItem("ownerid", value, "ownerId")

            #QFile::Permissions permissions () const
            perms = d.call(value, "permissions")
            if perms is None:
                d.putValue("<not available>")
            else:
                with SubItem(d, "permissions"):
                    d.putEmptyValue()
                    d.putType(ns + "QFile::Permissions")
                    d.putNumChild(10)
                    if d.isExpanded():
                        with Children(d, 10):
                            perms = perms['i']
                            d.putBoolItem("ReadOwner",  perms & 0x4000)
                            d.putBoolItem("WriteOwner", perms & 0x2000)
                            d.putBoolItem("ExeOwner",   perms & 0x1000)
                            d.putBoolItem("ReadUser",   perms & 0x0400)
                            d.putBoolItem("WriteUser",  perms & 0x0200)
                            d.putBoolItem("ExeUser",    perms & 0x0100)
                            d.putBoolItem("ReadGroup",  perms & 0x0040)
                            d.putBoolItem("WriteGroup", perms & 0x0020)
                            d.putBoolItem("ExeGroup",   perms & 0x0010)
                            d.putBoolItem("ReadOther",  perms & 0x0004)
                            d.putBoolItem("WriteOther", perms & 0x0002)
                            d.putBoolItem("ExeOther",   perms & 0x0001)

            #QDir absoluteDir () const
            #QDir dir () const
            d.putCallItem("caching", value, "caching")
            d.putCallItem("exists", value, "exists")
            d.putCallItem("isAbsolute", value, "isAbsolute")
            d.putCallItem("isDir", value, "isDir")
            d.putCallItem("isExecutable", value, "isExecutable")
            d.putCallItem("isFile", value, "isFile")
            d.putCallItem("isHidden", value, "isHidden")
            d.putCallItem("isReadable", value, "isReadable")
            d.putCallItem("isRelative", value, "isRelative")
            d.putCallItem("isRoot", value, "isRoot")
            d.putCallItem("isSymLink", value, "isSymLink")
            d.putCallItem("isWritable", value, "isWritable")
            d.putCallItem("created", value, "created")
            d.putCallItem("lastModified", value, "lastModified")
            d.putCallItem("lastRead", value, "lastRead")


def qdump__QFixed(d, value):
    v = int(value["val"])
    d.putValue("%s/64 = %s" % (v, v/64.0))
    d.putNumChild(0)


def qdump__QFiniteStack(d, value):
    alloc = int(value["_alloc"])
    size = int(value["_size"])
    d.check(0 <= size and size <= alloc and alloc <= 1000 * 1000 * 1000)
    d.putItemCount(size)
    d.putNumChild(size)
    if d.isExpanded():
        innerType = d.templateArgument(value.type, 0)
        d.putArrayData(innerType, value["_array"], size)

# Stock gdb 7.2 seems to have a problem with types here:
#
#  echo -e "namespace N { struct S { enum E { zero, one, two }; }; }\n"\
#      "int main() { N::S::E x = N::S::one;\n return x; }" >> main.cpp
#  g++ -g main.cpp
#  gdb-7.2 -ex 'file a.out' -ex 'b main' -ex 'run' -ex 'step' \
#     -ex 'ptype N::S::E' -ex 'python print gdb.lookup_type("N::S::E")' -ex 'q'
#  gdb-7.1 -ex 'file a.out' -ex 'b main' -ex 'run' -ex 'step' \
#     -ex 'ptype N::S::E' -ex 'python print gdb.lookup_type("N::S::E")' -ex 'q'
#  gdb-cvs -ex 'file a.out' -ex 'b main' -ex 'run' -ex 'step' \
#     -ex 'ptype N::S::E' -ex 'python print gdb.lookup_type("N::S::E")' -ex 'q'
#
# gives as of 2010-11-02
#
#  type = enum N::S::E {N::S::zero, N::S::one, N::S::two} \n
#    Traceback (most recent call last): File "<string>", line 1,
#      in <module> RuntimeError: No type named N::S::E.
#  type = enum N::S::E {N::S::zero, N::S::one, N::S::two} \n  N::S::E
#  type = enum N::S::E {N::S::zero, N::S::one, N::S::two} \n  N::S::E
#
# i.e. there's something broken in stock 7.2 that is was ok in 7.1 and is ok later.

def qdump__QFlags(d, value):
    i = value["i"]
    try:
        enumType = d.templateArgument(value.type.unqualified(), 0)
        d.putValue("%s (%s)" % (i.cast(enumType), i))
    except:
        d.putValue("%s" % i)
    d.putNumChild(0)


def qform__QHash():
    return mapForms()

def qdump__QHash(d, value):

    def hashDataFirstNode(dPtr, numBuckets):
        ePtr = dPtr.cast(nodeTypePtr)
        bucket = dPtr.dereference()["buckets"]
        for n in xrange(numBuckets - 1, -1, -1):
            n = n - 1
            if n < 0:
                break
            if d.pointerValue(bucket.dereference()) != d.pointerValue(ePtr):
                return bucket.dereference()
            bucket = bucket + 1
        return ePtr;

    def hashDataNextNode(nodePtr, numBuckets):
        nextPtr = nodePtr.dereference()["next"]
        if d.pointerValue(nextPtr.dereference()["next"]):
            return nextPtr
        start = (int(nodePtr.dereference()["h"]) % numBuckets) + 1
        dPtr = nextPtr.cast(dataTypePtr)
        bucket = dPtr.dereference()["buckets"] + start
        for n in xrange(numBuckets - start):
            if d.pointerValue(bucket.dereference()) != d.pointerValue(nextPtr):
                return bucket.dereference()
            bucket += 1
        return nextPtr

    keyType = d.templateArgument(value.type, 0)
    valueType = d.templateArgument(value.type, 1)

    anon = d.childAt(value, 0)
    d_ptr = anon["d"]
    e_ptr = anon["e"]
    size = int(d_ptr["size"])

    dataTypePtr = d_ptr.type    # QHashData *  = { Node *fakeNext, Node *buckets }
    nodeTypePtr = d_ptr.dereference()["fakeNext"].type    # QHashData::Node

    d.check(0 <= size and size <= 100 * 1000 * 1000)
    d.checkRef(d_ptr["ref"])

    d.putItemCount(size)
    d.putNumChild(size)
    if d.isExpanded():
        numBuckets = int(d_ptr.dereference()["numBuckets"])
        nodePtr = hashDataFirstNode(d_ptr, numBuckets)
        innerType = e_ptr.dereference().type
        isCompact = d.isMapCompact(keyType, valueType)
        childType = valueType if isCompact else innerType
        with Children(d, size, maxNumChild=1000, childType=childType):
            for i in d.childRange():
                it = nodePtr.dereference().cast(innerType)
                with SubItem(d, i):
                    if isCompact:
                        key = it["key"]
                        if not key:
                            # LLDB can't access directly since it's in anonymous union
                            # for Qt4 optimized int keytype
                            key = it[1]["key"]
                        d.putMapName(key)
                        d.putItem(it["value"])
                        d.putType(valueType)
                    else:
                        d.putItem(it)
                nodePtr = hashDataNextNode(nodePtr, numBuckets)


def qdump__QHashNode(d, value):
    key = value["key"]
    if not key:
        # LLDB can't access directly since it's in anonymous union
        # for Qt4 optimized int keytype
        key = value[1]["key"]
    val = value["value"]
    d.putEmptyValue()
    d.putNumChild(2)
    if d.isExpanded():
        with Children(d):
            d.putSubItem("key", key)
            d.putSubItem("value", val)


def qHashIteratorHelper(d, value):
    typeName = str(value.type)
    hashTypeName = typeName[0:typeName.rfind("::")]
    hashType = d.lookupType(hashTypeName)
    keyType = d.templateArgument(hashType, 0)
    valueType = d.templateArgument(hashType, 1)
    d.putNumChild(1)
    d.putEmptyValue()
    if d.isExpanded():
        with Children(d):
            # We need something like QHash<int, float>::iterator
            # -> QHashNode<int, float> with 'proper' spacing,
            # as space changes confuse LLDB.
            innerTypeName = hashTypeName.replace("QHash", "QHashNode", 1)
            node = value["i"].cast(d.lookupType(innerTypeName).pointer())
            d.putSubItem("key", node["key"])
            d.putSubItem("value", node["value"])

def qdump__QHash__const_iterator(d, value):
    qHashIteratorHelper(d, value)

def qdump__QHash__iterator(d, value):
    qHashIteratorHelper(d, value)


def qdump__QHostAddress(d, value):
    # QHostAddress in Qt 4.5 (byte offsets)
    #   quint32 a        (0)
    #   Q_IPV6ADDR a6    (4)
    #   protocol         (20)
    #   QString ipString (24)
    #   QString scopeId  (24 + ptrSize)
    #   bool isParsed    (24 + 2 * ptrSize)
    # QHostAddress in Qt 5.0
    #   QString ipString (0)
    #   QString scopeId  (ptrSize)
    #   quint32 a        (2*ptrSize)
    #   Q_IPV6ADDR a6    (2*ptrSize + 4)
    #   protocol         (2*ptrSize + 20)
    #   bool isParsed    (2*ptrSize + 24)

    privAddress = d.dereferenceValue(value)
    isQt5 = d.qtVersion() >= 0x050000
    sizeofQString = d.ptrSize()
    ipStringAddress = privAddress + (0 if isQt5 else 24)
    isParsedAddress = privAddress + 24 + 2 * sizeofQString
    # value.d.d->ipString
    ipString = d.encodeStringHelper(d.dereference(ipStringAddress))
    if d.extractByte(isParsedAddress) and len(ipString) > 0:
        d.putValue(ipString, Hex4EncodedLittleEndian)
    else:
        # value.d.d->protocol:
        #  QAbstractSocket::IPv4Protocol = 0
        #  QAbstractSocket::IPv6Protocol = 1
        protoAddress = privAddress + 20 + (2 * sizeofQString if isQt5 else 0);
        proto = d.extractInt(protoAddress)
        if proto == 1:
            # value.d.d->a6
            a6 = privAddress + 4 + (2 * sizeofQString if isQt5 else 0)
            data = d.readMemory(a6, 16)
            address = ':'.join("%x" % int(data[i:i+4], 16) for i in xrange(0, 32, 4))
            scopeId = privAddress + sizeofQString + (0 if isQt5 else 24)
            scopeId = d.encodeStringHelper(d.dereference(scopeId))
            d.putValue("%s%%%s" % (address, scopeId), IPv6AddressAndHexScopeId)
        elif proto == 0:
            # value.d.d->a
            a = d.extractInt(privAddress + (2 * sizeofQString if isQt5 else 0))
            a, n4 = divmod(a, 256)
            a, n3 = divmod(a, 256)
            a, n2 = divmod(a, 256)
            a, n1 = divmod(a, 256)
            d.putValue("%d.%d.%d.%d" % (n1, n2, n3, n4));
        else:
            d.putValue("<unspecified>")

    d.putPlainChildren(value["d"]["d"].dereference())


def qdump__Q_IPV6ADDR(d, value):
    data = d.readMemory(d.addressOf(value), 16)
    d.putValue(':'.join("%x" % int(data[i:i+4], 16) for i in xrange(0, 32, 4)))
    d.putPlainChildren(value["c"])

def qdump__QIPv6Address(d, value):
    qdump__Q_IPV6ADDR(d, value)


def qform__QList():
    return "Assume Direct Storage,Assume Indirect Storage"

def qdump__QList(d, value):
    dptr = d.childAt(value, 0)["d"]
    private = dptr.dereference()
    begin = int(private["begin"])
    end = int(private["end"])
    array = private["array"]
    d.check(begin >= 0 and end >= 0 and end <= 1000 * 1000 * 1000)
    size = end - begin
    d.check(size >= 0)
    d.checkRef(private["ref"])

    innerType = d.templateArgument(value.type, 0)

    d.putItemCount(size)
    d.putNumChild(size)
    if d.isExpanded():
        innerSize = innerType.sizeof
        stepSize = dptr.type.sizeof
        addr = d.addressOf(array) + begin * stepSize
        # The exact condition here is:
        #  QTypeInfo<T>::isLarge || QTypeInfo<T>::isStatic
        # but this data is available neither in the compiled binary nor
        # in the frontend.
        # So as first approximation only do the 'isLarge' check:
        format = d.currentItemFormat()
        if format == 1:
            isInternal = True
        elif format == 2:
            isInternal = False
        else:
            isInternal = innerSize <= stepSize and d.isMovableType(innerType)
        if isInternal:
            if innerSize == stepSize:
                p = d.createPointerValue(addr, innerType)
                d.putArrayData(innerType, p, size)
            else:
                with Children(d, size, childType=innerType):
                    for i in d.childRange():
                        p = d.createValue(addr + i * stepSize, innerType)
                        d.putSubItem(i, p)
        else:
            p = d.createPointerValue(addr, innerType.pointer())
            # about 0.5s / 1000 items
            with Children(d, size, maxNumChild=2000, childType=innerType):
                for i in d.childRange():
                    d.putSubItem(i, p.dereference().dereference())
                    p += 1

def qform__QImage():
    return "Normal,Displayed"

def qdump__QImage(d, value):
    # This relies on current QImage layout:
    # QImageData:
    # - QAtomicInt ref
    # - int width, height, depth, nbytes
    # - padding on 64 bit machines
    # - qreal devicePixelRatio  (+20 + padding)  # Assume qreal == double, Qt 5 only
    # - QVector<QRgb> colortable (+20 + padding + gap)
    # - uchar *data (+20 + padding + gap + ptr)
    # [- uchar **jumptable jumptable with Qt 3 suppor]
    # - enum format (+20 + padding + gap + 2 * ptr)

    ptrSize = d.ptrSize()
    isQt5 = d.qtVersion() >= 0x050000
    offset = (3 if isQt5 else 2) * ptrSize
    base = d.dereference(d.addressOf(value) + offset)
    width = d.extractInt(base + 4)
    height = d.extractInt(base + 8)
    nbytes = d.extractInt(base + 16)
    padding = d.ptrSize() - d.intSize()
    pixelRatioSize = 8 if isQt5 else 0
    jumpTableSize = ptrSize if not isQt5 else 0  # FIXME: Assumes Qt3 Support
    bits = d.dereference(base + 20 + padding + pixelRatioSize + ptrSize)
    iformat = d.extractInt(base + 20 + padding + pixelRatioSize + jumpTableSize + 2 * ptrSize)
    d.putValue("(%dx%d)" % (width, height))
    d.putNumChild(1)
    if d.isExpanded():
        with Children(d):
            d.putIntItem("width", width)
            d.putIntItem("height", height)
            d.putIntItem("nbytes", nbytes)
            d.putIntItem("format", iformat)
            with SubItem(d, "data"):
                d.putValue("0x%x" % bits)
                d.putNumChild(0)
                d.putType("void *")

    format = d.currentItemFormat()
    if format == 1:
        d.putDisplay(StopDisplay)
    elif format == 2:
        # This is critical for performance. Writing to an external
        # file using the following is faster when using GDB.
        #   file = tempfile.mkstemp(prefix="gdbpy_")
        #   filename = file[1].replace("\\", "\\\\")
        #   gdb.execute("dump binary memory %s %s %s" %
        #       (filename, bits, bits + nbytes))
        #   d.putDisplay(DisplayImageFile, " %d %d %d %d %s"
        #       % (width, height, nbytes, iformat, filename))
        d.putField("editformat", DisplayImageData)
        d.put('editvalue="')
        d.put('%08x%08x%08x%08x' % (width, height, nbytes, iformat))
        d.put(d.readMemory(bits, nbytes))
        d.put('",')


def qdump__QLinkedList(d, value):
    dd = d.dereferenceValue(value)
    ptrSize = d.ptrSize()
    n = d.extractInt(dd + 4 + 2 * ptrSize);
    ref = d.extractInt(dd + 2 * ptrSize);
    d.check(0 <= n and n <= 100*1000*1000)
    d.check(-1 <= ref and ref <= 1000)
    d.putItemCount(n)
    d.putNumChild(n)
    if d.isExpanded():
        innerType = d.templateArgument(value.type, 0)
        with Children(d, n, maxNumChild=1000, childType=innerType):
            pp = d.dereference(dd)
            for i in d.childRange():
                d.putSubItem(i, d.createValue(pp + 2 * ptrSize, innerType))
                pp = d.dereference(pp)

qqLocalesCount = None

def qdump__QLocale(d, value):
    # Check for uninitialized 'index' variable. Retrieve size of
    # QLocale data array from variable in qlocale.cpp.
    # Default is 368 in Qt 4.8, 438 in Qt 5.0.1, the last one
    # being 'System'.
    #global qqLocalesCount
    #if qqLocalesCount is None:
    #    #try:
    #        qqLocalesCount = int(value(ns + 'locale_data_size'))
    #    #except:
    #        qqLocalesCount = 438
    #try:
    #    index = int(value["p"]["index"])
    #except:
    #    try:
    #        index = int(value["d"]["d"]["m_index"])
    #    except:
    #        index = int(value["d"]["d"]["m_data"]...)
    #d.check(index >= 0)
    #d.check(index <= qqLocalesCount)
    d.putStringValue(d.call(value, "name"))
    d.putNumChild(0)
    return
    # FIXME: Poke back for variants.
    if d.isExpanded():
        ns = d.qtNamespace()
        with Children(d, childType=d.lookupType(ns + "QChar"), childNumChild=0):
            d.putCallItem("country", value, "country")
            d.putCallItem("language", value, "language")
            d.putCallItem("measurementSystem", value, "measurementSystem")
            d.putCallItem("numberOptions", value, "numberOptions")
            d.putCallItem("timeFormat_(short)", value,
                "timeFormat", ns + "QLocale::ShortFormat")
            d.putCallItem("timeFormat_(long)", value,
                "timeFormat", ns + "QLocale::LongFormat")
            d.putCallItem("decimalPoint", value, "decimalPoint")
            d.putCallItem("exponential", value, "exponential")
            d.putCallItem("percent", value, "percent")
            d.putCallItem("zeroDigit", value, "zeroDigit")
            d.putCallItem("groupSeparator", value, "groupSeparator")
            d.putCallItem("negativeSign", value, "negativeSign")


def qdump__QMapNode(d, value):
    d.putEmptyValue()
    d.putNumChild(2)
    if d.isExpanded():
        with Children(d):
            d.putSubItem("key", value["key"])
            d.putSubItem("value", value["value"])


def qdumpHelper__Qt4_QMap(d, value, forceLong):
    d_ptr = value["d"].dereference()
    e_ptr = value["e"].dereference()
    n = int(d_ptr["size"])
    d.check(0 <= n and n <= 100*1000*1000)
    d.checkRef(d_ptr["ref"])

    d.putItemCount(n)
    d.putNumChild(n)
    if d.isExpanded():
        if n > 10000:
            n = 10000

        keyType = d.templateArgument(value.type, 0)
        valueType = d.templateArgument(value.type, 1)
        isCompact = d.isMapCompact(keyType, valueType)

        it = e_ptr["forward"].dereference()

        # QMapPayloadNode is QMapNode except for the 'forward' member, so
        # its size is most likely the offset of the 'forward' member therein.
        # Or possibly 2 * sizeof(void *)
        nodeType = d.lookupType(d.qtNamespace() + "QMapNode<%s,%s>" % (keyType, valueType))
        nodePointerType = nodeType.pointer()
        payloadSize = nodeType.sizeof - 2 * nodePointerType.sizeof

        if isCompact:
            innerType = valueType
        else:
            innerType = nodeType

        with Children(d, n, childType=innerType):
            for i in xrange(n):
                base = it.cast(d.charPtrType()) - payloadSize
                node = base.cast(nodePointerType).dereference()
                with SubItem(d, i):
                    d.putField("iname", d.currentIName)
                    if isCompact:
                        #d.putType(valueType)
                        if forceLong:
                            d.putName("[%s] %s" % (i, node["key"]))
                        else:
                            d.putMapName(node["key"])
                        d.putItem(node["value"])
                    else:
                        d.putItem(node)
                it = it.dereference()["forward"].dereference()


def qdumpHelper__Qt5_QMap(d, value, forceLong):
    d_ptr = value["d"].dereference()
    n = int(d_ptr["size"])
    d.check(0 <= n and n <= 100*1000*1000)
    d.checkRef(d_ptr["ref"])

    d.putItemCount(n)
    d.putNumChild(n)
    if d.isExpanded():
        if n > 10000:
            n = 10000

        keyType = d.templateArgument(value.type, 0)
        valueType = d.templateArgument(value.type, 1)
        isCompact = d.isMapCompact(keyType, valueType)
        # Note: Keeping the spacing in the type lookup
        # below is important for LLDB.
        needle = str(d_ptr.type).replace("QMapData", "QMapNode", 1)
        nodeType = d.lookupType(needle)

        if isCompact:
            innerType = valueType
        else:
            innerType = nodeType

        with Children(d, n, childType=innerType):
            toDo = []
            i = -1
            node = d_ptr["header"]
            left = node["left"]
            if not d.isNull(left):
                toDo.append(left.dereference())
            right = node["right"]
            if not d.isNull(right):
                toDo.append(right.dereference())

            while len(toDo):
                node = toDo[0].cast(nodeType)
                toDo = toDo[1:]
                left = node["left"]
                if not d.isNull(left):
                    toDo.append(left.dereference())
                right = node["right"]
                if not d.isNull(right):
                    toDo.append(right.dereference())
                i += 1

                with SubItem(d, i):
                    d.putField("iname", d.currentIName)
                    if isCompact:
                        if forceLong:
                            d.putName("[%s] %s" % (i, node["key"]))
                        else:
                            d.putMapName(node["key"])
                        d.putItem(node["value"])
                    else:
                        qdump__QMapNode(d, node)


def qdumpHelper__QMap(d, value, forceLong):
    if d.fieldAt(value["d"].dereference().type, 0).name == "backward":
        qdumpHelper__Qt4_QMap(d, value, forceLong)
    else:
        qdumpHelper__Qt5_QMap(d, value, forceLong)

def qform__QMap():
    return mapForms()

def qdump__QMap(d, value):
    qdumpHelper__QMap(d, value, False)

def qform__QMultiMap():
    return mapForms()

def qdump__QMultiMap(d, value):
    qdumpHelper__QMap(d, value, True)


def extractCString(table, offset):
    result = ""
    while True:
        d = table[offset]
        if d == 0:
            break
        result += "%c" % d
        offset += 1
    return result


def qdump__QObject(d, value):
    d.putQObjectNameValue(value)
    ns = d.qtNamespace()

    try:
        privateTypeName = ns + "QObjectPrivate"
        privateType = d.lookupType(privateTypeName)
        staticMetaObject = value["staticMetaObject"]
    except:
        d.putPlainChildren(value)
        return
    #warn("SMO: %s " % staticMetaObject)
    #warn("SMO DATA: %s " % staticMetaObject["d"]["stringdata"])
    superData = staticMetaObject["d"]["superdata"]
    #warn("SUPERDATA: %s" % superData)
    #while not d.isNull(superData):
    #    superData = superData.dereference()["d"]["superdata"]
    #    warn("SUPERDATA: %s" % superData)

    if privateType is None:
        #d.putValue(cleanAddress(value.address))
        d.putPlainChildren(value)
        return

    #warn("OBJECTNAME: %s " % objectName)
    dd = value["d_ptr"]["d"]
    d_ptr = dd.cast(privateType.pointer()).dereference()
    #warn("D_PTR: %s " % d_ptr)
    mo = d_ptr["metaObject"]
    if d.isNull(mo):
        mo = staticMetaObject
    #warn("MO: %s " % mo)
    #warn("MO.D: %s " % mo["d"])
    metaData = mo["d"]["data"]
    metaStringData = mo["d"]["stringdata"]
    # This is char * in Qt 4 and ByteArrayData * in Qt 5.
    # Force it to the char * data in the Qt 5 case.
    try:
        offset = metaStringData["offset"]
        metaStringData = metaStringData.cast(d.charPtrType()) + int(offset)
    except:
        pass

    #extradata = mo["d"]["extradata"]   # Capitalization!
    #warn("METADATA: %s " % metaData)
    #warn("STRINGDATA: %s " % metaStringData)
    #warn("TYPE: %s " % value.type)
    #warn("INAME: %s " % d.currentIName)
    d.putEmptyValue()
    #QSignalMapper::staticMetaObject
    #d.checkRef(d_ptr["ref"])
    d.putNumChild(4)
    if d.isExpanded():
      print("DIR: %s\n" % dir())
      with Children(d):

        # Local data.
        if privateTypeName != ns + "QObjectPrivate":
            if not privateType is None:
              with SubItem(d, "data"):
                d.putEmptyValue()
                d.putNoType()
                d.putNumChild(1)
                if d.isExpanded():
                    with Children(d):
                        d.putFields(d_ptr, False)


        d.putFields(value)
        # Parent and children.
        if stripClassTag(str(value.type)) == ns + "QObject":
            d.putSubItem("parent", d_ptr["parent"])
            d.putSubItem("children", d_ptr["children"])

        # Properties.
        with SubItem(d, "properties"):
            # Prolog
            extraData = d_ptr["extraData"]   # Capitalization!
            if d.isNull(extraData):
                dynamicPropertyCount = 0
            else:
                extraDataType = d.lookupType(
                    ns + "QObjectPrivate::ExtraData").pointer()
                extraData = extraData.cast(extraDataType)
                ed = extraData.dereference()
                names = ed["propertyNames"]
                values = ed["propertyValues"]
                #userData = ed["userData"]
                namesBegin = names["d"]["begin"]
                namesEnd = names["d"]["end"]
                namesArray = names["d"]["array"]
                dynamicPropertyCount = namesEnd - namesBegin

            #staticPropertyCount = d.call(mo, "propertyCount")
            staticPropertyCount = metaData[6]
            #warn("PROPERTY COUNT: %s" % staticPropertyCount)
            propertyCount = staticPropertyCount + dynamicPropertyCount

            d.putNoType()
            d.putItemCount(propertyCount)
            d.putNumChild(propertyCount)

            if d.isExpanded():
                # FIXME: Make this global. Don't leak.
                variant = "'%sQVariant'" % ns
                # Avoid malloc symbol clash with QVector
                gdb.execute("set $d = (%s*)calloc(sizeof(%s), 1)"
                    % (variant, variant))
                gdb.execute("set $d.d.is_shared = 0")

                with Children(d):
                    # Dynamic properties.
                    if dynamicPropertyCount != 0:
                        dummyType = d.voidPtrType().pointer()
                        namesType = d.lookupType(ns + "QByteArray")
                        valuesBegin = values["d"]["begin"]
                        valuesEnd = values["d"]["end"]
                        valuesArray = values["d"]["array"]
                        valuesType = d.lookupType(ns + "QVariant")
                        p = namesArray.cast(dummyType) + namesBegin
                        q = valuesArray.cast(dummyType) + valuesBegin
                        for i in xrange(dynamicPropertyCount):
                            with SubItem(d, i):
                                pp = p.cast(namesType.pointer()).dereference();
                                d.putField("key", d.encodeByteArray(pp))
                                d.putField("keyencoded", Hex2EncodedLatin1)
                                qq = q.cast(valuesType.pointer().pointer())
                                qq = qq.dereference();
                                d.putField("addr", cleanAddress(qq))
                                d.putField("exp", "*(%s*)%s"
                                     % (variant, cleanAddress(qq)))
                                t = qdump__QVariant(d, qq)
                                # Override the "QVariant (foo)" output.
                                d.putBetterType(t)
                            p += 1
                            q += 1

                    # Static properties.
                    propertyData = metaData[7]
                    for i in xrange(staticPropertyCount):
                      with NoAddress(d):
                        offset = propertyData + 3 * i
                        propertyName = extractCString(metaStringData,
                                                      metaData[offset])
                        propertyType = extractCString(metaStringData,
                                                      metaData[offset + 1])
                        with SubItem(d, propertyName):
                            #flags = metaData[offset + 2]
                            #warn("FLAGS: %s " % flags)
                            #warn("PROPERTY: %s %s " % (propertyType, propertyName))
                            # #exp = '((\'%sQObject\'*)%s)->property("%s")' \
                            #     % (ns, value.address, propertyName)
                            #exp = '"((\'%sQObject\'*)%s)"' %
                            #(ns, value.address,)
                            #warn("EXPRESSION:  %s" % exp)
                            prop = d.call(value, "property",
                                str(cleanAddress(metaStringData + metaData[offset])))
                            value1 = prop["d"]
                            #warn("   CODE: %s" % value1["type"])
                            # Type 1 and 2 are bool and int.
                            # Try to save a few cycles in this case:
                            if int(value1["type"]) > 2:
                                # Poke back prop
                                gdb.execute("set $d.d.data.ull = %s"
                                        % value1["data"]["ull"])
                                gdb.execute("set $d.d.type = %s"
                                        % value1["type"])
                                gdb.execute("set $d.d.is_null = %s"
                                        % value1["is_null"])
                                prop = d.parseAndEvaluate("$d").dereference()
                            val, innert, handled = qdumpHelper__QVariant(d, prop)

                            if handled:
                                pass
                            else:
                                # User types.
                           #    func = "typeToName(('%sQVariant::Type')%d)"
                           #       % (ns, variantType)
                           #    type = str(d.call(value, func))
                           #    type = type[type.find('"') + 1 : type.rfind('"')]
                           #    type = type.replace("Q", ns + "Q") # HACK!
                           #    data = d.call(value, "constData")
                           #    tdata = data.cast(d.lookupType(type).pointer())
                           #      .dereference()
                           #    d.putValue("(%s)" % tdata.type)
                           #    d.putType(tdata.type)
                           #    d.putNumChild(1)
                           #    if d.isExpanded():
                           #        with Children(d):
                           #           d.putSubItem("data", tdata)
                                warn("FIXME: CUSTOM QOBJECT PROPERTY: %s %s"
                                    % (propertyType, innert))
                                d.putType(propertyType)
                                d.putValue("...")
                                d.putNumChild(0)

        # Connections.
        with SubItem(d, "connections"):
            d.putNoType()
            connections = d_ptr["connectionLists"]
            connectionListCount = 0
            if not d.isNull(connections):
                connectionListCount = connections["d"]["size"]
            d.putItemCount(connectionListCount, 0)
            d.putNumChild(connectionListCount)
            if d.isExpanded():
                pp = 0
                with Children(d):
                    vectorType = d.fieldAt(connections.type.target(), 0).type
                    innerType = d.templateArgument(vectorType, 0)
                    # Should check:  innerType == ns::QObjectPrivate::ConnectionList
                    p = gdb.Value(connections["p"]["array"]).cast(innerType.pointer())
                    for i in xrange(connectionListCount):
                        first = p.dereference()["first"]
                        while not d.isNull(first):
                            with SubItem(d, pp):
                                connection = first.dereference()
                                d.putItem(connection)
                                d.putValue(connection["callFunction"])
                            first = first["nextConnectionList"]
                            # We need to enforce some upper limit.
                            pp += 1
                            if pp > 1000:
                                break
                        p += 1
                if pp < 1000:
                    d.putItemCount(pp)


        # Signals.
        signalCount = metaData[13]
        with SubItem(d, "signals"):
            d.putItemCount(signalCount)
            d.putNoType()
            d.putNumChild(signalCount)
            if signalCount:
                # FIXME: empty type does not work for childtype
                #d.putField("childtype", ".")
                d.putField("childnumchild", "0")
            if d.isExpanded():
                with Children(d):
                    for signal in xrange(signalCount):
                        with SubItem(d, signal):
                            offset = metaData[14 + 5 * signal]
                            d.putName("signal %d" % signal)
                            d.putNoType()
                            d.putValue(extractCString(metaStringData, offset))
                            d.putNumChild(0)  # FIXME: List the connections here.

        # Slots.
        with SubItem(d, "slots"):
            slotCount = metaData[4] - signalCount
            d.putItemCount(slotCount)
            d.putNoType()
            d.putNumChild(slotCount)
            if slotCount:
                #d.putField("childtype", ".")
                d.putField("childnumchild", "0")
            if d.isExpanded():
                with Children(d):
                    for slot in xrange(slotCount):
                        with SubItem(d, slot):
                            offset = metaData[14 + 5 * (signalCount + slot)]
                            d.putName("slot %d" % slot)
                            d.putNoType()
                            d.putValue(extractCString(metaStringData, offset))
                            d.putNumChild(0)  # FIXME: List the connections here.

        # Active connection.
        with SubItem(d, "currentSender"):
            d.putNoType()
            sender = d_ptr["currentSender"]
            d.putValue(cleanAddress(sender))
            if d.isNull(sender):
                d.putNumChild(0)
            else:
                d.putNumChild(1)
                if d.isExpanded():
                    with Children(d):
                        # Sending object
                        d.putSubItem("object", sender["sender"])
                        # Signal in sending object
                        with SubItem(d, "signal"):
                            d.putValue(sender["signal"])
                            d.putNoType()
                            d.putNumChild(0)

# QObject

#   static const uint qt_meta_data_QObject[] = {

#   int revision;
#   int className;
#   int classInfoCount, classInfoData;
#   int methodCount, methodData;
#   int propertyCount, propertyData;
#   int enumeratorCount, enumeratorData;
#   int constructorCount, constructorData; //since revision 2
#   int flags; //since revision 3
#   int signalCount; //since revision 4

#    // content:
#          4,       // revision
#          0,       // classname
#          0,    0, // classinfo
#          4,   14, // methods
#          1,   34, // properties
#          0,    0, // enums/sets
#          2,   37, // constructors
#          0,       // flags
#          2,       // signalCount

#  /* 14 */

#    // signals: signature, parameters, type, tag, flags
#          9,    8,    8,    8, 0x05,
#         29,    8,    8,    8, 0x25,

#  /* 24 */
#    // slots: signature, parameters, type, tag, flags
#         41,    8,    8,    8, 0x0a,
#         55,    8,    8,    8, 0x08,

#  /* 34 */
#    // properties: name, type, flags
#         90,   82, 0x0a095103,

#  /* 37 */
#    // constructors: signature, parameters, type, tag, flags
#        108,  101,    8,    8, 0x0e,
#        126,    8,    8,    8, 0x2e,

#          0        // eod
#   };

#   static const char qt_meta_stringdata_QObject[] = {
#       "QObject\0\0destroyed(QObject*)\0destroyed()\0"
#       "deleteLater()\0_q_reregisterTimers(void*)\0"
#       "QString\0objectName\0parent\0QObject(QObject*)\0"
#       "QObject()\0"
#   };


# QSignalMapper

#   static const uint qt_meta_data_QSignalMapper[] = {

#    // content:
#          4,       // revision
#          0,       // classname
#          0,    0, // classinfo
#          7,   14, // methods
#          0,    0, // properties
#          0,    0, // enums/sets
#          0,    0, // constructors
#          0,       // flags
#          4,       // signalCount

#    // signals: signature, parameters, type, tag, flags
#         15,   14,   14,   14, 0x05,
#         27,   14,   14,   14, 0x05,
#         43,   14,   14,   14, 0x05,
#         60,   14,   14,   14, 0x05,

#    // slots: signature, parameters, type, tag, flags
#         77,   14,   14,   14, 0x0a,
#         90,   83,   14,   14, 0x0a,
#        104,   14,   14,   14, 0x08,

#          0        // eod
#   };

#   static const char qt_meta_stringdata_QSignalMapper[] = {
#       "QSignalMapper\0\0mapped(int)\0mapped(QString)\0"
#       "mapped(QWidget*)\0mapped(QObject*)\0"
#       "map()\0sender\0map(QObject*)\0"
#       "_q_senderDestroyed()\0"
#   };

#   const QMetaObject QSignalMapper::staticMetaObject = {
#       { &QObject::staticMetaObject, qt_meta_stringdata_QSignalMapper,
#         qt_meta_data_QSignalMapper, 0 }
#   };



# // Meta enumeration helpers
# static inline void dumpMetaEnumType(QDumper &d, const QMetaEnum &me)
# {
#     QByteArray type = me.scope()
#     if !type.isEmpty())
#         type += "::"
#     type += me.name()
#     d.putField("type", type.constData())
# }
#
# static inline void dumpMetaEnumValue(QDumper &d, const QMetaProperty &mop,
#                                      int value)
# {
#
#     const QMetaEnum me = mop.enumerator()
#     dumpMetaEnumType(d, me)
#     if const char *enumValue = me.valueToKey(value)) {
#         d.putValue(enumValue)
#     } else {
#         d.putValue(value)
#     }
#     d.putField("numchild", 0)
# }
#
# static inline void dumpMetaFlagValue(QDumper &d, const QMetaProperty &mop,
#                                      int value)
# {
#     const QMetaEnum me = mop.enumerator()
#     dumpMetaEnumType(d, me)
#     const QByteArray flagsValue = me.valueToKeys(value)
#     if flagsValue.isEmpty():
#         d.putValue(value)
#     else:
#         d.putValue(flagsValue.constData())
#     d.putNumChild(0)
# }

def qdump__QPixmap(d, value):
    offset = (3 if d.qtVersion() >= 0x050000 else 2) * d.ptrSize()
    base = d.dereference(d.addressOf(value) + offset)
    width = d.extractInt(base + d.ptrSize())
    height = d.extractInt(base + d.ptrSize() + 4)
    d.putValue("(%dx%d)" % (width, height))
    d.putNumChild(0)


def qdump__QPoint(d, value):
    x = int(value["xp"])
    y = int(value["yp"])
    d.putValue("(%s, %s)" % (x, y))
    d.putPlainChildren(value)


def qdump__QPointF(d, value):
    x = float(value["xp"])
    y = float(value["yp"])
    d.putValue("(%s, %s)" % (x, y))
    d.putPlainChildren(value)


def qdump__QRect(d, value):
    def pp(l):
        if l >= 0: return "+%s" % l
        return l
    x1 = int(value["x1"])
    y1 = int(value["y1"])
    x2 = int(value["x2"])
    y2 = int(value["y2"])
    w = x2 - x1 + 1
    h = y2 - y1 + 1
    d.putValue("%sx%s%s%s" % (w, h, pp(x1), pp(y1)))
    d.putPlainChildren(value)


def qdump__QRectF(d, value):
    def pp(l):
        if l >= 0: return "+%s" % l
        return l
    x = float(value["xp"])
    y = float(value["yp"])
    w = float(value["w"])
    h = float(value["h"])
    d.putValue("%sx%s%s%s" % (w, h, pp(x), pp(y)))
    d.putPlainChildren(value)


def qdump__QRegExp(d, value):
    # value.priv.engineKey.pattern
    privAddress = d.dereferenceValue(value)
    engineKeyAddress = privAddress + d.ptrSize()
    patternAddress = engineKeyAddress
    d.putStringValueByAddress(patternAddress)
    d.putNumChild(1)
    if d.isExpanded():
        with Children(d):
            # QRegExpPrivate:
            # - QRegExpEngine *eng               (+0)
            # - QRegExpEngineKey:                (+1ptr)
            #   - QString pattern;               (+1ptr)
            #   - QRegExp::PatternSyntax patternSyntax;  (+2ptr)
            #   - Qt::CaseSensitivity cs;        (+2ptr +1enum +pad?)
            # - bool minimal                     (+2ptr +2enum +2pad?)
            # - QString t                        (+2ptr +2enum +1bool +3pad?)
            # - QStringList captures             (+3ptr +2enum +1bool +3pad?)
            # FIXME: Remove need to call. Needed to warm up cache.
            d.call(value, "capturedTexts") # create cache
            ns = d.qtNamespace()
            with SubItem(d, "syntax"):
                # value["priv"]["engineKey"["capturedCache"]
                address = engineKeyAddress + d.ptrSize()
                typ = d.lookupType(ns + "QRegExp::PatternSyntax")
                d.putItem(d.createValue(address, typ))
            with SubItem(d, "captures"):
                # value["priv"]["capturedCache"]
                address = privAddress + 3 * d.ptrSize() + 12
                typ = d.lookupType(ns + "QStringList")
                d.putItem(d.createValue(address, typ))


def qdump__QRegion(d, value):
    p = value["d"].dereference()["qt_rgn"]
    if d.isNull(p):
        d.putValue("<empty>")
        d.putNumChild(0)
    else:
        # struct QRegionPrivate:
        # int numRects;
        # QVector<QRect> rects;
        # QRect extents;
        # QRect innerRect;
        # int innerArea;
        pp = d.dereferenceValue(p)
        n = d.extractInt(pp)
        d.putItemCount(n)
        d.putNumChild(n)
        if d.isExpanded():
            with Children(d):
                v = d.ptrSize()
                ns = d.qtNamespace()
                rectType = d.lookupType(ns + "QRect")
                d.putIntItem("numRects", n)
                d.putSubItem("extents", d.createValue(pp + 2 * v, rectType))
                d.putSubItem("innerRect", d.createValue(pp + 2 * v + rectType.sizeof, rectType))
                d.putIntItem("innerArea", d.extractInt(pp + 2 * v + 2 * rectType.sizeof))
                # FIXME
                try:
                    # Can fail if QVector<QRect> debuginfo is missing.
                    vectType = d.lookupType("%sQVector<%sQRect>" % (ns, ns))
                    d.putSubItem("rects", d.createValue(pp + v, vectType))
                except:
                    with SubItem(d, "rects"):
                        d.putItemCount(n)
                        d.putType("%sQVector<%sQRect>" % (ns, ns))
                        d.putNumChild(0)


def qdump__QScopedPointer(d, value):
    d.putBetterType(d.currentType)
    d.putItem(value["d"])


def qdump__QSet(d, value):

    def hashDataFirstNode(dPtr, numBuckets):
        ePtr = dPtr.cast(nodeTypePtr)
        bucket = dPtr["buckets"]
        for n in xrange(numBuckets - 1, -1, -1):
            n = n - 1
            if n < 0:
                break
            if d.pointerValue(bucket.dereference()) != d.pointerValue(ePtr):
                return bucket.dereference()
            bucket = bucket + 1
        return ePtr

    def hashDataNextNode(nodePtr, numBuckets):
        nextPtr = nodePtr.dereference()["next"]
        if d.pointerValue(nextPtr.dereference()["next"]):
            return nextPtr
        dPtr = nodePtr.cast(hashDataType.pointer()).dereference()
        start = (int(nodePtr.dereference()["h"]) % numBuckets) + 1
        bucket = dPtr.dereference()["buckets"] + start
        for n in xrange(numBuckets - start):
            if d.pointerValue(bucket.dereference()) != d.pointerValue(nextPtr):
                return bucket.dereference()
            bucket += 1
        return nodePtr

    anon = d.childAt(value, 0)
    if d.isLldb: # Skip the inheritance level.
        anon = d.childAt(anon, 0)
    d_ptr = anon["d"]
    e_ptr = anon["e"]
    size = int(d_ptr.dereference()["size"])

    d.check(0 <= size and size <= 100 * 1000 * 1000)
    d.checkRef(d_ptr["ref"])

    d.putItemCount(size)
    d.putNumChild(size)
    if d.isExpanded():
        hashDataType = d_ptr.type
        nodeTypePtr = d_ptr.dereference()["fakeNext"].type
        numBuckets = int(d_ptr.dereference()["numBuckets"])
        node = hashDataFirstNode(d_ptr, numBuckets)
        innerType = e_ptr.dereference().type
        with Children(d, size, maxNumChild=1000, childType=innerType):
            for i in d.childRange():
                it = node.dereference().cast(innerType)
                with SubItem(d, i):
                    d.putItem(it["key"])
                node = hashDataNextNode(node, numBuckets)


def qdump__QSharedData(d, value):
    d.putValue("ref: %s" % value["ref"]["_q_value"])
    d.putNumChild(0)


def qdump__QSharedDataPointer(d, value):
    d_ptr = value["d"]
    if d.isNull(d_ptr):
        d.putValue("(null)")
        d.putNumChild(0)
    else:
        # This replaces the pointer by the pointee, making the
        # pointer transparent.
        try:
            innerType = d.templateArgument(value.type, 0)
        except:
            d.putValue(d_ptr)
            d.putPlainChildren(value)
            return
        d.putBetterType(d.currentType)
        d.putItem(gdb.Value(d_ptr.cast(innerType.pointer())).dereference())
        # d.putItem(value.dereference())


def qdump__QSharedPointer(d, value):
    qdump__QWeakPointer(d, value)


def qdump__QSize(d, value):
    w = int(value["wd"])
    h = int(value["ht"])
    d.putValue("(%s, %s)" % (w, h))
    d.putPlainChildren(value)

def qdump__QSizeF(d, value):
    w = float(value["wd"])
    h = float(value["ht"])
    d.putValue("(%s, %s)" % (w, h))
    d.putPlainChildren(value)


def qdump__QStack(d, value):
    qdump__QVector(d, value)


def qdump__QStandardItem(d, value):
    d.putBetterType(d.currentType)
    try:
        d.putItem(value["d_ptr"])
    except:
        d.putPlainChildren(value)


def qedit__QString(expr, value):
    cmd = "call (%s).resize(%d)" % (expr, len(value))
    gdb.execute(cmd)
    d = gdb.parse_and_eval(expr)["d"]["data"]
    cmd = "set {short[%d]}%s={" % (len(value), d.pointerValue(d))
    for i in range(len(value)):
        if i != 0:
            cmd += ','
        cmd += str(ord(value[i]))
    cmd += '}'
    gdb.execute(cmd)

def qform__QString():
    return "Inline,Separate Window"

def qdump__QString(d, value):
    d.putStringValue(value)
    d.putNumChild(0)
    format = d.currentItemFormat()
    if format == 1:
        d.putDisplay(StopDisplay)
    elif format == 2:
        d.putField("editformat", DisplayUtf16String)
        d.putField("editvalue", d.encodeString(value))


def qdump__QStringRef(d, value):
    if d.isNull(value["m_string"]):
        d.putValue("(null)");
        d.putNumChild(0)
        return
    s = value["m_string"].dereference()
    data, size, alloc = d.stringData(s)
    data += 2 * int(value["m_position"])
    size = int(value["m_size"])
    s = d.readMemory(data, 2 * size)
    d.putValue(s, Hex4EncodedLittleEndian)
    d.putPlainChildren(value)


def qdump__QStringList(d, value):
    listType = d.directBaseClass(value.type).type
    qdump__QList(d, value.cast(listType))
    d.putBetterType(value.type)


def qdump__QTemporaryFile(d, value):
    qdump__QFile(d, value)


def qdump__QTextCodec(d, value):
    name = d.call(value, "name")
    d.putValue(d.encodeByteArray(d, name), 6)
    d.putNumChild(2)
    if d.isExpanded():
        with Children(d):
            d.putCallItem("name", value, "name")
            d.putCallItem("mibEnum", value, "mibEnum")


def qdump__QTextCursor(d, value):
    privAddress = d.dereferenceValue(value)
    if privAddress == 0:
        d.putValue("(invalid)")
        d.putNumChild(0)
    else:
        positionAddress = privAddress + 2 * d.ptrSize() + 8
        d.putValue(d.extractInt(positionAddress))
        d.putNumChild(1)
    if d.isExpanded():
        with Children(d):
            positionAddress = privAddress + 2 * d.ptrSize() + 8
            d.putIntItem("position", d.extractInt(positionAddress))
            d.putIntItem("anchor", d.extractInt(positionAddress + intSize))
            d.putCallItem("selected", value, "selectedText")


def qdump__QTextDocument(d, value):
    d.putEmptyValue()
    d.putNumChild(1)
    if d.isExpanded():
        with Children(d):
            d.putCallItem("blockCount", value, "blockCount")
            d.putCallItem("characterCount", value, "characterCount")
            d.putCallItem("lineCount", value, "lineCount")
            d.putCallItem("revision", value, "revision")
            d.putCallItem("toPlainText", value, "toPlainText")


def qdump__QUrl(d, value):
    if d.qtVersion() < 0x050000:
        if not d.dereferenceValue(value):
            # d == 0 if QUrl was constructed with default constructor
            d.putValue("<invalid>")
            return
        data = value["d"].dereference()
        d.putByteArrayValue(data["encodedOriginal"])
        d.putPlainChildren(data)
    else:
        # QUrlPrivate:
        # - QAtomicInt ref;
        # - int port;
        # - QString scheme;
        # - QString userName;
        # - QString password;
        # - QString host;
        # - QString path;
        # - QString query;
        # - QString fragment;
        privAddress = d.dereferenceValue(value)
        if not privAddress:
            # d == 0 if QUrl was constructed with default constructor
            d.putValue("<invalid>")
            return
        schemeAddr = privAddress + 2 * d.intSize()
        scheme = d.encodeStringHelper(d.dereference(schemeAddr))
        userName = d.encodeStringHelper(d.dereference(schemeAddr + 1 * d.ptrSize()))
        password = d.encodeStringHelper(d.dereference(schemeAddr + 2 * d.ptrSize()))
        host = d.encodeStringHelper(d.dereference(schemeAddr + 3 * d.ptrSize()))
        path = d.encodeStringHelper(d.dereference(schemeAddr + 4 * d.ptrSize()))
        query = d.encodeStringHelper(d.dereference(schemeAddr + 5 * d.ptrSize()))
        fragment = d.encodeStringHelper(d.dereference(schemeAddr + 6 * d.ptrSize()))
        port = d.extractInt(d.dereferenceValue(value) + d.intSize())

        url = scheme
        url += "3a002f002f00"
        if len(userName):
            url += userName
            url += "4000"
        url += host
        if port >= 0:
            url += "3a00"
            url += ''.join(["%02x00" % ord(c) for c in str(port)])
        url += path
        d.putValue(url, Hex4EncodedLittleEndian)
        d.putNumChild(8)
        if d.isExpanded():
            stringType = d.lookupType(d.qtNamespace() + "QString")
            with Children(d):
                d.putIntItem("port", port)
                d.putGenericItem("scheme", stringType, scheme, Hex4EncodedLittleEndian)
                d.putGenericItem("userName", stringType, userName, Hex4EncodedLittleEndian)
                d.putGenericItem("password", stringType, password, Hex4EncodedLittleEndian)
                d.putGenericItem("host", stringType, host, Hex4EncodedLittleEndian)
                d.putGenericItem("path", stringType, path, Hex4EncodedLittleEndian)
                d.putGenericItem("query", stringType, query, Hex4EncodedLittleEndian)
                d.putGenericItem("fragment", stringType, fragment, Hex4EncodedLittleEndian)

def qdumpHelper_QVariant_0(d, data):
    # QVariant::Invalid
    d.putBetterType("%sQVariant (invalid)" % d.qtNamespace())
    d.putValue("(invalid)")

def qdumpHelper_QVariant_1(d, data):
    # QVariant::Bool
    d.putBetterType("%sQVariant (bool)" % d.qtNamespace())
    if int(data["b"]):
        d.putValue("true")
    else:
        d.putValue("false")

def qdumpHelper_QVariant_2(d, data):
    # QVariant::Int
    d.putBetterType("%sQVariant (int)" % d.qtNamespace())
    d.putValue(int(data["i"]))

def qdumpHelper_QVariant_3(d, data):
    # uint
    d.putBetterType("%sQVariant (uint)" % d.qtNamespace())
    d.putValue(int(data["u"]))

def qdumpHelper_QVariant_4(d, data):
    # qlonglong
    d.putBetterType("%sQVariant (qlonglong)" % d.qtNamespace())
    d.putValue(int(data["ll"]))

def qdumpHelper_QVariant_5(d, data):
    # qulonglong
    d.putBetterType("%sQVariant (qulonglong)" % d.qtNamespace())
    d.putValue(int(data["ull"]))

def qdumpHelper_QVariant_6(d, data):
    # QVariant::Double
    d.putBetterType("%sQVariant (double)" % d.qtNamespace())
    d.putValue(float(data["d"]))

qdumpHelper_QVariants_A = [
    qdumpHelper_QVariant_0,
    qdumpHelper_QVariant_1,
    qdumpHelper_QVariant_2,
    qdumpHelper_QVariant_3,
    qdumpHelper_QVariant_4,
    qdumpHelper_QVariant_5,
    qdumpHelper_QVariant_6
]


qdumpHelper_QVariants_B = [
    "QChar",       # 7
    "QVariantMap", # 8
    "QVariantList",# 9
    "QString",     # 10
    "QStringList", # 11
    "QByteArray",  # 12
    "QBitArray",   # 13
    "QDate",       # 14
    "QTime",       # 15
    "QDateTime",   # 16
    "QUrl",        # 17
    "QLocale",     # 18
    "QRect",       # 19
    "QRectF",      # 20
    "QSize",       # 21
    "QSizeF",      # 22
    "QLine",       # 23
    "QLineF",      # 24
    "QPoint",      # 25
    "QPointF",     # 26
    "QRegExp",     # 27
    "QVariantHash",# 28
]

qdumpHelper_QVariants_C = [
    "QFont",       # 64
    "QPixmap",     # 65
    "QBrush",      # 66
    "QColor",      # 67
    "QPalette",    # 68
    "QIcon",       # 69
    "QImage",      # 70
    "QPolygon",    # 71
    "QRegion",     # 72
    "QBitmap",     # 73
    "QCursor",     # 74
    "QSizePolicy", # 75
    "QKeySequence",# 76
    "QPen",        # 77
    "QTextLength", # 78
    "QTextFormat", # 79
    "X",           # 80
    "QTransform",  # 81
    "QMatrix4x4",  # 82
    "QVector2D",   # 83
    "QVector3D",   # 84
    "QVector4D",   # 85
    "QQuadernion"  # 86
]

def qdumpHelper__QVariant(d, value):
    data = value["d"]["data"]
    variantType = int(value["d"]["type"])
    #warn("VARIANT TYPE: %s : " % variantType)

    # Well-known simple type.
    if variantType <= 6:
        qdumpHelper_QVariants_A[variantType](d, data)
        d.putNumChild(0)
        return (None, None, True)

    # Unknown user type.
    if variantType > 86:
        return (None, "", False)

    # Known Core or Gui type.
    if variantType <= 28:
        innert = qdumpHelper_QVariants_B[variantType - 7]
    else:
        innert = qdumpHelper_QVariants_C[variantType - 64]

    inner = d.qtNamespace() + innert

    innerType = d.lookupType(inner)
    sizePD = 8 # sizeof(QVariant::Private::Data)
    isSpecial = d.qtVersion() >= 0x050000 \
            and (innert == "QVariantMap" or innert == "QVariantHash")
    if innerType.sizeof > sizePD or isSpecial:
        sizePS = 2 * d.ptrSize() # sizeof(QVariant::PrivateShared)
        val = (data.cast(d.charPtrType()) + sizePS) \
            .cast(innerType.pointer()).dereference()
    else:
        val = data.cast(innerType)

    d.putEmptyValue(-99)
    d.putItem(val)
    d.putBetterType("%sQVariant (%s)" % (d.qtNamespace(), innert))

    return (None, innert, True)


def qdump__QVariant(d, value):
    (val, innert, handled) = qdumpHelper__QVariant(d, value)

    if handled:
        return innert

    # User types.
    d_ptr = value["d"]
    typeCode = int(d_ptr["type"])
    ns = d.qtNamespace()
    try:
        exp = "((const char *(*)(int))%sQMetaType::typeName)(%d)" % (ns, typeCode)
        type = str(d.parseAndEvaluate(exp))
    except:
        exp = "%sQMetaType::typeName(%d)" % (ns, typeCode)
        type = str(d.parseAndEvaluate(exp))
    type = type[type.find('"') + 1 : type.rfind('"')]
    type = type.replace("Q", ns + "Q") # HACK!
    type = type.replace("uint", "unsigned int") # HACK!
    type = type.replace("COMMA", ",") # HACK!
    type = type.replace(" ,", ",") # Lldb
    #warn("TYPE: %s" % type)
    data = d.call(value, "constData")
    #warn("DATA: %s" % data)
    d.putEmptyValue(-99)
    d.putType("%sQVariant (%s)" % (ns, type))
    d.putNumChild(1)
    tdata = data.cast(d.lookupType(type).pointer()).dereference()
    if d.isExpanded():
        with Children(d):
            with NoAddress(d):
                d.putSubItem("data", tdata)
    return tdata.type


def qedit__QVector(expr, value):
    values = value.split(',')
    ob = gdb.parse_and_eval(expr)
    cmd = "call (%s).resize(%d)" % (expr, len(values))
    gdb.execute(cmd)
    innerType = d.templateArgument(ob.type, 0)
    ptr = ob["p"]["array"].cast(d.voidPtrType())
    cmd = "set {%s[%d]}%s={%s}" % (innerType, len(values), d.pointerValue(ptr), value)
    gdb.execute(cmd)


def qform__QVector():
    return arrayForms()


def qdump__QVector(d, value):
    private = value["d"]
    d.checkRef(private["ref"])
    alloc = int(private["alloc"])
    size = int(private["size"])
    innerType = d.templateArgument(value.type, 0)
    try:
        # Qt 5. Will fail on Qt 4 due to the missing 'offset' member.
        offset = private["offset"]
        data = private.cast(d.charPtrType()) + offset
    except:
        # Qt 4.
        data = value["p"]["array"]

    p = data.cast(innerType.pointer())

    d.check(0 <= size and size <= alloc and alloc <= 1000 * 1000 * 1000)
    d.putItemCount(size)
    d.putNumChild(size)
    d.putPlotData(innerType, p, size, 2)


def qdump__QWeakPointer(d, value):
    d_ptr = value["d"]
    val = value["value"]
    if d.isNull(d_ptr) and d.isNull(val):
        d.putValue("(null)")
        d.putNumChild(0)
        return
    if d.isNull(d_ptr) or d.isNull(val):
        d.putValue("<invalid>")
        d.putNumChild(0)
        return
    weakref = int(d_ptr["weakref"]["_q_value"])
    strongref = int(d_ptr["strongref"]["_q_value"])
    d.check(strongref >= -1)
    d.check(strongref <= weakref)
    d.check(weakref <= 10*1000*1000)

    innerType = d.templateArgument(value.type, 0)
    if d.isSimpleType(innerType):
        d.putSimpleValue(val.dereference())
    else:
        d.putEmptyValue()

    d.putNumChild(3)
    if d.isExpanded():
        with Children(d):
            d.putSubItem("data", val.dereference().cast(innerType))
            d.putIntItem("weakref", weakref)
            d.putIntItem("strongref", strongref)


def qdump__QxXmlAttributes(d, value):
    pass


#######################################################################
#
# Webkit
#
#######################################################################


def jstagAsString(tag):
    # enum { Int32Tag =        0xffffffff };
    # enum { CellTag =         0xfffffffe };
    # enum { TrueTag =         0xfffffffd };
    # enum { FalseTag =        0xfffffffc };
    # enum { NullTag =         0xfffffffb };
    # enum { UndefinedTag =    0xfffffffa };
    # enum { EmptyValueTag =   0xfffffff9 };
    # enum { DeletedValueTag = 0xfffffff8 };
    if tag == -1:
        return "Int32"
    if tag == -2:
        return "Cell"
    if tag == -3:
        return "True"
    if tag == -4:
        return "Null"
    if tag == -5:
        return "Undefined"
    if tag == -6:
        return "Empty"
    if tag == -7:
        return "Deleted"
    return "Unknown"



def qdump__QTJSC__JSValue(d, value):
    d.putEmptyValue()
    d.putNumChild(1)
    if d.isExpanded():
        with Children(d):
            tag = value["u"]["asBits"]["tag"]
            payload = value["u"]["asBits"]["payload"]
            #d.putIntItem("tag", tag)
            with SubItem(d, "tag"):
                d.putValue(jstagAsString(int(tag)))
                d.putNoType()
                d.putNumChild(0)

            d.putIntItem("payload", int(payload))
            d.putFields(value["u"])

            if tag == -2:
                cellType = d.lookupType("QTJSC::JSCell").pointer()
                d.putSubItem("cell", payload.cast(cellType))

            try:
                # FIXME: This might not always be a variant.
                delegateType = d.lookupType(d.qtNamespace() + "QScript::QVariantDelegate").pointer()
                delegate = scriptObject["d"]["delegate"].cast(delegateType)
                #d.putSubItem("delegate", delegate)
                variant = delegate["m_value"]
                d.putSubItem("variant", variant)
            except:
                pass


def qdump__QScriptValue(d, value):
    # structure:
    #  engine        QScriptEnginePrivate
    #  jscValue      QTJSC::JSValue
    #  next          QScriptValuePrivate *
    #  numberValue   5.5987310416280426e-270 myns::qsreal
    #  prev          QScriptValuePrivate *
    #  ref           QBasicAtomicInt
    #  stringValue   QString
    #  type          QScriptValuePrivate::Type: { JavaScriptCore, Number, String }
    #d.putEmptyValue()
    dd = value["d_ptr"]["d"]
    ns = d.qtNamespace()
    if d.isNull(dd):
        d.putValue("(invalid)")
        d.putNumChild(0)
        return
    if int(dd["type"]) == 1: # Number
        d.putValue(dd["numberValue"])
        d.putType("%sQScriptValue (Number)" % ns)
        d.putNumChild(0)
        return
    if int(dd["type"]) == 2: # String
        d.putStringValue(dd["stringValue"])
        d.putType("%sQScriptValue (String)" % ns)
        return

    d.putType("%sQScriptValue (JSCoreValue)" % ns)
    x = dd["jscValue"]["u"]
    tag = x["asBits"]["tag"]
    payload = x["asBits"]["payload"]
    #isValid = int(x["asBits"]["tag"]) != -6   # Empty
    #isCell = int(x["asBits"]["tag"]) == -2
    #warn("IS CELL: %s " % isCell)
    #isObject = False
    #className = "UNKNOWN NAME"
    #if isCell:
    #    # isCell() && asCell()->isObject();
    #    # in cell: m_structure->typeInfo().type() == ObjectType;
    #    cellType = d.lookupType("QTJSC::JSCell").pointer()
    #    cell = payload.cast(cellType).dereference()
    #    dtype = "NO DYNAMIC TYPE"
    #    try:
    #        dtype = cell.dynamic_type
    #    except:
    #        pass
    #    warn("DYNAMIC TYPE: %s" % dtype)
    #    warn("STATUC  %s" % cell.type)
    #    type = cell["m_structure"]["m_typeInfo"]["m_type"]
    #    isObject = int(type) == 7 # ObjectType;
    #    className = "UNKNOWN NAME"
    #warn("IS OBJECT: %s " % isObject)

    #inline bool JSCell::inherits(const ClassInfo* info) const
    #for (const ClassInfo* ci = classInfo(); ci; ci = ci->parentClass) {
    #    if (ci == info)
    #        return true;
    #return false;

    try:
        # This might already fail for "native" payloads.
        scriptObjectType = d.lookupType(ns + "QScriptObject").pointer()
        scriptObject = payload.cast(scriptObjectType)

        # FIXME: This might not always be a variant.
        delegateType = d.lookupType(ns + "QScript::QVariantDelegate").pointer()
        delegate = scriptObject["d"]["delegate"].cast(delegateType)
        #d.putSubItem("delegate", delegate)

        variant = delegate["m_value"]
        #d.putSubItem("variant", variant)
        t = qdump__QVariant(d, variant)
        # Override the "QVariant (foo)" output
        d.putBetterType("%sQScriptValue (%s)" % (ns, t))
        if t != "JSCoreValue":
            return
    except:
        pass

    # This is a "native" JSCore type for e.g. QDateTime.
    d.putValue("<native>")
    d.putNumChild(1)
    if d.isExpanded():
        with Children(d):
           d.putSubItem("jscValue", dd["jscValue"])

