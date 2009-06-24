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

#ifndef DEBUGGER_WATCHHANDLER_H
#define DEBUGGER_WATCHHANDLER_H

#include <QtCore/QPointer>
#include <QtCore/QObject>
#include <QtCore/QHash>
#include <QtCore/QSet>
#include <QtGui/QStandardItem>
#include <QtGui/QStandardItemModel>
#include <QtGui/QTreeView>
#include <QtScript/QScriptValue>

namespace Debugger {
namespace Internal {

class WatchItem;
class WatchHandler;
enum WatchType { LocalsWatch, WatchersWatch, TooltipsWatch };

class WatchData
{
public:
    WatchData();

    enum State
    {
        Complete = 0,
        HasChildrenNeeded = 1,
        ValueNeeded = 2,
        TypeNeeded = 4,
        ChildrenNeeded = 8,

        NeededMask = ValueNeeded
            | TypeNeeded
            | ChildrenNeeded
            | HasChildrenNeeded,

        InitialState = ValueNeeded
            | TypeNeeded
            | ChildrenNeeded
            | HasChildrenNeeded
    };

    void setValue(const QString &);
    void setType(const QString &);
    void setValueToolTip(const QString &);
    void setError(const QString &);
    void setAddress(const QString &address);

    bool isSomethingNeeded() const { return state & NeededMask; }
    void setAllNeeded() { state = NeededMask; }
    void setAllUnneeded() { state = State(0); }

    bool isTypeNeeded() const { return state & TypeNeeded; }
    bool isTypeKnown() const { return !(state & TypeNeeded); }
    void setTypeNeeded() { state = State(state | TypeNeeded); }
    void setTypeUnneeded() { state = State(state & ~TypeNeeded); }

    bool isValueNeeded() const { return state & ValueNeeded; }
    bool isValueKnown() const { return !(state & ValueNeeded); }
    void setValueNeeded() { state = State(state | ValueNeeded); }
    void setValueUnneeded() { state = State(state & ~ValueNeeded); }

    bool isChildrenNeeded() const { return state & ChildrenNeeded; }
    bool isChildrenKnown() const { return !(state & ChildrenNeeded); }
    void setChildrenNeeded() { state = State(state | ChildrenNeeded); }
    void setChildrenUnneeded() { state = State(state & ~ChildrenNeeded); }

    bool isHasChildrenNeeded() const { return state & HasChildrenNeeded; }
    bool isHasChildrenKnown() const { return !(state & HasChildrenNeeded); }
    void setHasChildrenNeeded() { state = State(state | HasChildrenNeeded); }
    void setHasChildrenUnneeded() { state = State(state & ~HasChildrenNeeded); }
    void setHasChildren(bool c) { hasChildren = c; setHasChildrenUnneeded();
        if (!c) setChildrenUnneeded(); }

    WatchData pointerChildPlaceHolder() const;

    QString toString() const;
    QString toToolTip() const;
    bool isLocal() const { return iname.startsWith(QLatin1String("local.")); }
    bool isWatcher() const { return iname.startsWith(QLatin1String("watch.")); }
    bool isValid() const { return !iname.isEmpty(); }

public:
    QString iname;        // internal name sth like 'local.baz.public.a'
    QString exp;          // the expression
    QString name;         // displayed name
    QString value;        // displayed value
    QByteArray editvalue; // displayed value
    QString valuetooltip; // tooltip in value column
    QString type;         // displayed type
    QString variable;     // name of internal Gdb variable if created
    QString addr;         // displayed adress
    QString saddr;        // stored address (pointer in container)
    QString framekey;     // key for type cache
    QScriptValue scriptValue; // if needed...
    bool hasChildren;
    int generation;       // when updated?
    bool valuedisabled;   // value will be greyed out

private:

public:
    int source;  // Used by some debuggers (CDB) to tell where it originates from (dumper or symbol evaluation)
    int state;
    bool changed;
};

enum WatchRoles
{
    INameRole = Qt::UserRole,
    ExpressionRole,
    ExpandedRole,
    ActiveDataRole,  // used for tooltip
};

class WatchModel : public QAbstractItemModel
{
    Q_OBJECT

private:
    explicit WatchModel(WatchHandler *handler, WatchType type);

    QVariant data(const QModelIndex &index, int role) const;
    bool setData(const QModelIndex &index, const QVariant &value, int role);
    QModelIndex index(int, int, const QModelIndex &idx) const;
    QModelIndex parent(const QModelIndex &idx) const;
    int rowCount(const QModelIndex &idx) const;
    int columnCount(const QModelIndex &idx) const;
    bool hasChildren(const QModelIndex &idx) const;
    Qt::ItemFlags flags(const QModelIndex &idx) const;
    QVariant headerData(int section, Qt::Orientation orientation,
        int role = Qt::DisplayRole) const;
    bool canFetchMore(const QModelIndex &parent) const;
    void fetchMore(const QModelIndex &parent);

    friend class WatchHandler;
    friend class GdbEngine;

    WatchItem *watchItem(const QModelIndex &) const;
    QModelIndex watchIndex(const WatchItem *needle) const;
    QModelIndex watchIndexHelper(const WatchItem *needle,
        const WatchItem *parentItem, const QModelIndex &parentIndex) const;

    void insertData(const WatchData &data);
    WatchItem *findItem(const QString &iname, WatchItem *root) const;
    void reinitialize();
    void removeOutdated();
    void removeOutdatedHelper(WatchItem *item);
    WatchItem *dummyRoot() const;
    void removeItem(WatchItem *item);
    void setActiveData(const QString &data) { m_activeData = data; }

private:
    WatchHandler *m_handler;
    WatchType m_type;
    WatchItem *m_root;
    QString m_activeData;
};

class WatchHandler : public QObject
{
    Q_OBJECT

public:
    WatchHandler();
    WatchModel *model(WatchType type) const;
    WatchModel *modelForIName(const QString &data) const;

//public slots:
    void cleanup();
    Q_SLOT void watchExpression(); // data in action->data().toString()
    Q_SLOT void watchExpression(const QString &exp);
    Q_SLOT void removeWatchExpression();
    Q_SLOT void removeWatchExpression(const QString &exp);
    void beginCycle(); // called at begin of updateLocals() cycle
    void updateWatchers(); // called after locals are fetched
    void endCycle(); // called after all results have been received
    void showEditValue(const WatchData &data);

    void insertData(const WatchData &data);
    void removeData(const QString &iname);
    WatchData *findItem(const QString &iname) const;

    void loadSessionData();
    void saveSessionData();

    bool isDisplayedIName(const QString &iname) const
        { return m_displayedINames.contains(iname); }
    bool isExpandedIName(const QString &iname) const
        { return m_expandedINames.contains(iname); }
    QSet<QString> expandedINames() const
        { return m_expandedINames; }

    static QString watcherEditPlaceHolder();

signals:
    void watchDataUpdateNeeded(const WatchData &data);
    void sessionValueRequested(const QString &name, QVariant *value);
    void setSessionValueRequested(const QString &name, const QVariant &value);

private:
    friend class WatchModel;

    void loadWatchers();
    void saveWatchers();

    bool m_expandPointers;
    bool m_inChange;

    typedef QMap<QString, QPointer<QWidget> > EditWindows;
    EditWindows m_editWindows;

    QHash<QString, int> m_watcherNames;
    QString watcherName(const QString &exp);

    void setDisplayedIName(const QString &iname, bool on);
    QSet<QString> m_expandedINames;  // those expanded in the treeview
    QSet<QString> m_displayedINames; // those with "external" viewers

    WatchModel *m_locals;
    WatchModel *m_watchers;
    WatchModel *m_tooltips;
};

} // namespace Internal
} // namespace Debugger

Q_DECLARE_METATYPE(Debugger::Internal::WatchData);

#endif // DEBUGGER_WATCHHANDLER_H
