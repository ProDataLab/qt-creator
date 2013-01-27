/****************************************************************************
**
** Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
** Contact: http://www.qt-project.org/legal
**
** This file is part of Qt Creator.
**
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and Digia.  For licensing terms and
** conditions see http://qt.digia.com/licensing.  For further information
** use the contact form at http://qt.digia.com/contact-us.
**
** GNU Lesser General Public License Usage
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 2.1 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL included in the
** packaging of this file.  Please review the following information to
** ensure the GNU Lesser General Public License version 2.1 requirements
** will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
**
** In addition, as a special exception, Digia gives you certain additional
** rights.  These rights are described in the Digia Qt LGPL Exception
** version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
**
****************************************************************************/

#include "completionproposalsbuilder.h"
#include "utils_p.h"

#include <QTextDocument>
#include <QCoreApplication>

namespace ClangCodeModel {

/**
 * @class ClangCodeModel::CompletionProposalsBuilder
 * @brief Captures completion lists and than processes sequence of completion chunks
 *
 * Can produce several completion proposals for one CXCompletionResult, if and
 * only if result contains chunks with kind 'Optional'
 * Different proposals can have the same text, it's normal behavior.
 *
 * @note Unresolved problems:
 *  Function hint not appear after space: "foo(1, ";
 *  Slot can have optional arguments, that produces 2 slots.
 */

CompletionProposalsBuilder::CompletionProposalsBuilder(QList<CodeCompletionResult> &results, quint64 contexts, bool isSignalSlotCompletion)
    : m_results(results)
    , m_contexts(contexts)
    , m_isSignalSlotCompletion(isSignalSlotCompletion)
{
}

void CompletionProposalsBuilder::operator ()(const CXCompletionResult &cxResult)
{
    resetWithResult(cxResult);

#if defined(CINDEX_VERSION) // since clang 3.2
    const QString brief = Internal::getQString(clang_getCompletionBriefComment(cxResult.CompletionString));
    if (!brief.isEmpty())
        m_comment += QLatin1String("<b>@brief</b> ") + Qt::escape(brief);
#endif

    if (m_resultAvailability == CodeCompletionResult::Deprecated) {
        m_comment += QLatin1String("<b>@note</b> ");
        m_comment += QCoreApplication::translate("deprecated C++ symbol", "Is deprecated");
    }

    m_hint = QLatin1String("<p>");
    switch (m_resultKind) {
    case CodeCompletionResult::ObjCMessageCompletionKind:
        concatChunksForObjectiveCMessage(cxResult.CompletionString);
        break;
    case CodeCompletionResult::ClassCompletionKind:
    case CodeCompletionResult::NamespaceCompletionKind:
    case CodeCompletionResult::EnumeratorCompletionKind:
        concatChunksForNestedName(cxResult.CompletionString);
        break;
    case CodeCompletionResult::ClangSnippetKind:
        concatChunksAsSnippet(cxResult.CompletionString);
        break;
    case CodeCompletionResult::SlotCompletionKind:
    case CodeCompletionResult::SignalCompletionKind:
        if (m_isSignalSlotCompletion)
            concatSlotSignalSignature(cxResult.CompletionString);
        else
            concatChunksOnlyTypedText(cxResult.CompletionString);
        break;
    default:
        concatChunksOnlyTypedText(cxResult.CompletionString);
        break;
    }
    m_hint += QLatin1String("</p>");
    m_hint += m_comment;

    finalize();
    foreach (const OptionalChunk &chunk, m_optionalChunks) {
        m_hint.insert(chunk.positionInHint, chunk.hint);
        finalize();
    }
}

/**
 * @return Internal ClangCodeModel's completion kind, that affects further postprocessing
 */
CodeCompletionResult::Kind CompletionProposalsBuilder::getKind(const CXCompletionResult &cxResult)
{
    CXCompletionString complStr = cxResult.CompletionString;
    CXCursorKind cursorKind = cxResult.CursorKind;

    switch (cursorKind) {
    case CXCursor_Constructor:
        return CodeCompletionResult::ConstructorCompletionKind;

    case CXCursor_Destructor:
        return CodeCompletionResult::DestructorCompletionKind;

    case CXCursor_CXXMethod: {
        const unsigned numAnnotations = clang_getCompletionNumAnnotations(complStr);
        bool isSignal = false, isSlot = false;
        for (unsigned i = 0; i < numAnnotations && !isSignal && !isSlot; ++i) {
            CXString cxAnn = clang_getCompletionAnnotation(complStr, i);
            QString ann = Internal::getQString(cxAnn);
            isSignal = ann == QLatin1String("qt_signal");
            isSlot = ann == QLatin1String("qt_slot");
        }
        if (isSignal)
            return CodeCompletionResult::SignalCompletionKind;
        if (isSlot)
            return CodeCompletionResult::SlotCompletionKind;
    } // intentional fall-through!
    case CXCursor_ConversionFunction:
    case CXCursor_FunctionDecl:
    case CXCursor_FunctionTemplate:
    case CXCursor_MemberRef:
    case CXCursor_MemberRefExpr:
        return CodeCompletionResult::FunctionCompletionKind;
        break;

    case CXCursor_FieldDecl:
    case CXCursor_VarDecl:
    case CXCursor_ParmDecl:
    case CXCursor_ObjCIvarDecl:
    case CXCursor_ObjCPropertyDecl:
    case CXCursor_ObjCSynthesizeDecl:
    case CXCursor_NonTypeTemplateParameter:
        return CodeCompletionResult::VariableCompletionKind;

    case CXCursor_Namespace:
    case CXCursor_NamespaceAlias:
    case CXCursor_NamespaceRef:
        return CodeCompletionResult::NamespaceCompletionKind;

    case CXCursor_StructDecl:
    case CXCursor_UnionDecl:
    case CXCursor_ClassDecl:
    case CXCursor_TypeRef:
    case CXCursor_TemplateRef:
    case CXCursor_TypedefDecl:
    case CXCursor_ClassTemplate:
    case CXCursor_ClassTemplatePartialSpecialization:
    case CXCursor_ObjCClassRef:
    case CXCursor_ObjCInterfaceDecl:
    case CXCursor_ObjCImplementationDecl:
    case CXCursor_ObjCCategoryDecl:
    case CXCursor_ObjCCategoryImplDecl:
    case CXCursor_ObjCProtocolDecl:
    case CXCursor_ObjCProtocolRef:
    case CXCursor_TemplateTypeParameter:
    case CXCursor_TemplateTemplateParameter:
        return CodeCompletionResult::ClassCompletionKind;

    case CXCursor_EnumConstantDecl:
        return CodeCompletionResult::EnumeratorCompletionKind;

    case CXCursor_EnumDecl:
        return CodeCompletionResult::EnumCompletionKind;

    case CXCursor_MacroDefinition: {
        const unsigned numChunks = clang_getNumCompletionChunks(complStr);
        for (unsigned i = 0; i < numChunks; ++i) {
            CXCompletionChunkKind kind = clang_getCompletionChunkKind(complStr, i);
            if (kind == CXCompletionChunk_Placeholder) {
                return CodeCompletionResult::FunctionCompletionKind;
            }
        }
        return CodeCompletionResult::PreProcessorCompletionKind;
    }

    case CXCursor_PreprocessingDirective:
    case CXCursor_MacroExpansion:
    case CXCursor_InclusionDirective:
        return CodeCompletionResult::PreProcessorCompletionKind;

    case CXCursor_ObjCClassMethodDecl:
    case CXCursor_ObjCInstanceMethodDecl:
        return CodeCompletionResult::ObjCMessageCompletionKind;

    case CXCursor_NotImplemented: {
        const unsigned numChunks = clang_getNumCompletionChunks(complStr);
        for (unsigned i = 0; i < numChunks; ++i) {
            CXCompletionChunkKind kind = clang_getCompletionChunkKind(complStr, i);
            if (kind == CXCompletionChunk_Placeholder) {
                return CodeCompletionResult::ClangSnippetKind;
            }
        }
        return CodeCompletionResult::KeywordCompletionKind;
    }

    default:
        break;
    }

    return CodeCompletionResult::Other;
}

/**
 * @return Symbol availability, which is almost unused
 */
CodeCompletionResult::Availability CompletionProposalsBuilder::getAvailability(const CXCompletionResult &cxResult)
{
    CXCompletionString complStr = cxResult.CompletionString;
    switch (clang_getCompletionAvailability(complStr)) {
    case CXAvailability_Deprecated:
        return CodeCompletionResult::Deprecated;

    case CXAvailability_NotAvailable:
        return CodeCompletionResult::NotAvailable;

    case CXAvailability_NotAccessible:
        return CodeCompletionResult::NotAccessible;

    default:
        return CodeCompletionResult::Available;
    }
}

/**
 * @return Start index of name, which is unused in Qt signal/slot signature
 * @param text Text of Placeholder completion string chunk
 */
int CompletionProposalsBuilder::findNameInPlaceholder(const QString &text)
{
    bool firstIdPassed = false;
    bool isInIdentifier = false;
    int bracesCounter = 0;
    int idStart = 0;

    for (int i = 0, n = text.size(); i < n; ++i) {
        const QChar ch = text[i];

        if (ch == QLatin1Char(':')) {
            firstIdPassed = false;
            isInIdentifier = false;
        }

        if (ch == QLatin1Char('<') || ch == QLatin1Char('(')) {
            if (isInIdentifier && text.mid(idStart, i - idStart) == QLatin1String("const"))
                firstIdPassed = false;
            ++bracesCounter;
            isInIdentifier = false;
        } else if (ch == QLatin1Char('>') || ch == QLatin1Char(')')) {
            if (isInIdentifier && text.mid(idStart, i - idStart) == QLatin1String("const"))
                firstIdPassed = false;
            --bracesCounter;
            isInIdentifier = false;
        } else if (bracesCounter == 0) {
            if (isInIdentifier) {
                isInIdentifier = ch.isLetterOrNumber() || (ch == QLatin1Char('_'));
                if (!isInIdentifier && text.mid(idStart, i - idStart) == QLatin1String("const"))
                    firstIdPassed = false;
            } else if (ch.isLetter() || (ch == QLatin1Char('_'))) {
                if (firstIdPassed)
                    return i;
                isInIdentifier = true;
                idStart = i;
                firstIdPassed = true;
            }
        }
    }
    return text.size();
}

void CompletionProposalsBuilder::resetWithResult(const CXCompletionResult &cxResult)
{
    m_priority = clang_getCompletionPriority(cxResult.CompletionString);
    m_resultKind = getKind(cxResult);
    m_resultAvailability = getAvailability(cxResult);
    m_hasParameters = false;
    m_hint.clear();
    m_text.clear();
    m_snippet.clear();
    m_comment.clear();
    m_optionalChunks.clear();
}

/**
 * @brief Appends completion proposal initialized with collected data
 */
void CompletionProposalsBuilder::finalize()
{
    // Fixes code completion: operator and destructor cases
    if ((m_contexts & CXCompletionContext_DotMemberAccess)
            || (m_contexts & CXCompletionContext_ArrowMemberAccess)
            || (m_contexts & CXCompletionContext_AnyValue)) {
        if (m_resultKind == CodeCompletionResult::DestructorCompletionKind)
            return;
        if (m_resultKind == CodeCompletionResult::FunctionCompletionKind)
            if (m_text.startsWith(QLatin1String("operator")))
                return;
    }

    CodeCompletionResult ccr(m_priority);
    ccr.setCompletionKind(m_resultKind);
    ccr.setAvailability(m_resultAvailability);
    ccr.setHasParameters(m_hasParameters);
    ccr.setHint(m_hint);
    ccr.setText(m_text);
    ccr.setSnippet(m_snippet);
    m_results.append(ccr);
}

/**
 * @brief Creates text, hint and snippet
 *
 * Text is just signature, e.g. 'length' for [NSString length] or 'respondsToSelector:'
 * for [id respondsToSelector:(SEL)sel].
 * Snippet is actual text, where any message parameter becames snippet part:
 * 'respondsToSelector:$(SEL)sel$'.
 * Hint consists of snippet preview and doxygen 'return' entry with returned type.
 */
void CompletionProposalsBuilder::concatChunksForObjectiveCMessage(const CXCompletionString &cxString)
{
    QString signature; // HTML compliant signature

    unsigned count = clang_getNumCompletionChunks(cxString);
    for (unsigned i = 0; i < count; ++i) {
        CXCompletionChunkKind chunkKind = clang_getCompletionChunkKind(cxString, i);
        const QString text = Internal::getQString(clang_getCompletionChunkText(cxString, i), false);
        bool chunkIsPlaceholder = false;

        switch (chunkKind) {
        case CXCompletionChunk_TypedText:
            signature += text;
            m_text += text;
            break;
        case CXCompletionChunk_Text:
        case CXCompletionChunk_LeftParen:
        case CXCompletionChunk_RightParen:
        case CXCompletionChunk_Comma:
        case CXCompletionChunk_HorizontalSpace:
            signature += text;
            break;
        case CXCompletionChunk_Placeholder:
            chunkIsPlaceholder = true;
            signature += QLatin1String("<b>");
            signature += Qt::escape(text);
            signature += QLatin1String("</b>");
            break;
        case CXCompletionChunk_LeftAngle:
            signature += QLatin1String("&lt;");
            break;
        case CXCompletionChunk_RightAngle:
            signature += QLatin1String("&gt;");
            break;
        case CXCompletionChunk_ResultType:
            attachResultTypeToComment(Qt::escape(text));
            break;
        default:
            break;
        }
    }

    m_hint += signature;

    signature.replace(QLatin1String("&lt;"), QLatin1String("<"));
    signature.replace(QLatin1String("&gt;"), QLatin1String(">"));

    m_snippet = signature;
    m_snippet.replace(QLatin1String("<b>"), QLatin1String("$"))
            .replace(QLatin1String("</b>"), QLatin1String("$"));
}

/**
 * @brief Creates entries like 'MyClass', 'MyNamespace::', 'MyEnumClass::Value1'
 */
void CompletionProposalsBuilder::concatChunksForNestedName(const CXCompletionString &cxString)
{
    unsigned count = clang_getNumCompletionChunks(cxString);
    for (unsigned i = 0; i < count; ++i) {
        CXCompletionChunkKind chunkKind = clang_getCompletionChunkKind(cxString, i);
        QString text = Internal::getQString(clang_getCompletionChunkText(cxString, i), false);

        switch (chunkKind) {
        case CXCompletionChunk_TypedText:
        case CXCompletionChunk_Text:
            m_text += text;
            break;

        default:
            break;
        }
    }
}

/**
 * @brief Creates text, snippet and hint for snippet preview
 *
 * Text is copy of snippet without '$' marks.
 * Hint also have 'return' doxygen entry if applicable (e.g. 'typeid...')
 */
void CompletionProposalsBuilder::concatChunksAsSnippet(const CXCompletionString &cxString)
{
    unsigned count = clang_getNumCompletionChunks(cxString);
    for (unsigned i = 0; i < count; ++i) {
        CXCompletionChunkKind chunkKind = clang_getCompletionChunkKind(cxString, i);
        const QString text = Internal::getQString(clang_getCompletionChunkText(cxString, i), false);

        switch (chunkKind) {
        case CXCompletionChunk_ResultType:
            attachResultTypeToComment(text);
            break;

        case CXCompletionChunk_Placeholder:
            m_text += text;
            m_snippet += QLatin1Char('$');
            m_snippet += text;
            m_snippet += QLatin1Char('$');
            m_hint += QLatin1String("<b>");
            m_hint += text;
            m_hint += QLatin1String("</b>");
            break;
        case CXCompletionChunk_LeftAngle:
            m_snippet += text;
            m_text += text;
            m_hint += QLatin1String("&lt;");
            break;
        case CXCompletionChunk_RightAngle:
            m_snippet += text;
            m_text += text;
            m_hint += QLatin1String("&gt;");
            break;

        case CXCompletionChunk_VerticalSpace:
            m_snippet += QLatin1Char('\n');
            m_text += QLatin1Char(' ');
            m_hint += QLatin1String("<br/>");
            break;

        default:
            m_snippet += text;
            m_text += text;
            m_hint += text;
            break;
        }
    }
}

/**
 * @brief Creates short text and hint with details
 *
 * Text is just function or variable name. Hint also contains function signature
 * or variable type.
 */
void CompletionProposalsBuilder::concatChunksOnlyTypedText(const CXCompletionString &cxString)
{
    bool previousChunkWasLParen = false;

    unsigned count = clang_getNumCompletionChunks(cxString);
    for (unsigned i = 0; i < count; ++i) {
        CXCompletionChunkKind chunkKind = clang_getCompletionChunkKind(cxString, i);
        QString text = Internal::getQString(clang_getCompletionChunkText(cxString, i), false);

        switch (chunkKind) {
        case CXCompletionChunk_LeftParen:
        case CXCompletionChunk_RightParen:
        case CXCompletionChunk_Comma:
        case CXCompletionChunk_HorizontalSpace:
        case CXCompletionChunk_Text:
        case CXCompletionChunk_Placeholder:
        case CXCompletionChunk_LeftAngle:
        case CXCompletionChunk_RightAngle:
            m_hint += Qt::escape(text);
            break;

        case CXCompletionChunk_TypedText:
            m_text = text;
            m_hint += QLatin1String("<b>");
            m_hint += Qt::escape(text);
            m_hint += QLatin1String("</b>");
            break;

        case CXCompletionChunk_ResultType: {
            m_hint += Qt::escape(text);
            QChar last = text[text.size() - 1];
            if (last != QLatin1Char('*') && last != QLatin1Char('&'))
                m_hint += QLatin1Char(' ');
        }
            break;

        case CXCompletionChunk_Informative:
            if (text == QLatin1String(" const"))
                m_hint += text;
            break;

        case CXCompletionChunk_Optional:
            appendOptionalChunks(clang_getCompletionChunkCompletionString(cxString, i),
                                 m_hint.size());
            break;

        default:
            break;
        }

        if (chunkKind == CXCompletionChunk_RightParen && previousChunkWasLParen)
            m_hasParameters = false;

        if (chunkKind == CXCompletionChunk_LeftParen) {
            previousChunkWasLParen = true;
            m_hasParameters = true;
        } else
            previousChunkWasLParen = false;
    }
}

/**
 * @brief Produces signal/slot signatures for 'connect' methods family
 */
void CompletionProposalsBuilder::concatSlotSignalSignature(const CXCompletionString &cxString)
{
    QString resultType;

    unsigned count = clang_getNumCompletionChunks(cxString);
    for (unsigned i = 0; i < count; ++i) {
        CXCompletionChunkKind chunkKind = clang_getCompletionChunkKind(cxString, i);
        QString text = Internal::getQString(clang_getCompletionChunkText(cxString, i), false);

        switch (chunkKind) {
        case CXCompletionChunk_Placeholder:
            text.truncate(findNameInPlaceholder(text));
            // fall-through
        case CXCompletionChunk_TypedText:
        case CXCompletionChunk_LeftParen:
        case CXCompletionChunk_RightParen:
        case CXCompletionChunk_Comma:
        case CXCompletionChunk_Text:
            m_text += text;
            break;
        case CXCompletionChunk_ResultType:
            resultType += text;
            resultType += QLatin1Char(' ');
            break;

        default:
            break;
        }
    }

    const QString parent = Internal::getQString(clang_getCompletionParent(cxString, NULL));
    if (m_resultKind == CodeCompletionResult::SlotCompletionKind)
        m_hint += QObject::tr("Slot of %1, returns %2").arg(parent).arg(resultType);
    else
        m_hint += QObject::tr("Signal of %1, returns %2").arg(parent).arg(resultType);
}

/**
 * @brief Stores optional part for further postprocessing in \a finalize()
 * @param insertionIndex Index where to insert optional chunk into hint
 */
void CompletionProposalsBuilder::appendOptionalChunks(const CXCompletionString &cxString,
                                                      int insertionIndex)
{
    OptionalChunk chunk;
    chunk.positionInHint = insertionIndex;

    unsigned count = clang_getNumCompletionChunks(cxString);
    for (unsigned i = 0; i < count; ++i) {
        CXCompletionChunkKind chunkKind = clang_getCompletionChunkKind(cxString, i);
        QString text = Internal::getQString(clang_getCompletionChunkText(cxString, i), false);

        switch (chunkKind) {
        case CXCompletionChunk_Placeholder:
            chunk.hint += Qt::escape(text);
            break;

        case CXCompletionChunk_Comma:
            chunk.hint += text;
            chunk.hint += QLatin1Char(' ');
            break;

        case CXCompletionChunk_Optional:
            m_optionalChunks.append(chunk);
            appendOptionalChunks(clang_getCompletionChunkCompletionString(cxString, i),
                                 insertionIndex + chunk.hint.size());
            return;

        default:
            break;
        }
    }

    m_optionalChunks.append(chunk);
}

void CompletionProposalsBuilder::attachResultTypeToComment(const QString &resultType)
{
    if (resultType.isEmpty())
        return;

    if (!m_comment.isEmpty())
        m_comment += QLatin1String("<br/>");

    m_comment += QLatin1String("<b>@return</b> ");
    m_comment += resultType;
}

} // namespace ClangCodeModel
