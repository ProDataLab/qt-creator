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

#include "abstractmobileappwizard.h"

#include "mobileappwizardpages.h"
#include "../qmakeprojectimporter.h"

#include <extensionsystem/pluginmanager.h>
#include <qmakeprojectmanager/qmakeproject.h>
#include <qmakeprojectmanager/qmakeprojectmanager.h>
#include <qtsupport/qtsupportconstants.h>
#include <qtsupport/qtkitinformation.h>
#include <projectexplorer/projectexplorer.h>
#include <projectexplorer/targetsetuppage.h>
#include <projectexplorer/customwizard/customwizard.h>
#include <coreplugin/editormanager/editormanager.h>

using namespace ProjectExplorer;

namespace QmakeProjectManager {

AbstractMobileAppWizardDialog::AbstractMobileAppWizardDialog(QWidget *parent,
                                                             const QtSupport::QtVersionNumber &minimumQtVersionNumber,
                                                             const QtSupport::QtVersionNumber &maximumQtVersionNumber,
                                                             const Core::WizardDialogParameters &parameters)
    : ProjectExplorer::BaseProjectWizardDialog(parent, parameters)
    , m_targetsPage(0)
    , m_genericOptionsPageId(-1)
    , m_targetsPageId(-1)
    , m_ignoreGeneralOptions(false)
    , m_targetItem(0)
    , m_genericItem(0)
    , m_kitIds(parameters.extraValues().value(QLatin1String(ProjectExplorer::Constants::PROJECT_KIT_IDS))
               .value<QList<Core::Id> >())
{
    if (!parameters.extraValues().contains(QLatin1String(ProjectExplorer::Constants::PROJECT_KIT_IDS))) {
        m_targetsPage = new ProjectExplorer::TargetSetupPage;
        m_targetsPage->setProjectImporter(new Internal::QmakeProjectImporter(path()));
        QString platform = selectedPlatform();
        if (platform.isEmpty()) {
            m_targetsPage->setPreferredKitMatcher(
                        new QtSupport::QtVersionKitMatcher(
                            Core::FeatureSet( QtSupport::Constants::FEATURE_MOBILE)));
        } else {
            m_targetsPage->setPreferredKitMatcher(new QtSupport::QtPlatformKitMatcher(platform));
        }
        m_targetsPage->setRequiredKitMatcher(new QtSupport::QtVersionKitMatcher(requiredFeatures(),
                                                                                minimumQtVersionNumber,
                                                                                maximumQtVersionNumber));
        resize(900, 450);
    }

    m_genericOptionsPage = new Internal::MobileAppWizardGenericOptionsPage;
}

void AbstractMobileAppWizardDialog::addMobilePages()
{
    if (m_targetsPage) {
        m_targetsPageId = addPageWithTitle(m_targetsPage, tr("Targets"));
        m_targetItem = wizardProgress()->item(m_targetsPageId);
    }

    const bool shouldAddGenericPage = m_targetsPage;

    if (shouldAddGenericPage) {
        m_genericOptionsPageId = addPageWithTitle(m_genericOptionsPage,
                                                  tr("Mobile Options"));
        m_genericItem = wizardProgress()->item(m_genericOptionsPageId);
    }

    if (m_targetItem)
        m_targetItem->setNextShownItem(0);
}

ProjectExplorer::TargetSetupPage *AbstractMobileAppWizardDialog::targetsPage() const
{
    return m_targetsPage;
}

int AbstractMobileAppWizardDialog::addPageWithTitle(QWizardPage *page, const QString &title)
{
    const int pageId = addPage(page);
    wizardProgress()->item(pageId)->setTitle(title);
    return pageId;
}

int AbstractMobileAppWizardDialog::nextId() const
{
    if (m_targetsPage) {
        if (currentPage() == m_targetsPage)
            return idOfNextGenericPage();
        if (currentPage() == m_genericOptionsPage)
            return idOfNextGenericPage();
    }
    return BaseProjectWizardDialog::nextId();
}

void AbstractMobileAppWizardDialog::initializePage(int id)
{
    if (m_targetItem) {
        if (id == startId()) {
            m_targetItem->setNextItems(QList<Utils::WizardProgressItem *>()
                    << m_genericItem << itemOfNextGenericPage());
        } else if (id == m_genericOptionsPageId) {
            QList<Utils::WizardProgressItem *> order;
            order << m_genericItem << itemOfNextGenericPage();
            for (int i = 0; i < order.count() - 1; i++)
                order.at(i)->setNextShownItem(order.at(i + 1));
        }
    }
    BaseProjectWizardDialog::initializePage(id);
}

void AbstractMobileAppWizardDialog::setIgnoreGenericOptionsPage(bool ignore)
{
    m_ignoreGeneralOptions = ignore;
}

Utils::WizardProgressItem *AbstractMobileAppWizardDialog::targetsPageItem() const
{
    return m_targetItem;
}

int AbstractMobileAppWizardDialog::idOfNextGenericPage() const
{
    return pageIds().at(pageIds().indexOf(m_genericOptionsPageId) + 1);
}

Utils::WizardProgressItem *AbstractMobileAppWizardDialog::itemOfNextGenericPage() const
{
    return wizardProgress()->item(idOfNextGenericPage());
}

bool AbstractMobileAppWizardDialog::isQtPlatformSelected(const QString &platform) const
{
    QList<Core::Id> selectedKitsList = selectedKits();

    foreach (Kit *k, KitManager::matchingKits(QtSupport::QtPlatformKitMatcher(platform)))
        if (selectedKitsList.contains(k->id()))
            return true;

    return false;
}

QList<Core::Id> AbstractMobileAppWizardDialog::selectedKits() const
{
    if (m_targetsPage)
        return m_targetsPage->selectedKits();
    return m_kitIds;
}



AbstractMobileAppWizard::AbstractMobileAppWizard(QObject *parent)
    : Core::BaseFileWizard(parent)
{ }

QWizard *AbstractMobileAppWizard::createWizardDialog(QWidget *parent,
                                                     const Core::WizardDialogParameters &wizardDialogParameters) const
{
    AbstractMobileAppWizardDialog * const wdlg
        = createWizardDialogInternal(parent, wizardDialogParameters);
    wdlg->setProjectName(ProjectExplorer::BaseProjectWizardDialog::uniqueProjectName(wizardDialogParameters.defaultPath()));
    wdlg->m_genericOptionsPage->setOrientation(app()->orientation());
    connect(wdlg, SIGNAL(projectParametersChanged(QString,QString)),
        SLOT(useProjectPath(QString,QString)));
    wdlg->addExtensionPages(wizardDialogParameters.extensionPages());

    return wdlg;
}

Core::GeneratedFiles AbstractMobileAppWizard::generateFiles(const QWizard *wizard,
    QString *errorMessage) const
{
    const AbstractMobileAppWizardDialog *wdlg
        = qobject_cast<const AbstractMobileAppWizardDialog*>(wizard);
    app()->setOrientation(wdlg->m_genericOptionsPage->orientation());
    prepareGenerateFiles(wizard, errorMessage);
    return app()->generateFiles(errorMessage);
}

bool AbstractMobileAppWizard::postGenerateFiles(const QWizard *w,
    const Core::GeneratedFiles &l, QString *errorMessage)
{
    Q_UNUSED(w)
    Q_UNUSED(l)
    Q_UNUSED(errorMessage)
    QmakeManager * const manager
        = ExtensionSystem::PluginManager::getObject<QmakeManager>();
    Q_ASSERT(manager);
    QmakeProject project(manager, app()->path(AbstractMobileApp::AppPro));
    bool success = true;
    if (wizardDialog()->m_targetsPage) {
        success = wizardDialog()->m_targetsPage->setupProject(&project);
        if (success) {
            project.saveSettings();
            success = ProjectExplorer::CustomProjectWizard::postGenerateOpen(l, errorMessage);
        }
    }
    if (success) {
        const QString fileToOpen = fileToOpenPostGeneration();
        if (!fileToOpen.isEmpty()) {
            Core::EditorManager::openEditor(fileToOpen);
            ProjectExplorer::ProjectExplorerPlugin::instance()->setCurrentFile(0, fileToOpen);
        }
    }
    return success;
}

void AbstractMobileAppWizard::useProjectPath(const QString &projectName,
    const QString &projectPath)
{
    app()->setProjectName(projectName);
    app()->setProjectPath(projectPath);
    if (wizardDialog()->m_targetsPage)
        wizardDialog()->m_targetsPage->setProjectPath(app()->path(AbstractMobileApp::AppPro));
    projectPathChanged(app()->path(AbstractMobileApp::AppPro));
}

} // namespace QmakeProjectManager
