import qbs.base 1.0

import QtcPlugin

QtcPlugin {
    name: "QmakeProjectManager"

    Depends { name: "Qt"; submodules: ["widgets", "network"] }
    Depends { name: "Core" }
    Depends { name: "ProjectExplorer" }
    Depends { name: "QtSupport" }
    Depends { name: "CppTools" }
    Depends { name: "QmlJS" }
    Depends { name: "TextEditor" }
    Depends { name: "QmlJSTools" }

    pluginRecommends: [
        "Designer"
    ]

    Group {
        name: "General"
        files: [
            "addlibrarywizard.cpp", "addlibrarywizard.h",
            "desktopqmakerunconfiguration.cpp", "desktopqmakerunconfiguration.h",
            "externaleditors.cpp", "externaleditors.h",
            "findqmakeprofiles.cpp", "findqmakeprofiles.h",
            "librarydetailscontroller.cpp", "librarydetailscontroller.h",
            "librarydetailswidget.ui",
            "makestep.cpp", "makestep.h", "makestep.ui",
            "profilecompletionassist.cpp", "profilecompletionassist.h",
            "profileeditor.cpp", "profileeditor.h",
            "profileeditorfactory.cpp", "profileeditorfactory.h",
            "profilehighlighter.cpp", "profilehighlighter.h",
            "profilehighlighterfactory.cpp", "profilehighlighterfactory.h",
            "profilehoverhandler.cpp", "profilehoverhandler.h",
            "qmakebuildinfo.h",
            "qmakeparser.cpp", "qmakeparser.h",
            "qmakekitconfigwidget.cpp", "qmakekitconfigwidget.h",
            "qmakekitinformation.cpp", "qmakekitinformation.h",
            "qmakeparser.cpp", "qmakeparser.h",
            "qmakeprojectimporter.cpp", "qmakeprojectimporter.h",
            "qmakerunconfigurationfactory.cpp", "qmakerunconfigurationfactory.h",
            "qmakestep.cpp", "qmakestep.h", "qmakestep.ui",
            "qmakebuildconfiguration.cpp", "qmakebuildconfiguration.h",
            "qmakenodes.cpp", "qmakenodes.h",
            "qmakeproject.cpp", "qmakeproject.h",
            "qmakeprojectconfigwidget.cpp", "qmakeprojectconfigwidget.h", "qmakeprojectconfigwidget.ui",
            "qmakeprojectmanager.cpp", "qmakeprojectmanager.h",
            "qmakeprojectmanager.qrc",
            "qmakeprojectmanager_global.h",
            "qmakeprojectmanagerconstants.h",
            "qmakeprojectmanagerplugin.cpp", "qmakeprojectmanagerplugin.h",
            "qtmodulesinfo.cpp", "qtmodulesinfo.h",
        ]
    }

    Group {
        name: "Custom Widget Wizard"
        prefix: "customwidgetwizard/"
        files: [
            "classdefinition.cpp", "classdefinition.h", "classdefinition.ui",
            "classlist.cpp", "classlist.h",
            "customwidgetpluginwizardpage.cpp", "customwidgetpluginwizardpage.h", "customwidgetpluginwizardpage.ui",
            "customwidgetwidgetswizardpage.cpp", "customwidgetwidgetswizardpage.h", "customwidgetwidgetswizardpage.ui",
            "customwidgetwizard.cpp", "customwidgetwizard.h",
            "customwidgetwizarddialog.cpp", "customwidgetwizarddialog.h",
            "filenamingparameters.h",
            "plugingenerator.cpp", "plugingenerator.h",
            "pluginoptions.h"
        ]
    }

    Group {
        name: "Images"
        prefix: "images/"
        files: [
            "headers.png",
            "run_qmake.png",
            "run_qmake_small.png",
            "sources.png",
            "unknown.png",
        ]
    }

    Group {
        name: "Wizards"
        prefix: "wizards/"
        files: [
            "abstractmobileapp.cpp", "abstractmobileapp.h",
            "abstractmobileappwizard.cpp", "abstractmobileappwizard.h",
            "consoleappwizard.cpp", "consoleappwizard.h",
            "consoleappwizarddialog.cpp", "consoleappwizarddialog.h",
            "emptyprojectwizard.cpp", "emptyprojectwizard.h",
            "emptyprojectwizarddialog.cpp", "emptyprojectwizarddialog.h",
            "filespage.cpp", "filespage.h",
            "guiappwizard.cpp", "guiappwizard.h",
            "guiappwizarddialog.cpp", "guiappwizarddialog.h",
            "html5app.cpp", "html5app.h",
            "html5appwizard.cpp", "html5appwizard.h",
            "html5appwizardpages.cpp", "html5appwizardpages.h",
            "html5appwizardsourcespage.ui",
            "libraryparameters.cpp", "libraryparameters.h",
            "librarywizard.cpp", "librarywizard.h",
            "librarywizarddialog.cpp", "librarywizarddialog.h",
            "mobileapp.cpp", "mobileapp.h",
            "mobileappwizardgenericoptionspage.ui",
            "mobileappwizardpages.cpp", "mobileappwizardpages.h",
            "mobilelibraryparameters.cpp", "mobilelibraryparameters.h",
            "mobilelibrarywizardoptionpage.cpp", "mobilelibrarywizardoptionpage.h", "mobilelibrarywizardoptionpage.ui",
            "modulespage.cpp", "modulespage.h",
            "qtprojectparameters.cpp", "qtprojectparameters.h",
            "qtquickapp.cpp", "qtquickapp.h",
            "qtquickappwizard.cpp", "qtquickappwizard.h",
            "qtquickappwizardpages.cpp", "qtquickappwizardpages.h",
            "qtquickcomponentsetoptionspage.ui",
            "qtwizard.cpp", "qtwizard.h",
            "subdirsprojectwizard.cpp", "subdirsprojectwizard.h",
            "subdirsprojectwizarddialog.cpp", "subdirsprojectwizarddialog.h",
            "testwizard.cpp", "testwizard.h",
            "testwizarddialog.cpp", "testwizarddialog.h",
            "testwizardpage.cpp", "testwizardpage.h",
            "testwizardpage.ui",
            "wizards.qrc"
        ]
    }

    Group {
        name: "Wizard Images"
        prefix: "wizards/images/"
        files: [
            "console.png",
            "gui.png",
            "html5app.png",
            "lib.png",
            "qtquickapp.png",
        ]
    }
}
