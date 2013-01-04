#include "gitoriousclonewizard.h"
#include <gerritplugin.h>
    Git::Constants::C_GITSUBMITEDITOR
    const QString description = QLatin1String("Git");
    m_commandLocator = new Locator::CommandLocator(description, prefix, prefix);
            = createFileAction(gitContainer,
                               tr("Blame Current File"), tr("Blame for \"%1\""),
                               Core::Id("Git.Blame"),
                               globalcontext, true, SLOT(blameFile()));
    parameterActionCommand.second->setDefaultKeySequence(QKeySequence(Core::UseMacShortcuts ? tr("Meta+G,Meta+B") : tr("Alt+G,Alt+B")));

    parameterActionCommand
            = createFileAction(gitContainer,
            = createFileAction(gitContainer,
    gitContainer->addSeparator(globalcontext);
            = createFileAction(gitContainer,
            = createFileAction(gitContainer,
            = createFileAction(gitContainer,
            = createFileAction(gitContainer,
    gitContainer->addSeparator(globalcontext);
            = createProjectAction(gitContainer,
            = createProjectAction(gitContainer,
                = createProjectAction(gitContainer,
    gitContainer->addSeparator(globalcontext);
    createRepositoryAction(gitContainer,
    createRepositoryAction(gitContainer,
    createRepositoryAction(gitContainer,
    createRepositoryAction(gitContainer,
    createRepositoryAction(gitContainer,
                           tr("Clean..."), Core::Id("Git.CleanRepository"),
                           globalcontext, true, SLOT(cleanRepository()));

    m_createRepositoryAction = new QAction(tr("Create Repository..."), this);
    Core::Command *createRepositoryCommand = Core::ActionManager::registerAction(m_createRepositoryAction, "Git.CreateRepository", globalcontext);
    connect(m_createRepositoryAction, SIGNAL(triggered()), this, SLOT(createRepository()));
    gitContainer->addAction(createRepositoryCommand);
    gitContainer->addSeparator(globalcontext);
    createRepositoryAction(gitContainer,
                           tr("Launch gitk"), Core::Id("Git.LaunchGitK"),
                           globalcontext, true, &GitClient::launchGitK);

    m_repositoryBrowserAction
            = createRepositoryAction(gitContainer,
                                     tr("Launch repository browser"), Core::Id("Git.LaunchRepositoryBrowser"),
                                     globalcontext, true, &GitClient::launchRepositoryBrowser).first;

    createRepositoryAction(gitContainer,
    createRepositoryAction(gitContainer,
                           tr("Remotes..."), Core::Id("Git.RemoteList"),
                           globalcontext, false, SLOT(remoteList()));

    m_showAction = new QAction(tr("Show..."), this);
    Core::Command *showCommitCommand = Core::ActionManager::registerAction(m_showAction, "Git.ShowCommit", globalcontext);
    connect(m_showAction, SIGNAL(triggered()), this, SLOT(showCommit()));
    gitContainer->addAction(showCommitCommand);


    gitContainer->addSeparator(globalcontext);
    patchMenu->menu()->setTitle(tr("Patch"));
    gitContainer->addMenu(patchMenu);
    stashMenu->menu()->setTitle(tr("Stash"));
    gitContainer->addMenu(stashMenu);
    ActionCommandPair actionCommand =
            createRepositoryAction(stashMenu,
                                   tr("Stash"), Core::Id("Git.Stash"),
                                   globalcontext, true, SLOT(stash()));
    subversionMenu->menu()->setTitle(tr("Subversion"));
    gitContainer->addMenu(subversionMenu);
    gitContainer->addSeparator(globalcontext);
    gitContainer->addSeparator(globalcontext);
    createRepositoryAction(gitContainer,
                           tr("Fetch"), Core::Id("Git.Fetch"),
                           globalcontext, true, SLOT(fetch()));
    createRepositoryAction(gitContainer,
                           tr("Pull"), Core::Id("Git.Pull"),
                           globalcontext, true, SLOT(pull()));
    actionCommand = createRepositoryAction(gitContainer,
                                           tr("Push"), Core::Id("Git.Push"),
                                           globalcontext, true, SLOT(push()));
    actionCommand = createRepositoryAction(gitContainer,
                                           tr("Commit..."), Core::Id("Git.Commit"),
                                           globalcontext, true, SLOT(startCommit()));
    actionCommand.second->setDefaultKeySequence(QKeySequence(Core::UseMacShortcuts ? tr("Meta+G,Meta+C") : tr("Alt+G,Alt+C")));
    createRepositoryAction(gitContainer,
                           tr("Amend Last Commit..."), Core::Id("Git.AmendCommit"),
                           globalcontext, true, SLOT(startAmendCommit()));
    // Subversion in a submenu.
    return gp->initialize(gitContainer);
        m_gitClient->hardReset(state.topLevel(), dialog.commit());
    if (amend) // Allow for just correcting the message
        submitEditor->setEmptyFileListEnabled(true);
    const bool rebase = m_gitClient->settings()->boolValue(GitSettings::pullRebaseKey);

    GitClient::StashResult stashResult = m_gitClient->ensureStash(state.topLevel());
    switch (stashResult) {
    case GitClient::StashUnchanged:
    case GitClient::Stashed:
        m_gitClient->synchronousPull(state.topLevel(), rebase);
        if (stashResult == GitClient::Stashed)
            m_gitClient->stashPop(state.topLevel());
        break;
    case GitClient::NotStashed:
        if (!rebase)
            m_gitClient->synchronousPull(state.topLevel(), false);
        break;
    default:
        break;
            if (qVariantCanConvert<GitClientMemberFunc>(v))
                return qVariantValue<GitClientMemberFunc>(v);
    switch (m_gitClient->ensureStash(workingDirectory)) {
    case GitClient::StashUnchanged:
    case GitClient::Stashed:
    case GitClient::NotStashed:
        break;
    default:
    }
        if (errorMessage.isEmpty()) {
        } else {
        }
    const QString id = m_gitClient->synchronousStash(state.topLevel(), QString(), 0);
    const QString id = m_gitClient->synchronousStash(state.topLevel(), QString(), GitClient::StashImmediateRestore|GitClient::StashPromptDescription);
    if (state.hasFile())
        m_changeSelectionDialog->setWorkingDirectory(state.currentFileDirectory());
    else if (state.hasTopLevel())
        m_changeSelectionDialog->setWorkingDirectory(state.topLevel());