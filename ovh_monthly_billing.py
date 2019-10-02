#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO
# . use *_id and *_name for project and instance
# . get *_id from *_name

# ovh_monthly_billing, an Ansible module for managing OVH monthly billing
# Copyright (C) 2019, Francois Lallart <fraff@free.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

DOCUMENTATION = '''
---
module: ovh_monthly_billing
author: Francois (fraff) Lallart, based on Carlos Izquierdo's ovh_dns
short_description: Manage OVH monthly billing
description:
    - Enable monthly billing on OVH cloud intances
requirements: [ "ovh" ]
options:
    project_id:
        required: true
        description:
            - ID of the project, get it with https://api.ovh.com/console/#/cloud/project#GET
    instance_id:
        required: true
        description:
            - ID of the instance, get it with https://api.ovh.com/console/#/cloud/project/%7BserviceName%7D/instance#GET
    state:
        required: false
        default: present
        choices: ['present', 'absent']
        description:
            - useless I guess
'''

EXAMPLES = '''
# basic
- ovh_monthly_billing: project_id=0c727a20aa144485b70c44dee9123b46 instance_id=8fa89ad2-8f08-4220-9fa4-9695ea23e948
'''

import os
import sys

try:
    import ovh
    import ovh.exceptions
    from ovh.exceptions import APIError
except ImportError:
    print "failed=True msg='ovh required for this module'"
    sys.exit(1)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            project_id = dict(required=True),
            instance_id = dict(required=True),
            state = dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode = True
    )

    # Get parameters
    project_id = module.params.get('project_id')
    instance_id = module.params.get('instance_id')
    state = module.params.get('state')
    project = ""
    instance = ""
#    infos = {}

    # Connect to OVH API
    client = ovh.Client()

#    # get list of projects
#    projects = client.get('/cloud/project')
#    for p in projects:
#        infos[p] = client.get('/cloud/project/{}'.format(p))
#
#    module.exit_json(msg=infos)

    if state == "absent":
        module.fail_json(msg="OVH API does not allow to remove monthly billing")

    # Check that the instance exists
    try:
        project = client.get('/cloud/project/{}'.format(project_id))
    except ovh.exceptions.ResourceNotFoundError:
        module.fail_json(msg='project {} does not exist'.format(project_id))

    # Check that the instance exists
    try:
        instance = client.get('/cloud/project/{}/instance/{}'.format(project_id, instance_id))
    except ovh.exceptions.ResourceNotFoundError:
        module.fail_json(msg='instance {} does not exist in project {}'.format(instance_id, project_id))
        # module.fail_json(msg='instance {} does not exist in project {}'.format(instance_id, project['description']))

#    module.warn("this is a scary warning.")
#    module.log(msg="this is a log() test sent to syslog")

    if instance['monthlyBilling'] is not None:
        if instance['monthlyBilling']['status'] in ['ok', 'activationPending']:
            module.exit_json(changed=False, monthlyBilling=instance['monthlyBilling'])

    if module.check_mode:
        module.exit_json(changed=True, msg="Dry Run!")

    else:
        try:
            client.post('/cloud/project/{}/instance/{}/activeMonthlyBilling'.format(project_id, instance_id))
            module.exit_json(changed=True)
        except APIError as apiError:
            module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))

    # We should never reach here
    module.fail_json(msg='Internal ovh_monthly_billing module error')


# import module snippets
from ansible.module_utils.basic import *

main()
