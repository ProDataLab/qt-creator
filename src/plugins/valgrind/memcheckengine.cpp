/****************************************************************************
**
** Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
** Contact: http://www.qt-project.org/legal
** Author: Nicolas Arnaud-Cormos, KDAB (nicolas.arnaud-cormos@kdab.com)
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

#include "memcheckengine.h"

#include "valgrindsettings.h"

#include <analyzerbase/analyzersettings.h>

#include <projectexplorer/projectexplorer.h>
#include <projectexplorer/taskhub.h>

#include <valgrind/xmlprotocol/error.h>
#include <valgrind/xmlprotocol/status.h>

#include <utils/qtcassert.h>

using namespace Analyzer;
using namespace ProjectExplorer;
using namespace Valgrind::XmlProtocol;

namespace Valgrind {
namespace Internal {

MemcheckRunControl::MemcheckRunControl(const AnalyzerStartParameters &sp,
        ProjectExplorer::RunConfiguration *runConfiguration)
    : ValgrindRunControl(sp, runConfiguration)
{
    connect(&m_parser, SIGNAL(error(Valgrind::XmlProtocol::Error)),
            SIGNAL(parserError(Valgrind::XmlProtocol::Error)));
    connect(&m_parser, SIGNAL(suppressionCount(QString,qint64)),
            SIGNAL(suppressionCount(QString,qint64)));
    connect(&m_parser, SIGNAL(internalError(QString)),
            SIGNAL(internalParserError(QString)));
    connect(&m_parser, SIGNAL(status(Valgrind::XmlProtocol::Status)),
            SLOT(status(Valgrind::XmlProtocol::Status)));

    m_progress->setProgressRange(0, XmlProtocol::Status::Finished + 1);
}

QString MemcheckRunControl::progressTitle() const
{
    return tr("Analyzing Memory");
}

Valgrind::ValgrindRunner *MemcheckRunControl::runner()
{
    return &m_runner;
}

bool MemcheckRunControl::startEngine()
{
    m_runner.setParser(&m_parser);

    // Clear about-to-be-outdated tasks.
    ProjectExplorerPlugin::instance()->taskHub()->clearTasks(Analyzer::Constants::ANALYZERTASK_ID);

    appendMessage(tr("Analyzing memory of %1\n").arg(executable()),
                        Utils::NormalMessageFormat);
    return ValgrindRunControl::startEngine();
}

void MemcheckRunControl::stopEngine()
{
    disconnect(&m_parser, SIGNAL(internalError(QString)),
               this, SIGNAL(internalParserError(QString)));
    ValgrindRunControl::stopEngine();
}

QStringList MemcheckRunControl::toolArguments() const
{
    QStringList arguments;
    arguments << QLatin1String("--gen-suppressions=all");

    ValgrindBaseSettings *memcheckSettings = m_settings->subConfig<ValgrindBaseSettings>();
    QTC_ASSERT(memcheckSettings, return arguments);

    if (memcheckSettings->trackOrigins())
        arguments << QLatin1String("--track-origins=yes");

    foreach (const QString &file, memcheckSettings->suppressionFiles())
        arguments << QString::fromLatin1("--suppressions=%1").arg(file);

    arguments << QString::fromLatin1("--num-callers=%1").arg(memcheckSettings->numCallers());
    return arguments;
}

QStringList MemcheckRunControl::suppressionFiles() const
{
    return m_settings->subConfig<ValgrindBaseSettings>()->suppressionFiles();
}

void MemcheckRunControl::status(const Status &status)
{
    m_progress->setProgressValue(status.state() + 1);
}

void MemcheckRunControl::receiveLogMessage(const QByteArray &b)
{
    QString error = QString::fromLocal8Bit(b);
    // workaround https://bugs.kde.org/show_bug.cgi?id=255888
    error.remove(QRegExp(QLatin1String("==*== </valgrindoutput>"), Qt::CaseSensitive, QRegExp::Wildcard));

    error = error.trimmed();

    if (error.isEmpty())
        return;

    stopEngine();

    QString file;
    int line = -1;

    QRegExp suppressionError(QLatin1String("in suppressions file \"([^\"]+)\" near line (\\d+)"),
                             Qt::CaseSensitive, QRegExp::RegExp2);
    if (suppressionError.indexIn(error) != -1) {
        file = suppressionError.cap(1);
        line = suppressionError.cap(2).toInt();
    }

    TaskHub *hub = ProjectExplorerPlugin::instance()->taskHub();
    hub->addTask(Task(Task::Error, error, Utils::FileName::fromUserInput(file), line,
                      Analyzer::Constants::ANALYZERTASK_ID));
    hub->requestPopup();
}

} // namespace Internal
} // namespace Valgrind
