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

#include "qmlapplicationwizard.h"

#include "qmlapp.h"

#include <extensionsystem/pluginmanager.h>
#include <projectexplorer/customwizard/customwizard.h>
#include <projectexplorer/kitmanager.h>
#include <projectexplorer/projectexplorerconstants.h>
#include <qmakeprojectmanager/qmakeproject.h>
#include <qmakeprojectmanager/qmakeprojectmanagerconstants.h>
#include <qtsupport/qtkitinformation.h>

#include "qmlprojectmanager.h"
#include "qmlproject.h"

#include <QIcon>

using namespace Core;
using namespace ExtensionSystem;
using namespace ProjectExplorer;
using namespace QmakeProjectManager;

namespace QmlProjectManager {
namespace Internal {

QmlApplicationWizardDialog::QmlApplicationWizardDialog(QmlApp *qmlApp, QWidget *parent, const WizardDialogParameters &parameters)
    : BaseProjectWizardDialog(parent, parameters),
      m_qmlApp(qmlApp)
{
    setWindowTitle(tr("New Qt Quick UI Project"));
    setIntroDescription(tr("This wizard generates a Qt Quick UI project."));
}

QmlApp *QmlApplicationWizardDialog::qmlApp() const
{
    return m_qmlApp;
}

QmlApplicationWizard::QmlApplicationWizard(const TemplateInfo &templateInfo)
    : m_qmlApp(new QmlApp(this))
{
    setWizardKind(ProjectWizard);
    setCategory(QLatin1String(ProjectExplorer::Constants::QT_APPLICATION_WIZARD_CATEGORY));
    setId(QLatin1String("QA.QMLB Application"));
    setIcon(QIcon(QLatin1String(QmakeProjectManager::Constants::ICON_QTQUICK_APP)));
    setDisplayCategory(
         QLatin1String(ProjectExplorer::Constants::QT_APPLICATION_WIZARD_CATEGORY_DISPLAY));
    setDisplayName(tr("Qt Quick Application"));
    setDescription(tr("Creates a Qt Quick application project."));

    m_qmlApp->setTemplateInfo(templateInfo);
}

void QmlApplicationWizard::createInstances(ExtensionSystem::IPlugin *plugin)
{
    foreach (const TemplateInfo &templateInfo, QmlApp::templateInfos()) {
        QmlApplicationWizard *wizard = new QmlApplicationWizard(templateInfo);
        wizard->setDisplayName(templateInfo.displayName);
        wizard->setDescription(templateInfo.description);
        const QString imagePath = templateInfo.templatePath + QLatin1String("/template.png");
        if (QFileInfo(imagePath).exists())
            wizard->setDescriptionImage(imagePath);
        wizard->setCategory(
                    QLatin1String(ProjectExplorer::Constants::QT_APPLICATION_WIZARD_CATEGORY));
        wizard->setDisplayCategory(
                    QLatin1String(ProjectExplorer::Constants::QT_APPLICATION_WIZARD_CATEGORY_DISPLAY));
        wizard->setWizardKind(IWizard::ProjectWizard);
        wizard->setId(templateInfo.wizardId);

        QStringList stringList =
                templateInfo.featuresRequired.split(QLatin1Char(','), QString::SkipEmptyParts);
        FeatureSet features;
        foreach (const QString &string, stringList) {
            Feature feature(Id::fromString(string.trimmed()));
            features |= feature;
        }

        wizard->setRequiredFeatures(features);
        wizard->setIcon(QIcon(QLatin1String(QmakeProjectManager::Constants::ICON_QTQUICK_APP)));
        plugin->addAutoReleasedObject(wizard);
    }
}

QWizard *QmlApplicationWizard::createWizardDialog(QWidget *parent,
    const WizardDialogParameters &wizardDialogParameters) const
{
    QmlApplicationWizardDialog *wizardDialog = new QmlApplicationWizardDialog(m_qmlApp,
                                                                              parent, wizardDialogParameters);

    connect(wizardDialog, SIGNAL(projectParametersChanged(QString,QString)), m_qmlApp,
        SLOT(setProjectNameAndBaseDirectory(QString,QString)));

    wizardDialog->setPath(wizardDialogParameters.defaultPath());

    wizardDialog->setProjectName(QmlApplicationWizardDialog::uniqueProjectName(wizardDialogParameters.defaultPath()));

    foreach (QWizardPage *page, wizardDialogParameters.extensionPages())
        applyExtensionPageShortTitle(wizardDialog, wizardDialog->addPage(page));

    return wizardDialog;
}

GeneratedFiles QmlApplicationWizard::generateFiles(const QWizard * /*wizard*/,
                                                       QString *errorMessage) const
{
    return m_qmlApp->generateFiles(errorMessage);
}

bool QmlApplicationWizard::postGenerateFiles(const QWizard * /*wizard*/, const GeneratedFiles &l,
    QString *errorMessage)
{
    return ProjectExplorer::CustomProjectWizard::postGenerateOpen(l, errorMessage);
}

} // namespace Internal
} // namespace QmlProjectManager
