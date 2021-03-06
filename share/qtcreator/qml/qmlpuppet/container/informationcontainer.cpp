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

#include "informationcontainer.h"

#include <QtDebug>

namespace QmlDesigner {

InformationContainer::InformationContainer()
    : m_instanceId(-1),
      m_name(NoName)
{
}

InformationContainer::InformationContainer(qint32 instanceId,
                                           InformationName name,
                                           const QVariant &information,
                                           const QVariant &secondInformation,
                                           const QVariant &thirdInformation)
    : m_instanceId(instanceId),
    m_name(name),
    m_information(information),
    m_secondInformation(secondInformation),
    m_thirdInformation(thirdInformation)
{
}

qint32 InformationContainer::instanceId() const
{
    return m_instanceId;
}

InformationName InformationContainer::name() const
{
    return InformationName(m_name);
}

QVariant InformationContainer::information() const
{
    return m_information;
}

QVariant InformationContainer::secondInformation() const
{
    return m_secondInformation;
}

QVariant InformationContainer::thirdInformation() const
{
    return m_thirdInformation;
}

QDataStream &operator<<(QDataStream &out, const InformationContainer &container)
{
    out << container.instanceId();//
    out << container.m_name;
    out << container.information();
    out << container.secondInformation();
    out << container.thirdInformation();

    return out;
}

QDataStream &operator>>(QDataStream &in, InformationContainer &container)
{

    in >> container.m_instanceId;
    in >> container.m_name;
    in >> container.m_information;
    in >> container.m_secondInformation;
    in >> container.m_thirdInformation;

    return in;
}

bool operator ==(const InformationContainer &first, const InformationContainer &second)
{
    return first.m_instanceId == second.m_instanceId
            && first.m_name == second.m_name
            && first.m_information == second.m_information
            && first.m_secondInformation == second.m_secondInformation
            && first.m_thirdInformation == second.m_thirdInformation;
}

#if QT_VERSION < QT_VERSION_CHECK(5, 2, 0)
static bool operator <(const QVariant &first, const QVariant &second)
{
    if (first.userType() == second.userType()) {
        if (first.canConvert<QByteArray>())
            return first.value<QByteArray>() < second.value<QByteArray>();
    }

    return true;
}
#endif

bool operator <(const InformationContainer &first, const InformationContainer &second)
{
    return (first.m_instanceId < second.m_instanceId)
        || (first.m_instanceId == second.m_instanceId && first.m_name < second.m_name)
        || (first.m_instanceId == second.m_instanceId && first.m_name == second.m_name && first.m_information < second.m_information);
}

QDebug operator <<(QDebug debug, const InformationContainer &container)
{
    debug.nospace() << "InformationContainer("
                    << "instanceId: " << container.instanceId() << ", "
                    << "name: " << container.name() << ", "
                    << "information: " << container.information();

    if (container.secondInformation().isValid())
        debug.nospace() << ", " << "secondInformation: " << container.secondInformation();

    if (container.thirdInformation().isValid())
        debug.nospace() << ", " << "thirdInformation: " << container.thirdInformation();

    return debug.nospace() << ")";
}

} // namespace QmlDesigner
