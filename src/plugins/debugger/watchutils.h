/**************************************************************************
**
** This file is part of Qt Creator
**
** Copyright (c) 2009 Nokia Corporation and/or its subsidiary(-ies).
**
** Contact: Nokia Corporation (qt-info@nokia.com)
**
** Commercial Usage
**
** Licensees holding valid Qt Commercial licenses may use this file in
** accordance with the Qt Commercial License Agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and Nokia.
**
** GNU Lesser General Public License Usage
**
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 2.1 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL included in the
** packaging of this file.  Please review the following information to
** ensure the GNU Lesser General Public License version 2.1 requirements
** will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
**
** If you are unsure which license is appropriate for your use, please
** contact the sales department at http://www.qtsoftware.com/contact.
**
**************************************************************************/

#ifndef WATCHUTILS_H
#define WATCHUTILS_H

#include <QtCore/QString>
#include <QtCore/QMap>

QT_BEGIN_NAMESPACE
class QDebug;
QT_END_NAMESPACE

namespace TextEditor {
    class ITextEditor;
}

namespace Core {
    class IEditor;
}

namespace Debugger {
namespace Internal {

class WatchData;

QString dotEscape(QString str);
QString currentTime();
bool isSkippableFunction(const QString &funcName, const QString &fileName);
bool isLeavableFunction(const QString &funcName, const QString &fileName);

inline bool isNameChar(char c)
{
    // could be 'stopped' or 'shlibs-added'
    return (c >= 'a' && c <= 'z') || c == '-';
}

bool hasLetterOrNumber(const QString &exp);
bool hasSideEffects(const QString &exp);
bool isKeyWord(const QString &exp);
bool isPointerType(const QString &type);
bool isAccessSpecifier(const QString &str);
bool startsWithDigit(const QString &str);
QString stripPointerType(QString type);
QString gdbQuoteTypes(const QString &type);
bool extractTemplate(const QString &type, QString *tmplate, QString *inner);
QString extractTypeFromPTypeOutput(const QString &str);
bool isIntOrFloatType(const QString &type);
bool isIntType(const QString &type);

enum GuessChildrenResult { HasChildren, HasNoChildren, HasPossiblyChildren };
GuessChildrenResult guessChildren(const QString &type);

QString sizeofTypeExpression(const QString &type);
QString quoteUnprintableLatin1(const QByteArray &ba);

// Editor tooltip support
bool isCppEditor(Core::IEditor *editor);
QString cppExpressionAt(TextEditor::ITextEditor *editor, int pos,
                        int *line, int *column, QString *function = 0);

// Decode string data as returned by the dumper helpers.
QString decodeData(const QByteArray &baIn, int encoding);

// Result of a dumper call.
struct QtDumperResult
{
    struct Child {
        Child();

        int keyEncoded;
        int valueEncoded;
        int childCount;
        bool valuedisabled;
        QString name;
        QString address;
        QString exp;
        QString type;
        QByteArray key;
        bool valueEncountered;
        QByteArray value;
    };

    QtDumperResult();
    void clear();
    QList<WatchData> toWatchData(int source = 0) const;

    QString iname;
    QString address;
    QString addressInfo; // "<synthetic>" or such, in the 2nd adress field.
    QString type;
    QString extra;
    QString displayedType;
    bool valueEncountered;
    QByteArray value;
    int valueEncoded;
    bool valuedisabled;
    int childCount;
    bool internal;
    QString childType;
    int childChildCount;
    QList <Child> children;
};

QDebug operator<<(QDebug in, const QtDumperResult &d);

/* Attempt to put common code of the dumper handling into a helper
 * class.
 * "Custom dumper" is a library compiled against the current
 * Qt containing functions to evaluate values of Qt classes
 * (such as QString, taking pointers to their addresses).
 * The library must be loaded into the debuggee.
 * It provides a function that takes input from an input buffer
 * and some parameters and writes output into an output buffer.
 * Parameter 1 is the protocol:
 * 1) Query. Fills output buffer with known types, Qt version and namespace.
 *    This information is parsed and stored by this class (special type
 *    enumeration).
 * 2) Evaluate symbol, taking address and some additional parameters
 *    depending on type. */

class QtDumperHelper
{
public:
    enum Debugger {
        GdbDebugger,  // Can evalulate expressions in function calls
        CdbDebugger   // Can only handle scalar, simple types in function calls
    };

    enum Type {
        UnknownType,
        SupportedType, // A type that requires no special handling by the dumper
        // Below types require special handling
        QAbstractItemType,
        QObjectType, QWidgetType, QObjectSlotType, QObjectSignalType,
        QVectorType, QMapType, QMultiMapType, QMapNodeType,
        StdVectorType, StdDequeType, StdSetType, StdMapType, StdStackType,
        StdStringType
    };

    // Type/Parameter struct required for building a value query
    struct TypeData {
        TypeData();
        void clear();

        Type type;
        bool isTemplate;
        QString tmplate;
        QString inner;
    };

    QtDumperHelper();
    void clear();

    double dumperVersion() const { return m_dumperVersion; }
    void setDumperVersion(double v)  { m_dumperVersion = v; }

    int typeCount() const;
    // Look up a simple, non-template  type
    Type simpleType(const QString &simpleType) const;
    // Look up a (potentially) template type and fill parameter struct
    TypeData typeData(const QString &typeName) const;
    Type type(const QString &typeName) const;

    int qtVersion() const;
    QString qtVersionString() const;
    void setQtVersion(int v);
    void setQtVersion(const QString &v);

    QString qtNamespace() const;
    void setQtNamespace(const QString &qtNamespace);

    // Complete parse of "query" (protocol 1) response from debuggee buffer.
    // 'data' excludes the leading indicator character.
    bool parseQuery(const char *data, Debugger debugger);
    // Set up from pre-parsed type list
    void parseQueryTypes(const QStringList &l, Debugger debugger);

    // Determine the parameters required for an "evaluate" (protocol 2) call
    void evaluationParameters(const WatchData &data,
                              const TypeData &td,
                              Debugger debugger,
                              QByteArray *inBuffer,
                              QStringList *extraParameters) const;

    // Parse the value response (protocol 2) from debuggee buffer.
    // 'data' excludes the leading indicator character.
    static bool parseValue(const char *data, QtDumperResult *r);

    // What kind of debugger expressions are required to dump that type.
    // A debugger with restricted expression syntax can handle
    // 'NeedsNoExpression' and 'NeedsCachedExpression' if it is found in
    // the cache.
    enum ExpressionRequirement {
        NeedsNoExpression,     // None, easy.
        NeedsCachedExpression, // Common values might be found in expression cache.
        NeedsComplexExpression // Totally arbitrary, adress-dependent expressions
    };
    static ExpressionRequirement expressionRequirements(Type t);

    QString toString(bool debug = false) const;

    // Helpers for debuggers that use a different dumper parser.
    void addSize(const QString &name, int size);
    void addExpression(const QString &expression, const QString &value);

    static QString msgDumperOutdated(double requiredVersion, double currentVersion);

private:
    typedef QMap<QString, Type> NameTypeMap;
    typedef QMap<QString, int> SizeCache;

    // Look up a simple (namespace) type
    static Type specialType(QString s);
    QString evaluationSizeofTypeExpression(const QString &typeName, Debugger d) const;

    NameTypeMap m_nameTypeMap;
    SizeCache m_sizeCache;

    // The initial dumper query function returns sizes of some special
    // types to aid CDB since it cannot determine the size of classes.
    // They are not complete (std::allocator<X>).
    enum SpecialSizeType { IntSize, PointerSize, StdAllocatorSize,
                           QSharedPointerSize, QSharedDataPointerSize,
                           QWeakPointerSize, QPointerSize, SpecialSizeCount };

    // Resolve name to enumeration or SpecialSizeCount (invalid)
    SpecialSizeType specialSizeType(const QString &t) const;

    int m_specialSizes[SpecialSizeCount];

    QMap<QString, QString> m_expressionCache;
    int m_qtVersion;
    double m_dumperVersion;
    QString m_qtNamespace;

    void setQClassPrefixes(const QString &qNamespace);

    QString m_qPointerPrefix;
    QString m_qSharedPointerPrefix;
    QString m_qSharedDataPointerPrefix;
    QString m_qWeakPointerPrefix;
};

QDebug operator<<(QDebug in, const QtDumperHelper::TypeData &d);

// remove the default template argument in std:: containers
QString removeDefaultTemplateArguments(QString type);

} // namespace Internal
} // namespace Debugger

#endif // WATCHUTILS_H
