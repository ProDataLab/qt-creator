/**************************************************************************
**
** This file is part of Qt Creator
**
** Copyright (c) 2012 Nokia Corporation and/or its subsidiary(-ies).
**
** Contact: Nokia Corporation (qt-info@nokia.com)
**
**
** GNU Lesser General Public License Usage
**
** This file may be used under the terms of the GNU Lesser General Public
** License version 2.1 as published by the Free Software Foundation and
** appearing in the file LICENSE.LGPL included in the packaging of this file.
** Please review the following information to ensure the GNU Lesser General
** Public License version 2.1 requirements will be met:
** http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
**
** In addition, as a special exception, Nokia gives you certain additional
** rights. These rights are described in the Nokia Qt LGPL Exception
** version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
**
** Other Usage
**
** Alternatively, this file may be used in accordance with the terms and
** conditions contained in a signed written agreement between you and Nokia.
**
** If you have questions regarding the use of this file, please contact
** Nokia at qt-info@nokia.com.
**
**************************************************************************/

#include "qmlprofilerviewmanager.h"

#include "qmlprofilertraceview.h"
#include "qmlprofilereventview.h"
#include "qmlprofilertool.h"
#include "qmlprofilerstatemanager.h"
#include "qmlprofilerdatamodel.h"

#include <utils/qtcassert.h>
#include <utils/fancymainwindow.h>
#include <analyzerbase/analyzermanager.h>


#include <QDockWidget>

using namespace Analyzer;

namespace QmlProfiler {
namespace Internal {

class QmlProfilerViewManager::QmlProfilerViewManagerPrivate {
public:
    QmlProfilerViewManagerPrivate(QmlProfilerViewManager *qq) { Q_UNUSED(qq); }

    QmlProfilerTraceView *traceView;
    QmlProfilerEventsWidget *eventsView;
    QmlProfilerEventsWidget *v8profilerView;
    QmlProfilerStateManager *profilerState;
    QmlProfilerDataModel *profilerDataModel;
    QmlProfilerTool *profilerTool;
};

QmlProfilerViewManager::QmlProfilerViewManager(QObject *parent,
                                               QmlProfilerTool *profilerTool,
                                               QmlProfilerDataModel *model,
                                               QmlProfilerStateManager *profilerState)
    : QObject(parent), d(new QmlProfilerViewManagerPrivate(this))
{
    setObjectName("QML Profiler View Manager");
    d->traceView = 0;
    d->eventsView = 0;
    d->v8profilerView = 0;
    d->profilerState = profilerState;
    d->profilerDataModel = model;
    d->profilerTool = profilerTool;
    createViews();
}

QmlProfilerViewManager::~QmlProfilerViewManager()
{
    delete d;
}

////////////////////////////////////////////////////////////
// Views
void QmlProfilerViewManager::createViews()
{
    QTC_ASSERT(d->profilerDataModel, return);
    QTC_ASSERT(d->profilerState, return);

    Utils::FancyMainWindow *mw = AnalyzerManager::mainWindow();

    d->traceView = new QmlProfilerTraceView(mw,
                                            d->profilerTool,
                                            this,
                                            d->profilerDataModel,
                                            d->profilerState);
    connect(d->traceView, SIGNAL(gotoSourceLocation(QString,int,int)),
            this, SIGNAL(gotoSourceLocation(QString,int,int)));

    d->traceView->reset();

    d->eventsView = new QmlProfilerEventsWidget(mw, d->profilerTool, this, d->profilerDataModel);
    connect(d->eventsView, SIGNAL(gotoSourceLocation(QString,int,int)), this,
            SIGNAL(gotoSourceLocation(QString,int,int)));
    connect(d->eventsView, SIGNAL(showEventInTimeline(int)), d->traceView,
            SLOT(selectNextEventWithId(int)));
    connect(d->traceView, SIGNAL(selectedEventChanged(int)), d->eventsView,
            SLOT(updateSelectedEvent(int)));

    d->v8profilerView = new QmlProfilerEventsWidget(mw, d->profilerTool,
                                                    this, d->profilerDataModel);
    d->v8profilerView->switchToV8View();
    connect(d->v8profilerView, SIGNAL(gotoSourceLocation(QString,int,int)),
            this, SIGNAL(gotoSourceLocation(QString,int,int)));
    connect(d->v8profilerView, SIGNAL(gotoSourceLocation(QString,int,int)),
            d->eventsView, SLOT(selectBySourceLocation(QString,int,int)));
    connect(d->eventsView, SIGNAL(gotoSourceLocation(QString,int,int)),
            d->v8profilerView, SLOT(selectBySourceLocation(QString,int,int)));

    QDockWidget *eventsDock = AnalyzerManager::createDockWidget
            (d->profilerTool, tr("Events"), d->eventsView, Qt::BottomDockWidgetArea);
    QDockWidget *timelineDock = AnalyzerManager::createDockWidget
            (d->profilerTool, tr("Timeline"), d->traceView, Qt::BottomDockWidgetArea);
    QDockWidget *v8profilerDock = AnalyzerManager::createDockWidget
            (d->profilerTool, tr("JavaScript"), d->v8profilerView, Qt::BottomDockWidgetArea);

    eventsDock->show();
    timelineDock->show();
    v8profilerDock->show();

    mw->splitDockWidget(mw->toolBarDockWidget(), timelineDock, Qt::Vertical);
    mw->tabifyDockWidget(timelineDock, eventsDock);
    mw->tabifyDockWidget(eventsDock, v8profilerDock);
}

bool QmlProfilerViewManager::hasValidSelection() const
{
    return d->traceView->hasValidSelection();
}

qint64 QmlProfilerViewManager::selectionStart() const
{
    return d->traceView->selectionStart();
}

qint64 QmlProfilerViewManager::selectionEnd() const
{
    return d->traceView->selectionEnd();
}

bool QmlProfilerViewManager::hasGlobalStats() const
{
    return d->eventsView->hasGlobalStats();
}

void QmlProfilerViewManager::getStatisticsInRange(qint64 rangeStart, qint64 rangeEnd)
{
    d->eventsView->getStatisticsInRange(rangeStart, rangeEnd);
}

void QmlProfilerViewManager::clear()
{
    d->traceView->clearDisplay();
    d->eventsView->clear();
    d->v8profilerView->clear();
}

} // namespace Internal
} // namespace QmlProfiler
